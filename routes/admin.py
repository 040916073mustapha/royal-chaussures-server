"""
Royal Chaussures — Admin Dashboard API
======================================
مسارات API خاصة بـ Super Admin (مصطفى):
- إحصائيات موحدة
- إدارة المستخدمين
- مراقبة السيرفر و الـ APIs
- تقارير شاملة
"""

from flask import Blueprint, request, jsonify, g, render_template
from middleware.auth import admin_required, token_required, generate_token
from werkzeug.security import check_password_hash, generate_password_hash

import os
import json as json_module

from database.db import (
    get_db, dict_from_row, dicts_from_rows,
    get_unified_dashboard,
    get_products, get_store_sales, get_online_orders,
    get_low_stock_items
)

admin_bp = Blueprint("admin", __name__, template_folder="../templates")


# ============================================================
# 🖥️ Admin Dashboard - صفحة التحكم
# ============================================================

@admin_bp.route("/dashboard", methods=["GET"])
def admin_dashboard():
    """عرض واجهة الـ Admin Dashboard"""
    return render_template("dashboard/index.html")


# ============================================================
# 🔐 Auth
# ============================================================

@admin_bp.route("/auth/login", methods=["POST"])
def admin_login():
    """تسجيل دخول Super Admin"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    db = get_db()
    user = dict_from_row(db.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1 AND role = 'admin'",
        [username]
    ).fetchone())
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    permissions = json_module.loads(user["permissions"]) if isinstance(user["permissions"], str) else user["permissions"]
    
    token = generate_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        permissions=permissions
    )
    
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"]
        }
    })


# ============================================================
# 📊 Unified Dashboard
# ============================================================

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def unified_dashboard():
    """لوحة التحكم الموحدة — إحصائيات المحل + الأونلاين (مع دعم Multi-Tenant)"""
    store_id = request.headers.get("X-Store-ID", type=int) or None
    dashboard = get_unified_dashboard(store_id=store_id)
    return jsonify(dashboard)


# ============================================================
# 📦 Products (Admin View)
# ============================================================

@admin_bp.route("/products", methods=["GET"])
@admin_required
def all_products():
    """كل المنتجات (لـ Super Admin)"""
    active_only = request.args.get("active", "true").lower() == "true"
    limit = int(request.args.get("limit", 500))
    offset = int(request.args.get("offset", 0))
    
    products = get_products(active_only=active_only, limit=limit, offset=offset)
    
    # إضافة المخزون
    from database.db import get_inventory
    inventory = {inv["product_id"]: inv for inv in get_inventory()}
    for product in products:
        inv = inventory.get(product["id"], {})
        product["store_quantity"] = inv.get("store_quantity", 0)
        product["online_quantity"] = inv.get("online_quantity", 0)
        product["warehouse_quantity"] = inv.get("warehouse_quantity", 0)
    
    return jsonify({"products": products, "count": len(products)})


# ============================================================
# 📈 Sales Reports
# ============================================================

@admin_bp.route("/sales/store", methods=["GET"])
@admin_required
def store_sales_report():
    """مبيعات المحل (جميع المتاجر)"""
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    limit = int(request.args.get("limit", 200))
    offset = int(request.args.get("offset", 0))
    
    sales = get_store_sales(
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset
    )
    
    # إجمالي
    total = sum(s["total"] for s in sales)
    
    return jsonify({
        "sales": sales,
        "count": len(sales),
        "total_revenue": total
    })


@admin_bp.route("/sales/online", methods=["GET"])
@admin_required
def online_orders_report():
    """الطلبات الأونلاين"""
    status = request.args.get("status")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    
    orders = get_online_orders(status=status, limit=limit, offset=offset)
    
    return jsonify({
        "orders": orders,
        "count": len(orders)
    })


# ============================================================
# 👥 Users Management
# ============================================================

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """عرض المستخدمين"""
    db = get_db()
    users = dicts_from_rows(db.execute(
        "SELECT id, username, role, store_id, display_name, is_active, created_at FROM users ORDER BY role, username"
    ).fetchall())
    
    return jsonify({"users": users, "count": len(users)})


@admin_bp.route("/users", methods=["POST"])
@admin_required
def create_user():
    """إنشاء مستخدم جديد"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    required = ["username", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    db = get_db()
    
    # التحقق من عدم التكرار
    existing = db.execute("SELECT id FROM users WHERE username = ?", [data["username"]]).fetchone()
    if existing:
        return jsonify({"error": "Username already exists"}), 409
    
    role = data.get("role", "store_manager")
    if role not in ["admin", "store_manager"]:
        return jsonify({"error": "Role must be 'admin' or 'store_manager'"}), 400
    
    permissions = json_module.dumps(data.get("permissions", []))
    
    db.execute("""
        INSERT INTO users (username, password_hash, role, store_id, display_name, permissions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        data["username"],
        generate_password_hash(data["password"]),
        role,
        data.get("store_id"),
        data.get("display_name", ""),
        permissions
    ])
    db.commit()
    
    return jsonify({"message": "User created"}), 201


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    """تحديث مستخدم"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    db = get_db()
    updates = []
    params = []
    
    if "password" in data:
        updates.append("password_hash = ?")
        params.append(generate_password_hash(data["password"]))
    if "display_name" in data:
        updates.append("display_name = ?")
        params.append(data["display_name"])
    if "is_active" in data:
        updates.append("is_active = ?")
        params.append(1 if data["is_active"] else 0)
    if "permissions" in data:
        updates.append("permissions = ?")
        params.append(json_module.dumps(data["permissions"]))
    if "store_id" in data:
        updates.append("store_id = ?")
        params.append(data["store_id"])
    
    if not updates:
        return jsonify({"error": "No fields to update"}), 400
    
    params.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    
    return jsonify({"message": "User updated"})


# ============================================================
# 🖥️ System Health
# ============================================================

@admin_bp.route("/system/health", methods=["GET"])
@admin_required
def system_health():
    """حالة النظام و الخدمات المتصلة"""
    db = get_db()
    
    # إحصائيات قاعدة البيانات
    db_stats = dict_from_row(db.execute("""
        SELECT 
            (SELECT COUNT(*) FROM products) as total_products,
            (SELECT COUNT(*) FROM store_sales) as total_store_sales,
            (SELECT COUNT(*) FROM online_orders) as total_online_orders,
            (SELECT COUNT(*) FROM users) as total_users
    """).fetchone())
    
    # حجم قاعدة البيانات
    db_path = os.environ.get("STORE_DB_PATH", "royal_store.db")
    db_size = 0
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
    
    return jsonify({
        "status": "healthy",
        "database": {
            "stats": db_stats,
            "size_bytes": db_size,
            "size_mb": round(db_size / (1024 * 1024), 2)
        },
        "environment": {
            "python": os.environ.get("PYTHON_VERSION", "unknown"),
            "platform": os.environ.get("RENDER", "local") if os.environ.get("RENDER") else "local"
        }
    })


@admin_bp.route("/system/env", methods=["GET"])
@admin_required
def system_env():
    """عرض متغيرات البيئة (بدون القيم الحساسة)"""
    safe_vars = {}
    sensitive_keys = ["TOKEN", "SECRET", "PASSWORD", "KEY", "ACCESS"]
    
    for key in sorted(os.environ.keys()):
        # نظهر فقط المتغيرات غير الحساسة
        if not any(s in key.upper() for s in sensitive_keys):
            safe_vars[key] = os.environ[key]
    
    return jsonify({
        "variables": safe_vars,
        "sensitive_hidden": len([k for k in os.environ if any(s in k.upper() for s in sensitive_keys)])
    })


# ============================================================
# 📋 Reports & Exports
# ============================================================

@admin_bp.route("/reports/low-stock", methods=["GET"])
@admin_required
def low_stock_report():
    """تقرير المنتجات المنخفضة المخزون"""
    items = get_low_stock_items()
    return jsonify({"items": items, "count": len(items)})


@admin_bp.route("/reports/profit", methods=["GET"])
@admin_required
def profit_report():
    """تقرير الأرباح (مبيعات - تكاليف)"""
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    
    db = get_db()
    
    # إجمالي مبيعات المحل
    sales_query = "SELECT COALESCE(SUM(total), 0) as total, COALESCE(SUM(quantity), 0) as items FROM store_sales WHERE 1=1"
    sales_params = []
    if from_date:
        sales_query += " AND sale_date >= ?"
        sales_params.append(from_date)
    if to_date:
        sales_query += " AND sale_date <= ?"
        sales_params.append(to_date)
    
    sales_total = dict_from_row(db.execute(sales_query, sales_params).fetchone())
    
    # إجمالي المصاريف
    exp_query = "SELECT COALESCE(SUM(amount), 0) as total FROM store_expenses WHERE 1=1"
    exp_params = []
    if from_date:
        exp_query += " AND expense_date >= ?"
        exp_params.append(from_date)
    if to_date:
        exp_query += " AND expense_date <= ?"
        exp_params.append(to_date)
    
    expenses_total = dict_from_row(db.execute(exp_query, exp_params).fetchone())
    
    revenue = sales_total["total"] or 0
    expenses = expenses_total["total"] or 0
    profit = revenue - expenses
    
    return jsonify({
        "period": {
            "from": from_date or "all",
            "to": to_date or "all"
        },
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit,
        "profit_margin": round((profit / revenue * 100), 2) if revenue > 0 else 0,
        "items_sold": sales_total["items"] or 0
    })


# ============================================================
# 📱 API Status (Shopify, ZR Express, etc.)
# ============================================================

@admin_bp.route("/integrations", methods=["GET"])
@admin_required
def integration_status():
    """حالة التكاملات الخارجية"""
    
    # Shopify
    shopify_configured = bool(os.environ.get("SHOPIFY_CATALOG_TOKEN"))
    
    # Facebook/Instagram
    fb_token = os.environ.get("FACEBOOK_ACCESS_TOKEN", "")
    fb_page_id = os.environ.get("FACEBOOK_PAGE_ID", "")
    fb_configured = bool(fb_token and fb_page_id)
    
    # WhatsApp
    wa_token = os.environ.get("WHATSAPP_TOKEN", "")
    wa_phone = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    wa_configured = bool(wa_token and wa_phone)
    
    return jsonify({
        "integrations": {
            "shopify": {
                "configured": shopify_configured,
                "token_present": bool(os.environ.get("SHOPIFY_CATALOG_TOKEN")),
                "orders_token_present": bool(os.environ.get("SHOPIFY_ORDERS_TOKEN"))
            },
            "facebook": {
                "configured": fb_configured,
                "page_id": fb_page_id[:10] + "..." if fb_page_id else None
            },
            "whatsapp": {
                "configured": wa_configured,
                "phone_id": wa_phone[:10] + "..." if wa_phone else None
            },
            "zr_express": {
                "configured": bool(os.environ.get("ZR_EXPRESS_API_KEY"))
            },
            "ai": {
                "model": os.environ.get("AI_MODEL", "not configured"),
                "configured": bool(os.environ.get("AI_MODEL"))
            }
        }
    })
