"""
SaaS Core — Auth API (Register / Login / JWT)
"""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, request, jsonify

import traceback as _tb
from ..config import Config
from ..database.models import User, get_session
import logging as _logging
_logger = _logging.getLogger("saas-core.auth")

auth_bp = Blueprint("auth", __name__)


# ─── Helpers ──────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """SHA-256 hash with salt"""
    salt = uuid.uuid4().hex[:16]
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash"""
    parts = stored.split("$")
    if len(parts) != 2:
        return False
    salt, expected = parts
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return h == expected


def create_token(user_id: str, email: str) -> str:
    """Create JWT token"""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify JWT and return payload"""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ─── Decorator ────────────────────────────────────────────────

def require_auth(f):
    """Decorator: require valid JWT in Authorization header"""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.current_user_id = payload["sub"]
        request.current_user_email = payload["email"]
        return f(*args, **kwargs)

    return decorated


# ─── Routes ───────────────────────────────────────────────────

@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    session = get_session()
    try:
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            plan="free",
        )
        session.add(user)
        session.commit()

        token = create_token(user.id, user.email)
        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "plan": user.plan,
            }
        }), 201

    except Exception as e:
        session.rollback()
        _logger.error(f"Register error: {_tb.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """Authenticate user and return JWT"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    session = get_session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid email or password"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is disabled"}), 403

        token = create_token(user.id, user.email)
        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "company": user.company,
                "plan": user.plan,
                "plan_status": user.plan_status,
            }
        })

    except Exception as e:
        _logger.error(f"Login error: {_tb.format_exc()}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@auth_bp.route("/api/auth/me", methods=["GET"])
@require_auth
def get_me():
    """Get current user profile"""
    session = get_session()
    try:
        user = session.query(User).filter_by(id=request.current_user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "company": user.company,
            "plan": user.plan,
            "plan_status": user.plan_status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    finally:
        session.close()
