"""
Nexus POS — PostgreSQL Engine (Neon-ready)
============================================
محرك قاعدة بيانات PostgreSQL لمنصة Nexus POS
يعمل بالتبادل مع SQLite عبر database/db.py

الاستخدام:
    DB_ENGINE=postgres DATABASE_URL=postgresql://user:pass@host:5432/db
"""

import os
import json
import time as _time
from datetime import datetime
from functools import wraps

import psycopg2
import psycopg2.extras
import psycopg2.pool

# ── Connection Pool ──────────────────────────────────────────
# نحافظ على pool واحد لكل التطبيق (ليس thread-local)

_pool = None
_local_conn = None  # للاستخدام thread-safe في غياب pool


def get_pool():
    global _pool
    if _pool is None:
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            raise RuntimeError("DATABASE_URL not set. Cannot connect to PostgreSQL.")

        # Neon recommends SSL
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=db_url,
            sslmode="require"
        )
        print(f"[PG] Connection pool created (min=2, max=10)")
    return _pool


def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        print("[PG] Connection pool closed")


# ── Core DB Functions ──────────────────────────────────────────

def get_db():
    """
    الحصول على اتصال من الـ pool
    يعيد كائن connection + cursor في dict للاستخدام المتوافق مع SQLite
    """
    pool = get_pool()
    conn = pool.getconn()
    conn.autocommit = False
    return _PGWrapper(conn, pool)


def close_db():
    """إرجاع الاتصال إلى الـ pool"""
    global _local_conn
    _local_conn = None


class _PGWrapper:
    """
    يغلف psycopg2 ليكون متوافقاً مع واجهة sqlite3 المستخدمة
    بحيث database/db.py لا يحتاج تغيير جذري
    """

    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool
        self.row_factory = None  # متوافق مع sqlite3.Row

    def execute(self, sql, params=None):
        """تنفيذ استعلام مع دعم ? parameters (تحويل لـ %s)"""
        if params is not None and not isinstance(params, (list, tuple)):
            params = [params]
        pg_sql = self._convert_sql(sql)
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(pg_sql, params or [])
        return _PGCursorResult(cur)

    def executescript(self, sql_script):
        """تنفيذ سكربت SQL متعدد العبارات"""
        cur = self._conn.cursor()
        # تقسيم السكربت إلى عبارات منفصلة
        statements = []
        current = ""
        for line in sql_script.split("\n"):
            stripped = line.strip()
            if stripped.startswith("--") or stripped.startswith("/*"):
                continue
            if stripped == "":
                continue
            current += line + "\n"
            if stripped.rstrip().endswith(";"):
                statements.append(current.strip().rstrip(";"))
                current = ""
        if current.strip():
            statements.append(current.strip().rstrip(";"))

        for stmt in statements:
            if stmt:
                try:
                    pg_stmt = self._convert_sql(stmt)
                    cur.execute(pg_stmt)
                except Exception as e:
                    if "already exists" in str(e).lower():
                        continue
                    raise
        cur.close()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        """إرجاع الاتصال للـ pool"""
        try:
            self._conn.commit()
        except:
            self._conn.rollback()
        finally:
            if self._pool:
                self._pool.putconn(self._conn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _convert_sql(sql):
        """تحويل ? إلى %s مع الحفاظ على JSON operators وغيرها"""
        import re
        result = []
        i = 0
        for ch in sql:
            if ch == '?':
                result.append('%s')
            else:
                result.append(ch)
        return ''.join(result)


class _PGCursorResult:
    """محاكاة sqlite3 cursor results"""

    def __init__(self, cur):
        self._cur = cur
        self._rows = None

    def fetchone(self):
        try:
            return self._cur.fetchone()
        except Exception:
            return None

    def fetchall(self):
        try:
            return self._cur.fetchall()
        except Exception:
            return []

    @property
    def lastrowid(self):
        """إرجاع id بعد INSERT (pg returns it via RETURNING)"""
        return self._cur.fetchone()["id"] if self._cur.rowcount > 0 else None

    @property
    def rowcount(self):
        return self._cur.rowcount


# ── Helper ──────────────────────────────────────────────────────

def dict_from_row(row):
    """تحويل RealDictRow إلى dict عادي"""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows):
    """تحويل قائمة RealDictRow إلى قائمة dict"""
    return [dict(r) for r in rows]


# ── Schema & Migration ─────────────────────────────────────────

def init_db():
    """تهيئة قاعدة PostgreSQL — إنشاء الجداول من schema"""
    db = get_db()
    try:
        _init_tables(db)
        _seed_default_store(db)
        _seed_default_users(db)
        db.commit()
        print("[PG] Database initialized successfully")
    finally:
        db.close()


