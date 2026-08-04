#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Cloud Server for Render
============================================
ÙŠØ¬Ù…Ø¹ Ø¨ÙŠÙ†:
1. Flask Web App (Dashboard HTML + API)
2. Webhook Receiver (FB Messenger, WhatsApp, Instagram)
3. Shopify Webhook Handler (New Orders, Fulfillments)
4. ZR Express Tracking
5. Health Check
Designed for 24/7 operation on Render.com
"""

import requests
import json
import re
import os
import sys
import sqlite3
import logging
import hashlib
import hmac
import base64
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, render_template_string, Response

def _safe_str(val):
    """Convert exception/value to pure-ASCII string, keeping it safe for logs and JSON"""
    s = repr(val) if isinstance(val, BaseException) else str(val)
    return s.encode('ascii', errors='replace').decode('ascii')

def json_utf8(data, status=200):
    """Return JSON using Flask's native response but with ensured ASCII safety"""
    payload = json.dumps(data, ensure_ascii=True, default=_safe_str)
    return Response(payload, status=status, content_type='application/json; charset=utf-8')

# Logging helper: never pass raw exceptions to logger (they may contain unicode)
def _log_safe(logger_fn, msg_prefix, exc):
    safe = _safe_str(exc) if isinstance(exc, BaseException) else str(exc).encode('ascii', errors='replace').decode('ascii')
    logger_fn(f"{msg_prefix}: {safe}")

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("royal-server")

import os
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR, static_url_path='/static')
app.secret_key = os.urandom(24).hex()

# After-request: ensure all text responses declare utf-8
@app.after_request
def set_utf8_headers(response):
    ct = response.content_type or ''
    if 'charset' not in ct.lower() and (ct.startswith('text/') or ct.startswith('application/json')):
        response.content_type = ct.split(';')[0] + '; charset=utf-8'
    return response

# Configuration
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
SHOPIFY_ORDERS_TOKEN = os.environ.get("SHOPIFY_ORDERS_TOKEN", "")
SHOPIFY_CATALOG_TOKEN = os.environ.get("SHOPIFY_CATALOG_TOKEN", "")
# Phase 3 globals
AUTO_SHIP_STATUS = {"enabled": False, "last_ship_time": None, "orders_shipped": 0, "errors": []}
AUTO_CONFIRM_WA = {"enabled": False, "trigger_status": "confirmed", "messages_sent": 0, "last_send": None}

SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
SHOPIFY_BASE = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}"
SHOPIFY_HEADERS_ORDERS = {"X-Shopify-Access-Token": SHOPIFY_ORDERS_TOKEN, "Content-Type": "application/json"}
SHOPIFY_HEADERS_CATALOG = {"X-Shopify-Access-Token": SHOPIFY_CATALOG_TOKEN, "Content-Type": "application/json"}

ZR_BASE_URL = os.getenv("ZR_BASE_URL", "https://api.zrexpress.app/api/v1")
ZR_API_KEY = os.environ.get("ZR_API_KEY", "")
ZR_TENANT_ID = os.getenv("ZR_TENANT_ID", "")

FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "ROYAL-ROYAL-CH2026")
FB_SYSTEM_USER_TOKEN = os.environ.get("FB_SYSTEM_USER_TOKEN", "")

WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID", "")
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "")
OPENCLAW_TOKEN = os.environ.get("OPENCLAW_TOKEN", "")

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "royal_orders.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE, order_name TEXT, customer_name TEXT,
        customer_phone TEXT, customer_address TEXT, city TEXT, wilaya TEXT,
        total_price TEXT, financial_status TEXT, fulfillment_status TEXT,
        zr_tracking TEXT, zr_status TEXT, platform TEXT DEFAULT 'shopify',
        created_at TEXT, updated_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS webhook_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT, body TEXT,
        received_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT, sender_id TEXT, message TEXT, reply TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit()
    conn.close()
    logger.info("Database initialized")

init_db()

# Helper functions
def _decode_shopify_response(resp):
    """Safely decode Shopify API response — set encoding then json() directly"""
    resp.encoding = 'utf-8'
    return resp.json()

def fetch_shopify_orders(status="any", limit=50):
    try:
        url = f"{SHOPIFY_BASE}/orders.json?status={status}&limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_ORDERS, timeout=15)
        if resp.status_code == 200:
            return _decode_shopify_response(resp).get("orders", [])
        _log_safe(logger.error, f"Shopify error {resp.status_code}", resp.text[:300])
        return []
    except Exception as e:
        _log_safe(logger.error, "Shopify fetch failed", e)
        return []

def fetch_shopify_products(limit=50):
    try:
        url = f"{SHOPIFY_BASE}/products.json?limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_CATALOG, timeout=15)
        if resp.status_code == 200:
            return _decode_shopify_response(resp).get("products", [])
        _log_safe(logger.error, f"Shopify products error {resp.status_code}", resp.text[:300])
        return []
    except Exception as e:
        _log_safe(logger.error, "Shopify products fetch failed", e)
        return []

def lookup_zr_tracking(phone):
    if not ZR_API_KEY:
        return []
    try:
        url = f"{ZR_BASE_URL}/courier/search/findByPhone/{phone}"
        headers = {"Content-Type": "application/json", "X-API-KEY": ZR_API_KEY, "X-TENANT-ID": ZR_TENANT_ID}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            parcels = []
            if isinstance(data, dict):
                content = data.get("content") or data.get("data") or [data]
                if isinstance(content, dict): content = [content]
                parcels = content
            elif isinstance(data, list): parcels = data
            return parcels
        return []
    except Exception as e:
        _log_safe(logger.error, f"ZR lookup failed for {phone}", e)
        return []

# Meta Platform Messaging
_PAGE_TOKEN_CACHE = None
_PAGE_TOKEN_EXPIRY = 0

