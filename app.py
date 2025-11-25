# satya ai/flask_app/app.py
import os
import uuid
import json
import pathlib

from dotenv import load_dotenv
load_dotenv()  # ✅ Load environment variables first

from flask import (
    Flask, render_template, request, redirect,
    url_for, send_from_directory, flash
)
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

# Local imports
from config import SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, OPENAI_API_KEY
from models import db, User, Check, CacheEntry
from utils.ocr_utils import ocr_from_path
from utils.video_utils import process_video_file
from utils.ai_utils import (
    search_wikipedia_snippet, ask_llm_for_verdict,
    transcribe_audio_path
)
from utils.trusted_sources import collect_trusted_sources


# ----------------------------
# ✅ Folder setup
# ----------------------------
BASE = os.path.dirname(__file__)
TEMPLATES = os.path.join(BASE, "templates")
STATIC = os.path.join(BASE, "static")

app = Flask(__name__, template_folder=TEMPLATES, static_folder=STATIC)

# ----------------------------
# ✅ Flask Configuration
# ----------------------------
app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE, 'satya.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300MB upload limit

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ----------------------------
# ✅ DB + Login Init
# ----------------------------
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# enable json.loads inside templates
app.jinja_env.filters['loads'] = lambda s: json.loads(s or '{}')


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None


# ✅ Create tables if not exist
with app.app_context():
    db.create_all()


# ----------------------------
# ✅ Helpers
# ----------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------
# ✅ Routes
# ----------------------------

@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        if not email or not password:
            flash("Email & password required")
            return redirect(url_for("signup"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("User already exists, please login")
            return redirect(url_for("login"))

        u = User(email=email, name=name or "", roles="user")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        login_user(u)
        flash("Account created!")
        return redirect(url_for("home"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password")
            return redirect(url_for("login"))

        login_user(user)
        flash("Logged in successfully")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out")
    return redirect(url_for("home"))


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/try-demo")
def try_demo():
    return redirect(url_for("home") + '#verify')


@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("history"))


@app.route("/verify")
@login_required
def verify():
    return render_template("verify.html")


# ✅ Analyze input
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():

    typ = request.form.get("type")
    text = request.form.get("text") or ""
    url = request.form.get("url") or ""
    file = request.files.get("file")
    extracted_text = ""

    # --- TEXT ---
    if typ == "text":
        extracted_text = text

    # --- URL ---
    elif typ == "url" and url:
        try:
            import requests, re
            r = requests.get(url, timeout=12)
            page_text = re.sub('<[^<]+?>', ' ', r.text)
            extracted_text = page_text[:20000]
        except:
            flash("Could not fetch URL content.")
            extracted_text = ""

    # --- FILE ---
    elif file and allowed_file(file.filename):
        safe = secure_filename(file.filename)
        save_name = f"{uuid.uuid4().hex}_{safe}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], save_name)

        try:
            file.save(save_path)
        except:
            flash("Failed to save file.")
            return redirect(url_for("verify"))

        ext = safe.rsplit(".", 1)[1].lower()

        try:
            if ext in ["png", "jpg", "jpeg", "gif"]:
                extracted_text = ocr_from_path(save_path)

            elif ext in ["mp3", "wav"]:
                extracted_text = transcribe_audio_path(save_path)

            elif ext in ["mp4", "mov", "mkv", "webm"]:
                info = process_video_file(save_path)
                extracted_text = (
                    info.get("audio_text", "")
                    + "\n\n"
                    + info.get("frames_text", "")
                ).strip()
        except:
            flash("Failed to process uploaded file.")
            extracted_text = ""
        finally:
            try:
                os.remove(save_path)
            except:
                pass

    else:
        flash("Invalid request — missing text, link, or file.")
        return redirect(url_for("verify"))

    # -------------------------
    # ✅ AI processing
    # -------------------------
    try:
        wiki_snip = search_wikipedia_snippet(extracted_text or url)
    except:
        wiki_snip = None

    try:
        trusted = collect_trusted_sources(extracted_text or url)
    except:
        trusted = {}

    try:
        verdict = ask_llm_for_verdict(extracted_text or url, trusted or {})
    except:
        verdict = {
            "status": "unknown",
            "confidence": 40,
            "reasoning": "",
            "sources": [],
            "risk_score": 50,
        }

    sources = verdict.get("sources") or []
    if not sources:
        if wiki_snip:
            sources = [wiki_snip]
        else:
            sources = list(trusted.values())

    result = {
        "status": verdict.get("status", "unknown"),
        "confidence": int(verdict.get("confidence", 40)),
        "reasoning": verdict.get("reasoning", ""),
        "sources": sources,
        "risk_score": int(verdict.get("risk_score", 50)),
    }

    # ✅ Save to DB
    chk = Check(
        user_id=current_user.id,
        input_type=typ,
        input_url=url,
        text_snippet=(extracted_text or "")[:4000],
        result_json=json.dumps(result),
    )
    db.session.add(chk)
    db.session.commit()

    # ✅ Redirect to stored result instead of rendering
    return redirect(url_for("results", check_id=chk.id))


# ✅ View saved result
@app.route("/results/<int:check_id>")
@login_required
def results(check_id):
    check = Check.query.filter_by(id=check_id, user_id=current_user.id).first_or_404()

    try:
        result = json.loads(check.result_json)
    except:
        result = {
            "status": "unknown",
            "confidence": 0,
            "reasoning": "",
            "sources": [],
            "risk_score": 0,
        }

    return render_template("results.html", result=result)


# ✅ Full history page
@app.route("/history")
@login_required
def history():
    checks = (
        Check.query.filter_by(user_id=current_user.id)
        .order_by(Check.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template("history.html", checks=checks)


# ✅ Admin stats
@app.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin():
        return "Forbidden", 403

    total = Check.query.count()
    fake = Check.query.filter(Check.result_json.like('%"status":"fake"%')).count()
    truec = Check.query.filter(Check.result_json.like('%"status":"true"%')).count()
    unknown = total - fake - truec

    return render_template(
        "admin.html",
        total=total,
        fake=fake,
        true=truec,
        unknown=unknown
    )


@app.route("/static/logo.png")
def serve_logo():
    return send_from_directory(os.path.join(app.root_path, "static"), "logo.png")


# ----------------------------
# ✅ Run App
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
