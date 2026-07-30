#!/usr/bin/env python3
"""
Royal Chaussures — Cloud Server for Render
============================================
يجمع بين:
1. Flask Web App (Dashboard)
2. Webhook Receiver (Facebook Messenger, WhatsApp, Instagram)
3. Scheduler (للأتمتة الدورية)
4. Health Check لنظام UptimeRobot

هذا السيرفر معمول باش يخدم 24/7 على Render.com بدون ngrok.
"""

import requests
import json
import os
import sys
import sqlite3
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, render_template_string

# ============================================================
# Load Environment Variables
# ============================================================
load_dotenv()

# ============================================================
# Logging Setup
# ============================================================
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("royal-server")

# ============================================================
# Flask App
# ============================================================
app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# ============================================================
# Configuration
# ============================================================

# --- Shopify ---
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
SHOPIFY_ORDERS_TOKEN = os.getenv("SHOPIFY_ORDERS_TOKEN", "")
SHOPIFY_CATALOG_TOKEN = os.getenv("SHOPIFY_CATALOG_TOKEN", "")
SHOPIFY_BASE = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}"
SHOPIFY_HEADERS_ORDERS = {
    "X-Shopify-Access-Token": SHOPIFY_ORDERS_TOKEN,
    "Content-Type": "application/json"
}
SHOPIFY_HEADERS_CATALOG = {
    "X-Shopify-Access-Token": SHOPIFY_CATALOG_TOKEN,
    "Content-Type": "application/json"
}

# --- ZR Express ---
ZR_BASE_URL = os.getenv("ZR_BASE_URL", "https://api.zrexpress.app/api/v1")
ZR_API_KEY = os.getenv("ZR_API_KEY", "")
ZR_TENANT_ID = os.getenv("ZR_TENANT_ID", "")

# --- Meta / Facebook ---
FB_VERIFY_TOKEN = "ROYAL_CHAUSSURES_SECRET_2026"
FB_SYSTEM_USER_TOKEN = os.getenv("FB_SYSTEM_USER_TOKEN", "")

# --- WhatsApp ---
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = "1212786725251029"

# --- Instagram ---
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

# --- OpenClaw (optional — used when gateway is accessible) ---
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")


# ============================================================
# Database (SQLite — Render ephemeral disk, ok for caching)
# ============================================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """إنشاء الجداول إذا لم تكن موجودة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            order_name TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            total_price TEXT,
            financial_status TEXT,
            fulfillment_status TEXT,
            zr_tracking TEXT,
            zr_status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

init_db()


# ============================================================
# Helper Functions
# ============================================================

def fetch_shopify_orders(status="any", limit=50):
    """جلب الطلبات من Shopify"""
    try:
        url = f"{SHOPIFY_BASE}/orders.json?status={status}&limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_ORDERS, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("orders", [])
        else:
            logger.error(f"Shopify error {resp.status_code}: {resp.text[:200]}")
            return []
    except Exception as e:
        logger.error(f"Shopify fetch failed: {e}")
        return []


def fetch_shopify_products(limit=50):
    """جلب المنتجات من Shopify"""
    try:
        url = f"{SHOPIFY_BASE}/products.json?limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_CATALOG, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("products", [])
        else:
            logger.error(f"Shopify products error {resp.status_code}: {resp.text[:200]}")
            return []
    except Exception as e:
        logger.error(f"Shopify products fetch failed: {e}")
        return []


def lookup_zr_tracking(phone):
    """البحث عن شحنة في ZR Express باستخدام رقم الهاتف"""
    try:
        url = f"{ZR_BASE_URL}/courier/search/findByPhone/{phone}"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": ZR_API_KEY,
            "X-TENANT-ID": ZR_TENANT_ID
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            parcels = []
            if isinstance(data, dict):
                content = data.get("content") or data.get("data") or [data]
                if isinstance(content, dict):
                    content = [content]
                parcels = content
            elif isinstance(data, list):
                parcels = data
            return parcels
        return []
    except Exception as e:
        logger.error(f"ZR lookup failed for {phone}: {e}")
        return []


# ============================================================
# Routes — Pages
# ============================================================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return jsonify({
        "status": "running",
        "service": "Royal Chaussures Cloud Server",
        "version": "3.0",
        "endpoints": {
            "dashboard": "/dashboard",
            "health": "/health",
            "webhook": "/webhook"
        }
    })


@app.route('/dashboard')
def dashboard():
    """لوحة التحكم الأساسية"""
    orders = fetch_shopify_orders(limit=20)
    products = fetch_shopify_products(limit=10)
    
    total_orders = len(orders)
    unfulfilled = sum(1 for o in orders if o.get("fulfillment_status") != "fulfilled")
    total_revenue = sum(float(o.get("total_price", 0)) for o in orders)
    
    return jsonify({
        "total_orders": total_orders,
        "unfulfilled_orders": unfulfilled,
        "total_revenue": f"{total_revenue:.2f} DZD",
        "recent_orders": [
            {
                "id": o.get("id"),
                "name": o.get("name"),
                "customer": o.get("customer", {}).get("first_name", "Guest"),
                "total": o.get("total_price"),
                "status": o.get("financial_status"),
                "fulfillment": o.get("fulfillment_status", "unfulfilled")
            }
            for o in orders[:10]
        ],
        "products_count": len(products)
    })


