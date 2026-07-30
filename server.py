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
import os
import sys
import sqlite3
import logging
import hashlib
import hmac
import base64
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, render_template_string, Response
from werkzeug.wrappers import Response as WerkzeugResponse
# Patch: Force all JSON responses to use utf-8 to avoid latin-1 encoding errors
_original_response_set_data = WerkzeugResponse.set_data
def _patched_set_data(self, value):
    if isinstance(value, bytes):
        self.content_type = 'application/json; charset=utf-8'
    return _original_response_set_data(self, value)
WerkzeugResponse.set_data = _patched_set_data

def json_utf8(data, status=200):
    """Return JSON response with explicit utf-8 encoding (bypasses latin-1 issue)"""
    return Response(
        json.dumps(data, ensure_ascii=False).encode('utf-8'),
        status=status,
        content_type='application/json; charset=utf-8'
    )

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("royal-server")

import os
_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=_TEMPLATE_DIR)
app.secret_key = os.urandom(24).hex()

# Configuration
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
SHOPIFY_ORDERS_TOKEN = os.environ.get("SHOPIFY_ORDERS_TOKEN", "")
SHOPIFY_CATALOG_TOKEN = os.environ.get("SHOPIFY_CATALOG_TOKEN", "")
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
def fetch_shopify_orders(status="any", limit=50):
    try:
        url = f"{SHOPIFY_BASE}/orders.json?status={status}&limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_ORDERS, timeout=15)
        if resp.status_code == 200:
            # Use raw content + json.loads to avoid latin-1 encoding issues
            return json.loads(resp.content.decode('utf-8')).get("orders", [])
        logger.error(f"Shopify error {resp.status_code}: {resp.content[:500]}")
        return []
    except Exception as e:
        logger.error(f"Shopify fetch failed: {e}")
        return []

def fetch_shopify_products(limit=50):
    try:
        url = f"{SHOPIFY_BASE}/products.json?limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_CATALOG, timeout=15)
        if resp.status_code == 200:
            # Use raw content + json.loads to avoid latin-1 encoding issues
            return json.loads(resp.content.decode('utf-8')).get("products", [])
        logger.error(f"Shopify products error {resp.status_code}: {resp.content[:500]}")
        return []
    except Exception as e:
        logger.error(f"Shopify products fetch failed: {e}")
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
        logger.error(f"ZR lookup failed for {phone}: {e}")
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
        logger.error(f"Failed to get page token: {e}")
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
        logger.error(f"Messenger error: {e}")
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
        logger.error(f"WhatsApp error: {e}")
        return False

def send_instagram_message(recipient_id, text):
    token = get_page_token()
    if not token: return False
    try:
        url = "https://graph.facebook.com/v20.0/me/messages?access_token=" + token
        payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Instagram error: {e}")
        return False

# OpenClaw / Auto Reply
def get_atlas_response(msg, uid, platform="messenger"):
    if OPENCLAW_API_URL and OPENCLAW_TOKEN:
        try:
            payload = {
                "model": "openclaw/customer_support",
                "messages": [{"role": "system", "content": "Ø£Ù†Øª Ù…ÙˆØ¸Ù Ø®Ø¯Ù…Ø© Ø¹Ù…Ù„Ø§Ø¡ ÙÙŠ Ù…ØªØ¬Ø± Royal ChaussuresØŒ Ù…ØªØ¬Ø± Ø¬Ø²Ø§Ø¦Ø±ÙŠ Ù„Ù„Ø£Ø­Ø°ÙŠØ© ÙˆØ§Ù„Ø¥ÙƒØ³Ø³ÙˆØ§Ø±Ø§Øª Ø§Ù„Ù†Ø³Ø§Ø¦ÙŠØ©. ØªØªØ­Ø¯Ø« Ø¨Ø§Ù„Ù„Ù‡Ø¬Ø© Ø§Ù„Ø¬Ø²Ø§Ø¦Ø±ÙŠØ© Ø§Ù„Ø¯Ø§Ø±Ø¬Ø©. Ø±Ø¯ÙˆØ¯Ùƒ Ù…Ø®ØªØµØ±Ø© (2-4 Ø¬Ù…Ù„). Ù„Ø§ ØªØªÙƒÙ„Ù… Ø¹Ù† Ù†ÙØ³Ùƒ ÙƒØ°ÙƒØ§Ø¡ Ø§ØµØ·Ù†Ø§Ø¹ÙŠ."}, {"role": "user", "content": msg}],
                "user": f"customer:{platform}:{uid}"
            }
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENCLAW_TOKEN}"}
            resp = requests.post(OPENCLAW_API_URL, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenClaw error: {e}")
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
        logger.error(f'Dashboard template error: {e}')
        return json_utf8({"error": str(e), "products_count":0, "recent_orders":[], "total_orders":0, "total_revenue":"0.00 DZD", "unfulfilled_orders":0})

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
        data = json.loads(resp.content.decode('utf-8'))
        orders = data.get("orders", [])
        return json_utf8({
            "success": True,
            "status_code": resp.status_code,
            "encoding_ok": True,
            "orders_count": len(orders),
            "sample": {"name": orders[0].get("name")} if orders else None
        })
    except Exception as e:
        return json_utf8({"success": False, "error": str(e), "error_type": type(e).__name__}, 500)


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
        logger.error(f"Dashboard data error: {e}")
        return json_utf8({"error": str(e)}, 500)

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
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message') and 'text' in messaging_event['message']:
                    sid = messaging_event['sender']['id']
                    msg = messaging_event['message']['text']
                    logger.info(f"[Instagram] {sid}: {msg[:100]}")
                    reply = get_atlas_response(msg, sid, "instagram")
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
            logger.error(f"Order save error: {e}")
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

if __name__ != '__main__':
    gunicorn_app = app

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Royal Chaussures Cloud Server starting on port {port}")
    logger.info(f"Shopify: {SHOPIFY_STORE}.myshopify.com")
    app.run(host="0.0.0.0", port=port, debug=False)
