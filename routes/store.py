"""
Royal Chaussures — Store POS API
================================
مسارات API خاصة بمدير المحل (أخوك):
- إدارة المنتجات و المخزون
- تسجيل المبيعات اليومية
- طباعة الباركود و الفواتير
- المصاريف
"""

from flask import Blueprint, request, jsonify, g, render_template
from database.db import (
    get_products, get_product, get_product_by_barcode, get_product_by_sku,
    create_product, update_product, search_products,
    get_inventory, update_inventory, deduct_store_inventory, get_low_stock_items,
    create_sale, get_store_sales, get_store_sale_items, get_store_daily_summary,
    create_expense, get_expenses,
    create_purchase_with_items, get_purchases, get_purchase_items,
    get_store_purchases, get_purchase_detail
)
from middleware.auth import store_manager_required, token_required, generate_token
from werkzeug.security import check_password_hash

import sqlite3
from database.db import get_db, dict_from_row

store_bp = Blueprint("store", __name__, template_folder="../templates", static_folder="../static")


# ============================================================
# 🏪 POS PWA - صفحة الكاشير
# ============================================================

@store_bp.route("/pos", methods=["GET"])
def pos_page():
    """عرض واجهة الـ POS PWA"""
    return render_template("pos/index.html")


# ============================================================
# 🔐 Auth
# ============================================================

@store_bp.route("/auth/login", methods=["POST"])
def login():
    """تسجيل دخول مدير المحل"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    db = get_db()
    user = dict_from_row(db.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        [username]
    ).fetchone())
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if user["role"] not in ["store_manager", "admin"]:
        return jsonify({"error": "Access denied"}), 403
    
    import json as json_module
    permissions = json_module.loads(user["permissions"]) if isinstance(user["permissions"], str) else user["permissions"]
    
    token = generate_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"],
        store_id=user.get("store_id"),
        permissions=permissions
    )
    
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
            "store_id": user["store_id"]
        }
    })


# ============================================================
# 👤 Profile
# ============================================================

@store_bp.route("/me", methods=["GET"])
@store_manager_required
def get_profile():
    """معلومات المستخدم الحالي"""
    return jsonify({
        "user": {
            "id": g.current_user["sub"],
            "username": g.current_user["username"],
            "role": g.current_user["role"],
            "store_id": g.current_user.get("store_id"),
            "permissions": g.current_user.get("permissions", [])
        }
    })


# ============================================================
# 📦 Products
# ============================================================

@store_bp.route("/products", methods=["GET"])
@store_manager_required
def list_products():
    """قائمة المنتجات"""
    active_only = request.args.get("active", "true").lower() == "true"
    limit = int(request.args.get("limit", 200))
    offset = int(request.args.get("offset", 0))
    
    products = get_products(active_only=active_only, limit=limit, offset=offset)
    
    # إضافة معلومات المخزون لكل منتج
    inventory = {inv["product_id"]: inv for inv in get_inventory()}
    for product in products:
        inv = inventory.get(product["id"], {})
        product["store_quantity"] = inv.get("store_quantity", 0)
        product["online_quantity"] = inv.get("online_quantity", 0)
        product["warehouse_quantity"] = inv.get("warehouse_quantity", 0)
    
    return jsonify({"products": products, "count": len(products)})


@store_bp.route("/products/search", methods=["GET"])
@store_manager_required
def search():
    """البحث في المنتجات"""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"products": [], "count": 0})
    
    limit = int(request.args.get("limit", 50))
    products = search_products(query, limit=limit)
    
    return jsonify({"products": products, "count": len(products)})


@store_bp.route("/products/barcode/<barcode>", methods=["GET"])
@store_manager_required
def get_by_barcode(barcode):
    """جلب منتج حسب الباركود (للكاشير)"""
    product = get_product_by_barcode(barcode)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    inv = get_inventory(product["id"])
    product["store_quantity"] = inv.get("store_quantity", 0) if inv else 0
    
    return jsonify({"product": product})


@store_bp.route("/products/<int:product_id>", methods=["GET"])
@store_manager_required
def get_single_product(product_id):
    """جلب منتج حسب ID"""
    product = get_product(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    inv = get_inventory(product_id)
    product["store_quantity"] = inv.get("store_quantity", 0) if inv else 0
    product["online_quantity"] = inv.get("online_quantity", 0) if inv else 0
    product["warehouse_quantity"] = inv.get("warehouse_quantity", 0) if inv else 0
    
    return jsonify({"product": product})


@store_bp.route("/products", methods=["POST"])
@store_manager_required
def add_product():
    """إضافة منتج جديد"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    required = ["name", "sku"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    # التحقق من عدم تكرار SKU
    existing = get_product_by_sku(data["sku"])
    if existing:
        return jsonify({"error": f"SKU '{data['sku']}' already exists"}), 409
    
    # التحقق من عدم تكرار الباركود
    barcode = data.get("barcode")
    if barcode:
        existing_barcode = get_product_by_barcode(barcode)
        if existing_barcode:
            return jsonify({"error": f"Barcode '{barcode}' already exists"}), 409
    
    product = create_product(data)
    
    # تحديث المخزون الابتدائي
    if "store_quantity" in data:
        update_inventory(product["id"], store_qty=data["store_quantity"])
    
    return jsonify({"product": product}), 201


