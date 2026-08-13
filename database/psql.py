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