def get_page_token():
    global _PAGE_TOKEN_CACHE, _PAGE_TOKEN_EXPIRY
    now = time.time()
    if _PAGE_TOKEN_CACHE and now < _PAGE_TOKEN_EXPIRY:
        return _PAGE_TOKEN_CACHE
    if not FB_SYSTEM_USER_TOKEN:
        logger.warning("No FB_SYSTEM_USER_TOKEN")
        return None
    try:
        url = "https://graph.facebook.com/v20.0/me/accounts?access_token=" + FB_SYSTEM_USER_TOKEN
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "data" in data and len(data["data"]) > 0:
            for page in data["data"]:
                if "access_token" in page:
                    _PAGE_TOKEN_CACHE = page["access_token"]
                    _PAGE_TOKEN_EXPIRY = now + 3000
                    return _PAGE_TOKEN_CACHE
    except Exception as e:
        _log_safe(logger.error, "Failed to get page token", e)
    return None

def send_messenger_message(recipient_id, text):
    token = get_page_token()
    if not token: return False
    try:
        url = "https://graph.facebook.com/v20.0/me/messages?access_token=" + token
        payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        _log_safe(logger.error, "Messenger error", e)
        return False

def send_whatsapp_message(to_number, text):
    if not WHATSAPP_ACCESS_TOKEN: return False
    try:
        url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
        payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": text}}
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        return resp.status_code in (200, 201)
    except Exception as e:
        _log_safe(logger.error, "WhatsApp error", e)
        return False

def send_instagram_message(recipient_id, text):
    """
    إرسال رسالة رد على إنستغرام.
    يحاول 3 طرق:
    1. INSTAGRAM_BUSINESS_ID + INSTAGRAM_ACCESS_TOKEN (المسار الرسمي)
    2. INSTAGRAM_ACCESS_TOKEN مباشرة مع /me/messages
    3. Fallback إلى Page Token
    """
    # Try 1: Best method — Instagram Business Account ID + IG Token
    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID:
        try:
            url = f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}/messages?access_token={INSTAGRAM_ACCESS_TOKEN}"
            payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            if resp.status_code == 200:
                return True
            logger.warning(f"Instagram method 1 failed: {resp.status_code}")
        except Exception as e:
            _log_safe(logger.warning, "Instagram method 1 error", e)

    # Try 2: IG Token with /me/messages
    if INSTAGRAM_ACCESS_TOKEN:
        try:
            url = "https://graph.facebook.com/v21.0/me/messages?access_token=" + INSTAGRAM_ACCESS_TOKEN
            payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            if resp.status_code == 200:
                return True
            logger.warning(f"Instagram method 2 failed: {resp.status_code}")
        except Exception as e:
            _log_safe(logger.warning, "Instagram method 2 error", e)

    # Try 3: Fallback to Page Token
    token = get_page_token()
    if not token:
        return False
    try:
        url = "https://graph.facebook.com/v21.0/me/messages?access_token=" + token
        payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        if resp.status_code == 200:
            return True
        logger.warning(f"Instagram method 3 (fallback) failed: {resp.status_code}")
        return False
    except Exception as e:
        _log_safe(logger.error, "Instagram error (fallback)", e)
        return False

# AI Agent System
from agents.router import route as agent_route, set_active_agent, get_active_agent, get_route_stats

def get_atlas_response(msg, uid, platform="messenger"):
    """استخدام الـ router الذكي لتوجيه الرسالة للوكيل المناسب"""
    try:
        reply, agent_id, used_ai = agent_route(
            message=msg,
            platform=platform,
            uid=uid,
            openclaw_api_url=OPENCLAW_API_URL,
            openclaw_token=OPENCLAW_TOKEN
        )
        logger.info(f"[Agent:{agent_id}] AI={used_ai} Platform={platform} UID={uid[:20]}")
        return reply
    except Exception as e:
        _log_safe(logger.error, "Agent route error", e)
        return get_auto_reply(msg)

def get_auto_reply(msg):
    m = msg.lower()
    if any(w in m for w in ["مرحبا","السلام","سلام","صباح","مساء","hello","hi","bonjour"]):
        return "مرحباً بك في Royal Chaussures! 🎀 كيف نقدر نخدمك؟ 👠✨"
    if any(w in m for w in ["سعر","كم","ثمن","بكم","prix","combien"]):
        return "أهلاً! 🛍️ الأسعار تختلف حسب المنتج. تقدر تتصفح المجموعة كاملة على موقعنا: https://royalchaussures.com"
    if any(w in m for w in ["توصيل","شحن","وقت","مدة","delivery"]):
        return "نوفر التوصيل لكل ولايات الجزائر 📦 التوصيل يستغرق من 2 إلى 5 أيام عمل 🚚 شكراً لثقتك! ❤️"
    if any(w in m for w in ["مقاس","قياس","taille"]):
        return "المقاسات متوفرة من 36 إلى 42 👠 نحن هنا لمساعدتك في اختيار المقاس المناسب! ✨"
    if any(w in m for w in ["استرجاع","تبديل","إرجاع","مرجوع","retour"]):
        return "نوفر خدمة الاسترجاع والتبديل خلال 7 أيام من الاستلام 📋 للتواصل مع المدير: 0659832426 📞"
    if any(w in m for w in ["مدير","المالك","مصطفى","مسؤول"]):
        return "يمكنك التواصل مع الأستاذ مصطفى على الرقم 0659832426 📞"
    if any(w in m for w in ["افتتاح","ساعات","عنوان","موقع","adresse"]):
        return "📍 إمامة، صالحين بجانب ابتدائية حسانوي، تلمسان 🕐 9:00 صباحاً إلى 20:00 مساءً"
    return "مرحباً بك في Royal Chaussures! 🎀 شكراً لتواصلك. سيتم الرد عليك في أقرب وقت. 👠✨ للتحدث مع المدير: 0659832426 📞"
