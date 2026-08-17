#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Cloud Server for Render
============================================
???????? ??????:
1. Flask Web App (Dashboard HTML + API)
2. Webhook Receiver (FB Messenger, WhatsApp, Instagram)
3. Shopify Webhook Handler (New Orders, Fulfillments)
4. ZR Express Tracking
5. Health Check
Designed for 24/7 operation on Render.com
"""
import requests
import json
import os
import sys
import sqlite3
import logging
import hashlib
import hmac
import re
import random
import base64
import time
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, render_template_string, Response


def _safe_str(val):
    s = repr(val) if isinstance(val, BaseException) else str(val)
    return s.encode('ascii', errors='replace').decode('ascii')


def json_utf8(data, status=200):
    payload = json.dumps(data, ensure_ascii=True, default=_safe_str)
    return Response(payload, status=status, content_type='application/json; charset=utf-8')


def _log_safe(logger_fn, msg_prefix, exc):
    safe = _safe_str(exc) if isinstance(exc, BaseException) else str(exc).encode('ascii', errors='replace').decode('ascii')
    logger_fn(f"{msg_prefix}: {safe}")


load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("royal-server")

# ????????? Environment Variables ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_URL = os.getenv("AI_API_URL", "https://api.deepinfra.com/v1/openai/chat/completions")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

# Shopify API config
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "")
SHOPIFY_CATALOG_TOKEN = os.getenv("SHOPIFY_CATALOG_TOKEN", "")
SHOPIFY_ORDERS_TOKEN = os.getenv("SHOPIFY_ORDERS_TOKEN", "")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")

# Phase 3 globals
AUTO_SHIP_STATUS = {"enabled": False, "last_ship_time": None, "orders_shipped": 0, "errors": []}
AUTO_CONFIRM_WA = {"enabled": False, "trigger_status": "confirmed", "messages_sent": 0, "last_send": None}

# ==================== SaaS DASHBOARD ENGINE ====================
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "royal_orders.db")


def _open_orders_db():
    """فتح اتصال بـ royal_orders.db مع WAL + busy_timeout لمنع القفل"""
    conn = sqlite3.connect(_DB_PATH, timeout=60, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    """
    تهيئة قاعدة البيانات المحلية (royal_orders.db)
    مع دعم Multi-Tenancy: store_id في كل الجداول
    """
    conn = _open_orders_db()
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER DEFAULT 1,
        shopify_order_id TEXT,
        customer_name TEXT, customer_phone TEXT,
        wilaya TEXT, municipality TEXT,
        product TEXT, variant TEXT,
        quantity INTEGER DEFAULT 1,
        total_price REAL DEFAULT 0,
        status TEXT DEFAULT 'Nouveau',
        delivery_method TEXT DEFAULT 'Home',
        delivery_fee REAL DEFAULT 0,
        source TEXT DEFAULT 'Shopify',
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(store_id, shopify_order_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER DEFAULT 1,
        name TEXT, phone TEXT,
        wilaya TEXT, municipality TEXT,
        total_orders INTEGER DEFAULT 1,
        total_spent REAL DEFAULT 0,
        last_order_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(store_id, phone)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER DEFAULT 1,
        platform TEXT, sender_id TEXT,
        message TEXT, reply TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    # ترقية الجداول القديمة — إضافة store_id إذا كان مفقوداً
    try:
        c.execute("SELECT store_id FROM orders LIMIT 1")
    except:
        c.execute("ALTER TABLE orders ADD COLUMN store_id INTEGER DEFAULT 1")
    try:
        c.execute("SELECT store_id FROM clients LIMIT 1")
    except:
        c.execute("ALTER TABLE clients ADD COLUMN store_id INTEGER DEFAULT 1")
    try:
        c.execute("SELECT store_id FROM messages LIMIT 1")
    except:
        c.execute("ALTER TABLE messages ADD COLUMN store_id INTEGER DEFAULT 1")
    conn.commit()
    conn.close()


def upsert_order_from_shopify(od):
    # Retry logic for database lock
    max_retries = 3
    retry_delay = 1
    last_error = None
    
    for attempt in range(max_retries):
        try:
            oid = str(od.get("id", ""))
            if not oid:
                return
            cust = od.get("customer", {}) or {}
            name = " ".join(filter(None, [cust.get("first_name", ""), cust.get("last_name", "")]))
            addr = cust.get("default_address", {}) or {}
            phone = cust.get("phone", "") or addr.get("phone", "")
            ship = od.get("shipping_address", {}) or {}
            wilaya = ship.get("province", "")
            city = ship.get("city", "")
            total = float(od.get("total_price", 0))
            items = od.get("line_items", [])
            product = items[0].get("title", "") if items else ""
            variant = items[0].get("variant_title", "") if items else ""
            conn = _open_orders_db()
            c = conn.cursor()
            # store_id=1 لـ Royal Chaussures — سيدعم Multi-Store لاحقاً عبر header
            store_id = 1
            c.execute("INSERT INTO orders (store_id, shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(store_id, shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')", (store_id, oid, name, phone, wilaya, city, product, variant, total))
            if phone:
                c.execute("SELECT id FROM clients WHERE store_id=? AND phone=?", (store_id, phone))
                if c.fetchone():
                    c.execute("UPDATE clients SET total_orders=total_orders+1, total_spent=total_spent+?, last_order_at=datetime('now') WHERE store_id=? AND phone=?", (total, store_id, phone))
                else:
                    c.execute("INSERT INTO clients (store_id, name, phone, wilaya, municipality, total_orders, total_spent, last_order_at) VALUES (?,?,?,?,?,1,?,datetime('now'))", (store_id, name, phone, wilaya, city, total))
            conn.commit()
            conn.close()
            return  # Success, exit retry loop
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                import time
                last_error = e
                logger.warning(f"[DB LOCK] Attempt {attempt+1}/{max_retries} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            raise  # Not a lock error, propagate
        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
            return
    
    # If we exhausted retries
    logger.error(f"[DB LOCK] All {max_retries} attempts failed. Last error: {last_error}")


def get_zr_shipments():
    zk = os.getenv("ZR_API_KEY", "")
    zu = os.getenv("ZR_BASE_URL", "")
    zt = os.getenv("ZR_TENANT_ID", "")
    if not zk or not zu:
        return []
    try:
        url = f"{zu}/tenant/{zt}/parcels?page=1&limit=20"
        headers = {"x-api-key": zk, "Content-Type": "application/json"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            return d.get("data", d.get("parcels", []))[:20]
    except Exception as e:
        logger.error(f"ZR error: {_safe_str(e)}")
    return []


init_db()

_SHOP_NAME = "Royal Chaussures"


def shopify_api(method="GET", endpoint="products.json", params=None, token_type="catalog"):
    """Make a Shopify Admin API request."""
    token = SHOPIFY_CATALOG_TOKEN if token_type == "catalog" else SHOPIFY_ORDERS_TOKEN
    if not SHOPIFY_STORE or not token:
        return None
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}/{endpoint}"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=headers, json=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        logger.warning(f"Shopify API {method} {endpoint}: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Shopify API error: {_safe_str(e)}")
    return None


def search_shopify_products(query=""):
    "Search products by name/query and return formatted results with EUROPEAN SIZES only."
    params = {"limit": 5, "status": "active"}
    if query:
        params["title"] = query
    data = shopify_api("GET", "products.json", params)
    if not data or "products" not in data:
        return "\u0639\u0630\u0631\u0627\u064b\u060c \u0644\u0645 \u0623\u062a\u0645\u0643\u0646 \u0645\u0646 \u062c\u0644\u0628 \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a \u062d\u0627\u0644\u064a\u0627\u064b. \U0001f6cd\ufe0f"
    products = data["products"]
    if not products:
        return "\u0646\u0639\u062a\u0630\u0631\u060c \u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u0646\u062a\u062c\u0627\u062a \u0645\u062a\u0627\u062d\u0629 \u062a\u0637\u0627\u0628\u0642 \u0637\u0644\u0628\u0643 \u062d\u0627\u0644\u064a\u0627\u064b. \U0001f622"
    result_lines = ["\U0001f6cd\ufe0f **\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a \u0627\u0644\u0645\u062a\u0648\u0641\u0631\u0629:**\n"]
    for p in products[:3]:
        title = p["title"]
        variants = p.get("variants", [])
        price_min = min(float(v.get("price", 0)) for v in variants) if variants else 0
        price_max = max(float(v.get("price", 0)) for v in variants) if variants else 0
        price_str = f"{int(price_min)} \u062f.\u062c" if price_min == price_max else f"{int(price_min)} - {int(price_max)} \u062f.\u062c"
        img_url = (p.get("images") or [{}])[0].get("src", "")
        # Extract European sizes from options, NOT from variant titles/inventory
        sizes = []
        options = p.get("options", [])
        for opt in options:
            if opt.get("name", "").lower() in ("size", "taille", "\u0627\u0644\u0645\u0642\u0627\u0633", "\u0645\u0642\u0627\u0633"):
                sizes = [v for v in opt.get("values", []) if v.replace(" ", "").replace("\u200e","").isdigit()]
                break
        if not sizes:
            sizes = []
            for v in variants:
                vt = v.get("title", "").strip()
                if vt.replace(" ", "").isdigit():
                    sizes.append(vt)
            sizes = sorted(set(sizes), key=lambda x: float(x.replace(" ", "")))
        size_str = "\u060c ".join(sizes) if sizes else "36 - 41"
        result_lines.append(f"\u2022 **{title}**")
        result_lines.append(f"  \u0627\u0644\u0633\u0639\u0631: {price_str}")
        result_lines.append(f"  \u0627\u0644\u0645\u0642\u0627\u0633\u0627\u062a \u0627\u0644\u0623\u0648\u0631\u0648\u0628\u064a\u0629: {size_str}")
        if img_url:
            result_lines.append(f"  {img_url}")
        result_lines.append("")
    return "\n".join(result_lines)
def check_product_inventory(product_query, size=None, color=None):
    """Check if a specific product/size/color is in stock."""
    params = {"limit": 5, "status": "active"}
    if product_query:
        params["title"] = product_query
    data = shopify_api("GET", "products.json", params)
    if not data or "products" not in data:
        return None
    for p in data.get("products", []):
        for v in p.get("variants", []):
            v_title = v.get("title", "").lower()
            qty = int(v.get("inventory_quantity", 0))
            match = True
            if size and size.lower() not in v_title:
                match = False
            if color and color.lower() not in v_title:
                match = False
            if match:
                return {
                    "product": p["title"],
                    "variant": v.get("title", ""),
                    "price": v.get("price", "0"),
                    "in_stock": qty > 0,
                    "quantity": qty,
                    "variant_id": v.get("id"),
                    "image": (p.get("images") or [{}])[0].get("src", "")
                }
    return None



# --- Conversation Memory (Thread Storage) ---
# Stores last N messages per sender_id for continuity
CONVERSATION_MEMORY = {}
MAX_HISTORY = 10  # keep last 10 exchanges per user


def get_conversation(sender_id):
    """Get or create conversation history for a sender."""
    if sender_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[sender_id] = []
    return CONVERSATION_MEMORY[sender_id]


def add_to_conversation(sender_id, role, text):
    """Add a message to conversation history."""
    conv = get_conversation(sender_id)
    conv.append({"role": role, "content": text})
    # Keep only last MAX_HISTORY*2 messages (user + assistant pairs)
    if len(conv) > MAX_HISTORY * 2:
        conv[:] = conv[-(MAX_HISTORY * 2):]


def sync_shopify_orders():
    try:
        data = shopify_api("GET", "orders.json", {"status": "any", "limit": 50}, token_type="orders")
        if data and "orders" in data:
            for o in data["orders"]:
                upsert_order_from_shopify(o)
            logger.info(f"Synced {len(data['orders'])} orders")
    except Exception as e:
        logger.error(f"sync error: {_safe_str(e)}")

threading.Thread(target=sync_shopify_orders, daemon=True).start()


def detect_product_query(user_message):
    """Detect if user is asking about products and return search query."""
    keywords = ["┘à┘åÏ¬Ï¼", "Ï¡Ï░ÏºÏí", "ÏÁ┘åÏ»┘ä", "Ï¿┘êÏ¬", "Ï¿Ïº┘ä┘èÏ▒┘è┘åÏº", "ÏºÏ│┘âÏ▒Ï¿┘è┘å",
                "escarpin", "ballerine", "botte", "sandale", "mule",
                "product", "shoe", "size", "price", "Ï│Ï╣Ï▒", "┘à┘éÏºÏ│",
                "┘ä┘ê┘å", "color", "┘àÏ¬┘ê┘üÏ▒", "disponible", "stock",
                "Ï╣┘åÏ»┘â┘à", "Ï╣┘åÏ»┘â", "Ï┤┘å┘ê", "┘êÏºÏ┤", "product"]
    msg_lower = user_message.lower()
    for kw in keywords:
        if kw in msg_lower:
            return user_message  # return the full query to search
    return None

FB_SYSTEM_USER_TOKEN = os.getenv("FB_SYSTEM_USER_TOKEN", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "ROYAL-ROYAL-CH2026")

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

_SHOP_NAME = "Royal Chaussures"

# ????????? Flask App Setup ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR, static_url_path='/static')
app.secret_key = os.urandom(24).hex()

# ==================== Store POS / Admin Blueprints ====================
# ?? NEW: Unified Store POS & Admin Dashboard (feature/store-pos)
# ?? Zero impact on existing webhooks/meta routes
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# ========== إصلاح قاعدة البيانات أولاً إن كانت تالفة ==========
import glob as _glob
_db_path = os.environ.get("STORE_DB_PATH", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "royal_store.db"))
_db_dir = os.path.dirname(_db_path)
# حذف أي ملفات WAL/SHM عالقة من جلسات سابقة
for _ext in ["-wal", "-shm"]:
    for _f in _glob.glob(os.path.join(_db_dir, "*" + _ext)):
        try:
            os.remove(_f)
            logger.info(f"[Store POS] Cleaned stale {_f}")
        except:
            pass
# اختبار قاعدة البيانات — إن كانت تالفة، احذفها
import sqlite3 as _sqlite3
try:
    _test_con = _sqlite3.connect(_db_path, timeout=5)
    _test_con.execute("SELECT 1")
    _test_con.close()
    logger.info("[Store POS] DB integrity check passed")
except Exception as _db_err:
    logger.warning(f"[Store POS] DB corrupted ({_db_err}), attempting rebuild...")
    try:
        _test_con.close()
    except:
        pass
    try:
        os.remove(_db_path)
        for _ext in ["-wal", "-shm"]:
            _p = _db_path + _ext
            if os.path.exists(_p):
                os.remove(_p)
        logger.info("[Store POS] Corrupted DB deleted, will be recreated")
    except Exception as _del_err:
        logger.error(f"[Store POS] Could not delete corrupted DB: {_del_err}")
# ==============================================================
# ========== Initialize Store POS Database ==========
_db_init_ok = False
import traceback as _tb
try:
    from database.db import init_db as init_store_db
    init_store_db()
    _db_init_ok = True
    logger.info("[Store POS] Database initialized successfully")
except Exception as e:
    logger.error(f"[Store POS] Database init FAILED: {e}")
    logger.error(f"[Store POS] Full traceback:\n{_tb.format_exc()}")

# ========== Register Store Blueprint ==========
_store_bp_ok = False
if _db_init_ok:
    try:
        from routes.store import store_bp
        app.register_blueprint(store_bp, url_prefix="/api/v1/store")
        _store_bp_ok = True
        logger.info("[Store POS] /api/v1/store blueprint registered")
    except Exception as e:
        import traceback as _tb
        logger.error(f"[Store POS] Store blueprint FAILED: {e}\n{_tb.format_exc()}")

# ========== Register Admin Blueprint ==========
if _db_init_ok:
    try:
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
        logger.info("[Store POS] /api/v1/admin blueprint registered")
    except Exception as e:
        import traceback as _tb
        logger.error(f"[Store POS] Admin blueprint FAILED: {e}\n{_tb.format_exc()}")

# ========== Register Inventory Agent Blueprint ==========
if _db_init_ok:
    try:
        from routes.inventory_agent import inv_agent_bp
        app.register_blueprint(inv_agent_bp, url_prefix="/api/v1/agent")
        logger.info("[Store POS] /api/v1/agent blueprint registered")
    except Exception as e:
        import traceback as _tb
        logger.error(f"[Store POS] Agent blueprint FAILED: {e}\n{_tb.format_exc()}")

# ========== Register Subscriptions Blueprint ==========
if _db_init_ok:
    try:
        from routes.subscriptions import subs_bp
        app.register_blueprint(subs_bp, url_prefix="/api/v1/subscription")
        logger.info("[Store POS] /api/v1/subscription blueprint registered")
    except Exception as e:
        import traceback as _tb
        logger.error(f"[Store POS] Subscription blueprint FAILED: {e}\n{_tb.format_exc()}")

# ========== Register POS Blueprint ==========
if _db_init_ok:
    try:
        from pos.routes import _pos_bp
        app.register_blueprint(_pos_bp)
        logger.info("[POS] Blueprint registered at /pos/")
    except Exception as e:
        import traceback as _tb
        logger.error(f"[POS] Blueprint FAILED: {e}\n{_tb.format_exc()}")

# ========== Teardown Handler ==========
if _db_init_ok:
    try:
        from database.db import close_db as close_store_db
        app.teardown_appcontext(lambda exc: close_store_db() if callable(close_store_db) else None)
        logger.info("[Store POS] DB teardown handler registered")
    except Exception as e:
        logger.error(f"[Store POS] Teardown handler FAILED: {e}")

# ========== POS Fallback Route ==========
@app.route('/api/v1/store/pos', endpoint='pos_direct', methods=['GET'])
def _pos_fallback_direct():
    return render_template('pos/index.html')

# ========== Debug endpoint to check registration status ==========
@app.route('/api/v1/debug/routes', methods=['GET'])
def _debug_routes():
    routes = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append({"path": rule.rule, "methods": methods, "endpoint": rule.endpoint})
    return jsonify({"db_ok": _db_init_ok, "store_ok": _store_bp_ok, "routes": routes})

# SaaS Onboarding page (register / login for new tenants)
@app.route('/api/v1/store/onboard', endpoint='nexus_onboard', methods=['GET'])
def _nexus_onboard():
    return render_template('nexus_auth.html')


# ====================================================================

# ????????? Dashboard HTTP Basic Auth ??????????????????????????????????????????????????????????????????????????????????
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "").strip()
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "").strip()
_DASHBOARD_AUTH_ENABLED = bool(DASHBOARD_USER and DASHBOARD_PASS)

# Paths that should NEVER require auth (webhooks, public APIs)
_AUTH_SAFE_PATHS = ("/health", "/webhook", "/whatsapp/webhook", "/", "/api/chatbot", "/api/v1", "/pos", "/api/v1/store/onboard", "/api/v1/store/pos/purchases", "/api/v1/store/pos/products", "/api/v1/store/pos/products/barcode", "/api/v1/store/pos/sales", "/api/v1/store/products", "/api/v1/store/products/barcode", "/api/v1/store/sales", "/api/v1/store/purchases")


@app.before_request
def require_auth_for_dashboard():
    """
    Apply HTTP Basic Auth to all /dashboard/* and /api/* paths,
    except whitelisted safe paths (webhooks, health, etc.).
    Soft-fail if DASHBOARD_USER/DASHBOARD_PASS not set in env.
    """
    if not _DASHBOARD_AUTH_ENABLED:
        return  # auth not configured, allow all
    path = request.path.rstrip("/")
    # Allow GET requests for webhook verification (hub.mode=subscribe)
    if request.method == "GET" and request.args.get("hub.mode") == "subscribe":
        return
    # Allow safe paths (webhooks, health, etc.)
    for safe in _AUTH_SAFE_PATHS:
        if path == safe or path.startswith(safe + "/"):
            return
    # Block /dashboard/* and /api/*
    if path.startswith("/dashboard") or path.startswith("/api"):
        auth = request.authorization
        if not auth or auth.username != DASHBOARD_USER or auth.password != DASHBOARD_PASS:
            return Response(
                "Authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="Royal Chaussures Dashboard"'}
            )


@app.after_request
def set_utf8_headers(response):
    ct = response.content_type or ''
    if 'charset' not in ct.lower() and (ct.startswith('text/') or ct.startswith('application/json')):
        response.content_type = ct.split(';')[0] + '; charset=utf-8'
    return response


# ????????? Facebook Page Token Cache ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????

_FB_PAGE_ACCESS_TOKEN = None


def get_fb_page_token():
    global _FB_PAGE_ACCESS_TOKEN
    if _FB_PAGE_ACCESS_TOKEN:
        return _FB_PAGE_ACCESS_TOKEN
    try:
        url = f"https://graph.facebook.com/v18.0/me/accounts?access_token={FB_SYSTEM_USER_TOKEN}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and len(data["data"]) > 0:
                for page in data["data"]:
                    if page["id"] == FB_PAGE_ID or not FB_PAGE_ID:
                        _FB_PAGE_ACCESS_TOKEN = page["access_token"]
                        logger.info(f"Page token obtained: {page['name']} ({page['id']})")
                        return _FB_PAGE_ACCESS_TOKEN
                _FB_PAGE_ACCESS_TOKEN = data["data"][0]["access_token"]
                logger.info(f"Page token (fallback): {data['data'][0]['name']}")
                return _FB_PAGE_ACCESS_TOKEN
        logger.warning(f"Failed to get page token: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.error(f"get_fb_page_token error: {_safe_str(e)}")
    return ""


# ????????? AI Reply ?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????


def generate_ai_reply(user_message, sender_id, image_url=''):
    if not AI_API_KEY:
        logger.warning("[AI] AI_API_KEY not set - token is empty. Bot cannot generate AI replies.")
        return "Merhaba, Royal Chaussures'a hos geldiniz! Nasil yardimci olabiliriz?"
    # Read system prompt from file (prompt.txt), fallback to env var, then to hardcoded default
    _prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.txt")
    system_prompt = ""
    try:
        with open(_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        logger.info(f"[PROMPT] Loaded system prompt from {_prompt_path} ({len(system_prompt)} chars)")
    except FileNotFoundError:
        system_prompt = os.getenv("AI_SYSTEM_PROMPT", "")
        if system_prompt:
            logger.info("[PROMPT] Loaded system prompt from env var AI_SYSTEM_PROMPT")
        else:
            system_prompt = (
                "[1. ROYAL IDENTITY]\n"
                "I represent Royal Chaussures...\n"
            )
            logger.info("[PROMPT] Using hardcoded default system prompt")

    # Pre-call Shopify inventory — always fetch live data for full context
    shopify_context = ""
    try:
        logger.info("Fetching live Shopify inventory...")
        import threading as _thr
        import time as _time
        _result = {"val": None}
        def _fetch_inventory():
            _result["val"] = search_shopify_products("")
        _t = _thr.Thread(target=_fetch_inventory, daemon=True)
        _t.start()
        _t.join(timeout=5)
        if _t.is_alive():
            logger.warning("Inventory fetch timed out (>5s), continuing without inventory data")
        else:
            live_inventory = _result["val"]
            if live_inventory:
                shopify_context = "\n\n[SHOPIFY INVENTORY DATA - LIVE]\n" + live_inventory + "\n[END INVENTORY DATA]\n"
                logger.info("Live inventory appended to AI context")
    except Exception as inv_err:
        logger.warning(f"Inventory fetch failed (non-critical), continuing: {_safe_str(inv_err)}")

    # Build messages with conversation history
    history = get_conversation(sender_id)
    messages = [{"role": "system", "content": system_prompt + shopify_context}]
    for msg in history[-8:]:
        messages.append(msg)
    # Add context flag: is this the first user message in this conversation?
    is_first_message = len([m for m in history if m["role"] == "user"]) <= 1
    if is_first_message:
        shopify_context += "\n\n[CONVERSATION STATE: FIRST MESSAGE — Welcome the customer warmly.]"
    else:
        shopify_context += "\n\n[CONVERSATION STATE: CONTINUING — Do NOT welcome again, continue naturally.]"
    # Rebuild system prompt with updated context
    messages[0] = {"role": "system", "content": system_prompt + shopify_context}
    # Build user content: plain string for text-only, OpenAI standard array for text+image
    user_message = user_message or ""
    if isinstance(image_url, str) and image_url.strip():
        user_content = [
            {"type": "text", "text": user_message if user_message else "What is in this image?"},
            {"type": "image_url", "image_url": {"url": image_url.strip()}}
        ]
        logger.info(f"[Vision] Including image in AI payload: {image_url.strip()[:80]}")
    else:
        user_content = user_message
    messages.append({"role": "user", "content": user_content})

    try:
        headers = {"Authorization": "Bearer " + AI_API_KEY, "Content-Type": "application/json"}
        # Log the content type being sent (str for text, list for vision)
        user_content_type = type(user_content).__name__
        user_content_preview = str(user_content)[:200] if isinstance(user_content, list) else str(user_content)[:100]
        logger.info(f"[AI] user_content type={user_content_type} preview={user_content_preview}")
        logger.info(f"[AI] Sending to {AI_API_URL} model={AI_MODEL}")
        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        resp = requests.post(AI_API_URL, json=payload, headers=headers, timeout=40)
        status_info = f"[AI] Response {resp.status_code} in {resp.elapsed.total_seconds():.1f}s"
        logger.info(status_info)
        logger.info(f"[AI] Response text (first 800): {resp.text[:800]}")
        if resp.status_code == 200:
            reply = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if reply:
                add_to_conversation(sender_id, "user", user_message)
                add_to_conversation(sender_id, "assistant", reply)
                return reply
            logger.warning("Empty AI reply content")
        else:
            logger.error("AI API error: " + str(resp.status_code) + " " + resp.text[:2000])
    except requests.exceptions.Timeout:
        logger.error(f"[AI] TIMEOUT after 40s — model={AI_MODEL}")
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"[AI] CONNECTION ERROR: {ce}")
    except Exception as e:
        logger.error("AI reply error: " + _safe_str(e))
    return "Merci de nous contacter! Nous reviendrons vers vous bientot."


# ????????? Facebook Messenger Reply ?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

def save_message_db(platform, sender_id, message, reply):
    """Save a message and its reply to the database for dashboard display"""
    try:
        conn = _open_orders_db()
        c = conn.cursor()
        c.execute("INSERT INTO messages (platform, sender_id, message, reply) VALUES (?,?,?,?)",
                  (platform, sender_id, str(message)[:1000], str(reply)[:1000]))
        conn.commit()
        conn.close()
        logger.info(f"[DB] Saved {platform} msg from {sender_id[:20] if sender_id else 'unknown'}: {str(message)[:40]}...")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[DB ERROR] save_message_db FAILED: {_safe_str(e)}")
        logger.error(f"[DB ERROR] Traceback:\n{tb}")

def send_fb_reply(sender_id, user_message, image_url=''):
    try:
        reply_text = generate_ai_reply(user_message, sender_id, image_url)
        page_token = get_fb_page_token()
        if not page_token:
            logger.warning("No page token, skipping FB reply")
            save_message_db("messenger", sender_id, user_message or "[Image]", "[No page token]")
            return
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={page_token}"
        payload = {"recipient": {"id": sender_id}, "message": {"text": reply_text}}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            logger.info(f"FB reply sent to {sender_id}: {reply_text[:60]}...")
        else:
            logger.warning(f"FB send failed ({resp.status_code}): {resp.text[:300]}")
        # Always save to DB regardless of send success
        logger.info(f"[DB] Attempting to save FB msg from {sender_id[:20]}...")
        save_message_db("messenger", sender_id, user_message or "[Image]", reply_text)
        logger.info(f"[DB] Successfully saved FB msg from {sender_id[:20]}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"send_fb_reply error: {_safe_str(e)}")
        logger.error(f"send_fb_reply traceback:\n{tb}")


# ????????? Instagram Reply ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

def send_ig_reply(sender_id, user_message, image_url=''):
    try:
        reply_text = generate_ai_reply(user_message, sender_id, image_url)

        # Priority: Page Token (has MESSAGING permission)
        page_token = get_fb_page_token()
        if page_token:
            ig_token = page_token
            logger.info("Using Page Token for Instagram reply")
        else:
            ig_token = INSTAGRAM_ACCESS_TOKEN
            logger.warning("No page token, trying INSTAGRAM_ACCESS_TOKEN")

        if not ig_token:
            logger.warning("No token available for Instagram reply")
            save_message_db("instagram", sender_id, user_message or "[Image]", "[No token]")
            return

        # Instagram DMs use /me/messages with a Page Token
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ig_token}"
        payload = {"recipient": {"id": sender_id}, "message": {"text": reply_text}}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            logger.info(f"IG reply sent to {sender_id}: {reply_text[:60]}...")
        else:
            err_body = resp.text[:300]
            logger.warning(f"IG send failed ({resp.status_code}): {err_body}")
            if 'does not exist' in err_body or 'capability' in err_body.lower():
                logger.info("Instagram reply needs 'Instagram Graph API' product.")
                logger.info("Fix: Add Instagram Graph API in Meta Developer App.")
        logger.info(f"[DB] Attempting to save IG msg from {sender_id[:20]}...")
        save_message_db("instagram", sender_id, user_message or "[Image]", reply_text)
        logger.info(f"[DB] Successfully saved IG msg from {sender_id[:20]}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"send_ig_reply error: {_safe_str(e)}")
        logger.error(f"send_ig_reply traceback:\n{tb}")
# ????????? WhatsApp Reply ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

def send_whatsapp_reply(to_number, user_message, image_url=''):
    try:
        reply_text = generate_ai_reply(user_message, to_number, image_url)
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp credentials not set")
            save_message_db("whatsapp", to_number, user_message or "[Image]", "[WA not configured]")
            return
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": reply_text}
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            logger.info(f"WA reply sent to {to_number}: {reply_text[:60]}...")
        else:
            logger.warning(f"WA send failed ({resp.status_code}): {resp.text[:200]}")
        logger.info(f"[DB] Attempting to save WA msg from {str(to_number)[:20]}...")
        save_message_db("whatsapp", to_number, user_message or "[Image]", reply_text)
        logger.info(f"[DB] Successfully saved WA msg from {str(to_number)[:20]}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"send_whatsapp_reply error: {_safe_str(e)}")
        logger.error(f"send_whatsapp_reply traceback:\n{tb}")


# ????????? Process common Messenger-style webhook payload ????????????????????????????????????????????????
# Shared by: Facebook Messenger (object=page) and Instagram (object=instagram)
# Both use the same: entry[].messaging[].sender.id + message.text structure

def process_messaging_entries(entries, platform, send_func):
    logger.info('[Webhook] process_messaging called: plat=' + platform + ' entries=' + str(len(entries)))
    for entry in entries:
        for messaging in entry.get('messaging', []):
            sid = messaging.get('sender', {}).get('id', '')
            msg_data = messaging.get('message', {})
            text = msg_data.get('text', '') or ''
            # Extract image_url from FB/IG attachments
            image_url = ''
            attachments = msg_data.get('attachments', [])
            if attachments:
                for att in attachments:
                    if att.get('type') == 'image':
                        payload = att.get('payload') or {}
                        image_url = payload.get('url') or att.get('url') or ''
                        if image_url:
                            break
            image_url = image_url or ''
            if sid and (text or image_url):
                logger.info(f"{platform} msg from {sid}: text='{text[:60] if text else '(none)'}' image_url={image_url[:60] if image_url else '(none)'}")
                threading.Thread(target=send_func, args=(sid, text, image_url), daemon=True).start()


# ????????? Process WhatsApp webhook payload ??????????????????????????????????????????????????????????????????????????????????????????
# Structure: entry[].changes[].value.messages[].from + text.body

def process_whatsapp_entries(entries):
    logger.info('[Webhook] process_whatsapp called: entries=' + str(len(entries)))
    for entry in entries:
        for change in entry.get('changes', []):
            for msg in change.get('value', {}).get('messages', []):
                sender = msg.get('from', '')
                text = (msg.get('text') or {}).get('body', '') or ''
                # WhatsApp image attachment (id or link)
                img = msg.get('image') or {}
                image_url = img.get('id') or img.get('link') or ''
                if image_url:
                    logger.info(f"WA msg with image from {sender}: id={image_url[:60]}")
                if sender and (text or image_url):
                    logger.info(f"WA msg from {sender}: text='{text[:60] if text else '(none)'}' image={image_url[:50] if image_url else '(none)'}")
                    threading.Thread(target=send_whatsapp_reply, args=(sender, text, image_url), daemon=True).start()


# ????????? App Secret (for X-Hub-Signature-256 verification) ??????????????????????????????
META_APP_SECRET = os.getenv("META_APP_SECRET", "")


def verify_webhook_signature(request_body, signature_header):
    """
    Verify X-Hub-Signature-256 header against request body using META_APP_SECRET.
    Returns True if valid or if signature/app_secret is not configured (soft fail).
    """
    if not META_APP_SECRET or not signature_header:
        return True  # soft pass if not configured
    try:
        expected_signature = "sha256=" + hmac.new(
            META_APP_SECRET.encode("utf-8"),
            request_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature_header)
    except Exception as e:
        logger.warning(f"[WEBHOOK] Signature verification error: {e}")
        return True  # soft pass on error to avoid breaking webhook


# ????????? Main Webhook ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
# Meta sends ALL subscribed objects (Messenger, Instagram, WhatsApp)
# to the SAME webhook URL (/webhook). The 'object' field differentiates them.

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # --- GET: Facebook verification challenge (for Messenger & Instagram) ---
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        logger.info(f"Webhook GET: mode={mode}")
        if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
            logger.info("Webhook verified!")
            return Response(challenge, status=200, content_type='text/plain')
        logger.warning("Webhook verify failed")
        return "Verification failed", 403

    # --- POST: Process incoming message ---
    logger.info("Webhook POST received")

    # Verify X-Hub-Signature-256 (soft fail if missing/unconfigured)
    signature = request.headers.get("X-Hub-Signature-256", "")
    raw_body = request.get_data()

    # DEBUG: Log signature details
    secret_status = "SET" if META_APP_SECRET else "MISSING"
    sig_status = "PRESENT" if signature else "MISSING"
    logger.info(f"[WEBHOOK] SIG DEBUG: secret={secret_status}, header_sig={sig_status}, body_len={len(raw_body)}, sig_preview={signature[:50] if signature else 'N/A'}")

    if not verify_webhook_signature(raw_body, signature):
        # DEBUG: Log expected vs actual
        if META_APP_SECRET and signature:
            expected_sig = "sha256=" + hmac.new(
                META_APP_SECRET.encode("utf-8"),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            logger.warning(f"[WEBHOOK] SIG MISMATCH: expected={expected_sig[:60]}..., received={signature[:60]}...")
        logger.warning(f"[WEBHOOK] Invalid signature! Possible tampering.")
        return json_utf8({"status": "signature_mismatch"}), 403

    data = request.get_json(silent=True)
    if not data:
        return json_utf8({"status": "ok"})

    obj = data.get('object', '')
    logger.info(f"Webhook object={obj}")

    if obj == 'page':
        # Facebook Messenger
        logger.info("Processing Facebook Messenger...")
        process_messaging_entries(data.get('entry', []), "FB", send_fb_reply)

    elif obj == 'instagram':
        # Instagram Direct Messages
        logger.info("Processing Instagram...")
        process_messaging_entries(data.get('entry', []), "IG", send_ig_reply)

    elif obj == 'whatsapp_business_account':
        # WhatsApp Business API
        logger.info("Processing WhatsApp...")
        process_whatsapp_entries(data.get('entry', []))

    else:
        logger.warning(f"Unknown webhook object: {obj}")
        # Try generic processing
        try:
            logger.info(f"Full payload: {json.dumps(data, ensure_ascii=True)[:800]}")
        except Exception:
            pass

    return json_utf8({"status": "ok"})


@app.route('/webhook/', methods=['GET', 'POST'])
def webhook_slash():
    return webhook()


# ????????? Legacy WhatsApp webhook path (kept for compatibility) ???????????????????????????

@app.route('/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    # GET: verification (for standalone WhatsApp callback)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
            return Response(challenge, status=200, content_type='text/plain')
        return "Verification failed", 403

    # POST: process WhatsApp payload
    data = request.get_json(silent=True)
    if data:
        logger.info(f"Legacy WA webhook: {json.dumps(data, ensure_ascii=True)[:500]}")
        process_whatsapp_entries(data.get('entry', []))
    return json_utf8({"status": "ok"})


# ????????? Pages ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????



# ==================== SaaS DASHBOARD API ====================

@app.before_request
def _maybe_sync():
    now = time.time()
    if not hasattr(_maybe_sync, "_last_sync"):
        _maybe_sync._last_sync = 0
    if now - _maybe_sync._last_sync > 120:
        _maybe_sync._last_sync = now
        threading.Thread(target=sync_shopify_orders, daemon=True).start()


@app.route('/api/stats')
def api_stats():
    conn = _open_orders_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Confirme'"); confirmed = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders"); revenue = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Livre'"); delivered = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Nouveau'"); pending = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT customer_phone) FROM orders WHERE customer_phone!=''"); clients_count = c.fetchone()[0]
    conn.close()
    return json_utf8({"total_orders": total, "confirmed": confirmed, "revenue": round(revenue, 2), "delivered": delivered, "pending": pending, "clients_count": clients_count, "delivery_rate": round((delivered/total*100) if total else 0, 1)})


@app.route('/api/orders')
def api_orders():
    sf = str(request.args.get('status', '')).strip()
    q = str(request.args.get('search', '')).strip()
    conn = _open_orders_db()
    c = conn.cursor()
    sql = "SELECT id, shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, quantity, total_price, status, delivery_method, created_at FROM orders WHERE 1=1"
    params = []
    if sf:
        sql += " AND status=?"; params.append(sf)
    if q:
        sql += " AND (customer_name LIKE ? OR customer_phone LIKE ? OR product LIKE ?)"
        s = f"%{q}%"; params += [s, s, s]
    sql += " ORDER BY created_at DESC LIMIT 100"
    c.execute(sql, params)
    return json_utf8({"orders": [{"id": r[0], "shopify_id": r[1], "customer": r[2], "phone": r[3], "wilaya": r[4], "municipality": r[5], "product": r[6], "variant": r[7], "qty": r[8], "total": r[9], "status": r[10], "delivery": r[11], "date": r[12]} for r in c.fetchall()]})
    conn.close()


@app.route('/api/orders/<int:oid>/status', methods=['PUT', 'POST'])
def api_update_status(oid):
    data = request.get_json(silent=True) or {}
    ns = data.get("status", "")
    if ns not in ("Nouveau", "Confirme", "Annule", "Livre"):
        return json_utf8({"error": "Invalid status"}, 400)
    conn = _open_orders_db()
    c = conn.cursor()
    c.execute("UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?", (ns, oid))
    conn.commit(); ok = c.rowcount > 0; conn.close()
    if ok:
        logger.info(f"[OrderDetail] Updated order {oid} status to {ns}")
        # AUTO-WHATSAPP: Send confirmation if enabled and status = confirmed
        if AUTO_CONFIRM_WA["enabled"] and ns.lower() in ("confirmed", "paid", "confirmé", "confirme"):
            try:
                shopify_orders_data = shopify_api("GET", "orders.json", {"status": "any", "limit": 250}, token_type="orders")
                if shopify_orders_data and "orders" in shopify_orders_data:
                    for so in shopify_orders_data["orders"]:
                        if str(so.get("id")) == str(oid) or so.get("name", "") == f"#{oid}":
                            send_confirmation_whatsapp(so)
                            logger.info(f"[OrderDetail] WA auto-confirm sent for {oid}")
                            break
            except Exception as wa_err:
                _log_safe(logger.warning, "WA auto-confirm failed", wa_err)
    return json_utf8({"success": ok, "status": ns})


@app.route('/api/products')
def api_products():
    data = shopify_api("GET", "products.json", {"limit": 50, "status": "active"})
    if not data or "products" not in data:
        return json_utf8({"products": []})
    return json_utf8({"products": [{"id": p["id"], "title": p["title"], "variants": len(p.get("variants", [])), "stock": sum(int(v.get("inventory_quantity", 0)) for v in p.get("variants", [])), "price_min": min((float(v.get("price", 0)) for v in p.get("variants", [])), default=0), "price_max": max((float(v.get("price", 0)) for v in p.get("variants", [])), default=0), "image": (p.get("images") or [{}])[0].get("src", ""), "status": p.get("status")} for p in data["products"]]})



# ============================================================
# POS Purchases API (Nouvel achat) — handled in routes/store.py blueprint
# ============================================================

# POS Products API (Liste des articles) — handled in routes/store.py blueprint
# ============================================================

@app.route('/api/clients')
def api_clients():
    conn = _open_orders_db()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, wilaya, municipality, total_orders, total_spent, last_order_at FROM clients ORDER BY total_orders DESC LIMIT 100")
    return json_utf8({"clients": [{"id": r[0], "name": r[1], "phone": r[2], "wilaya": r[3], "municipality": r[4], "orders": r[5], "spent": r[6], "last_order": r[7] or ""} for r in c.fetchall()]})
    conn.close()


@app.route('/api/shipments')
def api_shipments():
    return json_utf8({"shipments": get_zr_shipments()})


# --- Dashboard Pages ---

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html", active="dashboard")

@app.route('/dashboard/orders')
def dashboard_orders():
    return render_template("orders.html", active="orders")

@app.route('/dashboard/products')
def dashboard_products():
    return render_template("products.html", active="products")

@app.route('/dashboard/clients')
def dashboard_clients():
    return render_template("clients.html", active="clients")

@app.route('/dashboard/settings')
def dashboard_settings():
    settings_data = {
        "zr_express": {
            "status": "متصل",
            "tenant_id": "d2217f31-20f1-43c6-abd4-c420788a63ed",
            "last_sync": "منذ دقيقة",
            "server_status": "نشط"
        },
        "automations": {
            "status": "نشط",
            "items": [
                {"icon": "💬", "name": "WhatsApp - تأكيد الطلبات", "badge": "تلقائي"},
                {"icon": "📦", "name": "إشعارات الشحن", "badge": "تلقائي"},
                {"icon": "📊", "name": "تقرير الصباح اليومي", "badge": "09:00 صباحاً"}
            ]
        },
        "ai_agent": {
            "status": "متصل",
            "model": "DeepSeek-V4-Flash",
            "platforms": [
                {"name": "Messenger", "cls": "bg-blue-500/15 text-blue-400"},
                {"name": "WhatsApp", "cls": "bg-green-500/15 text-green-400"},
                {"name": "Instagram", "cls": "bg-pink-500/15 text-pink-400"}
            ]
        },
        "shopify": {
            "status": "متصل",
            "store": "rwqchh-na.myshopify.com",
            "auto_sync": "مفعلة",
            "last_update": "منذ ساعة"
        }
    }
    return render_template("dashboard_settings.html", active="settings", settings=settings_data)

@app.route('/')
def index():
    return json_utf8({"service": "Royal Chaussures Server", "status": "running", "version": "2.0"})


@app.route('/health')
def health():
    import os as _os
    db_engine = _os.environ.get("DB_ENGINE", "not-set")
    db_url_set = bool(_os.environ.get("DATABASE_URL", ""))
    return json_utf8({
        "status": "healthy",
        "db_engine": db_engine,
        "db_url_configured": db_url_set,
        "db_ok": globals().get("_db_init_ok", False),
        "store_ok": globals().get("_store_bp_ok", False),
        "timestamp": datetime.utcnow().isoformat()
    })


# ============================================================
# PHASE 3: AUTO-SHIP + WHATSAPP CONFIRM + LIVE CHAT
# ============================================================

def _clean_phone(phone):
    """Normalize phone to international format. Accepts str, int, float."""
    if phone is None:
        return ""
    if not isinstance(phone, str):
        phone = str(int(phone)) if isinstance(phone, float) else str(phone)
    phone = phone.strip()
    if not phone:
        return ""
    clean = re.sub(r"[^0-9]", "", phone)
    if not clean.startswith("213") and clean.startswith("0"):
        clean = "213" + clean[1:]
    elif not clean.startswith("213"):
        clean = "213" + clean
    return clean


def zr_create_shipment(order):
    """Create a shipment in ZR Express for an order"""
    try:
        zk = os.getenv("ZR_API_KEY", "")
        zu = os.getenv("ZR_BASE_URL", "")
        zt = os.getenv("ZR_TENANT_ID", "")
        if not zk or not zt:
            return {"success": False, "error": "ZR API not configured"}
        addr = order.get("shipping_address") or order.get("billing_address") or {}
        customer = order.get("customer") or {}
        phone = _clean_phone(addr.get("phone", "") or "")
        items = order.get("line_items", [])
        total = float(order.get("total_price", 0))
        payload = {
            "reference": order.get("name", f"ORDER-{order.get('id')}"),
            "shopify_order_id": str(order.get("id")),
            "customer_name": (f"{customer.get('first_name','') or ''} {customer.get('last_name','') or ''}").replace("None", "").strip(),
            "customer_phone": phone,
            "customer_address": (f"{addr.get('address1','')} {addr.get('address2','')}").strip(),
            "city": addr.get("city", ""),
            "wilaya": addr.get("province", ""),
            "total_amount": total,
            "items": [{"sku": i.get("sku",""), "name": i.get("title",""), "qty": i.get("quantity",1),
                       "price": float(i.get("price",0))} for i in items],
            "currency": "DZD",
            "notes": order.get("note", "")
        }
        headers = {"Content-Type": "application/json", "X-API-KEY": zk, "X-TENANT-ID": zt}
        url = f"{zu}/parcels/create"
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"success": True, "parcel_id": data.get("id",""), "tracking": data.get("tracking_number",""), "response": data}
        else:
            return {"success": False, "error": f"ZR API returned {resp.status_code}: {resp.text[:300]}"}
    except Exception as e:
        return {"success": False, "error": _safe_str(e)}


# ---- AUTO-SHIP ENDPOINTS ----

@app.route('/api/orders/auto-ship/status')
def api_auto_ship_status():
    return json_utf8({
        "enabled": AUTO_SHIP_STATUS["enabled"],
        "last_ship_time": AUTO_SHIP_STATUS["last_ship_time"],
        "orders_shipped": AUTO_SHIP_STATUS["orders_shipped"],
        "errors": AUTO_SHIP_STATUS["errors"][-10:]
    })


@app.route('/api/orders/auto-ship/toggle', methods=['POST'])
def api_auto_ship_toggle():
    try:
        data = request.get_json() or {}
        enabled = data.get("enabled", not AUTO_SHIP_STATUS["enabled"])
        AUTO_SHIP_STATUS["enabled"] = bool(enabled)
        logger.info(f"[AutoShip] {'Enabled' if enabled else 'Disabled'}")
        return json_utf8({"success": True, "enabled": AUTO_SHIP_STATUS["enabled"]})
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)})


@app.route('/api/orders/auto-ship/run', methods=['POST'])
def api_auto_ship_run():
    try:
        data = shopify_api("GET", "orders.json", {"status": "any", "limit": 50}, token_type="orders")
        orders = data.get("orders", []) if data else []
        unfulfilled = [o for o in orders if o.get("fulfillment_status") != "fulfilled" and o.get("financial_status") == "paid"]
        results = []
        for order in unfulfilled:
            result = zr_create_shipment(order)
            if result["success"]:
                AUTO_SHIP_STATUS["orders_shipped"] += 1
                logger.info(f"[AutoShip] Shipped {order.get('name')} -> {result.get('tracking','')}")
            else:
                AUTO_SHIP_STATUS["errors"].append({"order": order.get("name"), "error": result.get("error","")})
            results.append({"order_id": order.get("id"), "order_name": order.get("name"), **result})
        AUTO_SHIP_STATUS["last_ship_time"] = datetime.utcnow().isoformat()
        shipped = sum(1 for r in results if r["success"])
        return json_utf8({"success": True, "shipped": shipped, "failed": len(results)-shipped, "results": results})
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)})


@app.route('/api/orders/ship-single', methods=['POST'])
def api_orders_ship_single():
    try:
        data = request.get_json() or {}
        order_id = str(data.get("order_id", "")).strip()
        if not order_id:
            return json_utf8({"success": False, "error": "order_id required"}, 400)
        shopify_data = shopify_api("GET", "orders.json", {"status": "any", "limit": 250}, token_type="orders")
        orders = shopify_data.get("orders", []) if shopify_data else []
        order = next((o for o in orders if str(o.get("id")) == str(order_id) or o.get("name","") == f"#{order_id}"), None)
        if not order:
            return json_utf8({"success": False, "error": "Order not found"}, 404)
        result = zr_create_shipment(order)
        return json_utf8({"success": result["success"], "order_id": order_id, **result})
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)})


# ---- WHATSAPP CONFIRMATION ----

def send_confirmation_whatsapp(order):
    try:
        addr = order.get("shipping_address") or order.get("billing_address") or {}
        phone = _clean_phone(addr.get("phone", ""))
        if not phone:
            customer_phone = (order.get("customer") or {}).get("phone", "")
            phone = _clean_phone(customer_phone)
        if not phone:
            for attr in order.get("note_attributes", []):
                if "phone" in attr.get("name", "").lower():
                    phone = _clean_phone(attr.get("value", ""))
                    break
        # Fallback: look up in local DB by shopify_order_id
        if not phone:
            try:
                conn = _open_orders_db()
                _c = _conn.cursor()
                _c.execute("SELECT customer_phone FROM orders WHERE shopify_order_id=?", (str(order.get("id")),))
                _row = _c.fetchone()
                _conn.close()
                if _row and _row[0]:
                    phone = _clean_phone(_row[0])
                    logger.info(f"[WA Confirm] Got phone from local DB: {phone}")
            except:
                pass
        if not phone:
            logger.warning(f"[WA Confirm] No phone for order {order.get('name')}")
            return {"success": False, "error": "No phone number"}
        customer = order.get("customer") or {}
        name = (f"{customer.get('first_name','') or ''} {customer.get('last_name','') or ''}").replace("None", "").strip() or "عميلنا العزيز"
        items_summary = ", ".join([i.get("title","")[:30] for i in order.get("line_items", [])[:3]])
        message = (
            f"❤️ *Royal Chaussures* - تأكيد الطلب\n\n"
            f"مرحباً {name}،\n"
            f"✅ تم تأكيد طلبك *{order.get('name','')}*\n"
            f"📦 المنتجات: {items_summary}\n"
            f"💰 المبلغ: {order.get('total_price','0')} DZD\n"
            f"🚚 سيتم شحنه قريباً عبر ZR Express\n\n"
            f"شكراً لثقتك! 👠✨\n"
            f"📍 الإمامة، تلمسان | 📞 0659832426"
        )
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning(f"[WA Confirm] WA not configured (token={'set' if WHATSAPP_ACCESS_TOKEN else 'empty'}, id={'set' if WHATSAPP_PHONE_NUMBER_ID else 'empty'})")
            return {"success": False, "error": "WhatsApp not configured"}
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }
        logger.info(f"[WA Confirm] Sending to {phone} for order {order.get('name')}")
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        sent = resp.status_code in (200, 201)
        if not sent:
            logger.warning(f"[WA Confirm] FB API {resp.status_code}: {resp.text[:300]}")
        if sent:
            AUTO_CONFIRM_WA["messages_sent"] += 1
            AUTO_CONFIRM_WA["last_send"] = datetime.utcnow().isoformat()
            logger.info(f"[WA Confirm] Sent to {phone} for {order.get('name')}")
        return {"success": sent, "to": phone, "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"[WA Confirm] Exception: {_safe_str(e)}")
        return {"success": False, "error": _safe_str(e)}
@app.route('/api/whatsapp/confirm/status')
def api_wa_confirm_status():
    return json_utf8({
        "enabled": AUTO_CONFIRM_WA["enabled"],
        "trigger_status": AUTO_CONFIRM_WA["trigger_status"],
        "messages_sent": AUTO_CONFIRM_WA["messages_sent"],
        "last_send": AUTO_CONFIRM_WA["last_send"]
    })


@app.route('/api/whatsapp/confirm/toggle', methods=['POST'])
def api_wa_confirm_toggle():
    try:
        data = request.get_json() or {}
        enabled = data.get("enabled", not AUTO_CONFIRM_WA["enabled"])
        AUTO_CONFIRM_WA["enabled"] = bool(enabled)
        logger.info(f"[WA Confirm] {'Enabled' if enabled else 'Disabled'}")
        return json_utf8({"success": True, "enabled": AUTO_CONFIRM_WA["enabled"]})
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)})


@app.route('/api/whatsapp/confirm/send', methods=['POST'])
def api_wa_confirm_send():
    try:
        data = request.get_json() or {}
        order_id = str(data.get("order_id", "")).strip()
        if not order_id:
            return json_utf8({"success": False, "error": "order_id required"}, 400)
        # Step 1: Look up local DB to get shopify_order_id
        shopify_order_id = None
        try:
            conn = _open_orders_db()
            _c = _conn.cursor()
            # Try as local id first
            _c.execute("SELECT shopify_order_id FROM orders WHERE id=? OR shopify_order_id=?", (order_id, order_id))
            _row = _c.fetchone()
            if _row and _row[0]:
                shopify_order_id = _row[0]
                logger.info(f"[WA Confirm] Found local order: id={order_id}, shopify_id={shopify_order_id}")
            _conn.close()
        except Exception as db_err:
            logger.warning(f"[WA Confirm] DB lookup error: {_safe_str(db_err)}")
        # Step 2: Fetch from Shopify (by shopify_order_id or order name)
        shopify_data = shopify_api("GET", "orders.json", {"status": "any", "limit": 250}, token_type="orders")
        orders = shopify_data.get("orders", []) if shopify_data else []
        order = None
        if shopify_order_id:
            order = next((o for o in orders if str(o.get("id")) == str(shopify_order_id)), None)
        if not order:
            order = next((o for o in orders if str(o.get("id")) == str(order_id) or o.get("name","") == f"#{order_id}"), None)
        # Step 3: If still not found, build a minimal order dict from local DB
        if not order:
            try:
                conn = _open_orders_db()
                _c2 = _conn2.cursor()
                _c2.execute("SELECT shopify_order_id, customer_name, customer_phone, product, total_price FROM orders WHERE id=? OR shopify_order_id=?", (order_id, order_id))
                _row2 = _c2.fetchone()
                _conn2.close()
                if _row2:
                    soid, cname, cphone, prod, price = _row2
                    order = {
                        "id": int(soid) if soid and soid.isdigit() else 0,
                        "name": f"#{order_id}",
                        "customer": {"first_name": cname or "", "last_name": ""},
                        "shipping_address": {"phone": cphone or ""} if cphone else {},
                        "billing_address": {},
                        "line_items": [{"title": prod or "منتجات"}],
                        "total_price": str(price or "0")
                    }
                    logger.info(f"[WA Confirm] Built fallback order from local DB for {order_id}")
            except:
                pass
        if not order:
            return json_utf8({"success": False, "error": "Order not found"}, 404)
        result = send_confirmation_whatsapp(order)
        status_code = 200 if result.get("success") else (400 if result.get("error") else 500)
        return json_utf8({"success": result["success"], "order_id": order_id, **result}, status_code)
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)})


# ---- LIVE CHAT CONSOLE ----

@app.route('/dashboard/chat')
def dashboard_chat():
    """Live Chat Console page"""
    try:
        return render_template("chat_console.html")
    except Exception as e:
        _log_safe(logger.error, "Chat console template error", e)
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/messages')
def api_messages():
    """Get recent messages across all platforms"""
    try:
        limit = int(request.args.get("limit", 50))
        platform = request.args.get("platform", "")
        search = str(request.args.get("search", "")).strip()
        conn = _open_orders_db()
        c = conn.cursor()
        query = "SELECT * FROM messages"
        params = []
        conditions = []
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if search:
            conditions.append("(message LIKE ? OR reply LIKE ? OR sender_id LIKE ?)")
            s = f"%{search}%"
            params.extend([s, s, s])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        messages = []
        for r in rows:
            messages.append({
                "id": r[0],
                "platform": r[1],
                "sender_id": r[2],
                "message": r[3],
                "reply": r[4],
                "created_at": r[5]
            })
        return json_utf8({"success": True, "messages": messages, "count": len(messages)})
    except Exception as e:
        _log_safe(logger.error, "Messages API error", e)
        return json_utf8({"success": False, "error": _safe_str(e)})


@app.route('/api/profile')
def api_profile():
    """Get user profile name from Facebook/Instagram page token"""
    sender_id = request.args.get("sender_id", "")
    platform = request.args.get("platform", "")
    if not sender_id:
        return json_utf8({"success": False, "error": "Missing sender_id"})
    try:
        if platform in ("messenger", "instagram"):
            token = get_fb_page_token()
            if token:
                url = f"https://graph.facebook.com/v18.0/{sender_id}?fields=name&access_token={token}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return json_utf8({"success": True, "name": data.get("name", sender_id), "sender_id": sender_id})
        # Default fallback: return first 16 chars of sender_id
        display = sender_id[:20] if sender_id else "Unknown"
        return json_utf8({"success": True, "name": display, "sender_id": sender_id})
    except Exception as e:
        return json_utf8({"success": True, "name": sender_id[:20], "sender_id": sender_id})


# ????????? Main ?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    logger.info(f"Starting Royal Chaussures Server on port {port}")
    app.run(host='0.0.0.0', port=port)
