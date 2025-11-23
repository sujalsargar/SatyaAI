# satya ai/flask_app/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    password_hash = db.Column(db.String(255), nullable=False)
    roles = db.Column(db.String(255), default="user")  # 'admin,editor' comma-separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def is_admin(self):
        return "admin" in (self.roles or "").split(",")

    # For Flask-Login compatibility
    def get_id(self):
        return str(self.id)

class Check(db.Model):
    __tablename__ = "checks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    input_type = db.Column(db.String(32))
    input_url = db.Column(db.String(2000))
    text_snippet = db.Column(db.Text)
    result_json = db.Column(db.Text)  # store JSON as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CacheEntry(db.Model):
    __tablename__ = "cache"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(500), unique=True, nullable=False)
    value = db.Column(db.Text)  # store JSON/text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
