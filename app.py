# satya ai/flask_app/app.py
import os
import uuid
import json
import pathlib
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# local imports - make sure these exist and export the expected names
from config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, OPENAI_API_KEY
from models import db, User, Check, CacheEntry
from utils.ocr_utils import ocr_from_path
from utils.video_utils import process_video_file
from utils.ai_utils import search_wikipedia_snippet, ask_llm_for_verdict, transcribe_audio_path
from utils.trusted_sources import collect_trusted_sources

# App factory / setup
BASE = os.path.dirname(__file__)
TEMPLATES = os.path.join(BASE, "templates")
STATIC = os.path.join(BASE, "static")

app = Flask(__name__, template_folder=TEMPLATES, static_folder=STATIC)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE, 'satya.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024  # 300MB limit

# ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# init DB & LoginManager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# jinja helper to parse stored JSON in templates
app.jinja_env.filters['loads'] = lambda s: json.loads(s or '{}')

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_first_request
def create_tables():
    db.create_all()

# ---- Auth routes ----
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        if not email or not password:
            flash("Email & password required")
            return redirect(url_for('signup'))
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("User already exists, please login")
            return redirect(url_for('login'))
        u = User(email=email, name=name or "", roles="user")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash("Account created")
        return redirect(url_for('home'))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid credentials")
            return redirect(url_for('login'))
        login_user(user)
        flash("Logged in")
        return redirect(url_for('home'))
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out")
    return redirect(url_for('home'))

# ---- Home / analyze ----
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    """
    Accepts form fields:
      - type: text | url | image | audio | video
      - text: text content (if type == text)
      - url: article URL (if type == url)
      - file: uploaded file (if type in image/audio/video)
    Returns results page with structured JSON.
    """
    typ = request.form.get("type")
    text = request.form.get("text") or ""
    url = request.form.get("url") or ""
    file = request.files.get("file")
    extracted_text = ""

    # process input
    if typ == "text":
        extracted_text = text
    elif typ == "url" and url:
        try:
            import requests, re
            r = requests.get(url, timeout=12)
            page_text = re.sub('<[^<]+?>', ' ', r.text)
            extracted_text = page_text[:20000]
        except Exception:
            extracted_text = ""
            flash("Failed to fetch URL content.")
    elif file and allowed_file(file.filename):
        safe = secure_filename(file.filename)
        save_name = f"{uuid.uuid4().hex}_{safe}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
        try:
            file.save(save_path)
        except Exception:
            flash("Failed to save uploaded file.")
            return redirect(url_for("home"))

        ext = safe.rsplit(".", 1)[1].lower()
        try:
            if ext in ["png", "jpg", "jpeg", "gif"]:
                extracted_text = ocr_from_path(save_path)
            elif ext in ["mp3", "wav"]:
                extracted_text = transcribe_audio_path(save_path)
            elif ext in ["mp4", "mov", "mkv", "webm"]:
                info = process_video_file(save_path)
                extracted_text = (info.get("audio_text", "") + "\n\n" + info.get("frames_text", "")).strip()
            else:
                extracted_text = ""
        except Exception as e:
            extracted_text = ""
            flash("Failed to process uploaded file.")
        finally:
            # cleanup
            try:
                os.remove(save_path)
            except Exception:
                pass
    else:
        flash("Invalid request or missing file.")
        return redirect(url_for("home"))

    # Evidence collection
    # 1) small Wikipedia snippet search (quick)
    wiki_snip = None
    try:
        wiki_snip = search_wikipedia_snippet(extracted_text or url)
    except Exception:
        wiki_snip = None

    # 2) trusted sources aggregator (cached)
    trusted = {}
    try:
        trusted = collect_trusted_sources(extracted_text or url)
    except Exception:
        trusted = {}

    # Ask LLM (or fallback)
    try:
        verdict = ask_llm_for_verdict(extracted_text or url, trusted or {})
    except Exception:
        verdict = {"status": "unknown", "confidence": 40, "reasoning": "", "sources": [], "risk_score": 50}

    # Build result
    # sources: prefer verdict's sources, else include wiki_snip and trusted
    sources = verdict.get("sources") or []
    if not sources:
        if wiki_snip:
            sources = [wiki_snip]
        else:
            # take trusted source values (if dict)
            sources = [s for s in trusted.values() if s]

    result = {
        "status": verdict.get("status", "unknown"),
        "confidence": int(verdict.get("confidence", 40)),
        "reasoning": verdict.get("reasoning", ""),
        "sources": sources,
        "risk_score": int(verdict.get("risk_score", 50))
    }

    # Save history (truncate long text to fit DB field)
    try:
        chk = Check(
            user_id=current_user.id,
            input_type=typ,
            input_url=url,
            text_snippet=(extracted_text or "")[:4000],
            result_json=json.dumps(result)
        )
        db.session.add(chk)
        db.session.commit()
    except Exception:
        # don't break on DB failure; just warn
        app.logger.exception("Failed to save check to DB")

    return render_template("results.html", result=result)

# ---- User history ----
@app.route("/history")
@login_required
def history():
    checks = Check.query.filter_by(user_id=current_user.id).order_by(Check.created_at.desc()).limit(200).all()
    return render_template("history.html", checks=checks)

# ---- Admin panel ----
@app.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin():
        return "Forbidden", 403
    total = Check.query.count()
    fake = Check.query.filter(Check.result_json.like('%"status":"fake"%')).count()
    truec = Check.query.filter(Check.result_json.like('%"status":"true"%')).count()
    unknown = total - fake - truec
    return render_template("admin.html", total=total, fake=fake, true=truec, unknown=unknown)

# convenience route for logo if needed
@app.route("/static/logo.png")
def logo_redirect():
    return send_from_directory(os.path.join(app.root_path, "static"), "logo.png")

if __name__ == "__main__":
    # For production use a proper WSGI server; debug True is only for local dev.
    app.run(debug=True, port=5000)