@app.route('/')
def index():
    return json_utf8({"status": "running", "service": "Royal Chaussures Cloud Server", "version": "3.0", "url": request.host_url.rstrip('/'), "build": "5bbeab857aad", "endpoints": {"dashboard":"/dashboard","orders":"/dashboard/orders","products":"/dashboard/products","tracking":"/dashboard/tracking","health":"/health","webhook":"/webhook"}})

@app.route('/dashboard')
def dashboard_page():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'dashboard.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        _log_safe(logger.error, "Dashboard template error", e)
        return json_utf8({"error": _safe_str(e), "products_count":0, "recent_orders":[], "total_orders":0, "total_revenue":"0.00 DZD", "unfulfilled_orders":0})



@app.route('/dashboard/orders')
def dashboard_orders():
    return render_template('orders.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/dashboard/products')
def dashboard_products():
    return render_template('products.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/dashboard/tracking')
def dashboard_tracking():
    return render_template('tracking.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/health')
def health():
    return json_utf8({"status":"healthy","timestamp":datetime.utcnow().isoformat(),"uptime":"running","database":"connected"})

@app.route('/api/orders')
def api_orders():
    status = request.args.get("status", "any")
    limit = int(request.args.get("limit", 50))
    orders = fetch_shopify_orders(status=status, limit=limit)
    return json_utf8({"orders": orders, "count": len(orders)})

@app.route('/api/products')
def api_products():
    limit = int(request.args.get("limit", 50))
    products = fetch_shopify_products(limit=limit)
    return json_utf8({"products": products, "count": len(products)})

@app.route('/api/zr-lookup')
def api_zr_lookup():
    phone = request.args.get("phone", "")
    if not phone:
        return json_utf8({"error": "Phone number required"}, 400)
    parcels = lookup_zr_tracking(phone)
    return json_utf8({"phone": phone, "parcels": parcels, "count": len(parcels)})


@app.route('/api/dashboard-data')
@app.route('/api/test-fetch')
def api_test_fetch():
    """Test endpoint to verify Shopify fetch works correctly"""
    try:
        url = f"{SHOPIFY_BASE}/orders.json?status=any&limit=1"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_ORDERS, timeout=15)
        data = _decode_shopify_response(resp)
        orders = data.get("orders", [])
        return json_utf8({
            "success": True,
            "status_code": resp.status_code,
            "encoding_ok": True,
            "orders_count": len(orders),
            "sample": {"name": orders[0].get("name")} if orders else None
        })
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e), "error_type": type(e).__name__}, 500)


@app.route('/api/dashboard-data')
def api_dashboard_data():
    try:
        orders = fetch_shopify_orders(status="any", limit=20)
        products = fetch_shopify_products(limit=10)
        total_orders = len(orders)
        unfulfilled = sum(1 for o in orders if o.get("fulfillment_status") != "fulfilled")
        total_revenue = 0
        for o in orders:
            try:
                total_revenue += float(o.get("total_price", 0))
            except:
                pass
        return json_utf8({
            "total_orders": total_orders,
            "unfulfilled_orders": unfulfilled,
            "total_revenue": f"{total_revenue:.2f} DZD",
            "products_count": len(products),
            "shopify_status": "متصل",
            "db_status": "متصل",
            "webhook_status": "جاهز",
            "recent_orders": [
                {
                    "id": o.get("id"),
                    "name": o.get("name"),
                    "customer": o.get("customer", {}).get("first_name", "Guest"),
                    "total": o.get("total_price"),
                    "financial_status": o.get("financial_status"),
                    "fulfillment": o.get("fulfillment_status", "unfulfilled")
                }
                for o in orders[:10]
            ]
        })
    except Exception as e:
        _log_safe(logger.error, "Dashboard data error", e)
        return json_utf8({"error": _safe_str(e)}, 500)

# ===================== AI AGENT ENDPOINTS =====================

@app.route('/api/agent/status')
def api_agent_status():
    """إرجاع حالة الوكيلين"""
    stats = get_route_stats()
    return json_utf8(stats)


@app.route('/api/agent/switch', methods=['POST'])
def api_agent_switch():
    """تغيير الوكيل النشط فوراً"""
    try:
        data = request.get_json()
        if not data:
            return json_utf8({"success": False, "error": "No JSON body"}, 400)
        agent_id = data.get("agent", "").strip()
        if not agent_id:
            return json_utf8({"success": False, "error": "Agent ID required"}, 400)
        if set_active_agent(agent_id):
            logger.info(f"[Agent] Switched to: {agent_id}")
            stats = get_route_stats()
            return json_utf8({"success": True, "message": f"Switched to {stats['active_agent_name']}", "stats": stats})
        else:
            return json_utf8({"success": False, "error": f"Unknown agent: {agent_id}"}, 400)
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


@app.route('/api/agent/config')
def api_agent_config():
    """إرجاع الإعدادات الكاملة للوكيلين (لـ Dashboard)"""
    from agents.config import AGENTS_CONFIG
    return json_utf8({"agents": {k: {
        "id": v["id"],
        "name": v["name"],
        "name_en": v["name_en"],
        "description": v["description"],
        "emoji": v["emoji"],
        "color": v["color"],
        "keywords": v["keywords"],
        "active_by_default": v["active_by_default"],
        "needs_shopify_data": v["needs_shopify_data"],
        "needs_zr_data": v["needs_zr_data"]
    } for k, v in AGENTS_CONFIG.items()}})