@store_bp.route("/products/<int:product_id>", methods=["PUT"])
@store_manager_required
def edit_product(product_id):
    """تعديل منتج"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    product = update_product(product_id, data)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    # تحديث المخزون إذا وُجد
    if "store_quantity" in data:
        update_inventory(product_id, store_qty=data["store_quantity"])
        product = get_product(product_id)
        inv = get_inventory(product_id)
        product["store_quantity"] = inv.get("store_quantity", 0) if inv else 0
    
    return jsonify({"product": product})


@store_bp.route("/products/<int:product_id>", methods=["DELETE"])
@store_manager_required
def remove_product(product_id):
    """تعطيل منتج (soft delete)"""
    product = update_product(product_id, {"is_active": 0})
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify({"message": "Product disabled", "product": product})


# ============================================================
# 📊 Inventory
# ============================================================

@store_bp.route("/inventory", methods=["GET"])
@store_manager_required
def list_inventory():
    """عرض المخزون الكامل"""
    inventory = get_inventory()
    return jsonify({"inventory": inventory, "count": len(inventory)})


@store_bp.route("/inventory/low-stock", methods=["GET"])
@store_manager_required
def low_stock():
    """المنتجات المنخفضة المخزون"""
    items = get_low_stock_items()
    return jsonify({"items": items, "count": len(items)})


@store_bp.route("/inventory/<int:product_id>", methods=["PUT"])
@store_manager_required
def update_inv(product_id):
    """تحديث مخزون منتج"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    inv = update_inventory(
        product_id,
        store_qty=data.get("store_quantity"),
        online_qty=data.get("online_quantity"),
        warehouse_qty=data.get("warehouse_quantity")
    )
    
    return jsonify({"inventory": inv})


# ============================================================
# 💰 Sales (POS)
# ============================================================

@store_bp.route("/sales", methods=["POST"])
@store_manager_required
def record_sale():
    """تسجيل عملية بيع في المحل"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    required = ["product_id", "quantity"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    # تحديد store_id من المستخدم الحالي
    data["store_id"] = g.current_user.get("store_id") or 1
    data["cashier"] = g.current_user.get("username", "store")
    
    result = create_sale(data)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify({"sale": result}), 201


@store_bp.route("/sales/summary", methods=["GET"])
@store_manager_required
def daily_summary():
    """ملخص يومي"""
    store_id = g.current_user.get("store_id") or request.args.get("store_id", type=int)
    date_str = request.args.get("date")
    
    summary = get_store_daily_summary(store_id or 1, date_str)
    
    return jsonify({"summary": summary})


# ============================================================
# 💸 Expenses
# ============================================================

@store_bp.route("/expenses", methods=["POST"])
@store_manager_required
def add_expense():
    """تسجيل مصروف"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    required = ["category", "amount"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    data["store_id"] = g.current_user.get("store_id") or 1
    data["recorded_by"] = g.current_user.get("username", "store")
    
    expense = create_expense(data)
    
    return jsonify({"expense": expense}), 201


