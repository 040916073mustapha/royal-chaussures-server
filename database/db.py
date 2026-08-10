"""
Royal Chaussures — Unified Database Module
===========================================
قاعدة بيانات موحدة للمحل الفيزيائي و المتجر الإلكتروني
تستخدم SQLite — قابلة للترقية إلى PostgreSQL لاحقاً
"""

import sqlite3
import os
import json
import threading
from datetime import datetime

# موقع قاعدة البيانات (نفس مسار server.py)
DB_PATH = os.environ.get("STORE_DB_PATH", 
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "royal_store.db"))

# Thread-local connections for Flask (thread-safe)
_local = threading.local()


def get_db():
    """الحصول على اتصال بقاعدة البيانات (لكل thread connection منفصل)"""
    if not hasattr(_local, "connection") or _local.connection is None:
        _local.connection = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
        _local.connection.execute("PRAGMA journal_mode=WAL")
        _local.connection.execute("PRAGMA busy_timeout=10000")
        _local.connection.execute("PRAGMA synchronous=NORMAL")
        _local.connection.execute("PRAGMA foreign_keys=ON")
        _local.connection.execute("PRAGMA cache_size=-8000")
    return _local.connection


def close_db():
    """إغلاق الاتصال (ينادى عند نهاية الطلب)"""
    if hasattr(_local, "connection") and _local.connection is not None:
        try:
            _local.connection.commit()
            _local.connection.close()
        except:
            pass
        _local.connection = None


def init_db():
    """تهيئة قاعدة البيانات — إنشاء الجداول من schema.sql"""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        db.executescript(schema_sql)
        db.commit()
        print(f"[DB] Database initialized")
        print(f"[DB] Path: {DB_PATH}")
    else:
        print(f"[DB] Schema file not found at {schema_path}")
    
    # إنشاء مستخدم افتراضي للمحل إن لم يكن موجود
    _seed_default_users(db)


def _seed_default_users(db):
    """إنشاء المستخدمين الافتراضيين عند التشغيل الأول"""
    from werkzeug.security import generate_password_hash
    
    # Super Admin (مصطفى)
    admin_exists = db.execute("SELECT id FROM users WHERE username = ?", ["admin"]).fetchone()
    if not admin_exists:
        db.execute(
            "INSERT INTO users (username, password_hash, role, display_name, permissions) VALUES (?, ?, ?, ?, ?)",
            [
                "admin",
                generate_password_hash("rc-admin-2026"),  # سيتم تغييرها لاحقاً
                "admin",
                "مصطفى (مدير)",
                json.dumps(["admin:*", "store:*", "shared:*"])
            ]
        )
        print("[DB] Default admin user created")
    
    # Store Manager (أخوك)
    store_exists = db.execute("SELECT id FROM users WHERE username = ?", ["store"]).fetchone()
    if not store_exists:
        db.execute(
            "INSERT INTO users (username, password_hash, role, store_id, display_name, permissions) VALUES (?, ?, ?, ?, ?, ?)",
            [
                "store",
                generate_password_hash("rc-store-2026"),  # سيتم تغييرها لاحقاً
                "store_manager",
                1,
                "مدير المحل",
                json.dumps([
                    "store:products:*",
                    "store:sales:*",
                    "store:inventory:*",
                    "store:customers:*",
                    "store:print:*",
                    "store:expenses:*",
                    "shared:products:read",
                    "shared:inventory:read"
                ])
            ]
        )
        print("[DB] Default store manager user created")
    
    db.commit()


def dict_from_row(row):
    """تحويل sqlite3.Row إلى dict"""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows):
    """تحويل قائمة sqlite3.Row إلى قائمة dict"""
    return [dict(row) for row in rows]


# ============================================================
# Product Operations
# ============================================================

def get_products(active_only=True, limit=200, offset=0):
    """جلب قائمة المنتجات"""
    db = get_db()
    query = "SELECT * FROM products"
    params = []
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return dicts_from_rows(db.execute(query, params).fetchall())


def get_product(product_id):
    """جلب منتج حسب ID"""
    db = get_db()
    return dict_from_row(db.execute("SELECT * FROM products WHERE id = ?", [product_id]).fetchone())