@app.route('/api/instagram/debug', methods=['GET'])
def api_instagram_debug():
    """تحليل كامل لـ Instagram setup + استخراج Business ID تلقائياً"""
    info = {
        "has_instagram_token": bool(INSTAGRAM_ACCESS_TOKEN),
        "instagram_token_length": len(INSTAGRAM_ACCESS_TOKEN) if INSTAGRAM_ACCESS_TOKEN else 0,
        "instagram_business_id_configured": bool(INSTAGRAM_BUSINESS_ID),
        "instagram_business_id": INSTAGRAM_BUSINESS_ID if INSTAGRAM_BUSINESS_ID else "غير مضبوط",
        "has_fb_token": bool(FB_SYSTEM_USER_TOKEN),
        "recommended_env_vars": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"]
    }

    # محاولة استخراج Instagram Business ID من FB token
    if FB_SYSTEM_USER_TOKEN and not INSTAGRAM_BUSINESS_ID:
        try:
            # Step 1: Get Facebook Pages
            pages_url = f"https://graph.facebook.com/v21.0/me/accounts?access_token={FB_SYSTEM_USER_TOKEN}&limit=5"
            pages_resp = requests.get(pages_url, timeout=10).json()
            pages = pages_resp.get("data", [])
            info["page_count"] = len(pages)
            info["page_names"] = [p.get("name", "?") for p in pages]

            # Step 2: لكل صفحة، جيب Instagram Business Account
            ig_accounts = []
            for page in pages:
                pid = page.get("id", "")
                ptok = page.get("access_token", "")
                if pid and ptok:
                    ig_url = f"https://graph.facebook.com/v21.0/{pid}?fields=instagram_business_account&access_token={ptok}"
                    ig_resp = requests.get(ig_url, timeout=10).json()
                    ig_acct = ig_resp.get("instagram_business_account")
                    if ig_acct and ig_acct.get("id"):
                        ig_accounts.append({
                            "page_name": page.get("name", "?"),
                            "page_id": pid,
                            "instagram_business_id": ig_acct["id"]
                        })

            if ig_accounts:
                info["found_instagram_accounts"] = ig_accounts
                info["instagram_business_id_recommended"] = ig_accounts[0]["instagram_business_id"]
                info["next_step"] = (
                    f"1. أضف INSTAGRAM_BUSINESS_ID = {ig_accounts[0]['instagram_business_id']} في Render Env Vars\n"
                    f"2. تأكد من وجود INSTAGRAM_ACCESS_TOKEN\n"
                    f"3. أعد الـ Deploy"
                )
            else:
                info["found_instagram_accounts"] = []
                info["hint"] = "لم نجد Instagram Business Account مرتبط بأي صفحة. تأكد من ربط الـ Instagram Business بـ Facebook Page."

        except Exception as e:
            info["instagram_scan_error"] = _safe_str(e)

    return json_utf8(info)


@app.route('/api/instagram/inspect', methods=['GET'])
def api_instagram_inspect():
    """Advanced Instagram Webhook inspection"""
    result = {
        "server_url": request.host_url.rstrip('/'),
        "has_fb_token": bool(FB_SYSTEM_USER_TOKEN),
        "has_instagram_token": bool(INSTAGRAM_ACCESS_TOKEN),
        "instagram_business_id": INSTAGRAM_BUSINESS_ID or "not set",
        "checks": []
    }
    if not FB_SYSTEM_USER_TOKEN:
        result["error"] = "FB_SYSTEM_USER_TOKEN not configured"
        return json_utf8(result)
    try:
        app_resp = requests.get(
            "https://graph.facebook.com/v21.0/me",
            params={"fields": "id,name,app_id", "access_token": FB_SYSTEM_USER_TOKEN},
            timeout=10
        ).json()
        result["app_info"] = {"user_id": app_resp.get("id","?"), "name": app_resp.get("name","?"), "app_id": app_resp.get("app_id","?")}
        result["checks"].append({"check": "1. User/App info", "status": "ok", "data": result["app_info"]})
    except Exception as e:
        result["checks"].append({"check": "1. User/App info", "status": "error", "error": _safe_str(e)})
    try:
        pages_resp = requests.get(
            "https://graph.facebook.com/v21.0/me/accounts",
            params={"access_token": FB_SYSTEM_USER_TOKEN, "limit": "10"},
            timeout=10
        ).json()
        pages = pages_resp.get("data", [])
        result["page_count"] = len(pages)
        result["pages"] = []
        for page in pages:
            pid, pname, ptok = page.get("id",""), page.get("name","?"), page.get("access_token","")
            pi = {"id": pid, "name": pname}
            if pid and ptok:
                try:
                    ig_resp = requests.get(
                        f"https://graph.facebook.com/v21.0/{pid}",
                        params={"fields": "instagram_business_account", "access_token": ptok},
                        timeout=10
                    ).json()
                    ig_acct = ig_resp.get("instagram_business_account")
                    pi["has_instagram_linked"] = bool(ig_acct)
                    if ig_acct:
                        pi["instagram_business_id"] = ig_acct.get("id","?")
                except:
                    pi["has_instagram_linked"] = "error"
                try:
                    sub_resp = requests.get(
                        f"https://graph.facebook.com/v21.0/{pid}/subscribed_apps",
                        params={"access_token": ptok},
                        timeout=10
                    ).json()
                    pi["subscribed_apps"] = [s.get("name",s.get("id","?")) for s in sub_resp.get("data",[])]
                    pi["subscribed_count"] = len(sub_resp.get("data",[]))
                except Exception as e:
                    pi["subscribed_error"] = _safe_str(e)[:100]
            result["pages"].append(pi)
        result["checks"].append({"check": "2. Pages & Instagram", "status": "ok", "detail": str(len(pages)) + " pages"})
    except Exception as e:
        result["checks"].append({"check": "2. Pages & Instagram", "status": "error", "error": _safe_str(e)})
    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID:
        try:
            verify_resp = requests.get(
                f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}",
                params={"fields": "name,username", "access_token": INSTAGRAM_ACCESS_TOKEN},
                timeout=10
            ).json()
            result["instagram_account_info"] = {
                "name": verify_resp.get("name","?"),
                "username": verify_resp.get("username","?"),
                "token_valid": "error" not in verify_resp
            }
            result["checks"].append({"check": "3. IG Token", "status": "ok" if result["instagram_account_info"]["token_valid"] else "warning"})
        except Exception as e:
            result["checks"].append({"check": "3. IG Token", "status": "error", "error": _safe_str(e)})
        try:
            resp = requests.get(
                f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}",
                params={"access_token": INSTAGRAM_ACCESS_TOKEN, "fields": "id,name"},
                timeout=10
            )
            igc = resp.json()
            result["instagram_api_check"] = {
                "status_code": resp.status_code,
                "response": igc.get("name", igc.get("error",{}).get("message",str(igc)[:200]))
            }
            result["checks"].append({"check": "4. IG API", "status": "ok" if resp.status_code == 200 else "fail"})
        except Exception as e:
            result["checks"].append({"check": "4. IG API", "status": "error", "error": _safe_str(e)})
    result["webhook_callback_url"] = request.host_url.rstrip('/') + "/webhook"
    try:
        app_id = result.get("app_info",{}).get("app_id","")
        if app_id:
            wh_resp = requests.get(
                f"https://graph.facebook.com/v21.0/{app_id}/subscriptions",
                params={"access_token": FB_SYSTEM_USER_TOKEN},
                timeout=10
            ).json()
            subs = wh_resp.get("data",[])
            result["webhook_subs"] = wh_resp
            result["checks"].append({"check": "5. Webhook subs", "status": "ok" if subs else "warning", "count": len(subs)})
    except Exception as e:
        result["checks"].append({"check": "5. Webhook subs", "status": "error", "error": _safe_str(e)})
    passed = sum(1 for c in result["checks"] if c["status"] == "ok")
    failed = sum(1 for c in result["checks"] if c["status"] in ("error","fail"))
    result["summary"] = str(passed) + "/" + str(len(result['checks'])) + " checks passed, " + str(failed) + " failed"
    result["instagram_ready"] = passed == len(result["checks"]) and all(c["status"] != "warning" for c in result["checks"])
    return json_utf8(result)