@store_bp.route("/expenses", methods=["GET"])
@store_manager_required
def list_expenses():
    """جلب المصاريف"""
    store_id = g.current_user.get("store_id") or request.args.get("store_id", type=int)
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    limit = int(request.args.get("limit", 100))
    
    expenses = get_expenses(
        store_id=store_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    
    return jsonify({"expenses": expenses, "count": len(expenses)})


# ============================================================
# 📦 Purchases (Nouvel achat — Tamin al-makhzoun)
# ============================================================

@store_bp.route("/purchases", methods=["POST"])
@store_manager_required
def record_purchase():
    """تسجيل فاتورة شراء + إنشاء/تحديث المنتجات + تموين المخزون"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    if "items" not in data or not data["items"]:
        return jsonify({"error": "Au moins un article est requis"}), 400
    
    data["store_id"] = g.current_user.get("store_id") or 1
    data["recorded_by"] = g.current_user.get("username", "store")
    
    result = create_purchase_with_items(data)
    
    return jsonify({"purchase": result["purchase"], "items": result["items"]}), 201


@store_bp.route("/purchases", methods=["GET"])
@store_manager_required
def list_purchases():
    """جلب فواتير الشراء"""
    store_id = g.current_user.get("store_id") or request.args.get("store_id", type=int)
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    
    purchases = get_purchases(store_id=store_id, limit=limit, offset=offset)
    return jsonify({"purchases": purchases, "count": len(purchases)})


@store_bp.route("/purchases/<int:purchase_id>/items", methods=["GET"])
@store_manager_required
def get_purchase_items_route(purchase_id):
    """جلب عناصر فاتورة شراء"""
    items = get_purchase_items(purchase_id)
    return jsonify({"items": items, "count": len(items)})


@store_bp.route("/products/barcode/generate", methods=["POST"])
@store_manager_required
def generate_barcode():
    """توليد باركود عشوائي"""
    import random
    import string
    # توليد باركود EAN-13 وهمي
    code = "2" + "".join(random.choices(string.digits, k=11))
    # حساب checksum بسيط
    total = sum(int(code[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
    check = (10 - (total % 10)) % 10
    barcode = code + str(check)
    
    return jsonify({"barcode": barcode})


@store_bp.route("/products/demo-data", methods=["GET"])
@store_manager_required
def generate_demo_data():
    """توليد بيانات وهمية للاختبار السريع"""
    import random
    articles = [
        {"designation": "lazio 01", "prix_achat": 2500, "prix_vente": 3500},
        {"designation": "lazio 02", "prix_achat": 2800, "prix_vente": 3900},
        {"designation": "nike air max", "prix_achat": 4500, "prix_vente": 6500},
        {"designation": "adidas superstar", "prix_achat": 3200, "prix_vente": 4800},
        {"designation": "puma rs-x", "prix_achat": 3600, "prix_vente": 5200},
        {"designation": "reebok classic", "prix_achat": 2100, "prix_vente": 3200},
        {"designation": "converse all star", "prix_achat": 1800, "prix_vente": 2800},
        {"designation": "vans old skool", "prix_achat": 2200, "prix_vente": 3400}
    ]
    
    # توليد باركود عشوائي لكل منتج
    result = []
    for art in articles:
        code = "2" + "".join(random.choices("0123456789", k=11))
        total = sum(int(code[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
        check = (10 - (total % 10)) % 10
        barcode = code + str(check)
        result.append({
            **art,
            "barcode": barcode,
            "marge_pct": round(((art["prix_vente"] - art["prix_achat"]) / art["prix_achat"]) * 100, 1),
            "marge_montant": art["prix_vente"] - art["prix_achat"]
        })
    
    return jsonify({"articles": result})


# ============================================================
# 📋 Sales List (Liste des ventes)
# ============================================================

@store_bp.route("/sales", methods=["GET"])
@store_manager_required
def list_sales():
    """جلب المبيعات مع فلترة"""
    store_id = g.current_user.get("store_id") or request.args.get("store_id", type=int)
    
    filters = {
        "store_id": store_id,
        "from_date": request.args.get("date_from"),
        "to_date": request.args.get("date_to"),
        "code": request.args.get("code"),
        "client": request.args.get("client"),
        "vendeur": request.args.get("vendeur"),
        "cancelled": request.args.get("cancelled") == "1",
        "credit": request.args.get("credit") == "1",
        "search": request.args.get("q"),
        "limit": int(request.args.get("limit", 500)),
        "offset": int(request.args.get("offset", 0))
    }
    
    sales = get_store_sales(**filters)
    return jsonify({"sales": sales, "count": len(sales)})


@store_bp.route("/sales/<int:sale_id>", methods=["GET"])
@store_manager_required
def get_sale_detail(sale_id):
    """جلب تفاصيل فاتورة + عناصرها"""
    items = get_store_sale_items(sale_id)
    
    # Get the sale header
    from database.db import get_db, dict_from_row
    db = get_db()
    sale = dict_from_row(db.execute("SELECT * FROM store_sales WHERE id = ?", [sale_id]).fetchone())
    
    if not sale:
        return jsonify({"error": "Vente introuvable"}), 404
    
    return jsonify({"sale": sale, "items": items, "count": len(items)})


# ============================================================
# 📋 Purchase List (Liste des achats)
# ============================================================

@store_bp.route("/purchases/list", methods=["GET"])
@store_manager_required
def list_purchases_route():
    """جلب المشتريات مع فلترة"""
    store_id = g.current_user.get("store_id") or request.args.get("store_id", type=int)
    
    filters = {
        "store_id": store_id,
        "from_date": request.args.get("date_from"),
        "to_date": request.args.get("date_to"),
        "code": request.args.get("code"),
        "fournisseur": request.args.get("fournisseur"),
        "nom": request.args.get("nom"),
        "cancelled": request.args.get("cancelled") == "1",
        "search": request.args.get("q"),
        "limit": int(request.args.get("limit", 500)),
        "offset": int(request.args.get("offset", 0))
    }
    
    purchases = get_store_purchases(**filters)
    return jsonify({"purchases": purchases, "count": len(purchases)})


@store_bp.route("/purchases/<int:purchase_id>/detail", methods=["GET"])
@store_manager_required
def get_purchase_detail_route(purchase_id):
    """جلب تفاصيل فاتورة شراء"""
    purchase = get_purchase_detail(purchase_id)
    if not purchase:
        return jsonify({"error": "Achat introuvable"}), 404
    return jsonify(purchase)


# ============================================================
# 🖨️ Print
# ============================================================

@store_bp.route("/print/receipt/<int:sale_id>", methods=["GET"])
@store_manager_required
def print_receipt(sale_id):
    """طباعة فاتورة (ترجع HTML للطباعة)"""
    from database.db import get_db, dict_from_row
    
    db = get_db()
    sale = dict_from_row(db.execute("""
        SELECT ss.*, p.name as product_name, p.sku
        FROM store_sales ss
        JOIN products p ON p.id = ss.product_id
        WHERE ss.id = ?
    """, [sale_id]).fetchone())
    
    if not sale:
        return jsonify({"error": "Sale not found"}), 404
    
    return jsonify({"receipt": sale})


@store_bp.route("/print/barcode/<int:product_id>", methods=["GET"])
@store_manager_required
def print_barcode(product_id):
    """طباعة باركود منتج"""
    product = get_product(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    qty = request.args.get("qty", 1, type=int)
    
    # تسجيل طباعة الباركود
    db = get_db()
    db.execute(
        "INSERT INTO barcode_print_log (product_id, quantity, printed_by) VALUES (?, ?, ?)",
        [product_id, qty, g.current_user.get("username", "store")]
    )
    db.commit()
    
    return jsonify({
        "product": product,
        "quantity": qty,
        "barcode": product.get("barcode"),
        "message": f"Barcode printed for {product['name']} x{qty}"
    })