def get_product_by_sku(sku):
    """جلب منتج حسب SKU"""
    db = get_db()
    return dict_from_row(db.execute("SELECT * FROM products WHERE sku = ?", [sku]).fetchone())


def get_product_by_barcode(barcode):
    """جلب منتج حسب الباركود"""
    db = get_db()
    return dict_from_row(db.execute("SELECT * FROM products WHERE barcode = ?", [barcode]).fetchone())


def create_product(data):
    """إنشاء منتج جديد"""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO products (sku, name, description, category, color, size,
                              cost_price, online_price, store_price,
                              supplier, barcode, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        data.get("sku"), data.get("name"), data.get("description", ""),
        data.get("category", ""), data.get("color", ""), data.get("size", ""),
        data.get("cost_price", 0), data.get("online_price", 0), data.get("store_price", 0),
        data.get("supplier", ""), data.get("barcode"), data.get("image_url", "")
    ])
    product_id = cursor.lastrowid
    
    # إنشاء سجل مخزون للمنتج الجديد
    db.execute("INSERT INTO inventory (product_id) VALUES (?)", [product_id])
    db.commit()
    
    _log_sync("product", product_id, "create", "store")
    
    return get_product(product_id)


def update_product(product_id, data):
    """تحديث منتج"""
    db = get_db()
    allowed_fields = ["name", "description", "category", "color", "size",
                      "cost_price", "online_price", "store_price",
                      "supplier", "barcode", "image_url", "is_active"]
    
    updates = []
    params = []
    for field in allowed_fields:
        if field in data:
            updates.append(f"{field} = ?")
            params.append(data[field])
    
    if not updates:
        return get_product(product_id)
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(product_id)
    
    db.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    
    _log_sync("product", product_id, "update", "store")
    
    return get_product(product_id)


def search_products(query, limit=50):
    """البحث في المنتجات حسب الاسم أو SKU أو الباركود"""
    db = get_db()
    like_query = f"%{query}%"
    rows = db.execute("""
        SELECT * FROM products 
        WHERE (name LIKE ? OR sku LIKE ? OR barcode LIKE ? OR category LIKE ?)
        AND is_active = 1
        ORDER BY name ASC LIMIT ?
    """, [like_query, like_query, like_query, like_query, limit]).fetchall()
    return dicts_from_rows(rows)


# ============================================================
# Inventory Operations
# ============================================================

def get_inventory(product_id=None):
    """جلب المخزون — لكل المنتجات أو منتج معين"""
    db = get_db()
    if product_id:
        row = db.execute("""
            SELECT i.*, p.name, p.sku, p.barcode
            FROM inventory i
            JOIN products p ON p.id = i.product_id
            WHERE i.product_id = ?
        """, [product_id]).fetchone()
        return dict_from_row(row)
    
    rows = db.execute("""
        SELECT i.*, p.name, p.sku, p.barcode
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        ORDER BY p.name ASC
    """).fetchall()
    return dicts_from_rows(rows)


def update_inventory(product_id, store_qty=None, online_qty=None, warehouse_qty=None):
    """تحديث كميات المخزون"""
    db = get_db()
    updates = []
    params = []
    
    if store_qty is not None:
        updates.append("store_quantity = ?")
        params.append(store_qty)
    if online_qty is not None:
        updates.append("online_quantity = ?")
        params.append(online_qty)
    if warehouse_qty is not None:
        updates.append("warehouse_quantity = ?")
        params.append(warehouse_qty)
    
    if not updates:
        return get_inventory(product_id)
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(product_id)
    
    db.execute(f"UPDATE inventory SET {', '.join(updates)} WHERE product_id = ?", params)
    db.commit()
    
    _log_sync("inventory", product_id, "update", "store")
    
    return get_inventory(product_id)


def deduct_store_inventory(product_id, quantity):
    """خصم كمية من مخزون المحل (عند البيع)"""
    db = get_db()
    current = db.execute(
        "SELECT store_quantity FROM inventory WHERE product_id = ?", [product_id]
    ).fetchone()
    
    if not current:
        return {"error": "Product not found in inventory"}
    
    new_qty = current["store_quantity"] - quantity
    if new_qty < 0:
        return {"error": f"Insufficient stock. Available: {current['store_quantity']}"}
    
    db.execute("UPDATE inventory SET store_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
               [new_qty, product_id])
    db.commit()
    
    _log_sync("inventory", product_id, "deduct", "store")
    
    return {"success": True, "new_quantity": new_qty}


