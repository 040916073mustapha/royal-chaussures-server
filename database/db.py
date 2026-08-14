"""
Nexus POS — Unified Multi-Tenant Database Module
==================================================
محرك قاعدة بيانات قابل للتبديل بين SQLite و PostgreSQL (Neon)
اختر الـ engine عبر متغير DB_ENGINE في البيئة

Royal Chaussures هو المتجر الأول (store_id=1)

DB_ENGINE=sqlite     (الوضع الحالي — royal_store.db)
DB_ENGINE=postgres   (Neon PostgreSQL — يتطلب DATABASE_URL)
"""

import os
import json
import threading
from datetime import datetime

# اختيار محرك قاعدة البيانات
_DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").strip().lower()


# ============================================================
# PostgreSQL Engine
# ============================================================
_pg_import_ok = False
if _DB_ENGINE == "postgres":
    try:
        from database.psql import (
            get_db as _pg_get_db,
            close_db as _pg_close_db,
            dict_from_row, dicts_from_rows,
            init_db as _pg_init_db,
            _ensure_default_store as _pg_default_store,
            get_store, get_store_by_slug, get_stores, create_store, update_store,
            get_current_store_id,
            get_products, get_product, get_product_by_barcode, get_product_by_sku,
            create_product, update_product, search_products,
            get_inventory, update_inventory, deduct_store_inventory, get_low_stock_items,
            create_sale, get_store_sales, get_store_sale_items, get_store_daily_summary,
            create_expense, get_expenses,
            create_purchase_with_items, get_purchases, get_purchase_items,
            get_store_purchases, get_purchase_detail,
            get_unified_dashboard, get_online_orders
        )
        _pg_import_ok = True
        print(f"[DB] Engine: PostgreSQL (imported)")
    except ImportError as _pg_import_err:
        print(f"[DB] ⚠️ PostgreSQL import failed: {_pg_import_err}")
        print(f"[DB] ⚠️ Falling back to SQLite...")
        _DB_ENGINE_ORIG = _DB_ENGINE
        _DB_ENGINE = "sqlite"
        os.environ["DB_ENGINE"] = "sqlite"

if _pg_import_ok:
    def get_db():
        return _pg_get_db()

    def close_db():
        _pg_close_db()

    _local = threading.local()

    def init_db():
        return _pg_init_db()

    def _ensure_default_store():
        return _pg_default_store()