def _init_tables(db):
    """تنفيذ schema.sql مع دعم PostgreSQL syntax"""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_schema_pg.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        try:
            db.executescript(schema_sql)
            print("[PG] Schema executed successfully")
        except Exception as e:
            print(f"[PG] Schema execution warning: {e}")


def _seed_default_store(db):
    """التأكد من وجود Royal Chaussures كـ store_id=1"""
    row = db.execute("SELECT id FROM stores WHERE id = 1").fetchone()
    if not row:
        db.execute(
            "INSERT INTO stores (id, name, slug, email, phone, subscription_tier, subscription_status) "
            "VALUES (1, 'Royal Chaussures', 'royal-chaussures', 'royalchaussures2@gmail.com', "
            "'+213659832426', 'pro', 'active')"
        )
        print("[PG] Default store 'Royal Chaussures' created (id=1)")


def _seed_default_users(db):
    """إنشاء المستخدمين الافتراضيين"""
    from werkzeug.security import generate_password_hash

    admin = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin:
        db.execute(
            "INSERT INTO users (username, password_hash, role, display_name, permissions) "
            "VALUES ('admin', %s, 'admin', 'مصطفى (مدير)', %s)",
            [
                generate_password_hash("rc-admin-2026"),
                json.dumps(["admin:*", "store:*", "shared:*"])
            ]
        )
        print("[PG] Default admin user created")

    store_user = db.execute("SELECT id FROM users WHERE username = 'store' AND store_id = 1").fetchone()
    if not store_user:
        db.execute(
            "INSERT INTO users (username, password_hash, role, store_id, display_name, permissions) "
            "VALUES ('store', %s, 'store_manager', 1, 'مدير المحل', %s)",
            [
                generate_password_hash("rc-store-2026"),
                json.dumps([
                    "store:products:*", "store:sales:*", "store:inventory:*",
                    "store:customers:*", "store:print:*", "store:expenses:*",
                    "shared:products:read", "shared:inventory:read"
                ])
            ]
        )
        print("[PG] Default store manager user created")


# ── Store Management ────────────────────────────────────────────

def _ensure_default_store():
    """التأكد من وجود Royal Chaussures"""
    db = get_db()
    try:
        store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = 1").fetchone())
        if not store:
            _seed_default_store(db)
            db.commit()
            store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = 1").fetchone())
        return store
    finally:
        db.close()


def get_store(store_id):
    db = get_db()
    try:
        return dict_from_row(db.execute("SELECT * FROM stores WHERE id = %s", [store_id]).fetchone())
    finally:
        db.close()


def get_store_by_slug(slug):
    db = get_db()
    try:
        return dict_from_row(db.execute("SELECT * FROM stores WHERE slug = %s", [slug]).fetchone())
    finally:
        db.close()


def get_stores(active_only=True):
    db = get_db()
    try:
        query = "SELECT * FROM stores"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY name ASC"
        return dicts_from_rows(db.execute(query).fetchall())
    finally:
        db.close()


def create_store(data):
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO stores (name, slug, email, phone, address, logo_url, subscription_tier, settings) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            [
                data["name"], data["slug"],
                data.get("email", ""), data.get("phone", ""),
                data.get("address", ""), data.get("logo_url", ""),
                data.get("subscription_tier", "free"),
                json.dumps(data.get("settings", {}))
            ]
        )
        store_id = cur.lastrowid
        db.commit()
        return get_store(store_id)
    finally:
        db.close()


def update_store(store_id, data):
    db = get_db()
    try:
        allowed = ["name", "slug", "email", "phone", "address", "logo_url",
                   "subscription_tier", "subscription_status", "features", "settings", "is_active"]
        updates = []
        params = []
        for field in allowed:
            if field in data:
                val = json.dumps(data[field]) if field in ("features", "settings") else data[field]
                updates.append(f"{field} = %s")
                params.append(val)
        if updates:
            updates.append("updated_at = NOW()")
            params.append(store_id)
            db.execute(f"UPDATE stores SET {', '.join(updates)} WHERE id = %s", params)
            db.commit()
        return get_store(store_id)
    finally:
        db.close()


def get_current_store_id():
    """PostgreSQL version — يعيد store_id من thread-local أو 1"""
    import threading
    return getattr(threading.local(), "store_id", 1)


# ============================================================
# Product CRUD (PostgreSQL)
# ============================================================