def get_low_stock_items():
    """جلب المنتجات التي وصلت للحد الأدنى"""
    db = get_db()
    rows = db.execute("""
        SELECT i.*, p.name, p.sku, p.barcode
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        WHERE i.store_quantity <= i.low_stock_threshold
        OR i.online_quantity <= i.low_stock_threshold
        ORDER BY (i.store_quantity + i.online_quantity) ASC
    """).fetchall()
    return dicts_from_rows(rows)


# ============================================================
# Store Sales Operations
# ============================================================

def create_sale(data):
    """تسجيل عملية بيع في المحل مع خصم المخزون"""
    db = get_db()
    
    # خصم المخزون أولاً
    result = deduct_store_inventory(data["product_id"], data["quantity"])
    if "error" in result:
        return result
    
    product = get_product(data["product_id"])
    if not product:
        return {"error": "Product not found"}
    
    unit_price = data.get("unit_price", product["store_price"])
    quantity = data["quantity"]
    discount = data.get("discount", 0)
    total = (unit_price * quantity) - discount
    
    # توليد رقم فاتورة
    receipt = f"POS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{data['store_id']}"
    
    cursor = db.execute("""
        INSERT INTO store_sales (product_id, quantity, unit_price, total, discount,
                                 payment_method, notes, store_id, cashier,
                                 customer_phone, customer_name, receipt_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        data["product_id"], quantity, unit_price, total, discount,
        data.get("payment_method", "cash"), data.get("notes", ""),
        data["store_id"], data["cashier"],
        data.get("customer_phone", ""), data.get("customer_name", ""),
        receipt
    ])
    
    sale_id = cursor.lastrowid
    db.commit()
    
    _log_sync("sale", sale_id, "create", "store")
    
    return dict_from_row(db.execute("SELECT * FROM store_sales WHERE id = ?", [sale_id]).fetchone())


def get_store_sales(store_id=None, from_date=None, to_date=None, limit=100, offset=0):
    """جلب مبيعات المحل مع فلترة"""
    db = get_db()
    query = "SELECT ss.*, p.name as product_name, p.sku FROM store_sales ss JOIN products p ON p.id = ss.product_id WHERE 1=1"
    params = []
    
    if store_id:
        query += " AND ss.store_id = ?"
        params.append(store_id)
    if from_date:
        query += " AND ss.sale_date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND ss.sale_date <= ?"
        params.append(to_date)
    
    query += " ORDER BY ss.sale_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return dicts_from_rows(db.execute(query, params).fetchall())


def get_store_daily_summary(store_id, date_str=None):
    """ملخص يومي للمبيعات"""
    db = get_db()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    row = db.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(total) as total_revenue,
            SUM(discount) as total_discounts,
            SUM(quantity) as total_items
        FROM store_sales
        WHERE store_id = ? AND DATE(sale_date) = ?
    """, [store_id, date_str]).fetchone()
    
    return dict_from_row(row)


# ============================================================
# Expenses Operations
# ============================================================