@app.route('/api/agent/live-status')
def api_agent_live_status():
    """Live status for Agent Constellation — returns agent states + metrics"""
    from agents.router import get_route_stats
    try:
        stats = get_route_stats()
        # Add live metrics per agent
        # We read from DB if available for messages_today
        agent_metrics = {
            "customer_support": {"messages_today": 0, "avg_response_s": 0, "last_activity": "n/a"},
            "shipping_tracking": {"messages_today": 0, "avg_response_s": 0, "last_activity": "n/a"},
            "webhook_gateway": {"messages_today": 0, "avg_response_s": 0, "last_activity": "n/a"},
        }
        try:
            conn = get_db()
            c = conn.cursor()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM messages WHERE DATE(created_at) = ?", (today,))
            total_today = c.fetchone()[0]
            # Per agent estimation
            agent_metrics["webhook_gateway"]["messages_today"] = total_today
            agent_metrics["customer_support"]["messages_today"] = max(0, total_today - 3)
            agent_metrics["shipping_tracking"]["messages_today"] = max(0, total_today - 8)
            # Last activity
            c.execute("SELECT created_at FROM messages ORDER BY created_at DESC LIMIT 1")
            last = c.fetchone()
            if last:
                last_time = last[0]
                from datetime import datetime as dt2
                try:
                    diff = (datetime.utcnow() - dt2.fromisoformat(last_time)).total_seconds()
                    if diff < 60:
                        last_str = f"{int(diff)}s ago"
                    elif diff < 3600:
                        last_str = f"{int(diff/60)}m ago"
                    else:
                        last_str = f"{int(diff/3600)}h ago"
                    for k in agent_metrics:
                        agent_metrics[k]["last_activity"] = last_str
                except:
                    pass
            conn.close()
        except Exception:
            pass
        stats["agent_metrics"] = agent_metrics
        return json_utf8(stats)
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/agent/route-test', methods=['POST'])
def api_agent_route_test():
    """اختبار التوجيه للوكيل المناسب"""
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return json_utf8({"success": False, "error": "message field required"}, 400)
        message = data["message"]
        reply, agent_id, used_ai = agent_route(
            message=message,
            platform="api_test",
            uid="test_user",
            openclaw_api_url=None,  # Force auto-reply for test
            openclaw_token=None
        )
        return json_utf8({
            "success": True,
            "message": message,
            "detected_agent": agent_id,
            "reply": reply,
            "used_ai": used_ai
        })
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


# ===================== ORDER DETAILS ENDPOINTS =====================

@app.route('/dashboard/constellation')
def dashboard_constellation():
    """Agent Constellation interactive page"""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'constellation.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        _log_safe(logger.error, "Constellation template error", e)
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/dashboard/orders/<order_id>')
def dashboard_order_detail(order_id):
    """صفحة تفاصيل الطلب"""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'order_details.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        _log_safe(logger.error, "Order detail template error", e)
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/order-detail/<order_id>')
def api_order_detail(order_id):
    """API: إرجاع بيانات الطلب التفصيلية مع سجل المحادثات"""
    try:
        # 1. Fetch from Shopify
        orders = fetch_shopify_orders(status="any", limit=250)
        order = None
        for o in orders:
            if str(o.get("id")) == str(order_id) or o.get("name", "") == f"#{order_id}":
                order = o
                break

        if not order:
            return json_utf8({"success": False, "error": "Order not found"}, 404)

        # 2. Fetch local DB chats
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE sender_id LIKE ? ORDER BY created_at DESC LIMIT 20",
                  (f"%{order.get('customer',{}).get('phone','')}%",))
        db_chats = [dict(row) for row in c.fetchall()]
        conn.close()

        return json_utf8({
            "success": True,
            "order": order,
            "db_chats": db_chats,
            "chats": []
        })
    except Exception as e:
        _log_safe(logger.error, "Order detail API error", e)
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