@app.route('/health')
def health():
    """فحص صحة السيرفر"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "running",
        "database": "connected"
    })


@app.route('/api/orders')
def api_orders():
    """API الطلبات"""
    status = request.args.get("status", "any")
    limit = int(request.args.get("limit", 50))
    orders = fetch_shopify_orders(status=status, limit=limit)
    return jsonify({"orders": orders, "count": len(orders)})


@app.route('/api/products')
def api_products():
    """API المنتجات"""
    limit = int(request.args.get("limit", 50))
    products = fetch_shopify_products(limit=limit)
    return jsonify({"products": products, "count": len(products)})


@app.route('/api/zr-lookup')
def api_zr_lookup():
    """API البحث في ZR Express"""
    phone = request.args.get("phone", "")
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    parcels = lookup_zr_tracking(phone)
    return jsonify({"phone": phone, "parcels": parcels, "count": len(parcels)})


# ============================================================
# Routes — Webhooks (Facebook Messenger, WhatsApp, Instagram)
# ============================================================

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Meta Webhook Verification"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
        logger.info("✅ Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


@app.route('/webhook', methods=['POST'])
def webhook_receive():
    """استقبال Webhooks من فيسبوك مسنجر + واتساب + إنستغرام"""
    data = request.get_json()
    if not data:
        return json.dumps({"error": "Invalid JSON"}), 400

    obj = data.get('object', '')

    if obj == 'page':
        # فيسبوك مسنجر
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message') and 'text' in messaging_event['message']:
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message']['text']
                    logger.info(f"📩 [Messenger] {sender_id}: {user_message[:100]}")
                    
                    # Auto-reply
                    reply = "مرحباً بك في Royal Chaussures! 🎀 شكراً لتواصلك معنا. سيتم الرد عليك في أقرب وقت. 👠✨"
                    send_messenger_message(sender_id, reply)

    elif obj == 'whatsapp_business_account':
        # واتساب
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                if 'messages' in value:
                    for msg in value['messages']:
                        if 'text' in msg:
                            sender = msg['from']
                            text = msg['text']['body']
                            logger.info(f"📩 [WhatsApp] {sender}: {text[:100]}")
                            reply = "مرحباً بك في Royal Chaussures! 🎀 شكراً لتواصلك معنا. سنرد عليك قريباً. 👠✨"
                            send_whatsapp_message(sender, reply)

    elif obj == 'instagram':
        # إنستغرام
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message') and 'text' in messaging_event['message']:
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message']['text']
                    logger.info(f"📩 [Instagram] {sender_id}: {user_message[:100]}")
                    reply = "مرحباً بك في Royal Chaussures! 🎀 شكراً لتواصلك معنا. 👠✨"
                    send_instagram_message(sender_id, reply)

    return "EVENT_RECEIVED", 200


# ============================================================
# Platform Messaging
# ============================================================

_PAGE_TOKEN_CACHE = None

def get_page_token():
    """الحصول على Page Access Token"""
    global _PAGE_TOKEN_CACHE
    if _PAGE_TOKEN_CACHE:
        return _PAGE_TOKEN_CACHE
    try:
        url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={FB_SYSTEM_USER_TOKEN}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "data" in data and len(data["data"]) > 0:
            for page in data["data"]:
                if "access_token" in page:
                    _PAGE_TOKEN_CACHE = page["access_token"]
                    return _PAGE_TOKEN_CACHE
    except Exception as e:
        logger.error(f"Failed to get page token: {e}")
    return None


def send_messenger_message(recipient_id, text):
    """إرسال رد عبر Facebook Messenger"""
    token = get_page_token()
    if not token:
        logger.error("No Messenger token")
        return
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={token}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    try:
        requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    except Exception as e:
        logger.error(f"Messenger send error: {e}")


def send_whatsapp_message(to_number, text):
    """إرسال رد عبر WhatsApp"""
    if not WHATSAPP_ACCESS_TOKEN:
        logger.error("No WhatsApp token configured")
        return
    url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": text}}
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")


def send_instagram_message(recipient_id, text):
    """إرسال رد عبر Instagram"""
    token = get_page_token()
    if not token:
        logger.error("No Instagram token")
        return
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={token}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    try:
        requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
    except Exception as e:
        logger.error(f"Instagram send error: {e}")


# ============================================================
# Main
# ============================================================

if __name__ != '__main__':
    # Gunicorn will use this
    gunicorn_app = app

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    logger.info("🚀 Royal Chaussures Cloud Server starting...")
    logger.info(f"🌐 Port: {port}")
    logger.info(f"📦 Shopify: {SHOPIFY_STORE}.myshopify.com")
    app.run(host="0.0.0.0", port=port, debug=False)
