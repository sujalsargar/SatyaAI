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

<<<<<<< HEAD
# App factory / setup
=======
# -------------------------------------------------------------------
# App Setup
# -------------------------------------------------------------------

>>>>>>> 38dad19 (Clean commit)
BASE = os.path.dirname(__file__)
TEMPLATES = os.path.join(BASE, "templates")
STATIC = os.path.join(BASE, "static")

app = Flask(__name__, template_folder=TEMPLATES, static_folder=STATIC)
<<<<<<< HEAD
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

=======
app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE, 'satya.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300MB

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# -------------------------------------------------------------------
# Database + Login Manager
# -------------------------------------------------------------------

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Jinja filter for loading JSON from DB
app.jinja_env.filters['loads'] = lambda s: json.loads(s or '{}')


>>>>>>> 38dad19 (Clean commit)
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
<<<<<<< HEAD
    except Exception:
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_first_request
def create_tables():
    db.create_all()

# ---- Auth routes ----
=======
    except:
        return None


# -------------------------------------------------------------------
# Flask 2.3+ Compatible DB Initialization (NO before_first_request)
# -------------------------------------------------------------------

with app.app_context():
    db.create_all()


# -------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------

def allowed_file(filename):
    """Check if the uploaded file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------------

>>>>>>> 38dad19 (Clean commit)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
<<<<<<< HEAD
        if not email or not password:
            flash("Email & password required")
            return redirect(url_for('signup'))
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("User already exists, please login")
            return redirect(url_for('login'))
=======

        if not email or not password:
            flash("Email & password required")
            return redirect(url_for("signup"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("User already exists, please login")
            return redirect(url_for("login"))

>>>>>>> 38dad19 (Clean commit)
        u = User(email=email, name=name or "", roles="user")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
<<<<<<< HEAD
        login_user(u)
        flash("Account created")
        return redirect(url_for('home'))
    return render_template("signup.html")

=======

        login_user(u)
        flash("Account created!")
        return redirect(url_for("home"))

    return render_template("signup.html")


>>>>>>> 38dad19 (Clean commit)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
<<<<<<< HEAD
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid credentials")
            return redirect(url_for('login'))
        login_user(user)
        flash("Logged in")
        return redirect(url_for('home'))
    return render_template("login.html")

=======

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password")
            return redirect(url_for("login"))

        login_user(user)
        flash("Logged in successfully")
        return redirect(url_for("home"))

    return render_template("login.html")


>>>>>>> 38dad19 (Clean commit)
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out")
<<<<<<< HEAD
    return redirect(url_for('home'))

# ---- Home / analyze ----
@app.route("/")
def home():
    return render_template("home.html")
=======
    return redirect(url_for("home"))


# -------------------------------------------------------------------
# Home & Public Pages
# -------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("landing.html")


# new public routes
@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")

@app.route("/verify")
@login_required
def verify():
    return render_template("verify.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/try-demo")
def try_demo():
    # redirect to the verification section on the home page
    return redirect(url_for('home') + '#verify')


@app.route("/dashboard")
@login_required
def dashboard():
    # show dashboard view (could reuse history.html for now)
    return render_template("history.html")


# -------------------------------------------------------------------
# Analysis Route
# -------------------------------------------------------------------
>>>>>>> 38dad19 (Clean commit)

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
<<<<<<< HEAD
    """
    Accepts form fields:
      - type: text | url | image | audio | video
      - text: text content (if type == text)
      - url: article URL (if type == url)
      - file: uploaded file (if type in image/audio/video)
    Returns results page with structured JSON.
    """
=======
>>>>>>> 38dad19 (Clean commit)
    typ = request.form.get("type")
    text = request.form.get("text") or ""
    url = request.form.get("url") or ""
    file = request.files.get("file")
    extracted_text = ""

<<<<<<< HEAD
    # process input
    if typ == "text":
        extracted_text = text
=======
    # ----------------------------------------------------
    # TEXT
    # ----------------------------------------------------
    if typ == "text":
        extracted_text = text

    # ----------------------------------------------------
    # URL
    # ----------------------------------------------------
>>>>>>> 38dad19 (Clean commit)
    elif typ == "url" and url:
        try:
            import requests, re
            r = requests.get(url, timeout=12)
            page_text = re.sub('<[^<]+?>', ' ', r.text)
            extracted_text = page_text[:20000]
<<<<<<< HEAD
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
=======
        except:
            flash("Could not fetch URL content.")
            extracted_text = ""

    # ----------------------------------------------------
    # FILE UPLOADS
    # ----------------------------------------------------
    elif file and allowed_file(file.filename):
        safe = secure_filename(file.filename)
        save_name = f"{uuid.uuid4().hex}_{safe}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], save_name)

        try:
            file.save(save_path)
        except:
            flash("Failed to save file.")
            return redirect(url_for("home"))

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

        except Exception:
            app.logger.exception("Error processing uploaded file")
            flash("Failed to process uploaded file.")
            extracted_text = ""

        finally:
>>>>>>> 38dad19 (Clean commit)
            try:
                os.remove(save_path)
            except Exception:
                pass
<<<<<<< HEAD
=======

>>>>>>> 38dad19 (Clean commit)
    else:
        flash("Invalid request or missing file.")
        return redirect(url_for("home"))

<<<<<<< HEAD
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
=======
    # ----------------------------------------------------
    # Evidence & Verdict
    # ----------------------------------------------------

    # Wikipedia snippet
    try:
        wiki_snip = search_wikipedia_snippet(extracted_text or url)
    except:
        wiki_snip = None

    # Trusted sources
    try:
        trusted = collect_trusted_sources(extracted_text or url)
    except:
        trusted = {}

    # AI verdict
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

    # Prepare result
>>>>>>> 38dad19 (Clean commit)
    sources = verdict.get("sources") or []
    if not sources:
        if wiki_snip:
            sources = [wiki_snip]
        else:
<<<<<<< HEAD
            # take trusted source values (if dict)
            sources = [s for s in trusted.values() if s]
=======
            sources = list(trusted.values())
>>>>>>> 38dad19 (Clean commit)

    result = {
        "status": verdict.get("status", "unknown"),
        "confidence": int(verdict.get("confidence", 40)),
        "reasoning": verdict.get("reasoning", ""),
        "sources": sources,
<<<<<<< HEAD
        "risk_score": int(verdict.get("risk_score", 50))
    }

    # Save history (truncate long text to fit DB field)
=======
        "risk_score": int(verdict.get("risk_score", 50)),
    }
    
    # Clean sources to avoid None items
    # Keep only dicts (structured sources). If you prefer to keep strings/urls,
    # change the filter accordingly.
    clean_sources = []
    for item in sources:
        if item is None:
            continue
        if isinstance(item, dict):
            clean_sources.append(item)
        else:
            # keep strings (urls or text) too
            clean_sources.append(item)
    sources = clean_sources
    result["sources"] = sources

    # Save to history
>>>>>>> 38dad19 (Clean commit)
    try:
        chk = Check(
            user_id=current_user.id,
            input_type=typ,
            input_url=url,
            text_snippet=(extracted_text or "")[:4000],
<<<<<<< HEAD
            result_json=json.dumps(result)
=======
            result_json=json.dumps(result),
>>>>>>> 38dad19 (Clean commit)
        )
        db.session.add(chk)
        db.session.commit()
    except Exception:
<<<<<<< HEAD
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
=======
        app.logger.exception("Failed to save user check.")

    return render_template("results.html", result=result)


# -------------------------------------------------------------------
# User History
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Admin Panel
# -------------------------------------------------------------------

>>>>>>> 38dad19 (Clean commit)
@app.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin():
        return "Forbidden", 403
<<<<<<< HEAD
=======

>>>>>>> 38dad19 (Clean commit)
    total = Check.query.count()
    fake = Check.query.filter(Check.result_json.like('%"status":"fake"%')).count()
    truec = Check.query.filter(Check.result_json.like('%"status":"true"%')).count()
    unknown = total - fake - truec
<<<<<<< HEAD
    return render_template("admin.html", total=total, fake=fake, true=truec, unknown=unknown)

# convenience route for logo if needed
@app.route("/static/logo.png")
def logo_redirect():
    return send_from_directory(os.path.join(app.root_path, "static"), "logo.png")

if __name__ == "__main__":
    # For production use a proper WSGI server; debug True is only for local dev.
=======

    return render_template(
        "admin.html",
        total=total,
        fake=fake,
        true=truec,
        unknown=unknown
    )

# view a saved check/result by id (keeps template url_for('results')?id=... working)
@app.route("/results")
@login_required
def results():
    # read id from querystring: /results?id=123
    check_id = request.args.get("id")
    if not check_id:
        flash("Missing result id.")
        return redirect(url_for("history"))

    try:
        check_id = int(check_id)
    except ValueError:
        flash("Invalid result id.")
        return redirect(url_for("history"))

    chk = Check.query.get(check_id)
    if not chk:
        flash("Result not found.")
        return redirect(url_for("history"))

    # Permission: owner or admin only
    try:
        owner_ok = (chk.user_id is None) or (chk.user_id == current_user.id)
    except Exception:
        owner_ok = False

    if not owner_ok and not current_user.is_admin():
        # don't reveal existence to non-admins
        return "Forbidden", 403

    # load the stored JSON result (defensive)
    try:
        result = json.loads(chk.result_json or "{}")
    except Exception:
        result = {
            "status": "unknown",
            "confidence": 0,
            "reasoning": "Failed to parse stored result.",
            "sources": [],
            "risk_score": 0,
        }

    # ensure fields exist so templates don't crash
    result = {
        "status": result.get("status", "unknown"),
        "confidence": int(result.get("confidence", 0) or 0),
        "reasoning": result.get("reasoning", "") or "",
        "sources": result.get("sources") or [],
        "risk_score": int(result.get("risk_score", 0) or 0),
    }

    return render_template("results.html", result=result)

@app.route("/result/<int:id>")
@login_required
def view_result(id):
    chk = Check.query.get(id)
    if not chk:
        flash("Result not found.")
        return redirect(url_for("history"))

    # Permission check: owner or admin
    try:
        owner_ok = (chk.user_id is None) or (chk.user_id == current_user.id)
    except:
        owner_ok = False

    if not owner_ok and not current_user.is_admin():
        return "Forbidden", 403

    # Parse stored JSON safely
    try:
        raw = json.loads(chk.result_json or "{}")
    except Exception:
        raw = {}

    result = {
        "status": raw.get("status", "unknown"),
        "confidence": int(raw.get("confidence", 0) or 0),
        "reasoning": raw.get("reasoning", "") or "",
        "sources": raw.get("sources") or [],
        "risk_score": int(raw.get("risk_score", 0) or 0),
    }

    return render_template("results.html", result=result)

# -------------------------------------------------------------------
# Logo Handler
# -------------------------------------------------------------------

@app.route("/static/logo.png")
def serve_logo():
    return send_from_directory(os.path.join(app.root_path, "static"), "logo.png")


# -------------------------------------------------------------------
# Run Application
# -------------------------------------------------------------------

if __name__ == "__main__":
>>>>>>> 38dad19 (Clean commit)
    app.run(debug=True, port=5000)