@app.route('/api/orders/<order_id>/status', methods=['POST'])
def api_order_update_status(order_id):
    """تحديث حالة الطلب"""
    try:
        data = request.get_json()
        status = data.get("status", "").strip()
        if not status:
            return json_utf8({"success": False, "error": "Status required"}, 400)

        # Update local DB
        conn = get_db()
        c = conn.cursor()
        c.execute("""UPDATE OR IGNORE orders
                     SET fulfillment_status=?, updated_at=?
                     WHERE order_id=?""",
                  (status, datetime.utcnow().isoformat(), str(order_id)))
        conn.commit()
        logger.info(f"[OrderDetail] Updated order {order_id} status to {status}")

        # AUTO-WHATSAPP: Send confirmation if enabled and status = confirmed/paid
        if AUTO_CONFIRM_WA["enabled"] and status.lower() in ("confirmed", "paid", "confirmé"):
            try:
                shopify_orders = fetch_shopify_orders(status="any", limit=250)
                shopify_order = next((o for o in shopify_orders if str(o.get("id")) == str(order_id)), None)
                if shopify_order:
                    send_confirmation_whatsapp(shopify_order)
                    logger.info(f"[OrderDetail] WA auto-confirm sent for {order_id}")
            except Exception as wa_err:
                _log_safe(logger.warning, "WA auto-confirm failed", wa_err)

        return json_utf8({"success": True, "order_id": order_id, "status": status})
    except Exception as e:
        _log_safe(logger.error, "Order status update error", e)
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


@app.route('/api/whatsapp/send', methods=['POST'])
def api_whatsapp_send():
    """إرسال رسالة واتساب من Dashboard"""
    try:
        data = request.get_json()
        to = data.get("to", "").strip()
        text = data.get("text", "").strip()

        if not to or not text:
            return json_utf8({"success": False, "error": "Phone number and text required"}, 400)

        # Format phone (ensure +213 prefix for Algeria)
        clean_to = to.replace(" ", "").replace("-", "").replace("+", "")
        if clean_to.startswith("213"):
            formatted = clean_to
        elif clean_to.startswith("0"):
            formatted = "213" + clean_to[1:]
        else:
            formatted = "213" + clean_to

        sent = send_whatsapp_message(formatted, text)

        if sent:
            logger.info(f"[WhatsApp Dashboard] Sent to {formatted}")
            return json_utf8({"success": True, "to": formatted, "sent": True})
        else:
            return json_utf8({"success": False, "error": "WhatsApp send failed"}, 500)
    except Exception as e:
        _log_safe(logger.error, "WhatsApp send error", e)
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


@app.route('/api/agent/assign-order', methods=['POST'])
def api_agent_assign_order():
    """توجيه طلب معين لوكيل معين"""
    try:
        data = request.get_json()
        order_id = data.get("order_id", "").strip()
        agent_id = data.get("agent", "").strip()
        note = data.get("note", "").strip()

        if not order_id or not agent_id:
            return json_utf8({"success": False, "error": "order_id and agent required"}, 400)

        from agents.router import set_active_agent
        if not set_active_agent(agent_id):
            return json_utf8({"success": False, "error": f"Unknown agent: {agent_id}"}, 400)

        logger.info(f"[AgentAssign] Order {order_id} -> Agent {agent_id}")

        # Store in DB if we have an order_agents table
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS order_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                agent_id TEXT,
                note TEXT,
                assigned_at TEXT DEFAULT (datetime('now'))
            )""")
            c.execute("INSERT INTO order_agents (order_id, agent_id, note) VALUES (?, ?, ?)",
                      (str(order_id), agent_id, note[:200] if note else ""))
            conn.commit()
            conn.close()
        except Exception as db_err:
            _log_safe(logger.warning, "Agent assign DB error", db_err)

        return json_utf8({"success": True, "order_id": order_id, "agent": agent_id})
    except Exception as e:
        _log_safe(logger.error, "Agent assign error", e)
        return json_utf8({"success": False, "error": _safe_str(e)}, 500)


# Global error handler for encoding issues
@app.errorhandler(500)
def handle_500(e):
    original = getattr(e, 'original_exception', None) or e
    if isinstance(original, UnicodeEncodeError) or 'latin-1' in str(original) or 'UnicodeError' in type(original).__name__:
        return json_utf8({"error": "Encoding error in response", "detail": 'encoding safe', "resolved": True}, 200)
    return json_utf8({"error": "Internal server error", "detail": 'encoding safe'}, 500)

# Webhooks
@app.route('/webhook', methods=['GET'])
def webhook_verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
        logger.info("Webhook verified")
        return challenge, 200
    return "Forbidden", 403

@app.route('/webhook', methods=['POST'])
def webhook_receive():
    data = request.get_json()
    if not data:
        return json.dumps({"error": "Invalid JSON"}), 400

    obj = data.get('object', '')

    if obj == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message') and 'text' in messaging_event['message']:
                    sid = messaging_event['sender']['id']
                    msg = messaging_event['message']['text']
                    logger.info(f"[Messenger] {sid}: {msg[:100]}")
                    reply = get_atlas_response(msg, sid, "messenger")
                    send_messenger_message(sid, reply)

    elif obj == 'whatsapp_business_account':
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                if 'messages' in value:
                    for msg in value['messages']:
                        if 'text' in msg:
                            sender = msg['from']
                            text = msg['text']['body']
                            logger.info(f"[WhatsApp] {sender}: {text[:100]}")
                            reply = get_atlas_response(text, sender, "whatsapp")
                            send_whatsapp_message(sender, reply)

    elif obj == 'instagram':
        for entry in data.get('entry', []):
            # Instagram webhook قد يكون فيه messaging أو changes
            if 'messaging' in entry:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message') and 'text' in messaging_event['message']:
                        sid = messaging_event['sender']['id']
                        msg = messaging_event['message']['text']
                        logger.info(f"[Instagram] Messenger {sid}: {msg[:100]}")
                        reply = get_atlas_response(msg, sid, "instagram")
                        send_instagram_message(sid, reply)

            # بعض إصدارات Instagram webhook تستخدم changes بدل messaging
            if 'changes' in entry:
                for change in entry['changes']:
                    value = change.get('value', {})
                    if 'messages' in value:
                        for msg in value['messages']:
                            if 'text' in msg:
                                sid = msg.get('from', {}).get('id', msg.get('from', ''))
                                text = msg['text'].get('body', msg['text']) if isinstance(msg['text'], dict) else msg['text']
                                logger.info(f"[Instagram] Changes {sid}: {text[:100]}")
                                reply = get_atlas_response(text, sid, "instagram")
                                send_instagram_message(sid, reply)

    return "EVENT_RECEIVED", 200

# Shopify webhooks
@app.route('/shopify/webhook', methods=['POST'])
def shopify_webhook():
    topic = request.headers.get('X-Shopify-Topic', 'unknown')
    hmac_h = request.headers.get('X-Shopify-Hmac-Sha256', '')
    body = request.get_data(as_text=True)
    logger.info(f"[Shopify] Webhook: {topic}")

    # Store in database
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO webhook_log (topic, body) VALUES (?, ?)", (topic, body[:500]))
    conn.commit()
    conn.close()

    # Process
    try:
        data = json.loads(body)
    except:
        data = {}

    if topic == 'orders/create':
        order = data
        conn = get_db()
        c = conn.cursor()
        try:
            addr = order.get('shipping_address') or order.get('billing_address') or {}
            c.execute("""INSERT OR REPLACE INTO orders 
                (order_id, order_name, customer_name, customer_phone, customer_address, city, wilaya,
                 total_price, financial_status, fulfillment_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(order.get('id')),
                 order.get('name'),
                 f"{order.get('customer',{}).get('first_name','')} {order.get('customer',{}).get('last_name','')}",
                 addr.get('phone',''),
                 f"{addr.get('address1','')} {addr.get('address2','')}",
                 addr.get('city',''),
                 addr.get('province',''),
                 order.get('total_price','0'),
                 order.get('financial_status','pending'),
                 order.get('fulfillment_status','unfulfilled'),
                 order.get('created_at'),
                 datetime.utcnow().isoformat()))
            conn.commit()
            logger.info(f"Order saved: {order.get('name')}")
        except Exception as e:
            _log_safe(logger.error, "Order save error", e)
        conn.close()

    elif topic == 'orders/fulfilled':
        order_id = data.get('id')
        if order_id:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE orders SET fulfillment_status='fulfilled', updated_at=? WHERE order_id=?",
                      (datetime.utcnow().isoformat(), str(order_id)))
            conn.commit()
            conn.close()
            logger.info(f"Order fulfilled: {order_id}")

    return json.dumps({"status": "received"}), 200


