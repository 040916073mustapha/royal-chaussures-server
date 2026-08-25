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

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RC Agents Platform - Multi-Tenant SaaS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
PLATFORM_DOMAIN = os.getenv("PLATFORM_DOMAIN", "rcagents.space")
import hmac
import re
import random
import secrets
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
# Force AI_MODEL â€” set in os.environ so all downstream readers see it
if "AI_MODEL" not in os.environ:
    os.environ["AI_MODEL"] = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
AI_MODEL = os.environ["AI_MODEL"]

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
    """ÙØªØ­ Ø§ØªØµØ§Ù„ Ø¨Ù€ royal_orders.db Ù…Ø¹ WAL + busy_timeout Ù„Ù…Ù†Ø¹ Ø§Ù„Ù‚ÙÙ„"""
    conn = sqlite3.connect(_DB_PATH, timeout=60, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    """
    ØªÙ‡ÙŠØ¦Ø© Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø­Ù„ÙŠØ© (royal_orders.db)
    Ù…Ø¹ Ø¯Ø¹Ù… Multi-Tenancy: store_id ÙÙŠ ÙƒÙ„ Ø§Ù„Ø¬Ø¯Ø§ÙˆÙ„
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
    # ØªØ±Ù‚ÙŠØ© Ø§Ù„Ø¬Ø¯Ø§ÙˆÙ„ Ø§Ù„Ù‚Ø¯ÙŠÙ…Ø© â€” Ø¥Ø¶Ø§ÙØ© store_id Ø¥Ø°Ø§ ÙƒØ§Ù† Ù…ÙÙ‚ÙˆØ¯Ø§Ù‹
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
            # store_id=1 Ù„Ù€ Royal Chaussures â€” Ø³ÙŠØ¯Ø¹Ù… Multi-Store Ù„Ø§Ø­Ù‚Ø§Ù‹ Ø¹Ø¨Ø± header
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
# ðŸ†• Multi-Tenant: CONVERSATION_MEMORY[store_id][sender_id] = [...]
CONVERSATION_MEMORY = {}
MAX_HISTORY = 10  # keep last 10 exchanges per user


def get_conversation(sender_id, store_id=1):
    """Get or create conversation history for a sender (isolated per store)."""
    if store_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[store_id] = {}
    if sender_id not in CONVERSATION_MEMORY[store_id]:
        CONVERSATION_MEMORY[store_id][sender_id] = []
    return CONVERSATION_MEMORY[store_id][sender_id]


def add_to_conversation(sender_id, role, text, store_id=1):
    """Add a message to conversation history (isolated per store)."""
    conv = get_conversation(sender_id, store_id)
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
    keywords = ["â”˜Ã â”˜Ã¥ÃÂ¬ÃÂ¼", "ÃÂ¡Ãâ–‘ÃÂºÃÃ­", "ÃÃâ”˜Ã¥ÃÂ»â”˜Ã¤", "ÃÂ¿â”˜ÃªÃÂ¬", "ÃÂ¿ÃÂºâ”˜Ã¤â”˜Ã¨Ãâ–’â”˜Ã¨â”˜Ã¥ÃÂº", "ÃÂºÃâ”‚â”˜Ã¢Ãâ–’ÃÂ¿â”˜Ã¨â”˜Ã¥",
                "escarpin", "ballerine", "botte", "sandale", "mule",
                "product", "shoe", "size", "price", "Ãâ”‚Ãâ•£Ãâ–’", "â”˜Ã â”˜Ã©ÃÂºÃâ”‚",
                "â”˜Ã¤â”˜Ãªâ”˜Ã¥", "color", "â”˜Ã ÃÂ¬â”˜Ãªâ”˜Ã¼Ãâ–’", "disponible", "stock",
                "Ãâ•£â”˜Ã¥ÃÂ»â”˜Ã¢â”˜Ã ", "Ãâ•£â”˜Ã¥ÃÂ»â”˜Ã¢", "Ãâ”¤â”˜Ã¥â”˜Ãª", "â”˜ÃªÃÂºÃâ”¤", "product"]
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
# ========== Ø¥ØµÙ„Ø§Ø­ Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø£ÙˆÙ„Ø§Ù‹ Ø¥Ù† ÙƒØ§Ù†Øª ØªØ§Ù„ÙØ© ==========
import glob as _glob
_db_path = os.environ.get("STORE_DB_PATH", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "royal_store.db"))
_db_dir = os.path.dirname(_db_path)
# Ø­Ø°Ù Ø£ÙŠ Ù…Ù„ÙØ§Øª WAL/SHM Ø¹Ø§Ù„Ù‚Ø© Ù…Ù† Ø¬Ù„Ø³Ø§Øª Ø³Ø§Ø¨Ù‚Ø©
for _ext in ["-wal", "-shm"]:
    for _f in _glob.glob(os.path.join(_db_dir, "*" + _ext)):
        try:
            os.remove(_f)
            logger.info(f"[Store POS] Cleaned stale {_f}")
        except:
            pass
# Ø§Ø®ØªØ¨Ø§Ø± Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª â€” Ø¥Ù† ÙƒØ§Ù†Øª ØªØ§Ù„ÙØ©ØŒ Ø§Ø­Ø°ÙÙ‡Ø§
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
    _db_url = __import__('os').environ.get('DATABASE_URL', '')
    if _db_url:
        from database.db import init_db as init_store_db
        init_store_db()
        _db_init_ok = True
        logger.info("[Store POS] Database initialized successfully")
    else:
        logger.warning("[Store POS] DATABASE_URL not set â€” skipping store DB init (SaaS Core will handle DB)")
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
_AUTH_SAFE_PATHS = ("/health", "/webhook", "/whatsapp/webhook", "/", "/sitemap.xml", "/privacy", "/terms", "/onboard", "/dashboard", "/dashboard/", "/dashboard/login", "/api/chatbot", "/api/v1", "/pos", "/api/tenant/onboard", "/api/tenant/login", "/api/sync/notion", "/api/stats", "/api/orders", "/api/products", "/api/clients", "/api/store", "/api/messages", "/api/profile", "/api/v1/store/onboard", "/api/v1/store/pos/purchases", "/api/v1/store/pos/products", "/api/v1/store/pos/products/barcode", "/api/v1/store/pos/sales", "/api/v1/store/products", "/api/v1/store/products/barcode", "/api/v1/store/sales", "/api/v1/store/purchases")


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
    # The new multi-tenant dashboard is public (no auth for subdomain paths)
    # Check if this is a /dashboard/<store_id> or /dashboard path (public access)
    # Also check if host has a subdomain (e.g., puma.rcagents.space)
    _host = request.headers.get("Host", "")
    _is_store_subdomain = _host.count(".") >= 2 and "." in _host.split(".", 1)[0]
    _pub_dash = re.match(r"^/dashboard(/\d+)?$", path)
    if _pub_dash or _is_store_subdomain:
        return
    # Allow API calls that include store_id parameter (from subdomain dashboard)
    _has_store_id = request.args.get("store_id") is not None
    if _has_store_id and path.startswith("/api/"):
        return
    # Allow any API call from a subdomain host
    if path.startswith("/api/") and _is_store_subdomain:
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


def _get_store_id_from_subdomain():
    """
    Ø§Ø³ØªØ®Ø±Ø§Ø¬ store_id Ù…Ù† Ø§Ù„Ù€ Subdomain ÙÙŠ Host header
    Ù…Ø«Ø§Ù„: puma.rcagents.space â†’ ÙŠØ³ØªØ®Ø±Ø¬ 'puma' ÙˆÙŠØ¨Ø­Ø« Ø¹Ù† store_id ÙÙŠ DB
    """
    _host = request.headers.get("Host", "")
    if _host.count(".") >= 2:
        _slug = _host.split(".")[0]
        from database.db import get_store_by_slug
        store = get_store_by_slug(_slug)
        if store:
            return store["id"]
    return None


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


def generate_ai_reply(user_message, sender_id, image_url='', store_id=1):
    """
    ØªÙˆÙ„ÙŠØ¯ Ø±Ø¯ AI Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… System Prompt Ø®Ø§Øµ Ø¨Ø§Ù„Ù…ØªØ¬Ø±
    store_id: 1 = Royal Chaussures (default)
    """
    if not AI_API_KEY:
        logger.warning("[AI] AI_API_KEY not set - token is empty. Bot cannot generate AI replies.")
        return "Merhaba, Royal Chaussures'a hos geldiniz! Nasil yardimci olabiliriz?"
    
    # ===== PHASE 2: SMART AGENT ROUTING =====
    # Detect the best agent for this message using keyword-based intent detection
    _detected_agent = "customer_support"
    _agent_name = "Customer Support"
    try:
        from agents.router import route_by_intent
        _routing = route_by_intent(user_message or "", "auto", sender_id, image_url, store_id)
        _detected_agent = _routing.get("agent_id", "customer_support")
        _agent_name = _routing.get("agent_name", "Customer Support")
        logger.info(f"[AI ROUTER] Detected agent: {_detected_agent} ({_agent_name}) for message: {(user_message or '')[ :60]}...")
    except Exception as _re:
        logger.warning(f"[AI ROUTER] Detection failed (non-critical): {_safe_str(_re)}")
    
    # ðŸ†• Multi-Tenant: Ù‚Ø±Ø§Ø¡Ø© AI Model Ùˆ System Prompt Ù…Ù† Ù‚Ø§Ø¹Ø¯Ø© Ø¨ÙŠØ§Ù†Ø§Øª SaaS Core
    # Multi-Tenant: read system prompt from PostgreSQL via subprocess psql
    _model = AI_MODEL  # ALWAYS from env (forced in code)
    system_prompt = ""
    try:
        import subprocess as _sp
        _db_url = os.getenv("SAAS_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
        if _db_url and _db_url.startswith("postgres"):
            _parts = _db_url.split("://")[1].split("@")
            _up = _parts[0].split(":")
            _hd = _parts[1].split("/")
            _hp = _hd[0].split(":")
            _env = os.environ.copy()
            _env["PGPASSWORD"] = _up[1] if len(_up) > 1 else ""
            _dbn = _hd[1].split("?")[0] if len(_hd) > 1 else "rcagents"
            _c = f'psql -h {_hp[0]} -p {int(_hp[1]) if len(_hp) > 1 else 5432} -U {_up[0]} -d {_dbn} -t -A -c "SELECT system_prompt FROM ai_settings WHERE store_id = \'{store_id}\'"'
            _r = _sp.run(_c, shell=True, capture_output=True, text=True, timeout=10, env=_env)
            if _r.returncode == 0 and _r.stdout.strip():
                system_prompt = _r.stdout.strip()
                logger.info(f"[AI] Loaded system prompt from DB for store {store_id} ({len(system_prompt)} chars)")
    except Exception as _e:
        logger.warning(f"[AI] DB read skipped (non-critical), using env: {_safe_str(_e)}")

    # Try loading agent-specific prompt from DB
    _prompt_type = _detected_agent  # e.g. "sales_agent", "campaign_agent", etc.
    if not system_prompt:
        try:
            _old_engine = os.environ.get('DB_ENGINE', '')
            if not _old_engine:
                os.environ['DB_ENGINE'] = 'sqlite'
            from database.db import get_store_prompt
            _db_prompt = get_store_prompt(store_id, _prompt_type)
            if _db_prompt:
                system_prompt = _db_prompt
                logger.info(f"[PROMPT] Loaded {_prompt_type} prompt for store_id={store_id} ({len(system_prompt)} chars)")
            else:
                # Fallback to the agent's built-in system prompt
                try:
                    from agents.router import get_agent_config
                    _cfg = get_agent_config(_prompt_type)
                    if _cfg and _cfg.get("system_prompt"):
                        system_prompt = _cfg["system_prompt"]
                        logger.info(f"[PROMPT] Using built-in {_prompt_type} prompt from config ({len(system_prompt)} chars)")
                except Exception as _cfg_err:
                    logger.warning(f"[PROMPT] Agent config fallback failed: {_safe_str(_cfg_err)}")
                    # Ultimate fallback: get customer_support prompt
                    _db_cs = get_store_prompt(store_id, "customer_support")
                    if _db_cs:
                        system_prompt = _db_cs
        except Exception as _prompt_err:
            logger.warning(f"[PROMPT] DB prompt failed, falling back to file: {_safe_str(_prompt_err)}")
    
    # Fallback: Ù…Ù„Ù prompt.txt Ø¥Ø°Ø§ Ù…Ø§ÙƒØ§Ù†Ø´ prompt ÙÙŠ DB
    if not system_prompt:
        _prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.txt")
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

    # Pre-call Shopify inventory â€” always fetch live data for full context
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

    # Build messages with conversation history (isolated per store_id)
    history = get_conversation(sender_id, store_id)
    messages = [{"role": "system", "content": system_prompt + shopify_context}]
    for msg in history[-8:]:
        messages.append(msg)
    # Add context flag: is this the first user message in this conversation?
    is_first_message = len([m for m in history if m["role"] == "user"]) <= 1
    if is_first_message:
        shopify_context += "\n\n[CONVERSATION STATE: FIRST MESSAGE â€” Welcome the customer warmly.]"
    else:
        shopify_context += "\n\n[CONVERSATION STATE: CONTINUING â€” Do NOT welcome again, continue naturally.]"
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
        logger.info(f"[AI] Agent={_detected_agent} user_content type={user_content_type} preview={user_content_preview}")
        logger.info(f"[AI] Sending to {AI_API_URL} model={_model}")
        payload = {
            "model": _model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        resp = requests.post(AI_API_URL, json=payload, headers=headers, timeout=90)
        status_info = f"[AI] Response {resp.status_code} in {resp.elapsed.total_seconds():.1f}s"
        logger.info(status_info)
        logger.info(f"[AI] Response text (first 800): {resp.text[:800]}")
        if resp.status_code == 200:
            reply = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if reply:
                add_to_conversation(sender_id, "user", user_message, store_id)
                add_to_conversation(sender_id, "assistant", reply, store_id)
                return reply
            logger.warning("Empty AI reply content")
        else:
            logger.error("AI API error: " + str(resp.status_code) + " " + resp.text[:2000])
    except requests.exceptions.Timeout:
        logger.error(f"[AI] timeout after 90s â€” model={_model}")
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"[AI] CONNECTION ERROR: {ce}")
    except Exception as e:
        logger.error("AI reply error: " + _safe_str(e))
    return "Merci de nous contacter! Nous reviendrons vers vous bientot."


# ????????? Facebook Messenger Reply ?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

def save_message_db(platform, sender_id, message, reply, store_id=1):
    """Save a message and its reply to the database for dashboard display"""
    try:
        conn = _open_orders_db()
        c = conn.cursor()
        c.execute("INSERT INTO messages (store_id, platform, sender_id, message, reply) VALUES (?,?,?,?,?)",
                  (store_id, platform, sender_id, str(message)[:1000], str(reply)[:1000]))
        conn.commit()
        conn.close()
        logger.info(f"[DB] Saved {platform} msg from {sender_id[:20] if sender_id else 'unknown'}: {str(message)[:40]}...")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[DB ERROR] save_message_db FAILED: {_safe_str(e)}")
        logger.error(f"[DB ERROR] Traceback:\n{tb}")

def send_fb_reply(sender_id, user_message, image_url='', store_id=1):
    try:
        reply_text = generate_ai_reply(user_message, sender_id, image_url, store_id)
        page_token = get_fb_page_token()
        if not page_token:
            logger.warning("No page token, skipping FB reply")
            save_message_db("messenger", sender_id, user_message or "[Image]", "[No page token]", store_id)
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
        save_message_db("messenger", sender_id, user_message or "[Image]", reply_text, store_id)
        logger.info(f"[DB] Successfully saved FB msg from {sender_id[:20]}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"send_fb_reply error: {_safe_str(e)}")
        logger.error(f"send_fb_reply traceback:\n{tb}")


# ????????? Instagram Reply ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

def send_ig_reply(sender_id, user_message, image_url='', store_id=1):
    try:
        reply_text = generate_ai_reply(user_message, sender_id, image_url, store_id)

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
            save_message_db("instagram", sender_id, user_message or "[Image]", "[No token]", store_id)
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
        save_message_db("instagram", sender_id, user_message or "[Image]", reply_text, store_id)
        logger.info(f"[DB] Successfully saved IG msg from {sender_id[:20]}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"send_ig_reply error: {_safe_str(e)}")
        logger.error(f"send_ig_reply traceback:\n{tb}")
# ????????? WhatsApp Reply ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

def send_whatsapp_reply(to_number, user_message, image_url='', store_id=1):
    try:
        reply_text = generate_ai_reply(user_message, to_number, image_url, store_id)
        if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp credentials not set")
            save_message_db("whatsapp", to_number, user_message or "[Image]", "[WA not configured]", store_id)
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
        save_message_db("whatsapp", to_number, user_message or "[Image]", reply_text, store_id)
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
                # ðŸ†• Multi-Tenant: Ø¥ÙŠØ¬Ø§Ø¯ store_id Ù…Ù† Ø§Ù„Ù…Ø­Ø§Ø¯Ø«Ø© (FB Page ID)
                store_id = 1
                try:
                    _old_engine2 = __import__('os').environ.get('DB_ENGINE', '')
                    if not _old_engine2:
                        __import__('os').environ['DB_ENGINE'] = 'sqlite'
                    from database.db import get_store_id_by_platform
                    # Ù†Ù…Ø±Ø± ØµÙØ­Ø© FB ID â€” Ø³Ù†Ø£Ø®Ø°Ù‡Ø§ Ù…Ù† Ø£ÙˆÙ„ entry ÙÙŠ webhook
                    entry_page_id = entry.get('id', '')
                    if entry_page_id:
                        sid_from_registry = get_store_id_by_platform('messenger' if platform == 'FB' else 'instagram', str(entry_page_id))
                        if sid_from_registry:
                            store_id = sid_from_registry
                            logger.info(f"[WEBHOOK] Routed {platform} msg to store_id={store_id} (page={entry_page_id})")
                except Exception as wh_err:
                    logger.warning(f"[WEBHOOK] Store lookup failed: {_safe_str(wh_err)}")
                logger.info(f"{platform} msg from {sid}: text='{text[:60] if text else '(none)'}' image_url={image_url[:60] if image_url else '(none)'} store_id={store_id}")
                threading.Thread(target=send_func, args=(sid, text, image_url, store_id), daemon=True).start()


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
                    # ðŸ†• Multi-Tenant: Ø¥ÙŠØ¬Ø§Ø¯ store_id Ù…Ù† WhatsApp Phone Number ID
                    store_id = 1
                    try:
                        _old_engine3 = __import__('os').environ.get('DB_ENGINE', '')
                        if not _old_engine3:
                            __import__('os').environ['DB_ENGINE'] = 'sqlite'
                        from database.db import get_store_id_by_whatsapp_phone
                        # Ù†Ø­Ø§ÙˆÙ„ Ù†Ø¬ÙŠØ¨ Ø§Ù„Ù€ metadata_phone_number_id Ù…Ù† Ø§Ù„Ù€ webhook payload
                        metadata = change.get('value', {}).get('metadata', {})
                        phone_id = metadata.get('phone_number_id', '')
                        if phone_id:
                            sid_from_registry = get_store_id_by_whatsapp_phone(str(phone_id))
                            if sid_from_registry:
                                store_id = sid_from_registry
                                logger.info(f"[WEBHOOK] Routed WA msg to store_id={store_id}")
                    except Exception as wh_err:
                        logger.warning(f"[WEBHOOK] WA store lookup failed: {_safe_str(wh_err)}")
                    logger.info(f"WA msg from {sender}: text='{text[:60] if text else '(none)'}' image={image_url[:50] if image_url else '(none)'} store_id={store_id}")
                    threading.Thread(target=send_whatsapp_reply, args=(sender, text, image_url, store_id), daemon=True).start()


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
    # Auto-detect store_id from subdomain first, fallback to query param, then to 1
    _sd = _get_store_id_from_subdomain()
    store_id = _sd if _sd else request.args.get("store_id", 1, type=int)
    conn = _open_orders_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE store_id=?", [store_id]); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE store_id=? AND status='Confirme'", [store_id]); confirmed = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE store_id=?", [store_id]); revenue = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE store_id=? AND status='Livre'", [store_id]); delivered = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE store_id=? AND status='Nouveau'", [store_id]); pending = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT customer_phone) FROM orders WHERE store_id=? AND customer_phone!=''", [store_id]); clients_count = c.fetchone()[0]
    conn.close()
    return json_utf8({"total_orders": total, "confirmed": confirmed, "revenue": round(revenue, 2), "delivered": delivered, "pending": pending, "clients_count": clients_count, "delivery_rate": round((delivered/total*100) if total else 0, 1)})


@app.route('/api/orders')
def api_orders():
    sf = str(request.args.get('status', '')).strip()
    q = str(request.args.get('search', '')).strip()
    # Auto-detect store_id from subdomain first
    _sd = _get_store_id_from_subdomain()
    store_id = _sd if _sd else request.args.get("store_id", 1, type=int)
    conn = _open_orders_db()
    c = conn.cursor()
    sql = "SELECT id, shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, quantity, total_price, status, delivery_method, created_at FROM orders WHERE store_id=?"
    params = [store_id]
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
        if AUTO_CONFIRM_WA["enabled"] and ns.lower() in ("confirmed", "paid", "confirmÃ©", "confirme"):
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
# POS Purchases API (Nouvel achat) â€” handled in routes/store.py blueprint
# ============================================================

# POS Products API (Liste des articles) â€” handled in routes/store.py blueprint
# ============================================================

@app.route('/api/clients')
def api_clients():
    _sd = _get_store_id_from_subdomain()
    store_id = _sd if _sd else request.args.get("store_id", 1, type=int)
    conn = _open_orders_db()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, wilaya, municipality, total_orders, total_spent, last_order_at FROM clients WHERE store_id=? ORDER BY total_orders DESC LIMIT 100", [store_id])
    return json_utf8({"clients": [{"id": r[0], "name": r[1], "phone": r[2], "wilaya": r[3], "municipality": r[4], "orders": r[5], "spent": r[6], "last_order": r[7] or ""} for r in c.fetchall()]})
    conn.close()


@app.route('/api/shipments')
def api_shipments():
    return json_utf8({"shipments": get_zr_shipments()})


# --- Dashboard Pages ---

def _get_store_context(store_id=None):
    """Ø§Ø³ØªØ®Ø±Ø§Ø¬ Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…ØªØ¬Ø± Ù…Ù† store_id (Ù…Ù† URL Ø£Ùˆ Ù…Ù† session)"""
    if store_id is None:
        store_id = request.args.get("store_id", 1, type=int)
    try:
        from database.db import get_store
        store = get_store(int(store_id))
        if store:
            return store
    except Exception:
        pass
    return {"id": 1, "name": "Ù…ØªØ¬Ø± ØºÙŠØ± Ù…Ø¹Ø±ÙˆÙ", "slug": "unknown"}


# Redirect root dashboard to store 1 (Royal Chaussures) for backwards compat
@app.route('/dashboard')
def dashboard():
    store_id = request.args.get("store_id", 1, type=int)
    return render_template("dashboard.html", active="dashboard", store_id=store_id)

@app.route('/dashboard/<int:store_id>')
def dashboard_store(store_id):
    return render_template("store_dashboard.html", store_id=store_id)

@app.route('/dashboard')
def dashboard_subdomain():
    """Public dashboard accessed via subdomain (e.g., puma.rcagents.space/dashboard)"""
    _host = request.headers.get("Host", "")
    _slug = _host.split(".")[0] if _host.count(".") >= 2 else ""
    if _slug:
        from database.db import get_store_by_slug
        store = get_store_by_slug(_slug)
        if store:
            return render_template("store_dashboard.html", store_id=store["id"])
    return render_template("dashboard.html", active="dashboard", store_id=1)

@app.route('/dashboard/')
def dashboard_subdomain_slash():
    return dashboard_subdomain()

@app.route('/dashboard/<int:store_id>/orders')
def dashboard_store_orders(store_id):
    return render_template("orders.html", active="orders", store_id=store_id)

@app.route('/dashboard/<int:store_id>/products')
def dashboard_store_products(store_id):
    return render_template("products.html", active="products", store_id=store_id)

@app.route('/dashboard/<int:store_id>/clients')
def dashboard_store_clients(store_id):
    return render_template("clients.html", active="clients", store_id=store_id)

@app.route('/dashboard/<int:store_id>/settings')
def dashboard_store_settings(store_id):
    return render_template("settings.html", active="settings", store_id=store_id)

@app.route('/dashboard/orders')
def dashboard_orders_old():
    store_id = request.args.get("store_id", 1, type=int)
    return render_template("orders.html", active="orders", store_id=store_id)

@app.route('/dashboard/products')
def dashboard_products_old():
    store_id = request.args.get("store_id", 1, type=int)
    return render_template("products.html", active="products", store_id=store_id)

@app.route('/dashboard/clients')
def dashboard_clients_old():
    store_id = request.args.get("store_id", 1, type=int)
    return render_template("clients.html", active="clients", store_id=store_id)

@app.route('/dashboard/settings')
def dashboard_settings_old():
    settings_data = {
        "zr_express": {
            "status": "Ù…ØªØµÙ„",
            "tenant_id": "d2217f31-20f1-43c6-abd4-c420788a63ed",
            "last_sync": "Ù…Ù†Ø° Ø¯Ù‚ÙŠÙ‚Ø©",
            "server_status": "Ù†Ø´Ø·"
        },
        "automations": {
            "status": "Ù†Ø´Ø·",
            "items": [
                {"icon": "ðŸ’¬", "name": "WhatsApp - ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨Ø§Øª", "badge": "ØªÙ„Ù‚Ø§Ø¦ÙŠ"},
                {"icon": "ðŸ“¦", "name": "Ø¥Ø´Ø¹Ø§Ø±Ø§Øª Ø§Ù„Ø´Ø­Ù†", "badge": "ØªÙ„Ù‚Ø§Ø¦ÙŠ"},
                {"icon": "ðŸ“Š", "name": "ØªÙ‚Ø±ÙŠØ± Ø§Ù„ØµØ¨Ø§Ø­ Ø§Ù„ÙŠÙˆÙ…ÙŠ", "badge": "09:00 ØµØ¨Ø§Ø­Ø§Ù‹"}
            ]
        },
        "ai_agent": {
            "status": "Ù…ØªØµÙ„",
            "model": "DeepSeek-V4-Flash",
            "platforms": [
                {"name": "Messenger", "cls": "bg-blue-500/15 text-blue-400"},
                {"name": "WhatsApp", "cls": "bg-green-500/15 text-green-400"},
                {"name": "Instagram", "cls": "bg-pink-500/15 text-pink-400"}
            ],
            "agents_link": "/dashboard/agents"
        },
        "shopify": {
            "status": "Ù…ØªØµÙ„",
            "store": "rwqchh-na.myshopify.com",
            "auto_sync": "Ù…ÙØ¹Ù„Ø©",
            "last_update": "Ù…Ù†Ø° Ø³Ø§Ø¹Ø©"
        }
    }
    return render_template("dashboard_settings.html", active="settings", settings=settings_data)

@app.route('/')
def index():
    return render_template("landing.html")


@app.route('/sitemap.xml')
def sitemap():
    """Sitemap XML for Google Search Console indexing"""
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    pages = [
        {"loc": f"https://{PLATFORM_DOMAIN}/", "priority": "1.0", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/onboard", "priority": "0.9", "changefreq": "monthly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard", "priority": "0.7", "changefreq": "monthly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/orders", "priority": "0.5", "changefreq": "daily"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/products", "priority": "0.5", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/clients", "priority": "0.4", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/chat", "priority": "0.6", "changefreq": "daily"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/analytics", "priority": "0.5", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/settings", "priority": "0.3", "changefreq": "monthly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/shipments", "priority": "0.4", "changefreq": "daily"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/constellation", "priority": "0.3", "changefreq": "monthly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/agents", "priority": "0.5", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/marketing", "priority": "0.3", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/inventory", "priority": "0.4", "changefreq": "daily"},
        {"loc": f"https://{PLATFORM_DOMAIN}/dashboard/auto-ship", "priority": "0.3", "changefreq": "weekly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/privacy", "priority": "0.6", "changefreq": "monthly"},
        {"loc": f"https://{PLATFORM_DOMAIN}/terms", "priority": "0.6", "changefreq": "monthly"},
    ]
    
    for page in pages:
        url = ET.SubElement(root, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = page["loc"]
        priority = ET.SubElement(url, "priority")
        priority.text = page["priority"]
        changefreq = ET.SubElement(url, "changefreq")
        changefreq.text = page["changefreq"]
    
    rough_string = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent="  ", encoding="utf-8")
    return Response(pretty, mimetype="application/xml")


@app.route('/privacy')
def privacy():
    return render_template("privacy.html")


@app.route('/terms')
def terms():
    return render_template("terms.html")


# ============================================================
# ðŸ§  AI Prompts Management API (Multi-Tenant)
# ============================================================

@app.route('/api/store/prompts', methods=['GET'])
def api_get_prompts():
    """Ù‚Ø±Ø§Ø¡Ø© Ø¬Ù…ÙŠØ¹ Ø§Ù„Ù€ Prompts Ù„Ù„Ù…ØªØ¬Ø±"""
    try:
        from database.db import get_all_store_prompts
        store_id = request.args.get('store_id', 1, type=int)
        prompts = get_all_store_prompts(store_id)
        return json_utf8({"store_id": store_id, "prompts": prompts})
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/store/prompts', methods=['POST'])
def api_set_prompt():
    """ØªØ­Ø¯ÙŠØ« System Prompt Ù„Ù…ØªØ¬Ø±"""
    try:
        from database.db import set_store_prompt
        data = request.get_json()
        if not data:
            return json_utf8({"error": "Request body required"}, 400)
        store_id = data.get('store_id', 1)
        prompt_type = data.get('prompt_type', 'customer_support')
        prompt_text = data.get('prompt_text', '')
        if not prompt_text:
            return json_utf8({"error": "prompt_text required"}, 400)
        set_store_prompt(store_id, prompt_type, prompt_text)
        return json_utf8({"success": True, "store_id": store_id, "prompt_type": prompt_type})
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/store/prompt/default', methods=['GET'])
def api_get_default_prompt():
    """Ø§Ø³ØªØ¹Ø±Ø§Ø¶ Ù…Ø­ØªÙˆÙ‰ prompt.txt (Ø§Ù„Ù€ fallback) Ù…Ø¹ Ø¥Ù…ÙƒØ§Ù†ÙŠØ© Ù†Ø³Ø®Ù‡ Ù„Ù…ØªØ¬Ø± Ø¬Ø¯ÙŠØ¯"""
    _prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.txt")
    try:
        with open(_prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        return json_utf8({"file": "prompt.txt", "content": content, "length": len(content)})
    except FileNotFoundError:
        return json_utf8({"error": "prompt.txt not found"}, 404)


# ============================================================
# ðŸ”— Store Webhook Registry API (Multi-Tenant Routing)
# ============================================================

@app.route('/api/webhooks/register', methods=['POST'])
def api_register_webhook():
    """ØªØ³Ø¬ÙŠÙ„ platform Ù„Ù…ØªØ¬Ø± Ù…Ø¹ÙŠÙ† Ù„Ø±Ø¨Ø· Webhooks Ø¨Ù€ store_id"""
    try:
        from database.db import register_webhook
        data = request.get_json()
        if not data:
            return json_utf8({"error": "Request body required"}, 400)
        store_id = data.get('store_id', 1)
        platform = data.get('platform', '')  # messenger, whatsapp, instagram
        account_id = data.get('platform_account_id', '')
        phone_id = data.get('platform_phone_id', None)
        if not platform or not account_id:
            return json_utf8({"error": "platform and platform_account_id required"}, 400)
        ok = register_webhook(store_id, platform, account_id, phone_id)
        return json_utf8({"success": ok, "store_id": store_id, "platform": platform})
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/webhooks/lookup', methods=['GET'])
def api_lookup_webhook():
    """Ø¥ÙŠØ¬Ø§Ø¯ store_id Ù…Ù† platform_account_id"""
    try:
        from database.db import get_store_id_by_platform
        platform = request.args.get('platform', '')
        account_id = request.args.get('account_id', '')
        if not platform or not account_id:
            return json_utf8({"error": "platform and account_id required"}, 400)
        store_id = get_store_id_by_platform(platform, account_id)
        return json_utf8({"store_id": store_id, "platform": platform, "account_id": account_id})
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/store/<int:store_id>')
def api_store_info(store_id):
    try:
        from database.db import get_store
        store = get_store(store_id)
        if store:
            return json_utf8({"id": store["id"], "name": store["name"], "slug": store["slug"]})
        return json_utf8({"error": "Store not found"}, 404)
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/webhooks/registered', methods=['GET'])
def api_list_webhooks():
    """Ø¹Ø±Ø¶ Ø¬Ù…ÙŠØ¹ Ø§Ù„ØªØ³Ø¬ÙŠÙ„Ø§Øª"""
    try:
        from database.db import get_all_registered_webhooks
        hooks = get_all_registered_webhooks()
        return json_utf8({"webhooks": hooks})
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


# ============================================================
# ðŸ‘‘ Tenant Onboarding â€” ØªØ³Ø¬ÙŠÙ„ ØªØ§Ø¬Ø± Ø¬Ø¯ÙŠØ¯ ÙƒØ§Ù…Ù„
# ============================================================

@app.route('/api/tenant/onboard', methods=['POST'])
def api_tenant_onboard():
    """
    ØªØ³Ø¬ÙŠÙ„ ØªØ§Ø¬Ø± Ø¬Ø¯ÙŠØ¯ ÙƒØ§Ù…Ù„ Ù…Ø¹:
    - Ø¥Ù†Ø´Ø§Ø¡ Ø§Ù„Ù…ØªØ¬Ø± (store)
    - Ø¥Ù†Ø´Ø§Ø¡ Ù…Ø¯ÙŠØ± Ø§Ù„Ø­Ø³Ø§Ø¨ (user)
    - ØªÙˆÙÙŠØ± AI Prompts Ø§ÙØªØ±Ø§Ø¶ÙŠØ©
    - ØªØ³Ø¬ÙŠÙ„ Agent Configs
    - ØªØ³Ø¬ÙŠÙ„ Webhooks (Ø§Ø®ØªÙŠØ§Ø±ÙŠ)
    
    JSON Body:
    {
        "store_name": "Ù…ØªØ¬Ø± Ø§Ù„Ø£Ø²ÙŠØ§Ø¡",
        "email": "store@example.com",
        "phone": "+213xxxxxxxx",
        "username": "admin123",
        "password": "securepass",
        "webhooks": {
            "messenger": "FB_PAGE_ID",
            "whatsapp": "WA_PHONE_NUMBER_ID",
            "instagram": "IG_ID"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return json_utf8({"error": "Request body required"}, 400)

        store_name = data.get("store_name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        webhooks = data.get("webhooks", {})

        if not store_name or not username or not password:
            return json_utf8({"error": "store_name, username, password are required"}, 400)

        # 1. ØªÙˆÙ„ÙŠØ¯ slug ÙˆØ­ÙŠØ¯ Ù…Ù† Ø§Ø³Ù… Ø§Ù„Ù…ØªØ¬Ø±
        import re, time, secrets, string as _str_mod
        slug = store_name.lower().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        if not slug or slug.strip("-") == "":
            slug = "store-" + "".join(secrets.choice(_str_mod.ascii_lowercase) for _ in range(8))

        from database.db import get_store_by_slug
        existing = get_store_by_slug(slug)
        if existing:
            slug = f"{slug}-{int(time.time())}"

        # 2. Ø¥Ù†Ø´Ø§Ø¡ store + Ù…Ø³ØªØ®Ø¯Ù… Ù…Ø¯ÙŠØ±
        store_id = 2  # Default (1 = Royal Chaussures)
        from database.db import create_store
        store_row = create_store({"name": store_name, "slug": slug, "email": email, "phone": phone})
        if store_row and isinstance(store_row, dict):
            store_id = store_row.get("id", 2)
        
        # Ø¥Ù†Ø´Ø§Ø¡ Ù…Ø³ØªØ®Ø¯Ù… admin
        from database.db import get_db
        import hashlib
        hashed = hashlib.sha256(password.encode()).hexdigest()
        _sec_db = get_db()
        _pg_mode = (os.environ.get("DB_ENGINE", "postgres") == "postgres")
        _ph = "%s" if _pg_mode else "?"
        try:
            _sec_db.execute(f"INSERT INTO users (store_id, username, password_hash, role) VALUES ({_ph}, {_ph}, {_ph}, 'store_manager')", [store_id, username, hashed])
            _sec_db.commit()
        except Exception as ue:
            logger.info(f"[ONBOARDING] User note: {_safe_str(ue)}")
        finally:
            try:
                _sec_db.close()
            except:
                pass

        # 3. AI Prompts Ø§ÙØªØ±Ø§Ø¶ÙŠØ© Ù„ÙƒÙ„ Ù…ØªØ¬Ø±
        from database.db import set_store_prompt
        set_store_prompt(store_id, "customer_support",
            f"[1. STORE IDENTITY]\nYou are the AI Customer Support Agent for {store_name}. "
            f"Be welcoming, helpful, and professional.\nKeep responses concise (2-4 sentences).")
        set_store_prompt(store_id, "sales_agent",
            f"[SALES AGENT]\nYou help customers find products at {store_name}. Recommend based on preferences.")
        set_store_prompt(store_id, "shipping_tracking",
            f"[SHIPPING AGENT]\nYou track shipments for {store_name} orders.")
        set_store_prompt(store_id, "inventory_agent",
            f"[INVENTORY AGENT]\nYou manage stock queries for {store_name}.")

        # 4. Webhooks Ø¥Ù† ÙˆØ¬Ø¯Øª (Ø§Ø®ØªÙŠØ§Ø±ÙŠ)
        from database.db import register_webhook
        for platform, account_id in webhooks.items():
            if account_id:
                wa_phone = None
                if platform == "whatsapp" and isinstance(account_id, list):
                    wa_phone = account_id[1] if len(account_id) > 1 else None
                    account_id = account_id[0]
                register_webhook(store_id, platform, str(account_id), wa_phone)

        store_subdomain = f"{slug}.{PLATFORM_DOMAIN}" if slug != "royal-chaussures" else PLATFORM_DOMAIN
        dashboard_url = f"https://{PLATFORM_DOMAIN}/dashboard/{store_id}"

        logger.info(f"[ONBOARDING] New tenant created: store_id={store_id}, name={store_name}, slug={slug}, subdomain={store_subdomain}")

        return json_utf8({
            "success": True,
            "store_id": store_id,
            "store_name": store_name,
            "slug": slug,
            "username": username,
            "subdomain": store_subdomain,
            "dashboard_url": dashboard_url,
            "message": f"Ù…ØªØ¬Ø± {store_name} Ø¬Ø§Ù‡Ø²! ØªÙ… ØªÙØ¹ÙŠÙ„ 4 ÙˆÙƒÙ„Ø§Ø¡ AI ÙˆØ§Ø³ØªÙ‚Ø¨Ø§Ù„ Ø§Ù„Ø·Ù„Ø¨Ø§Øª."
        })

    except Exception as e:
        logger.error(f"[ONBOARDING] Failed: {_safe_str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/tenant/login', methods=['POST'])
def api_tenant_login():
    """
    ØªØ³Ø¬ÙŠÙ„ Ø¯Ø®ÙˆÙ„ Ø§Ù„ØªØ§Ø¬Ø± ÙˆØ§Ù„Ø­ØµÙˆÙ„ Ø¹Ù„Ù‰ store_id Ù…Ø¹ session token
    JSON Body: {"username": "...", "password": "..."}
    """
    try:
        data = request.get_json()
        if not data:
            return json_utf8({"error": "Request body required"}, 400)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return json_utf8({"error": "username and password are required"}, 400)

        import hashlib
        from database.db import get_db
        db = get_db()
        try:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            row = db.execute(
                "SELECT u.id, u.store_id, u.role, s.name as store_name, s.slug "
                "FROM users u JOIN stores s ON u.store_id = s.id "
                "WHERE u.username = %s AND u.password_hash = %s AND s.is_active = TRUE",
                [username, hashed]
            ).fetchone()
            if not row:
                return json_utf8({"error": "Invalid credentials"}, 401)

            session_token = hashlib.sha256(f"{row['id']}:{row['store_id']}:{time.time()}:{secrets.token_hex(8)}".encode()).hexdigest()

            return json_utf8({
                "success": True,
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "slug": row["slug"],
                "role": row["role"],
                "session_token": session_token
            })
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[LOGIN] Failed: {_safe_str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return json_utf8({"error": _safe_str(e)}, 500)


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


@app.route('/onboard')
def onboard_page():
    """ØµÙØ­Ø© ØªØ³Ø¬ÙŠÙ„ Ø§Ù„ØªØ§Ø¬Ø± Ø§Ù„Ø¬Ø¯ÙŠØ¯ (Frontend Onboarding)"""
    return render_template("onboard.html")


@app.route('/api/sync/notion', methods=['POST'])
def api_sync_notion():
    """Ù†Ù‚Ø·Ø© ØªØ´ØºÙŠÙ„ Ù…Ø²Ø§Ù…Ù†Ø© Notion Ø¹Ø¨Ø± API (Ø¯ÙˆÙ† Auth Ù„Ù„Ø­Ø§Ù„Ø©)"""
    try:
        from services.notion_sync import sync_roadmap_to_notion
        success = sync_roadmap_to_notion()
        if success:
            return json_utf8({"success": True, "message": "âœ… ROADMAP â†’ Notion synced!"})
        else:
            return json_utf8({"success": False, "message": "âŒ Sync failed (check NOTION_TOKEN config)"}, 500)
    except Exception as e:
        logger.error(f"[NOTION SYNC] Failed: {_safe_str(e)}")
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/dashboard/login')
def dashboard_login_page():
    """ØµÙØ­Ø© ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù„Ù„Ù…ØªØ§Ø¬Ø±"""
    return render_template("dashboard_login.html")


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
        name = (f"{customer.get('first_name','') or ''} {customer.get('last_name','') or ''}").replace("None", "").strip() or "Ø¹Ù…ÙŠÙ„Ù†Ø§ Ø§Ù„Ø¹Ø²ÙŠØ²"
        items_summary = ", ".join([i.get("title","")[:30] for i in order.get("line_items", [])[:3]])
        message = (
            f"â¤ï¸ *Royal Chaussures* - ØªØ£ÙƒÙŠØ¯ Ø§Ù„Ø·Ù„Ø¨\n\n"
            f"Ù…Ø±Ø­Ø¨Ø§Ù‹ {name}ØŒ\n"
            f"âœ… ØªÙ… ØªØ£ÙƒÙŠØ¯ Ø·Ù„Ø¨Ùƒ *{order.get('name','')}*\n"
            f"ðŸ“¦ Ø§Ù„Ù…Ù†ØªØ¬Ø§Øª: {items_summary}\n"
            f"ðŸ’° Ø§Ù„Ù…Ø¨Ù„Øº: {order.get('total_price','0')} DZD\n"
            f"ðŸšš Ø³ÙŠØªÙ… Ø´Ø­Ù†Ù‡ Ù‚Ø±ÙŠØ¨Ø§Ù‹ Ø¹Ø¨Ø± ZR Express\n\n"
            f"Ø´ÙƒØ±Ø§Ù‹ Ù„Ø«Ù‚ØªÙƒ! ðŸ‘ âœ¨\n"
            f"ðŸ“ Ø§Ù„Ø¥Ù…Ø§Ù…Ø©ØŒ ØªÙ„Ù…Ø³Ø§Ù† | ðŸ“ž 0659832426"
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
                        "line_items": [{"title": prod or "Ù…Ù†ØªØ¬Ø§Øª"}],
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


@app.route('/dashboard/agents')
def dashboard_agents():
    """AI Agents Management Dashboard page"""
    try:
        return render_template("agents_dashboard.html")
    except Exception as e:
        _log_safe(logger.error, "Agents dashboard template error", e)
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/messages')
def api_messages():
    """Get recent messages across all platforms (Multi-Store)"""
    try:
        limit = int(request.args.get("limit", 50))
        platform = request.args.get("platform", "")
        search = str(request.args.get("search", "")).strip()
        _sd = _get_store_id_from_subdomain()
        store_id = _sd if _sd else request.args.get("store_id", 1, type=int)
        conn = _open_orders_db()
        c = conn.cursor()
        query = "SELECT * FROM messages WHERE store_id=?"
        params = [store_id]
        conditions = []
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if search:
            conditions.append("(message LIKE ? OR reply LIKE ? OR sender_id LIKE ?)")
            s = f"%{search}%"
            params.extend([s, s, s])
        if conditions:
            query += " AND " + " AND ".join(conditions)
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


# ============================================================
# PHASE 2: AI AGENTS MANAGEMENT API (5 Agents System)
# ============================================================
# يدير الوكلاء الخمسة: Sales, Campaign, Engagement, Analytics + Customer Support + Shipping

@app.route('/api/agents/config', methods=['GET'])
def api_agents_config():
    """إرجاع إعدادات جميع الوكلاء"""
    try:
        from agents.router import get_route_stats
        stats = get_route_stats()
        return json_utf8(stats)
    except Exception as e:
        return json_utf8({"error": _safe_str(e), "agents": []}, 500)


@app.route('/api/agents/switch', methods=['POST'])
def api_agents_switch():
    """تغيير الوكيل النشط"""
    try:
        from agents.router import set_active_agent, get_active_agent
        data = request.get_json() or {}
        agent_id = data.get("agent_id", "")
        if not agent_id:
            return json_utf8({"error": "agent_id required"}, 400)
        if set_active_agent(agent_id):
            current_id, current_config = get_active_agent()
            logger.info(f"[AGENTS] Switched to {agent_id} ({current_config['name']})")
            return json_utf8({"success": True, "active_agent": current_id, "agent": current_config})
        return json_utf8({"error": f"Unknown agent: {agent_id}"}, 400)
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


@app.route('/api/agents/detect', methods=['POST'])
def api_agents_detect():
    """كشف الوكيل المناسب لرسالة معينة"""
    try:
        from agents.router import route_by_intent
        data = request.get_json() or {}
        message = data.get("message", "")
        platform = data.get("platform", "messenger")
        uid = data.get("uid", "unknown")
        if not message:
            return json_utf8({"error": "message required"}, 400)
        result = route_by_intent(message, platform, uid)
        return json_utf8(result)
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/agents/<agent_id>/info', methods=['GET'])
def api_agent_info(agent_id):
    """معلومات وكيل معين"""
    try:
        from agents.router import get_agent_config
        config = get_agent_config(agent_id)
        if config:
            return json_utf8(config)
        return json_utf8({"error": f"Agent {agent_id} not found"}, 404)
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


# ============================================================
# CAMPAIGN AGENT API (العروض والحملات التسويقية)
# ============================================================

@app.route('/api/campaigns/active', methods=['GET'])
def api_campaigns_active():
    """إرجاع الحملات النشطة حالياً"""
    try:
        from agents.campaign_agent import get_active_campaigns, format_campaign_reply
        campaigns = get_active_campaigns()
        return json_utf8({
            "active_campaigns": campaigns,
            "count": len(campaigns),
            "formatted": format_campaign_reply(campaigns)
        })
    except Exception as e:
        return json_utf8({"error": _safe_str(e), "active_campaigns": []}, 500)


@app.route('/api/campaigns/register', methods=['POST'])
def api_campaigns_register():
    """تسجيل حملة جديدة (في الذاكرة فقط حالياً)"""
    # TODO: تخزين الحملات في قاعدة البيانات
    return json_utf8({"success": True, "message": "Campaign registration API ready. DB storage coming soon."})


# ============================================================
# ANALYTICS AGENT API (التقارير والتحليلات)
# ============================================================

@app.route('/api/analytics/sales-summary', methods=['GET'])
def api_analytics_sales_summary():
    """تقرير مبيعات مختصر"""
    try:
        _sd = _get_store_id_from_subdomain()
        store_id = _sd if _sd else request.args.get("store_id", 1, type=int)
        period = request.args.get("period", "daily")  # daily, weekly, monthly
        
        conn = _open_orders_db()
        c = conn.cursor()
        
        if period == "daily":
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders WHERE store_id=? AND date(created_at)=date('now')", [store_id])
            today = c.fetchone()
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders WHERE store_id=? AND date(created_at)=date('now','-1 day')", [store_id])
            yesterday = c.fetchone()
        elif period == "weekly":
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders WHERE store_id=? AND created_at >= datetime('now', '-7 days')", [store_id])
            today = c.fetchone()
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders WHERE store_id=? AND created_at >= datetime('now', '-14 days') AND created_at < datetime('now', '-7 days')", [store_id])
            yesterday = c.fetchone()
        else:  # monthly
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders WHERE store_id=? AND strftime('%Y-%m', created_at)=strftime('%Y-%m', 'now')", [store_id])
            today = c.fetchone()
            c.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders WHERE store_id=? AND strftime('%Y-%m', created_at)=strftime('%Y-%m', 'now', '-1 month')", [store_id])
            yesterday = c.fetchone()
        
        # Top products
        c.execute("SELECT product, COUNT(*) as cnt, SUM(total_price) as rev FROM orders WHERE store_id=? GROUP BY product ORDER BY cnt DESC LIMIT 5", [store_id])
        top_products = [{"name": r[0], "count": r[1], "revenue": r[2]} for r in c.fetchall()]
        
        conn.close()
        
        return json_utf8({
            "period": period,
            "current_period": {"orders": today[0], "revenue": today[1]},
            "previous_period": {"orders": yesterday[0], "revenue": yesterday[1]},
            "top_products": top_products,
            "store_id": store_id
        })
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


# ============================================================
# ENGAGEMENT AGENT API (التفاعل والولاء)
# ============================================================

@app.route('/api/engagement/loyalty-status', methods=['GET'])
def api_engagement_loyalty():
    """حالة برنامج الولاء (جاهزية API)"""
    return json_utf8({
        "status": "ready",
        "features": ["post_purchase_followup", "review_collection", "loyalty_points", "birthday_greetings", "satisfaction_survey"],
        "note": "Engagement API ready. Full loyalty program DB storage coming soon."
    })


@app.route('/api/engagement/followup', methods=['POST'])
def api_engagement_followup():
    """إرسال متابعة لزبون بعد الشراء"""
    try:
        from agents.engagement_agent import format_followup_reply
        data = request.get_json() or {}
        customer_name = data.get("customer_name", "عميلتنا")
        days_since = data.get("days_since_purchase", 3)
        product_name = data.get("product_name", "منتج")
        reply = format_followup_reply(customer_name, days_since, product_name)
        return json_utf8({"success": True, "message": reply})
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


# ????????? Main ?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    logger.info(f"Starting Royal Chaussures Server on port {port}")
    app.run(host='0.0.0.0', port=port)