# ============================================================
# SQLite Engine (الافتراضي)
# ============================================================
if not _pg_import_ok:
    import sqlite3

    DB_PATH = os.environ.get("STORE_DB_PATH",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "royal_store.db"))

    _local = threading.local()

    print(f"[DB] Engine: SQLite ({DB_PATH})")


    def get_db():
        """الحصول على اتصال بقاعدة البيانات (لكل thread connection منفصل)"""
        if not hasattr(_local, "connection") or _local.connection is None:
            _local.connection = _connect_or_repair(DB_PATH)
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
                conn.execute("SELECT 1")
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

        raise RuntimeError(f"Cannot connect to database after 5 attempts: {db_path}")


    def _check_and_remove_corrupted(db_path):
        """فحص قاعدة البيانات عند أول تشغيل — لا تمسح الملف أبداً"""
        pass


    # ============================================================
    # Store Management (Multi-Tenant) — SQLite version
    # ============================================================

    DEFAULT_STORE_SLUG = "royal-chaussures"
    DEFAULT_STORE_NAME = "Royal Chaussures"


    def _ensure_default_store():
        """التأكد من وجود المتجر الافتراضي (Royal Chaussures = store_id=1)"""
        db = get_db()
        store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = 1").fetchone())
        if not store:
            db.execute(
                "INSERT INTO stores (id, name, slug, email, phone, subscription_tier, subscription_status) "
                "VALUES (1, ?, ?, ?, ?, 'pro', 'active')",
                [DEFAULT_STORE_NAME, DEFAULT_STORE_SLUG,
                 "royalchaussures2@gmail.com", "+213659832426"]
            )
            db.commit()
            store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = 1").fetchone())
            print(f"[DB] Default store '{DEFAULT_STORE_NAME}' created (id=1)")
        return store


    def get_store(store_id):
        db = get_db()
        return dict_from_row(db.execute("SELECT * FROM stores WHERE id = ?", [store_id]).fetchone())


    def get_store_by_slug(slug):
        db = get_db()
        return dict_from_row(db.execute("SELECT * FROM stores WHERE slug = ?", [slug]).fetchone())


    def get_stores(active_only=True):
        db = get_db()
        query = "SELECT * FROM stores"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name ASC"
        return dicts_from_rows(db.execute(query).fetchall())


    def create_store(data):
        db = get_db()
        cursor = db.execute(
            "INSERT INTO stores (name, slug, email, phone, address, logo_url, subscription_tier, settings) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                data["name"], data["slug"],
                data.get("email", ""), data.get("phone", ""),
                data.get("address", ""), data.get("logo_url", ""),
                data.get("subscription_tier", "free"),
                json.dumps(data.get("settings", {}))
            ]
        )
        store_id = cursor.lastrowid
        db.commit()
        return get_store(store_id)


    def update_store(store_id, data):
        db = get_db()
        allowed_fields = ["name", "slug", "email", "phone", "address", "logo_url",
                          "subscription_tier", "subscription_status", "features",
                          "settings", "is_active"]
        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                if field in ("features", "settings"):
                    updates.append(f"{field} = ?")
                    params.append(json.dumps(data[field]))
                else:
                    updates.append(f"{field} = ?")
                    params.append(data[field])
        if not updates:
            return get_store(store_id)
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(store_id)
        db.execute(f"UPDATE stores SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
        return get_store(store_id)


    # ============================================================
    # Product CRUD (SQLite)
    # ============================================================

    def get_products(store_id=None, page=1, per_page=50, **filters):
        db = get_db()
        query = 'SELECT * FROM products'
        params = []
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def get_product(product_id):
        db = get_db()
        return dict_from_row(db.execute('SELECT * FROM products WHERE id = ?', [product_id]).fetchone())

    def get_product_by_barcode(barcode, store_id=None):
        db = get_db()
        params = [barcode]
        query = 'SELECT * FROM products WHERE barcode = ?'
        if store_id:
            query += ' AND store_id = ?'
            params.append(store_id)
        return dict_from_row(db.execute(query, params).fetchone())

    def get_product_by_sku(sku, store_id=None):
        db = get_db()
        params = [sku]
        query = 'SELECT * FROM products WHERE sku = ?'
        if store_id:
            query += ' AND store_id = ?'
            params.append(store_id)
        return dict_from_row(db.execute(query, params).fetchone())

    def create_product(data):
        db = get_db()
        cursor = db.execute('INSERT INTO products (store_id, name, sku, barcode, category, price, cost, unit, image_url, description, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data['name'], data.get('sku', ''), data.get('barcode', ''), data.get('category', ''), float(data.get('price', 0)), float(data.get('cost', 0)), data.get('unit', 'piece'), data.get('image_url', ''), data.get('description', ''), data.get('is_active', True)])
        db.commit()
        return get_product(cursor.lastrowid)

    def update_product(product_id, data):
        db = get_db()
        allowed = ['name','sku','barcode','category','price','cost','unit','image_url','description','is_active']
        updates = []
        params = []
        for field in allowed:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])
        if not updates:
            return get_product(product_id)
        params.append(product_id)
        db.execute(f'UPDATE products SET ' + ', '.join(updates) + ' WHERE id = ?', params)
        db.commit()
        return get_product(product_id)

    def search_products(query, store_id=None, limit=20):
        db = get_db()
        params = [f'%{query}%', f'%{query}%']
        sql = 'SELECT * FROM products WHERE (name LIKE ? OR sku LIKE ?)'
        if store_id:
            sql += ' AND store_id = ?'
            params.append(store_id)
        sql += ' LIMIT ?'
        params.append(limit)
        return dicts_from_rows(db.execute(sql, params).fetchall())

    # ============================================================
    # Inventory (SQLite)
    # ============================================================

    def get_inventory(product_id=None, store_id=None):
        db = get_db()
        params = []
        query = 'SELECT * FROM inventory'
        conditions = []
        if product_id:
            conditions.append('product_id = ?')
            params.append(product_id)
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        return dicts_from_rows(db.execute(query, params).fetchall())

    def update_inventory(product_id, data):
        db = get_db()
        existing = get_inventory(product_id)
        store_id = data.get('store_id', 1)
        if existing:
            updates = []
            params = []
            for field in ['store_quantity','online_quantity','warehouse_quantity']:
                if field in data:
                    updates.append(f'{field} = ?')
                    params.append(data[field])
            if updates:
                params.append(product_id)
                db.execute(f'UPDATE inventory SET ' + ', '.join(updates) + ' WHERE product_id = ?', params)
                db.commit()
        else:
            db.execute('INSERT INTO inventory (product_id, store_id, store_quantity, online_quantity, warehouse_quantity) VALUES (?, ?, ?, ?, ?)', [product_id, store_id, data.get('store_quantity', 0), data.get('online_quantity', 0), data.get('warehouse_quantity', 0)])
            db.commit()
        return get_inventory(product_id)

    def deduct_store_inventory(product_id, quantity, store_id=None):
        db = get_db()
        inv = get_inventory(product_id)
        if not inv:
            return {'error': 'Product not found in inventory'}
        inv = inv[0]
        new_qty = max(0, inv['store_quantity'] - quantity)
        db.execute('UPDATE inventory SET store_quantity = ? WHERE product_id = ?', [new_qty, product_id])
        db.commit()
        return {'store_quantity': new_qty}

    def get_low_stock_items(threshold=10, store_id=None):
        db = get_db()
        params = [threshold]
        query = 'SELECT p.*, i.store_quantity, i.online_quantity, i.warehouse_quantity FROM products p JOIN inventory i ON i.product_id = p.id WHERE i.store_quantity < ?'
        if store_id:
            query += ' AND p.store_id = ?'
            params.append(store_id)
        query += ' ORDER BY i.store_quantity ASC'
        return dicts_from_rows(db.execute(query, params).fetchall())

    # ============================================================
    # Sales (SQLite)
    # ============================================================

    def create_sale(data):
        db = get_db()
        try:
            cursor = db.execute('INSERT INTO store_sales (store_id, customer_name, customer_phone, cashier, subtotal, discount, tax, total, payment_method, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data.get('customer_name', ''), data.get('customer_phone', ''), data.get('cashier', 'caisse'), float(data.get('subtotal', 0)), float(data.get('discount', 0)), float(data.get('tax', 0)), float(data.get('total', 0)), data.get('payment_method', 'cash'), data.get('notes', '')])
            sale_id = cursor.lastrowid
            for item in data.get('items', []):
                db.execute('INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?, ?)', [sale_id, item.get('product_id'), item.get('product_name', ''), int(item.get('quantity', 1)), float(item.get('unit_price', 0)), float(item.get('total_price', 0))])
                deduct_store_inventory(item['product_id'], int(item.get('quantity', 1)))
            db.commit()
            return {'id': sale_id}
        except Exception as e:
            db.rollback()
            return {'error': str(e)}

    def get_store_sales(store_id=None, page=1, per_page=50, **filters):
        db = get_db()
        params = []
        query = 'SELECT * FROM store_sales'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def get_store_sale_items(sale_id):
        db = get_db()
        return dicts_from_rows(db.execute('SELECT * FROM sale_items WHERE sale_id = ?', [sale_id]).fetchall())

    def get_store_daily_summary(store_id=None, date=None):
        db = get_db()
        from datetime import date as dt_date
        today = date or dt_date.today().isoformat()
        params = [today]
        query = 'SELECT COUNT(*) as total_sales, COALESCE(SUM(total), 0) as total_revenue FROM store_sales WHERE DATE(created_at) = ?'
        if store_id:
            query += ' AND store_id = ?'
            params.append(store_id)
        return dict_from_row(db.execute(query, params).fetchone())

    def create_expense(data):
        db = get_db()
        cursor = db.execute('INSERT INTO expenses (store_id, description, amount, category, paid_by, notes) VALUES (?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data['description'], float(data['amount']), data.get('category', 'general'), data.get('paid_by', 'caisse'), data.get('notes', '')])
        db.commit()
        return {'id': cursor.lastrowid}

    def get_expenses(store_id=None, page=1, per_page=50):
        db = get_db()
        params = []
        query = 'SELECT * FROM expenses'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def create_purchase_with_items(data):
        db = get_db()
        try:
            cursor = db.execute('INSERT INTO purchases (store_id, supplier_name, supplier_phone, reference, subtotal, discount, tax, total, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [data.get('store_id', 1), data.get('supplier_name', ''), data.get('supplier_phone', ''), data.get('reference', ''), float(data.get('subtotal', 0)), float(data.get('discount', 0)), float(data.get('tax', 0)), float(data.get('total', 0)), data.get('notes', ''), data.get('status', 'pending')])
            purchase_id = cursor.lastrowid
            for item in data.get('items', []):
                db.execute('INSERT INTO purchase_items (purchase_id, product_id, product_name, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?, ?)', [purchase_id, item.get('product_id'), item.get('product_name', ''), int(item.get('quantity', 1)), float(item.get('unit_price', 0)), float(item.get('total_price', 0))])
            db.commit()
            return {'id': purchase_id}
        except Exception as e:
            db.rollback()
            return {'error': str(e)}

    def get_purchases(store_id=None, page=1, per_page=50):
        db = get_db()
        params = []
        query = 'SELECT * FROM purchases'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC'
        if per_page:
            query += f' LIMIT {int(per_page)} OFFSET {(int(page)-1)*int(per_page)}'
        return dicts_from_rows(db.execute(query, params).fetchall())

    def get_purchase_items(purchase_id):
        db = get_db()
        return dicts_from_rows(db.execute('SELECT * FROM purchase_items WHERE purchase_id = ?', [purchase_id]).fetchall())

    def get_store_purchases(store_id=None, page=1, per_page=50):
        return get_purchases(store_id, page, per_page)

    def get_purchase_detail(purchase_id):
        db = get_db()
        purchase = dict_from_row(db.execute('SELECT * FROM purchases WHERE id = ?', [purchase_id]).fetchone())
        if not purchase:
            return None
        purchase['items'] = get_purchase_items(purchase_id)
        return purchase

    def get_unified_dashboard(store_id=None):
        db = get_db()
        sid = store_id or 1
        from datetime import date as dt_date
        today = dt_date.today().isoformat()
        summary = get_store_daily_summary(sid, today)
        products = get_products(sid)
        sales = get_store_sales(sid, per_page=10)
        low_stock = get_low_stock_items(store_id=sid)
        online_orders = get_online_orders(sid)
        return {'summary': summary, 'products_count': len(products), 'recent_sales': sales, 'low_stock_items': low_stock, 'online_orders': online_orders}

    def get_online_orders(store_id=None):
        db = get_db()
        params = []
        query = 'SELECT * FROM orders'
        conditions = []
        if store_id:
            conditions.append('store_id = ?')
            params.append(store_id)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY id DESC LIMIT 20'
        return dicts_from_rows(db.execute(query, params).fetchall())


    def get_current_store_id():
        """الحصول على store_id الخاص بالطلب الحالي"""
        return getattr(_local, "store_id", 1)


    # ============================================================
    # Query helpers
    # ============================================================

    def dict_from_row(row):
        if row is None:
            return None
        return dict(row)


    def dicts_from_rows(rows):
        return [dict(r) for r in rows]


    # ============================================================
    # Schema & Migration
    # ============================================================

    def _init_tables(db):
        """إنشاء الجداول من schema.sql مع دعم ALTER TABLE للترقية"""
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            try:
                statements = []
                current = ""
                for line in schema_sql.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("--") or stripped.startswith("/*"):
                        continue
                    if stripped == "":
                        continue
                    current += line + "\n"
                    if stripped.endswith(";"):
                        statements.append(current.strip())
                        current = ""

                for stmt in statements:
                    try:
                        db.execute(stmt)
                    except Exception as stmt_err:
                        err_msg = str(stmt_err)
                        if "already exists" in err_msg or "duplicate column" in err_msg:
                            continue
                        if "no such table" in err_msg and "REFERENCES" in stmt:
                            continue
                        if "no such column" not in err_msg and "cannot add" not in err_msg:
                            print(f"[DB] Schema statement warning: {stmt_err}")
                db.commit()
            except Exception as e:
                print(f"[DB] Schema execution error: {e}")

        _migrate_existing_tables(db)

        from database.db import _seed_default_users
        _seed_default_users(db)


    def _migrate_existing_tables(db):
        """ترقية الجداول القديمة التي لا تحتوي store_id"""
        tables_with_store = ["products", "inventory", "online_orders", "sync_log", "barcode_print_log"]
        for table in tables_with_store:
            try:
                db.execute(f"ALTER TABLE {table} ADD COLUMN store_id INTEGER NOT NULL DEFAULT 1")
                db.commit()
                print(f"[DB] Migrated table '{table}' — added store_id")
            except Exception:
                pass
        for table in ["store_sales", "store_expenses", "store_purchases"]:
            try:
                db.execute(f"UPDATE {table} SET store_id = 1 WHERE store_id IS NULL OR store_id = 0")
                db.commit()
            except Exception:
                pass


    def init_db():
        """تهيئة قاعدة البيانات — إنشاء الجداول من schema.sql (اتصال منفصل)"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA cache_size=-8000")
            _init_tables(conn)
            conn.close()

            db = get_db()
            _ensure_default_store()
            print(f"[DB] Database initialized at {DB_PATH}")
        except Exception as e:
            print(f"[DB] Init error: {e}")
            import traceback
            traceback.print_exc()


    def _seed_default_users(db):
        """إنشاء المستخدمين الافتراضيين عند التشغيل الأول"""
        from werkzeug.security import generate_password_hash

        _ensure_default_store()

        admin_exists = db.execute("SELECT id FROM users WHERE username = ?", ["admin"]).fetchone()
        if not admin_exists:
            db.execute(
                "INSERT INTO users (username, password_hash, role, display_name, permissions) VALUES (?, ?, ?, ?, ?)",
                [
                    "admin",
                    generate_password_hash("rc-admin-2026"),
                    "admin",
                    "مصطفى (مدير)",
                    json.dumps(["admin:*", "store:*", "shared:*"])
                ]
            )
            print("[DB] Default admin user created")

        store_exists = db.execute("SELECT id FROM users WHERE username = ? AND store_id = 1", ["store"]).fetchone()
        if not store_exists:
            db.execute(
                "INSERT INTO users (username, password_hash, role, store_id, display_name, permissions) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    "store",
                    generate_password_hash("rc-store-2026"),
                    "store_manager",
                    1,
                    "مدير المحل",
                    json.dumps([
                        "store:products:*", "store:sales:*", "store:inventory:*",
                        "store:customers:*", "store:print:*", "store:expenses:*",
                        "shared:products:read", "shared:inventory:read"
                    ])
                ]
            )
            print("[DB] Default store manager user created (store_id=1)")

        db.commit()
