"""
RC Agents — SaaS Core Backend (Multi-Tenant)
Flask application entry point
Uses relative imports only — clean, works from any context
"""

import os
import sys
import logging

# Add parent directory to path (works for both run_saas.py and direct execution)
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import hashlib
import hmac
import uuid

from flask import Flask, jsonify, send_from_directory, request, Response, render_template
from flask_cors import CORS

from .config import Config
from .database.models import init_db

# Import API Blueprints
from .api.auth import auth_bp
from .api.stores import stores_bp
from .api.settings import settings_bp
from .api.conversations import conversations_bp
from .api.zr_express import zr_bp
from .api.stats import stats_bp

# ─── Logging ──────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("saas-core")


# ─── App Factory ──────────────────────────────────────────────

def create_app():
    app = Flask(__name__, static_folder="frontend", static_url_path="")

    # CORS — allow all origins during development
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(stores_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(zr_bp)
    app.register_blueprint(stats_bp)

    # Configure template folder for Dark Neon Dashboard
    _template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "templates")
    if os.path.isdir(_template_dir):
        app.template_folder = _template_dir
        app.jinja_loader = __import__("jinja2").FileSystemLoader(_template_dir)
        app.logger.info(f"Using template folder: {_template_dir}")
    
    # ─── Init Database ────────────────────────────────────────
    with app.app_context():
        try:
            engine = init_db()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ DB init (will retry on first request): {e}")

    # ─── Routes ──────────────────────────────────────────────

    @app.route("/")
    def index():
        """Landing Page — the main entrance to RC Agents"""
        try:
            return render_template("landing.html")
        except Exception:
            return send_from_directory(app.static_folder, "landing.html")

    @app.route("/dashboard")
    def dashboard():
        """Dark Neon Cyberpunk Dashboard — full with AI Brain + Charts + Live Chat"""
        try:
            return render_template("dashboard.html")
        except Exception:
            try:
                return render_template("dashboard_base.html")
            except Exception:
                return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/onboard")
    def onboard():
        """Onboarding / Sign-Up page"""
        try:
            return render_template("onboard.html")
        except Exception:
            return send_from_directory(app.static_folder, "onboard.html")

    @app.route("/login")
    def login():
        """Login page"""
        try:
            return render_template("dashboard_login.html")
        except Exception:
            return send_from_directory(app.static_folder, "dashboard_login.html")

    @app.route("/privacy")
    def privacy():
        """Privacy Policy — required for Meta App Review"""
        try:
            return render_template("privacy.html")
        except Exception:
            return send_from_directory(app.static_folder, "privacy.html")

    @app.route("/terms")
    def terms():
        """Terms of Service — required for Meta App Review"""
        try:
            return render_template("terms.html")
        except Exception:
            return send_from_directory(app.static_folder, "terms.html")

    # ─── Dynamic Dashboard Routes ────────────────────────────
    # All /dashboard/* sub-routes render the same Dark Neon Cyberpunk template
    # AlpineJS handles client-side navigation and active tab state

    _dashboard_pages = [
        "orders", "clients", "products", "chat", "settings",
        "shipments", "constellation", "auto-ship", "agents",
        "analytics", "inventory", "marketing", "integrations",
    ]

    @app.route("/dashboard/<page>")
    def dashboard_page(page):
        if page not in _dashboard_pages:
            return send_from_directory(app.static_folder, "dashboard.html"), 404
        try:
            return render_template("dashboard.html")
        except Exception:
            return send_from_directory(app.static_folder, "dashboard.html")

    # ─── Webhook Endpoint (Messenger & Instagram) ────────────

    FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "ROYAL-ROYAL-CH2026")

    @app.route("/webhook", methods=["GET", "POST"])
    def webhook():
        # GET: Facebook verification challenge
        if request.method == "GET":
            mode = request.args.get("hub.mode")
            token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")
            logger.info(f"Webhook GET: mode={mode}")
            if mode == "subscribe" and token == FB_VERIFY_TOKEN:
                logger.info("Webhook verified!")
                return Response(challenge, status=200, content_type="text/plain")
            logger.warning("Webhook verify failed")
            return "Verification failed", 403

        # POST: Process incoming message
        logger.info("Webhook POST received")
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "ok"})

        obj = data.get("object", "")
        logger.info(f"Webhook object={obj}")

        # TEMP: Legacy flow — import from server.py
        if obj == "page":
            process_messaging_entries(data.get("entry", []), "FB", send_fb_reply)
        elif obj == "instagram":
            process_messaging_entries(data.get("entry", []), "IG", send_ig_reply)
        elif obj == "whatsapp_business_account":
            _process_whatsapp_multi(data.get("entry", []))
        else:
            logger.warning(f"Unknown webhook object: {obj}")

        return jsonify({"status": "ok"})

    @app.route("/webhook/", methods=["GET", "POST"])
    def webhook_slash():
        return webhook()

    @app.route("/whatsapp/webhook", methods=["GET", "POST"])
    def whatsapp_webhook():
        if request.method == "GET":
            mode = request.args.get("hub.mode")
            token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")
            if mode == "subscribe" and token == FB_VERIFY_TOKEN:
                return Response(challenge, status=200, content_type="text/plain")
            return "Verification failed", 403

        data = request.get_json(silent=True)
        if data:
            logger.info(f"WhatsApp webhook received")
            _process_whatsapp_multi(data.get("entry", []))
        return jsonify({"status": "ok"})

    # ─── Import webhook handlers from root server.py ────────
    import importlib.util
    _server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")
    _spec = importlib.util.spec_from_file_location("webhook_server", _server_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    process_messaging_entries = _mod.process_messaging_entries
    process_whatsapp_entries = _mod.process_whatsapp_entries
    send_fb_reply = _mod.send_fb_reply
    send_ig_reply = _mod.send_ig_reply
    send_whatsapp_reply = _mod.send_whatsapp_reply

    # ─── Multi-Tenant Webhook Processors ─────────────────────

    from .database.crud import get_store_id_by_platform, get_store_id_by_whatsapp_phone, get_or_create_conversation, save_message, get_or_create_ai_settings

    def _get_store_id_from_entry(entry, channel_type):
        """Extract store_id from webhook entry based on channel type"""
        entry_id = entry.get("id", "")
        if entry_id:
            sid = get_store_id_by_platform(channel_type, str(entry_id))
            if sid:
                return sid
        return None

    def _process_messaging_multi(entries, platform, send_func):
        """Multi-tenant: process Messenger/Instagram messages with store_id lookup"""
        logger.info(f"[MT] process_messaging: plat={platform} entries={len(entries)}")
        channel_type = "messenger" if platform == "FB" else "instagram"
        for entry in entries:
            store_id = _get_store_id_from_entry(entry, channel_type)
            if not store_id:
                logger.warning(f"[MT] No store for {channel_type} entry {entry.get('id','')}, falling back to legacy")
                process_messaging_entries([entry], platform, send_func)
                continue
            for messaging in entry.get("messaging", []):
                sid = messaging.get("sender", {}).get("id", "")
                msg_data = messaging.get("message", {})
                text = msg_data.get("text", "") or ""
                image_url = ""
                attachments = msg_data.get("attachments", [])
                if attachments:
                    for att in attachments:
                        if att.get("type") == "image":
                            payload = att.get("payload") or {}
                            image_url = payload.get("url") or att.get("url") or ""
                            if image_url:
                                break
                image_url = image_url or ""
                if sid and (text or image_url):
                    conv = get_or_create_conversation(store_id, channel_type, sid, customer_platform_id=sid)
                    save_message(conv.id, store_id, "user", text or "[Image]", channel_type, "image" if image_url else "text", image_url)
                    logger.info(f"[MT] {platform} msg from {sid}: text='{text[:60]}' store={store_id}")
                    send_func(sid, text, image_url, store_id)

    def _process_whatsapp_multi(entries):
        """Multi-tenant: process WhatsApp messages with store_id lookup"""
        logger.info(f"[MT] process_whatsapp: entries={len(entries)}")
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                phone_id = metadata.get("phone_number_id", "")
                store_id = None
                if phone_id:
                    store_id = get_store_id_by_whatsapp_phone(str(phone_id))
                if not store_id:
                    logger.warning(f"[MT] No store for WA phone {phone_id}, falling back to legacy")
                    process_whatsapp_entries([entry])
                    continue
                for msg in value.get("messages", []):
                    sender = msg.get("from", "")
                    text = (msg.get("text") or {}).get("body", "") or ""
                    img = msg.get("image") or {}
                    image_url = img.get("id") or img.get("link") or ""
                    if sender and (text or image_url):
                        conv = get_or_create_conversation(store_id, "whatsapp", sender, customer_platform_id=sender)
                        save_message(conv.id, store_id, "user", text or "[Image]", "whatsapp", "image" if image_url else "text", image_url)
                        logger.info(f"[MT] WA msg from {sender}: text='{text[:60]}' store={store_id}")
                        import threading
                        threading.Thread(target=send_whatsapp_reply, args=(sender, text, image_url, store_id), daemon=True).start()

    # Assign multi-tenant processors to webhook routes
    import threading
    process_messaging_entries = _process_messaging_multi
    process_whatsapp_entries = _process_whatsapp_multi

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "rc-agents-saas-core",
            "version": "2.0.0",
        })

    @app.route("/api/plans")
    def list_plans():
        return jsonify(Config.PLANS)

    # ─── API: Tenant Onboard (Multi-Store Registration) ─────

    @app.route("/api/tenant/onboard", methods=["POST"])
    def tenant_onboard():
        """Register a new store/tenant"""
        try:
            data = request.get_json(force=True)
            store_name = data.get("store_name", "").strip()
            email = data.get("email", "").strip()
            phone = data.get("phone", "").strip()
            username = data.get("username", "").strip()
            password = data.get("password", "")
            webhooks = data.get("webhooks", {})

            if not store_name or not username or not password:
                return jsonify({"success": False, "error": "store_name, username, and password are required"}), 400
            if len(password) < 6:
                return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

            store_id = str(uuid.uuid4())[:8]
            slug = store_name.lower().replace(" ", "-").replace("'", "")[:20]

            # Simple in-memory registration for now (DB persistence in next iteration)
            _tenant_registry = getattr(app, "_tenant_registry", {})
            _tenant_registry[store_id] = {
                "store_name": store_name,
                "email": email,
                "phone": phone,
                "username": username,
                "password": password,
                "webhooks": webhooks,
                "slug": slug,
                "store_id": store_id,
            }
            app._tenant_registry = _tenant_registry

            logger.info(f"✅ New tenant registered: {store_name} (ID: {store_id})")

            return jsonify({
                "success": True,
                "store_name": store_name,
                "store_id": store_id,
                "slug": slug,
                "username": username,
                "subdomain": f"{slug}.rcagents.space",
            })
        except Exception as e:
            logger.error(f"Tenant onboard error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # ─── Error Handlers ──────────────────────────────────────

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/admin/migrate")
    def api_migrate():
        """Run DB migration — create all tables on PostgreSQL"""
        try:
            from .database.models import Base, get_engine
            url = os.getenv("DATABASE_URL") or os.getenv("SAAS_DATABASE_URL")
            if not url:
                return jsonify({"error": "No DATABASE_URL in environment"}), 400
            engine = get_engine(url)
            Base.metadata.create_all(engine)
            inspector = __import__("sqlalchemy").inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"Migration complete: {', '.join(tables)}")
            return jsonify({"status": "ok", "tables": tables})
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return jsonify({"error": str(e)}), 500

    # ─── Shopify Sync Helper ──────────────────────────────────

    def _sync_shopify_catalog(shopify_domain, access_token, store_id, app_instance):
        """Sync products and orders from Shopify into memory cache"""
        import requests as _req
        import json as _json

        products = []
        orders = []
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        base_url = f"https://{shopify_domain}/admin/api/2024-10"

        # Fetch products
        try:
            resp = _req.get(f"{base_url}/products.json?limit=50", headers=headers, timeout=15)
            if resp.status_code == 200:
                products = resp.json().get("products", [])
                logger.info(f"Synced {len(products)} products from {shopify_domain}")
        except Exception as e:
            logger.warning(f"Shopify products sync error: {e}")

        # Fetch orders
        try:
            resp = _req.get(f"{base_url}/orders.json?status=any&limit=50", headers=headers, timeout=15)
            if resp.status_code == 200:
                orders = resp.json().get("orders", [])
                logger.info(f"Synced {len(orders)} orders from {shopify_domain}")
        except Exception as e:
            logger.warning(f"Shopify orders sync error: {e}")

        # Store synced data in app config (in-memory)
        _shopify_cache = getattr(app_instance, "_shopify_cache", {})
        _shopify_cache[store_id] = {
            "products": products,
            "orders": orders,
            "last_sync": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        }
        app_instance._shopify_cache = _shopify_cache

        return {"products": len(products), "orders": len(orders)}

    # ─── API: Integrations Connect ────────────────────────────

    @app.route("/api/integrations/connect", methods=["POST"])
    def integrations_connect():
        """Connect a platform integration for a store"""
        try:
            data = request.get_json(force=True)
            store_id = data.get("store_id", "")
            platform = data.get("platform", "")  # shopify, meta, zr_express
            credentials = data.get("credentials", {})
            sync_now = data.get("sync", False)

            if not store_id:
                return jsonify({"success": False, "error": "store_id is required"}), 400
            if platform not in ("shopify", "meta", "zr_express"):
                return jsonify({"success": False, "error": "Invalid platform"}), 400

            _integrations = getattr(app, "_integrations", {})
            if store_id not in _integrations:
                _integrations[store_id] = {}

            if platform == "shopify":
                shopify_domain = credentials.get("shopify_domain", "")
                access_token = credentials.get("access_token", "")
                if not shopify_domain or not access_token:
                    return jsonify({"success": False, "error": "Shopify domain and access token are required"}), 400
                _integrations[store_id]["shopify"] = {
                    "shopify_domain": shopify_domain,
                    "access_token": access_token,
                }
                app._integrations = _integrations
                logger.info(f"✅ Shopify connected for store {store_id}: {shopify_domain}")

                # Initial sync — fetch products and orders from Shopify
                if sync_now:
                    try:
                        sync_result = _sync_shopify_catalog(shopify_domain, access_token, store_id, app)
                        return jsonify({
                            "success": True,
                            "message": f"Shopify connected! Synced {sync_result.get('products', 0)} products and {sync_result.get('orders', 0)} orders.",
                            **sync_result
                        })
                    except Exception as sync_err:
                        logger.warning(f"Shopify initial sync failed: {sync_err}")
                        return jsonify({
                            "success": True,
                            "message": f"Shopify connected but initial sync failed: {sync_err}",
                            "sync_error": str(sync_err)
                        }), 200

                return jsonify({"success": True, "message": "Shopify connected successfully"})

            elif platform == "meta":
                access_token = credentials.get("access_token", "")
                page_id = credentials.get("page_id", "")
                if not access_token or not page_id:
                    return jsonify({"success": False, "error": "Access token and Page ID are required"}), 400
                _integrations[store_id]["meta"] = {
                    "access_token": access_token,
                    "page_id": page_id,
                }
                app._integrations = _integrations
                logger.info(f"✅ Meta connected for store {store_id}: page={page_id}")
                return jsonify({"success": True, "message": "Meta connected successfully! The webhook will receive messages shortly."})

            elif platform == "zr_express":
                api_key = credentials.get("api_key", "")
                if not api_key:
                    return jsonify({"success": False, "error": "ZR Express API key is required"}), 400
                _integrations[store_id]["zr_express"] = {
                    "api_key": api_key,
                }
                app._integrations = _integrations
                logger.info(f"✅ ZR Express connected for store {store_id}")
                return jsonify({"success": True, "message": "ZR Express connected! Shipping rates and tracking will be available."})

        except Exception as e:
            logger.error(f"Integrations connect error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return app


# ─── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", Config.DASHBOARD_PORT))
    logger.info(f"RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
