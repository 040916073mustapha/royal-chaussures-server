#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Cloud Server for Render
============================================
يجمع بين:
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
from flask import Flask, request, jsonify, render_template, render_template_string

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("royal-server")

app = Flask(__name__)
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
            return resp.json().get("orders", [])
        logger.error(f"Shopify error {resp.status_code}: {resp.text[:200]}")
        return []
    except Exception as e:
        logger.error(f"Shopify fetch failed: {e}")
        return []

def fetch_shopify_products(limit=50):
    try:
        url = f"{SHOPIFY_BASE}/products.json?limit={limit}"
        resp = requests.get(url, headers=SHOPIFY_HEADERS_CATALOG, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("products", [])
        logger.error(f"Shopify products error {resp.status_code}: {resp.text[:200]}")
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
        url = "https://graph.facebook.com/v20.0/me/accounts?access_token=" + FB_SYSTEM_USER_TOKEN***}"
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
        url = "https://graph.facebook.com/v20.0/me/messages?access_token=" + token***}"
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
        url = "https://graph.facebook.com/v20.0/me/messages?access_token=" + token***}"
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
                "messages": [{"role": "system", "content": "أنت موظف خدمة عملاء في متجر Royal Chaussures، متجر جزائري للأحذية والإكسسوارات النسائية. تتحدث باللهجة الجزائرية الدارجة. ردودك مختصرة (2-4 جمل). لا تتكلم عن نفسك كذكاء اصطناعي."}, {"role": "user", "content": msg}],
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

# Routes
@app.route('/')
def index():
    return jsonify({"status": "running", "service": "Royal Chaussures Cloud Server", "version": "3.0", "url": request.host_url.rstrip('/'), "build": "5bbeab857aad", "endpoints": {"dashboard":"/dashboard","orders":"/dashboard/orders","products":"/dashboard/products","tracking":"/dashboard/tracking","health":"/health","webhook":"/webhook"}})

@app.route('/dashboard')
def dashboard_page():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'dashboard.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html)
    except Exception as e:
        logger.error(f'Dashboard template error: {e}')
        return jsonify({"error": str(e), "products_count":0, "recent_orders":[], "total_orders":0, "total_revenue":"0.00 DZD", "unfulfilled_orders":0})

@app.route('/dashboard/orders')
def dashboard_orders():
    return render_template_string("""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Royal Chaussures - الطلبات</title><style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',Tahoma,sans-serif;}body{background:#0a0a1a;color:#e0e0e0;padding:32px;}.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;}.header h1{font-size:24px;color:#fff;}.header a{color:#e94560;text-decoration:none;font-size:14px;}table{width:100%;border-collapse:collapse;}th{text-align:right;padding:12px 16px;color:#667;font-size:13px;border-bottom:1px solid rgba(255,255,255,0.06);}td{padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:14px;}tr:hover{background:rgba(233,69,96,0.03);}.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}.badge-pending{background:rgba(255,193,7,0.15);color:#ffc107;}.badge-paid{background:rgba(0,123,255,0.15);color:#0d6efd;}.badge-shipped{background:rgba(13,202,240,0.15);color:#0dcaf0;}.badge-delivered{background:rgba(25,135,84,0.15);color:#198754;}.loading{text-align:center;color:#667;padding:48px;}</style></head><body><div class="header"><h1>📦 جميع الطلبات</h1><a href="/dashboard">← العودة</a></div><table><thead><tr><th>الطلب</th><th>الزبون</th><th>الهاتف</th><th>المبلغ</th><th>المالية</th><th>الشحن</th></tr></thead><tbody id="ordersBody"><tr><td colspan="6" class="loading">جاري التحميل...</td></tr></tbody></table><script>async function load(){try{const r=await fetch('/api/orders');const d=await r.json();const b=document.getElementById('ordersBody');if(!d.orders||d.orders.length===0){b.innerHTML='<tr><td colspan="6" class="loading">لا توجد طلبات</td></tr>';return}b.innerHTML=d.orders.map(o=>{const fc=o.financial_status==='paid'?'badge-paid':'badge-pending';const fl=o.fulfillment_status||'unfulfilled';const flc=fl==='fulfilled'?'badge-delivered':fl==='partial'?'badge-shipped':'badge-pending';const c=o.customer||{};const a=(o.shipping_address||o.billing_address||{});return '<tr><td>'+(o.name||o.id)+'</td><td>'+(c.first_name||'')+' '+(c.last_name||'')+'</td><td>'+(a.phone||'-')+'</td><td>'+(o.total_price||'0')+' DZD</td><td><span class="badge '+fc+'">'+(o.financial_status||'pending')+'</span></td><td><span class="badge '+flc+'">'+fl+'</span></td></tr>'}).join('')}catch(e){document.getElementById('ordersBody').innerHTML='<tr><td colspan="6" class="loading" style="color:#dc3545;">⚠️ فشل التحميل</td></tr>'}}load();setInterval(load,60000);</script></body></html>""")

