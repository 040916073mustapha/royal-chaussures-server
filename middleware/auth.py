"""
Royal Chaussures — JWT Auth Middleware
======================================
Role-Based Access Control للـ Store POS و Admin Dashboard
"""

import json
import os
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import request, jsonify, g

# JWT Secret — من Environment Variable أو قيمة افتراضية للتطوير
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "rc-store-pos-dev-secret-key-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


# ============================================================
# Permission Definitions
# ============================================================

# صلاحيات مدير المحل
STORE_PERMISSIONS = [
    "store:products:*",
    "store:sales:*",
    "store:inventory:*",
    "store:customers:*",
    "store:print:*",
    "store:expenses:*",
    "shared:products:read",
    "shared:inventory:read"
]

# صلاحيات Super Admin
ADMIN_PERMISSIONS = [
    "admin:*",
    "store:*",
    "shared:*"
]


# ============================================================
# Token Generation
# ============================================================

def generate_token(user_id, username, role, store_id=None, permissions=None):
    """توليد JWT Token"""
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "store_id": store_id,
        "permissions": permissions or [],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    """فك تشفير JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================================
# Permission Checker
# ============================================================

def has_permission(user_permissions, required_permission):
    """
    التحقق مما إذا كان المستخدم لديه صلاحية معينة
    يدعم wildcard: "store:products:*" يغطي "store:products:read"
    """
    for user_perm in user_permissions:
        if user_perm.endswith(":*"):
            # Wildcard: "store:products:*" matches "store:products:read", "store:products:write", etc.
            prefix = user_perm[:-2]  # Remove ":*"
            if required_permission.startswith(prefix):
                return True
        elif user_perm == required_permission:
            return True
    return False


# ============================================================
# Middleware Decorators
# ============================================================

def token_required(f):
    """يتأكد من وجود JWT Token صالح في الطلب"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # استخراج token من الـ Header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        # أو من الـ cookie (للواجهة)
        if not token:
            token = request.cookies.get("auth_token")
        
        if not token:
            return jsonify({"error": "Authentication required", "code": "AUTH_REQUIRED"}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token", "code": "TOKEN_INVALID"}), 401
        
        # تخزين معلومات المستخدم في الـ request context
        g.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated


def require_permission(permission):
    """يتأكد من أن المستخدم لديه صلاحية معينة (يستخدم بعد token_required)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "current_user"):
                return jsonify({"error": "Authentication required"}), 401
            
            user_permissions = g.current_user.get("permissions", [])
            
            # Admin يملك كل الصلاحيات
            if "admin:*" in user_permissions or "*" in user_permissions:
                return f(*args, **kwargs)
            
            if not has_permission(user_permissions, permission):
                return jsonify({
                    "error": "Insufficient permissions",
                    "code": "FORBIDDEN",
                    "required": permission
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def store_manager_required(f):
    """يتأكد من أن المستخدم هو مدير محل (اختصار)"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.get("role") not in ["store_manager", "admin"]:
            return jsonify({"error": "Store manager access required", "code": "STORE_ONLY"}), 403
        
        # تخزين store_id للاستخدام في الـ endpoint
        g.store_id = g.current_user.get("store_id")
        if not g.store_id and g.current_user.get("role") == "admin":
            g.store_id = None  # Admin يرى كل المتاجر
        
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """يتأكد من أن المستخدم هو Super Admin (اختصار)"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required", "code": "ADMIN_ONLY"}), 403
        return f(*args, **kwargs)
    return decorated
