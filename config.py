import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_secret_for_dev")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # optional
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp3", "wav", "mp4", "mov", "mkv", "webm"}