@app.route('/dashboard/products')
def dashboard_products():
    return render_template_string("""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Royal Chaussures - المنتجات</title><style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',Tahoma,sans-serif;}body{background:#0a0a1a;color:#e0e0e0;padding:32px;}.header{display:flex;justify-content:space-between;margin-bottom:24px;}.header h1{font-size:24px;color:#fff;}.header a{color:#e94560;text-decoration:none;font-size:14px;}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;}.card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px;}.card .title{font-size:14px;font-weight:600;margin-bottom:8px;}.card .price{color:#e94560;font-size:18px;font-weight:700;}.card .meta{font-size:12px;color:#667;margin-top:4px;}.loading{text-align:center;color:#667;padding:48px;grid-column:1/-1;}</style></head><body><div class="header"><h1>🛍️ المنتجات</h1><a href="/dashboard">← العودة</a></div><div class="grid" id="productsGrid"><div class="loading">جاري التحميل...</div></div><script>async function load(){try{const r=await fetch('/api/products');const d=await r.json();const g=document.getElementById('productsGrid');if(!d.products||d.products.length===0){g.innerHTML='<div class="loading">لا توجد منتجات</div>';return}g.innerHTML=d.products.map(p=>{const v=p.variants&&p.variants[0];return '<div class="card"><div class="title">'+p.title+'</div><div class="price">'+(v?v.price:'0')+' DZD</div><div class="meta">'+(p.variants?p.variants.length+' مقاس':'0 مقاس')+'</div></div>'}).join('')}catch(e){document.getElementById('productsGrid').innerHTML='<div class="loading" style="color:#dc3545;">⚠️ فشل التحميل</div>'}}load();</script></body></html>""")

@app.route('/dashboard/tracking')
def dashboard_tracking():
    return render_template_string("""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Royal Chaussures - تتبع الشحنات</title><style>*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',Tahoma,sans-serif;}body{background:#0a0a1a;color:#e0e0e0;padding:32px;}.header{display:flex;justify-content:space-between;margin-bottom:24px;}.header h1{font-size:24px;color:#fff;}.header a{color:#e94560;text-decoration:none;font-size:14px;}.search-box{display:flex;gap:12px;margin-bottom:24px;}.search-box input{flex:1;padding:12px 16px;border-radius:10px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:#fff;font-size:16px;direction:ltr;}.search-box button{padding:12px 24px;border-radius:10px;background:#e94560;color:#fff;border:none;cursor:pointer;font-size:14px;}.result-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px;margin-bottom:12px;}.result-card .field{display:flex;justify-content:space-between;padding:6px 0;font-size:14px;border-bottom:1px solid rgba(255,255,255,0.03);}.result-card .field:last-child{border-bottom:none;}.result-card .label{color:#667;}.result-card .value{color:#fff;}.loading{text-align:center;color:#667;padding:48px;}</style></head><body><div class="header"><h1>🔍 تتبع الشحنات - ZR Express</h1><a href="/dashboard">← العودة</a></div><div class="search-box"><input type="text" id="phoneInput" placeholder="رقم الهاتف (مثال: 0659832426)" dir="ltr"><button onclick="search()">🔍 بحث</button></div><div id="results"><div class="loading">أدخل رقم الهاتف للبحث</div></div><script>async function search(){const r=document.getElementById('results');const p=document.getElementById('phoneInput').value.trim();if(!p){r.innerHTML='<div class="loading">الرجاء إدخال رقم الهاتف</div>';return}r.innerHTML='<div class="loading">جاري البحث...</div>';try{const res=await fetch('/api/zr-lookup?phone='+encodeURIComponent(p));const d=await res.json();if(!d.parcels||d.parcels.length===0){r.innerHTML='<div class="loading">لا توجد شحنات لهذا الرقم</div>';return}r.innerHTML=d.parcels.map(par=>{const f=par||{};let html='<div class="result-card">';Object.keys(f).forEach(k=>{if(typeof f[k]!=='object')html+='<div class="field"><span class="label">'+k+'</span><span class="value">'+f[k]+'</span></div>'});html+='</div>';return html}).join('')}catch(e){r.innerHTML='<div class="error" style="color:#dc3545;text-align:center;">⚠️ فشل البحث</div>'}}document.getElementById('phoneInput').addEventListener('keypress',function(e){if(e.key==='Enter')search()});</script></body></html>""")

@app.route('/health')
def health():
    return jsonify({"status":"healthy","timestamp":datetime.utcnow().isoformat(),"uptime":"running","database":"connected"})

@app.route('/api/orders')
def api_orders():
    status = request.args.get("status", "any")
    limit = int(request.args.get("limit", 50))
    orders = fetch_shopify_orders(status=status, limit=limit)
    return jsonify({"orders": orders, "count": len(orders)})

@app.route('/api/products')
def api_products():
    limit = int(request.args.get("limit", 50))
    products = fetch_shopify_products(limit=limit)
    return jsonify({"products": products, "count": len(products)})

@app.route('/api/zr-lookup')
def api_zr_lookup():
    phone = request.args.get("phone", "")
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    parcels = lookup_zr_tracking(phone)
    return jsonify({"phone": phone, "parcels": parcels, "count": len(parcels)})

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