def get_products(store_id=None, page=1, per_page=50, active_only=None, limit=None, **filters):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM products"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if active_only is not None:
        conditions.append("is_active = %s")
        params.append(active_only)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    actual_limit = limit or per_page
    if actual_limit:
        query += " LIMIT %s OFFSET %s"
        params.append(int(actual_limit))
        params.append((int(page) - 1) * int(actual_limit))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_product(product_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products WHERE id = %s", [product_id])
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def get_product_by_barcode(barcode, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [barcode]
    query = "SELECT * FROM products WHERE barcode = %s"
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def get_product_by_sku(sku, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [sku]
    query = "SELECT * FROM products WHERE sku = %s"
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def create_product(data):
    db = get_db()
    cur = db._conn.cursor()
    cur.execute(
        "INSERT INTO products (store_id, name, sku, barcode, category, price, cost, unit, image_url, description, is_active) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        [data.get("store_id", 1), data["name"], data.get("sku", ""),
         data.get("barcode", ""), data.get("category", ""),
         float(data.get("price", 0)), float(data.get("cost", 0)),
         data.get("unit", "piece"), data.get("image_url", ""),
         data.get("description", ""), data.get("is_active", True)]
    )
    product_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    return get_product(product_id)


def update_product(product_id, data):
    db = get_db()
    allowed = ["name","sku","barcode","category","price","cost","unit","image_url","description","is_active"]
    updates = []
    params = []
    for field in allowed:
        if field in data:
            updates.append(f"{field} = %s")
            params.append(data[field])
    if not updates:
        return get_product(product_id)
    params.append(product_id)
    cur = db._conn.cursor()
    cur.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = %s", params)
    db.commit()
    cur.close()
    return get_product(product_id)


def search_products(query, store_id=None, limit=20):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [f"%{query}%", f"%{query}%"]
    sql = "SELECT * FROM products WHERE (name ILIKE %s OR sku ILIKE %s)"
    if store_id:
        sql += " AND store_id = %s"
        params.append(store_id)
    sql += " LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# ============================================================
# Inventory (PostgreSQL)
# ============================================================

def get_inventory(product_id=None, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM inventory"
    if product_id:
        conditions.append("product_id = %s")
        params.append(product_id)
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def update_inventory(product_id, data):
    db = get_db()
    cur = db._conn.cursor()
    existing = get_inventory(product_id)
    store_id = data.get("store_id", 1)
    if existing:
        updates = []
        params = []
        for field in ["store_quantity","online_quantity","warehouse_quantity"]:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        if updates:
            params.append(product_id)
            cur.execute(f"UPDATE inventory SET {', '.join(updates)} WHERE product_id = %s", params)
            db.commit()
    else:
        cur.execute(
            "INSERT INTO inventory (product_id, store_id, store_quantity, online_quantity, warehouse_quantity) "
            "VALUES (%s, %s, %s, %s, %s)",
            [product_id, store_id, data.get("store_quantity", 0),
             data.get("online_quantity", 0), data.get("warehouse_quantity", 0)]
        )
        db.commit()
    cur.close()
    return get_inventory(product_id)


def deduct_store_inventory(product_id, quantity, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM inventory WHERE product_id = %s", [product_id])
    inv = cur.fetchone()
    if not inv:
        cur.close()
        return {"error": "Product not found in inventory"}
    new_qty = max(0, inv["store_quantity"] - quantity)
    cur.execute("UPDATE inventory SET store_quantity = %s WHERE product_id = %s", [new_qty, product_id])
    db.commit()
    cur.close()
    return {"store_quantity": new_qty}


def get_low_stock_items(threshold=10, store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = [threshold]
    query = "SELECT p.*, i.store_quantity, i.online_quantity, i.warehouse_quantity FROM products p JOIN inventory i ON i.product_id = p.id WHERE i.store_quantity < %s"
    if store_id:
        query += " AND p.store_id = %s"
        params.append(store_id)
    query += " ORDER BY i.store_quantity ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# ============================================================
# Sales (PostgreSQL)
# ============================================================

def create_sale(data):
    db = get_db()
    try:
        cur = db._conn.cursor()
        cur.execute(
            "INSERT INTO store_sales (store_id, customer_name, customer_phone, cashier, subtotal, discount, tax, total, payment_method, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            [data.get("store_id", 1), data.get("customer_name", ""),
             data.get("customer_phone", ""), data.get("cashier", "caisse"),
             float(data.get("subtotal", 0)), float(data.get("discount", 0)),
             float(data.get("tax", 0)), float(data.get("total", 0)),
             data.get("payment_method", "cash"), data.get("notes", "")]
        )
        sale_id = cur.fetchone()[0]
        for item in data.get("items", []):
            cur.execute(
                "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [sale_id, item.get("product_id"), item.get("product_name", ""),
                 int(item.get("quantity", 1)), float(item.get("unit_price", 0)),
                 float(item.get("total_price", 0))]
            )
            deduct_store_inventory(item["product_id"], int(item.get("quantity", 1)))
        db.commit()
        cur.close()
        return {"id": sale_id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


def get_store_sales(store_id=None, page=1, per_page=50, **filters):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM store_sales"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if per_page:
        query += " LIMIT %s OFFSET %s"
        params.append(int(per_page))
        params.append((int(page) - 1) * int(per_page))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_store_sale_items(sale_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM sale_items WHERE sale_id = %s", [sale_id])
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_store_daily_summary(store_id=None, date=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    from datetime import date as dt_date
    today = date or dt_date.today().isoformat()
    params = [today]
    query = "SELECT COUNT(*) as total_sales, COALESCE(SUM(total), 0) as total_revenue FROM store_sales WHERE DATE(created_at) = %s"
    if store_id:
        query += " AND store_id = %s"
        params.append(store_id)
    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()
    return dict(row) if row else None


def create_expense(data):
    db = get_db()
    cur = db._conn.cursor()
    cur.execute(
        "INSERT INTO expenses (store_id, description, amount, category, paid_by, notes) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        [data.get("store_id", 1), data["description"], float(data["amount"]),
         data.get("category", "general"), data.get("paid_by", "caisse"), data.get("notes", "")]
    )
    expense_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    return {"id": expense_id}


def get_expenses(store_id=None, page=1, per_page=50):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM expenses"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if per_page:
        query += " LIMIT %s OFFSET %s"
        params.append(int(per_page))
        params.append((int(page) - 1) * int(per_page))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


# ============================================================
# Purchases (PostgreSQL)
# ============================================================

def create_purchase_with_items(data):
    db = get_db()
    try:
        cur = db._conn.cursor()
        cur.execute(
            "INSERT INTO purchases (store_id, supplier_name, supplier_phone, reference, subtotal, discount, tax, total, notes, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            [data.get("store_id", 1), data.get("supplier_name", ""),
             data.get("supplier_phone", ""), data.get("reference", ""),
             float(data.get("subtotal", 0)), float(data.get("discount", 0)),
             float(data.get("tax", 0)), float(data.get("total", 0)),
             data.get("notes", ""), data.get("status", "pending")]
        )
        purchase_id = cur.fetchone()[0]
        for item in data.get("items", []):
            cur.execute(
                "INSERT INTO purchase_items (purchase_id, product_id, product_name, quantity, unit_price, total_price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [purchase_id, item.get("product_id"), item.get("product_name", ""),
                 int(item.get("quantity", 1)), float(item.get("unit_price", 0)),
                 float(item.get("total_price", 0))]
            )
        db.commit()
        cur.close()
        return {"id": purchase_id}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


def get_purchases(store_id=None, page=1, per_page=50):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    conditions = []
    query = "SELECT * FROM purchases"
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    if per_page:
        query += " LIMIT %s OFFSET %s"
        params.append(int(per_page))
        params.append((int(page) - 1) * int(per_page))
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_purchase_items(purchase_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM purchase_items WHERE purchase_id = %s", [purchase_id])
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]


def get_store_purchases(store_id=None, page=1, per_page=50):
    return get_purchases(store_id, page, per_page)


def get_purchase_detail(purchase_id):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM purchases WHERE id = %s", [purchase_id])
    purchase = cur.fetchone()
    if not purchase:
        cur.close()
        return None
    purchase = dict(purchase)
    cur.close()
    purchase["items"] = get_purchase_items(purchase_id)
    return purchase


# ============================================================
# Dashboard (PostgreSQL)
# ============================================================

def get_unified_dashboard(store_id=None):
    sid = store_id or 1
    from datetime import date as dt_date
    today = dt_date.today().isoformat()
    summary = get_store_daily_summary(sid, today)
    products = get_products(sid)
    sales = get_store_sales(sid, per_page=10)
    low_stock = get_low_stock_items(store_id=sid)
    online_orders = get_online_orders(sid)
    return {
        "summary": summary,
        "products_count": len(products),
        "recent_sales": sales,
        "low_stock_items": low_stock,
        "online_orders": online_orders
    }


def get_online_orders(store_id=None):
    db = get_db()
    cur = db._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    params = []
    query = "SELECT * FROM orders"
    conditions = []
    if store_id:
        conditions.append("store_id = %s")
        params.append(store_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT 20"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]
