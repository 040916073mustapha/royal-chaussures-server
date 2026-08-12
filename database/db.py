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
    global DB_PATH
    if not hasattr(_local, "connection") or _local.connection is None:
        _local.connection = _connect_or_repair(DB_PATH)
    return _local.connection


def _connect_or_repair(db_path):
    """محاولة الاتصال بقاعدة البيانات — لا تمسح الملف أبداً"""
    import time as _time
    
    for attempt in range(5):
        try:
            conn = sqlite3.connect(db_path, timeout=60, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA cache_size=-8000")
            # اختبار بسيط
            conn.execute("SELECT 1")
            # إذا كانت قاعدة البيانات جديدة (بدون جداول)، أنشئها
            try:
                conn.execute("SELECT count(*) FROM users").fetchone()
            except sqlite3.OperationalError:
                print("[DB] Fresh database detected, initializing tables...")
                _init_tables(conn)
            return conn
        except sqlite3.DatabaseError as e:
            print(f"[DB] Database error (attempt {attempt+1}/5): {e}")
            try:
                conn.close()
            except:
                pass
            _time.sleep(1.0 * (attempt + 1))
    
    # بعد 5 محاولات — أرمي استثناء، لا تمسح الـ DB
    raise RuntimeError(f"Cannot connect to database after 5 attempts: {db_path}")


def _check_and_remove_corrupted(db_path):
    """معطل — لا تمسح قاعدة البيانات أبداً في الإنتاج"""
    # لم نعد نحذف قاعدة البيانات. WAL mode + busy_timeout كافيان للتعامل مع التنافس.
    pass


def close_db():
    """إغلاق الاتصال (ينادى عند نهاية الطلب)"""
    if hasattr(_local, "connection") and _local.connection is not None:
        try:
            _local.connection.commit()
            _local.connection.close()
        except:
            pass
        _local.connection = None


def _init_tables(db):
    """إنشاء الجداول من schema.sql (داخلي)"""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        try:
            db.executescript(schema_sql)
            db.commit()
        except Exception as e:
            print(f"[DB] Schema execution error: {e}")
    _seed_default_users(db)


def init_db():
    """تهيئة قاعدة البيانات — إنشاء الجداول من schema.sql (آمن، اتصال منفصل)"""
    try:
        # نستخدم اتصالاً منفصلاً لا يعتمد على _local
        conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-8000")
        # إنشاء الجداول
        _init_tables(conn)
        conn.close()
        # الآن نخزن الاتصال في _local للاستخدام العادي
        db = get_db()
        print(f"[DB] Database initialized at {DB_PATH}")
    except Exception as e:
        import traceback
        print(f"[DB] Init error (non-fatal): {e}")
        traceback.print_exc()


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


# Old get_store_sales replaced by enhanced version below


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




def get_store_sales(store_id=None, from_date=None, to_date=None, limit=100, offset=0,
                    code=None, client=None, vendeur=None, cancelled=None, credit=None, search=None):
    """جلب مبيعات المحل مع فلترة متقدمة"""
    db = get_db()
    
    # تجميع المبيعات بكل عناصرها — نأخذ distinct receipt
    query = """
        SELECT 
            ss.id, ss.receipt_number, ss.sale_date, ss.total, ss.discount as remise,
            ss.total as amount_paid, '' as status, ss.payment_method,
            ss.customer_name, ss.cashier as seller_name, ss.cashier as recorded_by, ss.sale_date as created_at,
            ss.unit_price as cost_price
        FROM store_sales ss
        WHERE 1=1
    """
    params = []
    
    if store_id:
        query += " AND ss.store_id = ?"
        params.append(store_id)
    if from_date:
        query += " AND ss.sale_date >= ?"
        params.append(f"{from_date} 00:00:00")
    if to_date:
        query += " AND ss.sale_date <= ?"
        params.append(f"{to_date} 23:59:59")
    if code:
        query += " AND ss.receipt_number LIKE ?"
        params.append(f"%{code}%")
    if client:
        query += " AND ss.customer_name LIKE ?"
        params.append(f"%{client}%")
    if vendeur:
        query += " AND ss.seller_name LIKE ?"
        params.append(f"%{vendeur}%")
    if not cancelled:
        pass  # ss.status not available
    if credit:
        query += " AND ss.status = 'credit'"
    if search:
        query += " AND (ss.receipt_number LIKE ? OR ss.customer_name LIKE ? OR ss.seller_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY ss.sale_date DESC, ss.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return dicts_from_rows(db.execute(query, params).fetchall())


def get_store_sale_items(sale_id):
    """جلب عناصر فاتورة مبيعة"""
    db = get_db()
    return dicts_from_rows(db.execute("""
        SELECT 
            ss.id, ss.product_id, ss.quantity, ss.unit_price, ss.discount,
            ss.total as line_total, p.name as product_name, p.sku, p.barcode
        FROM store_sales ss
        JOIN products p ON p.id = ss.product_id
        WHERE ss.id = ?
        ORDER BY ss.id ASC
    """, [sale_id]).fetchall())


# ============================================================
# Purchase List (Liste des achats)
# ============================================================

def get_store_purchases(store_id=None, from_date=None, to_date=None, limit=500, offset=0,
                        code=None, fournisseur=None, nom=None, cancelled=None, search=None):
    """جلب المشتريات مع فلترة متقدمة"""
    db = get_db()
    query = """
        SELECT 
            sp.id, sp.supplier, sp.purchase_date as date_achat,
            sp.total as montant_total, sp.notes,
            sp.created_at, sp.recorded_by,
            COALESCE((SELECT COUNT(*) FROM store_purchase_items WHERE purchase_id = sp.id), 0) as nombre_article,
            sp.total as montant_verse,
            0.0 as montant_reste,
            0.0 as tva_pct,
            0.0 as montant_tva,
            sp.total as total_ht
        FROM store_purchases sp
        WHERE 1=1
    """
    params = []
    
    if store_id:
        query += " AND sp.store_id = ?"
        params.append(store_id)
    if from_date:
        query += " AND sp.purchase_date >= ?"
        params.append(f"{from_date} 00:00:00")
    if to_date:
        query += " AND sp.purchase_date <= ?"
        params.append(f"{to_date} 23:59:59")
    if code:
        query += " AND CAST(sp.id AS TEXT) LIKE ?"
        params.append(f"%{code}%")
    if fournisseur:
        query += " AND sp.supplier LIKE ?"
        params.append(f"%{fournisseur}%")
    if nom:
        query += " AND sp.notes LIKE ?"
        params.append(f"%{nom}%")
    if not cancelled:
        query += " AND (sp.status IS NULL OR sp.status != 'cancelled')"
    
    query += " ORDER BY sp.purchase_date DESC, sp.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return dicts_from_rows(db.execute(query, params).fetchall())


def get_purchase_detail(purchase_id):
    """جلب تفاصيل فاتورة شراء مع العناصر"""
    db = get_db()
    purchase = dict_from_row(db.execute("""
        SELECT sp.*,
            COALESCE((SELECT COUNT(*) FROM store_purchase_items WHERE purchase_id = sp.id), 0) as nombre_article
        FROM store_purchases sp WHERE sp.id = ?
    """, [purchase_id]).fetchone())
    
    if purchase:
        purchase["items"] = dicts_from_rows(db.execute("""
            SELECT spi.*, p.name as product_name
            FROM store_purchase_items spi
            LEFT JOIN products p ON p.id = spi.product_id
            WHERE spi.purchase_id = ?
            ORDER BY spi.id ASC
        """, [purchase_id]).fetchall())
    
    return purchase


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
# Store Purchase Operations (Nouvel achat)
# ============================================================

def create_purchase(data):
    """إنشاء عملية شراء جديدة (تموين المخزون)"""
    db = get_db()
    total = data.get("total", 0)
    cursor = db.execute("""
        INSERT INTO store_purchases (supplier, purchase_date, total, notes, store_id, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        data.get("supplier", "divers"),
        data.get("purchase_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        total,
        data.get("notes", ""),
        data.get("store_id", 1),
        data.get("recorded_by", "store")
    ])
    purchase_id = cursor.lastrowid
    db.commit()
    
    _log_sync("purchase", purchase_id, "create", "store")
    
    return dict_from_row(db.execute("SELECT * FROM store_purchases WHERE id = ?", [purchase_id]).fetchone())


def add_purchase_item(purchase_id, item_data):
    """إضافة منتج إلى فاتورة شراء"""
    db = get_db()
    prix_total = item_data["prix_achat"] * item_data["quantite"]
    cursor = db.execute("""
        INSERT INTO store_purchase_items (purchase_id, product_id, barcode, designation, prix_achat, prix_vente, quantite, prix_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        purchase_id,
        item_data.get("product_id"),
        item_data.get("barcode", ""),
        item_data["designation"],
        item_data["prix_achat"],
        item_data["prix_vente"],
        item_data["quantite"],
        prix_total
    ])
    item_id = cursor.lastrowid
    
    # تحديث إجمالي فاتورة الشراء
    db.execute("UPDATE store_purchases SET total = (SELECT COALESCE(SUM(prix_total), 0) FROM store_purchase_items WHERE purchase_id = ?) WHERE id = ?",
               [purchase_id, purchase_id])
    db.commit()
    
    return dict_from_row(db.execute("SELECT * FROM store_purchase_items WHERE id = ?", [item_id]).fetchone())


def get_purchases(store_id=None, limit=100, offset=0):
    """جلب فواتير الشراء"""
    db = get_db()
    query = "SELECT * FROM store_purchases WHERE 1=1"
    params = []
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    query += " ORDER BY purchase_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return dicts_from_rows(db.execute(query, params).fetchall())


def get_purchase_items(purchase_id):
    """جلب عناصر فاتورة شراء"""
    db = get_db()
    return dicts_from_rows(db.execute("""
        SELECT * FROM store_purchase_items WHERE purchase_id = ? ORDER BY id ASC
    """, [purchase_id]).fetchall())


def create_purchase_with_items(data):
    """إنشاء فاتورة شراء مع عناصرها دفعة واحدة + تحديث المخزون"""
    db = get_db()
    
    # 1. إنشاء الفاتورة
    total = sum(
        item.get("prix_achat", 0) * item.get("quantite", 1)
        for item in data.get("items", [])
    )
    cursor = db.execute("""
        INSERT INTO store_purchases (supplier, purchase_date, total, notes, store_id, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        data.get("supplier", "divers"),
        data.get("purchase_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        total,
        data.get("notes", ""),
        data.get("store_id", 1),
        data.get("recorded_by", "store")
    ])
    purchase_id = cursor.lastrowid
    
    # 2. إضافة العناصر + تحديث المخزون
    created_items = []
    for item in data.get("items", []):
        designation = item.get("designation", "")
        barcode = item.get("barcode", "")
        prix_achat = item.get("prix_achat", 0)
        prix_vente = item.get("prix_vente", 0)
        quantite = item.get("quantite", 1)
        prix_total = prix_achat * quantite
        
        # البحث عن منتج موجود بالباركود أو إنشاء جديد
        product_id = item.get("product_id")
        if not product_id and barcode:
            existing = dict_from_row(db.execute("SELECT id FROM products WHERE barcode = ?", [barcode]).fetchone())
            if existing:
                product_id = existing["id"]
        
        # إذا لا يوجد منتج — ننشئ واحد جديد
        if not product_id:
            # توليد SKU من الباركود أو عشوائي
            sku = barcode if barcode else f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item.get('pos', 0)}"
            cursor2 = db.execute("""
                INSERT INTO products (sku, name, barcode, cost_price, store_price, category, supplier, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, [
                sku,
                designation,
                barcode,
                prix_achat,
                prix_vente,
                data.get("category", ""),
                data.get("supplier", "divers")
            ])
            product_id = cursor2.lastrowid
            # إنشاء سجل مخزون
            db.execute("INSERT INTO inventory (product_id, store_quantity) VALUES (?, ?)",
                       [product_id, quantite])
        else:
            # تحديث المخزون — زيادة الكمية
            existing_inv = dict_from_row(db.execute(
                "SELECT store_quantity FROM inventory WHERE product_id = ?", [product_id]
            ).fetchone())
            if existing_inv:
                new_qty = existing_inv["store_quantity"] + quantite
                db.execute("UPDATE inventory SET store_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
                           [new_qty, product_id])
            else:
                db.execute("INSERT INTO inventory (product_id, store_quantity) VALUES (?, ?)",
                           [product_id, quantite])
            
            # تحديث السعر إذا كانت القيم الجديدة مختلفة
            db.execute("UPDATE products SET cost_price = ?, store_price = ? WHERE id = ? AND (cost_price != ? OR store_price != ?)",
                       [prix_achat, prix_vente, product_id, prix_achat, prix_vente])
        
        # إضافة عنصر الشراء
        db.execute("""
            INSERT INTO store_purchase_items (purchase_id, product_id, barcode, designation, prix_achat, prix_vente, quantite, prix_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [purchase_id, product_id, barcode, designation, prix_achat, prix_vente, quantite, prix_total])
        
        created_items.append({
            "product_id": product_id,
            "designation": designation,
            "barcode": barcode,
            "prix_achat": prix_achat,
            "prix_vente": prix_vente,
            "quantite": quantite,
            "prix_total": prix_total
        })
    
    db.commit()
    _log_sync("purchase", purchase_id, "create", "store")
    
    return {
        "purchase": dict_from_row(db.execute("SELECT * FROM store_purchases WHERE id = ?", [purchase_id]).fetchone()),
        "items": created_items
    }


def update_inventory_from_purchase(product_id, quantity, cost_price, store_price):
    """تحديث المخزون وسعر الشراء بعد عملية شراء"""
    db = get_db()
    existing_inv = dict_from_row(db.execute(
        "SELECT store_quantity FROM inventory WHERE product_id = ?", [product_id]
    ).fetchone())
    
    if existing_inv:
        new_qty = existing_inv["store_quantity"] + quantity
        db.execute(
            "UPDATE inventory SET store_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ?",
            [new_qty, product_id]
        )
    else:
        db.execute(
            "INSERT INTO inventory (product_id, store_quantity) VALUES (?, ?)",
            [product_id, quantity]
        )
    
    # تحديث أسعار المنتج
    db.execute(
        "UPDATE products SET cost_price = ?, store_price = ? WHERE id = ?",
        [cost_price, store_price, product_id]
    )
    db.commit()
    return {"success": True, "new_quantity": quantity}


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
