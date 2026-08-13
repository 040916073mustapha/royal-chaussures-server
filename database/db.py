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
if _DB_ENGINE == "postgres":
    from database.psql import (
        get_db as _pg_get_db,
        close_db as _pg_close_db,
        dict_from_row, dicts_from_rows,
        init_db as _pg_init_db,
        _ensure_default_store as _pg_default_store,
        get_store, get_store_by_slug, get_stores, create_store, update_store,
        get_current_store_id
    )

    def get_db():
        return _pg_get_db()

    def close_db():
        _pg_close_db()

    _local = threading.local()

    def init_db():
        return _pg_init_db()

    def _ensure_default_store():
        return _pg_default_store()

    print(f"[DB] Engine: PostgreSQL")

# ============================================================
# SQLite Engine (الافتراضي)
# ============================================================
else:
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