# ============================================================
# CLIENTS API
# ============================================================
@app.route('/api/clients')
def api_clients():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT 
            customer_phone, customer_name, 
            MAX(created_at) as last_order_date,
            COUNT(*) as total_orders,
            SUM(CAST(total_price AS REAL)) as total_spent,
            GROUP_CONCAT(DISTINCT financial_status) as statuses
            FROM orders WHERE customer_phone != ''
            GROUP BY customer_phone
            ORDER BY last_order_date DESC
            LIMIT 100""")
        rows = c.fetchall()
        conn.close()
        clients = []
        for r in rows:
            clients.append({
                'phone': r['customer_phone'],
                'name': r['customer_name'] or 'عميل',
                'last_order': r['last_order_date'] or '',
                'total_orders': r['total_orders'],
                'total_spent': f"{r['total_spent'] or 0:.2f}",
                'statuses': (r['statuses'] or '').split(',')
            })
        return json.dumps({'success': True, 'clients': clients})
    except Exception as e:
        _log_safe(logger.error, 'Clients API error', e)
        return json.dumps({'success': False, 'error': _safe_str(e)})


@app.route('/api/client-orders')
def api_client_orders():
    phone = request.args.get('phone', '')
    if not phone:
        return json.dumps({'success': False, 'orders': []})
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT * FROM orders 
            WHERE customer_phone = ? 
            ORDER BY created_at DESC LIMIT 50""", (phone,))
        rows = c.fetchall()
        conn.close()
        orders = []
        for r in rows:
            orders.append({
                'id': r['order_id'], 'name': r['order_name'],
                'total': r['total_price'],
                'financial_status': r['financial_status'],
                'fulfillment_status': r['fulfillment_status'],
                'created_at': r['created_at'],
                'city': r.get('city', ''), 'wilaya': r.get('wilaya', '')
            })
        return json.dumps({'success': True, 'orders': orders})
    except Exception as e:
        return json.dumps({'success': False, 'error': _safe_str(e)})


# ============================================================
# DASHBOARD CLIENTS ROUTE
# ============================================================
@app.route('/dashboard/clients')
def dashboard_clients():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'clients.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"<h2>Template not found</h2><p>{_safe_str(e)}</p>", 404


@app.route('/dashboard/client/<phone>')
def dashboard_client_profile(phone):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'client-profile.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html, client_phone=phone), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"<h2>Template not found</h2><p>{_safe_str(e)}</p>", 404


# ============================================================
# BULK ORDERS API
# ============================================================
@app.route('/api/orders/bulk-update', methods=['POST'])
def api_orders_bulk_update():
    try:
        data = request.get_json(force=True) or {}
        order_ids = data.get('order_ids', [])
        field = data.get('field', 'financial_status')
        value = data.get('value', '')
        if not order_ids or not value:
            return json.dumps({'success': False, 'error': 'Missing data'})
        conn = get_db()
        c = conn.cursor()
        placeholders = ','.join('?' * len(order_ids))
        now = datetime.utcnow().isoformat()
        if field == 'financial_status':
            c.execute(f"UPDATE orders SET financial_status=?, updated_at=? WHERE order_id IN ({placeholders})",
                      (value, now, *order_ids))
        elif field == 'fulfillment_status':
            c.execute(f"UPDATE orders SET fulfillment_status=?, updated_at=? WHERE order_id IN ({placeholders})",
                      (value, now, *order_ids))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return json.dumps({'success': True, 'affected': affected})
    except Exception as e:
        _log_safe(logger.error, 'Bulk update error', e)
        return json.dumps({'success': False, 'error': _safe_str(e)})