def create_expense(data):
    """تسجيل مصروف في المحل"""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO store_expenses (category, amount, description, store_id, recorded_by)
        VALUES (?, ?, ?, ?, ?)
    """, [
        data["category"], data["amount"], data.get("description", ""),
        data["store_id"], data["recorded_by"]
    ])
    db.commit()
    return dict_from_row(db.execute("SELECT * FROM store_expenses WHERE id = ?", [cursor.lastrowid]).fetchone())


def get_expenses(store_id=None, from_date=None, to_date=None, limit=100):
    """جلب المصاريف"""
    db = get_db()
    query = "SELECT * FROM store_expenses WHERE 1=1"
    params = []
    
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    if from_date:
        query += " AND expense_date >= ?"
        params.append(from_date)
    if to_date:
        query += " AND expense_date <= ?"
        params.append(to_date)
    
    query += " ORDER BY expense_date DESC LIMIT ?"
    params.append(limit)
    
    return dicts_from_rows(db.execute(query, params).fetchall())


# ============================================================
# Online Orders Operations
# ============================================================

def get_online_orders(status=None, limit=50, offset=0):
    """جلب الطلبات الأونلاين"""
    db = get_db()
    query = "SELECT * FROM online_orders"
    params = []
    
    if status:
        query += " WHERE status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return dicts_from_rows(db.execute(query, params).fetchall())


def upsert_online_order(shopify_data):
    """إضافة أو تحديث طلب من Shopify"""
    db = get_db()
    existing = db.execute(
        "SELECT id FROM online_orders WHERE shopify_order_id = ?",
        [shopify_data["shopify_order_id"]]
    ).fetchone()
    
    if existing:
        # تحديث
        updates = []
        params = []
        for field in ["status", "payment_status", "shipping_status", "total", "notes"]:
            if field in shopify_data:
                updates.append(f"{field} = ?")
                params.append(shopify_data[field])
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(existing["id"])
            db.execute(f"UPDATE online_orders SET {', '.join(updates)} WHERE id = ?", params)
        
        db.commit()
        return dict_from_row(db.execute("SELECT * FROM online_orders WHERE id = ?", [existing["id"]]).fetchone())
    else:
        cursor = db.execute("""
            INSERT INTO online_orders (shopify_order_id, order_number, customer_name, customer_phone,
                                       customer_email, customer_address, wilaya, commune,
                                       total, subtotal, shipping_cost, discount, status,
                                       payment_status, shipping_status, items, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            shopify_data.get("shopify_order_id"),
            shopify_data.get("order_number"),
            shopify_data.get("customer_name", ""),
            shopify_data.get("customer_phone", ""),
            shopify_data.get("customer_email", ""),
            shopify_data.get("customer_address", ""),
            shopify_data.get("wilaya", ""),
            shopify_data.get("commune", ""),
            shopify_data.get("total", 0),
            shopify_data.get("subtotal", 0),
            shopify_data.get("shipping_cost", 0),
            shopify_data.get("discount", 0),
            shopify_data.get("status", "pending"),
            shopify_data.get("payment_status", "pending"),
            shopify_data.get("shipping_status", "pending"),
            json.dumps(shopify_data.get("items", [])),
            shopify_data.get("notes", "")
        ])
        db.commit()
        
        _log_sync("online_order", cursor.lastrowid, "create", "online")
        
        return dict_from_row(db.execute("SELECT * FROM online_orders WHERE id = ?", [cursor.lastrowid]).fetchone())


# ============================================================
# Dashboard / Reports
# ============================================================

def get_unified_dashboard():
    """إحصائيات موحدة للـ Super Admin Dashboard"""
    db = get_db()
    
    # إجمالي مبيعات اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    
    store_today = dict_from_row(db.execute("""
        SELECT COALESCE(SUM(total), 0) as total, COUNT(*) as count
        FROM store_sales WHERE DATE(sale_date) = ?
    """, [today]).fetchone())
    
    # آخر 10 مبيعات محل
    recent_store = dicts_from_rows(db.execute("""
        SELECT ss.*, p.name as product_name
        FROM store_sales ss
        JOIN products p ON p.id = ss.product_id
        ORDER BY ss.sale_date DESC LIMIT 10
    """).fetchall())
    
    # آخر 10 طلبات أونلاين
    recent_online = dicts_from_rows(db.execute("""
        SELECT * FROM online_orders
        ORDER BY created_at DESC LIMIT 10
    """).fetchall())
    
    # إجمالي المخزون
    inventory_summary = dict_from_row(db.execute("""
        SELECT 
            COUNT(*) as total_products,
            SUM(store_quantity) as total_store_stock,
            SUM(online_quantity) as total_online_stock
        FROM inventory
    """).fetchone())
    
    # المنتجات المنخفضة
    low_stock = len(get_low_stock_items())
    
    return {
        "store_today": store_today,
        "recent_store_sales": recent_store,
        "recent_online_orders": recent_online,
        "inventory_summary": inventory_summary,
        "low_stock_count": low_stock,
        "date": today
    }


# ============================================================
# Sync Log
# ============================================================

def _log_sync(entity_type, entity_id, action, source, details=None):
    """تسجيل عملية في سجل التزامن"""
    db = get_db()
    db.execute("""
        INSERT INTO sync_log (entity_type, entity_id, action, source, details)
        VALUES (?, ?, ?, ?, ?)
    """, [entity_type, entity_id, action, source, json.dumps(details or {})])
    db.commit()