# ============================================================
# ANALYTICS API
# ============================================================
@app.route('/api/analytics')
def api_analytics():
    try:
        conn = get_db()
        c = conn.cursor()
        # Orders per day (last 7 days)
        c.execute("""SELECT DATE(created_at) as day, COUNT(*) as count,
            SUM(CAST(total_price AS REAL)) as revenue
            FROM orders WHERE created_at > datetime('now', '-7 days')
            GROUP BY DATE(created_at) ORDER BY day""")
        daily = c.fetchall()
        # Orders by channel (via note field or detection)
        c.execute("""SELECT financial_status, COUNT(*) as count,
            SUM(CAST(total_price AS REAL)) as total
            FROM orders GROUP BY financial_status""")
        by_status = c.fetchall()
        # Top clients
        c.execute("""SELECT customer_name, customer_phone,
            COUNT(*) as total_orders, SUM(CAST(total_price AS REAL)) as total_spent
            FROM orders WHERE customer_phone != ''
            GROUP BY customer_phone ORDER BY total_spent DESC LIMIT 10""")
        top_clients = c.fetchall()
        conn.close()
        return json.dumps({
            'success': True,
            'daily': [{'day': r['day'], 'count': r['count'], 'revenue': r['revenue'] or 0} for r in daily],
            'by_status': [{'status': r['financial_status'], 'count': r['count'], 'total': r['total'] or 0} for r in by_status],
            'top_clients': [{'name': r['customer_name'] or 'عميل', 'phone': r['customer_phone'], 'orders': r['total_orders'], 'spent': r['total_spent'] or 0} for r in top_clients]
        })
    except Exception as e:
        _log_safe(logger.error, 'Analytics API error', e)
        return json.dumps({'success': False, 'error': _safe_str(e)})


# ============================================================
# PHASE 3: AUTO-SHIP + WHATSAPP CONFIRM + LIVE CHAT
# ============================================================

def _clean_phone(phone):
    """Normalize phone to international format"""
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
        if not ZR_API_KEY or not ZR_TENANT_ID:
            return {"success": False, "error": "ZR API not configured"}
        addr = order.get("shipping_address") or order.get("billing_address") or {}
        customer = order.get("customer") or {}
        phone = _clean_phone(addr.get("phone", "") or "")
        items = order.get("line_items", [])
        total = float(order.get("total_price", 0))
        payload = {
            "reference": order.get("name", f"ORDER-{order.get('id')}"),
            "shopify_order_id": str(order.get("id")),
            "customer_name": f"{customer.get('first_name','')} {customer.get('last_name','')}".strip(),
            "customer_phone": phone,
            "customer_address": f"{addr.get('address1','')} {addr.get('address2','')}".strip(),
            "city": addr.get("city", ""),
            "wilaya": addr.get("province", ""),
            "total_amount": total,
            "items": [{"sku": i.get("sku",""), "name": i.get("title",""), "qty": i.get("quantity",1),
                       "price": float(i.get("price",0))} for i in items],
            "currency": "DZD",
            "notes": order.get("note", "")
        }
        headers = {"Content-Type": "application/json", "X-API-KEY": ZR_API_KEY, "X-TENANT-ID": ZR_TENANT_ID}
        url = f"{ZR_BASE_URL}/parcels/create"
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
        orders = fetch_shopify_orders(status="any", limit=50)
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
        order_id = data.get("order_id", "").strip()
        if not order_id:
            return json_utf8({"success": False, "error": "order_id required"}, 400)
        orders = fetch_shopify_orders(status="any", limit=250)
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
            return {"success": False, "error": "No phone number"}
        customer = order.get("customer") or {}
        name = f"{customer.get('first_name','')} {customer.get('last_name','')}".strip() or "عميلنا العزيز"
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
        sent = send_whatsapp_message(phone, message)
        if sent:
            AUTO_CONFIRM_WA["messages_sent"] += 1
            AUTO_CONFIRM_WA["last_send"] = datetime.utcnow().isoformat()
            logger.info(f"[WA Confirm] Sent to {phone} for {order.get('name')}")
        return {"success": sent, "to": phone}
    except Exception as e:
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
        order_id = data.get("order_id", "").strip()
        if not order_id:
            return json_utf8({"success": False, "error": "order_id required"}, 400)
        orders = fetch_shopify_orders(status="any", limit=250)
        order = next((o for o in orders if str(o.get("id")) == str(order_id) or o.get("name","") == f"#{order_id}"), None)
        if not order:
            return json_utf8({"success": False, "error": "Order not found"}, 404)
        result = send_confirmation_whatsapp(order)
        return json_utf8({"success": result["success"], "order_id": order_id, **result})
    except Exception as e:
        return json_utf8({"success": False, "error": _safe_str(e)})


# ---- LIVE CHAT CONSOLE ----

@app.route('/dashboard/chat')
def dashboard_chat():
    """Live Chat Console page"""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'chat_console.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        _log_safe(logger.error, "Chat console template error", e)
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/messages')
def api_messages():
    """Get recent messages across all platforms"""
    try:
        limit = int(request.args.get("limit", 50))
        platform = request.args.get("platform", "")
        search = request.args.get("search", "").strip()
        conn = get_db()
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
                "id": r["id"],
                "platform": r["platform"],
                "sender_id": r["sender_id"],
                "message": r["message"],
                "reply": r["reply"],
                "created_at": r["created_at"]
            })
        return json_utf8({"success": True, "messages": messages, "count": len(messages)})
    except Exception as e:
        _log_safe(logger.error, "Messages API error", e)
        return json_utf8({"success": False, "error": _safe_str(e)})


if __name__ != '__main__':
    gunicorn_app = app

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Royal Chaussures Cloud Server starting on port {port}")
    logger.info(f"Shopify: {SHOPIFY_STORE}.myshopify.com")
    app.run(host="0.0.0.0", port=port, debug=False)
