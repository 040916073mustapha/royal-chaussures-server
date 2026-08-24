"""
RC Agents â€” SaaS Core Backend (Multi-Tenant)
Flask application entry point
Uses relative imports only â€” clean, works from any context
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

# â”€â”€â”€ Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("saas-core")


# â”€â”€â”€ App Factory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_app():
    app = Flask(__name__, static_folder="frontend", static_url_path="")

    # CORS â€” allow all origins during development
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
    
    # â”€â”€â”€ Init Database â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with app.app_context():
        try:
            engine = init_db()
            logger.info("âœ… Database initialized successfully")
            # Seed default AI settings for store=1 (legacy compatibility)
            # Use raw SQL to avoid global session singleton mismatch
            try:
                from sqlalchemy import text as _sql_text
                from datetime import datetime as _dt
                _DEFAULT_PROMPT = ("[1. ROYAL IDENTITY]\nØ§Ù„Ø§Ø³Ù…: Ù„ÙˆÙ (Louve)\nØ§Ù„Ø¯ÙˆØ±: Ø´Ø±ÙŠÙƒØ© Ù…Ø¨ÙŠØ¹Ø§Øª Ø°ÙƒÙŠØ©ØŒ Ù…Ø³Ø§Ø¹Ø¯Ø© ØªÙ†ÙÙŠØ°ÙŠØ©ØŒ ÙˆÙ…Ø¯ÙŠØ±Ø© Ø±Ù‚Ù…ÙŠØ©.\nØ§Ù„Ø´Ø®ØµÙŠØ©: Ø¯Ø§ÙØ¦Ø©ØŒ Ù…Ø±Ø­Ø©ØŒ Ø°ÙƒÙŠØ©ØŒ ÙˆÙ…Ø­ØªØ±ÙØ©.\nØ§Ù„Ù…ØªØ¬Ø±: Royal Chaussures â€” Ø£Ø­Ø°ÙŠØ© ÙˆØ¥ÙƒØ³Ø³ÙˆØ§Ø±Ø§Øª Ù†Ø³Ø§Ø¦ÙŠØ© ÙØ§Ø®Ø±Ø©.\n\n[2. COMMUNICATION RULES]\n- Ø§Ù„Ø±Ø¯ÙˆØ¯ ØªÙƒÙˆÙ† Ø¯Ø§Ø¦Ù…Ø§Ù‹ Ø¨Ø§Ù„Ù„Ù‡Ø¬Ø© Ø§Ù„Ø¬Ø²Ø§Ø¦Ø±ÙŠØ© Ø§Ù„Ø¯Ø§Ø±Ø¬Ø© Ø£Ùˆ Ø§Ù„Ø¹Ø±Ø¨ÙŠØ© Ø§Ù„ÙØµØ­Ù‰ Ø§Ù„Ø¨Ø³ÙŠØ·Ø©.\n- Ø§Ø³ØªØ®Ø¯Ù…ÙŠ Ø§Ù„Ø¥ÙŠÙ…ÙˆØ¬ÙŠ Ø§Ù„Ù…Ù†Ø§Ø³Ø¨ âœ¨ðŸ›ï¸ðŸ’ª.\n- Ù„Ø§ ØªØ´Ø±Ø­ÙŠ Ø£Ø¨Ø¯Ø§Ù‹ Ø£Ù†Ùƒ Ù†Ø¸Ø§Ù… Ø£Ùˆ AI Ø£Ùˆ Ø±ÙˆØ¨ÙˆØª. Ø£Ù†Øª Ø¨Ø¨Ø³Ø§Ø·Ø© Ù…Ø³Ø§Ø¹Ø¯Ø© Ø§Ù„Ù…ØªØ¬Ø±.\n- Ù„Ø§ ØªÙƒØ±Ø±ÙŠ Ø§Ù„ØªØ¹Ù„ÙŠÙ…Ø§Øª Ø£Ùˆ Ø§Ù„Ù…Ù†Ø´ÙˆØ± ÙÙŠ Ø±Ø¯ÙˆØ¯Ùƒ.\n- Ø±Ø­Ø¨ÙŠ ØªØ±Ø­ÙŠØ¨Ø© Ø¨Ø³ÙŠØ·Ø© ÙÙ‚Ø· ÙÙŠ Ø£ÙˆÙ„ Ø±Ø³Ø§Ù„Ø© Ù„ÙƒÙ„ Ø²Ø¨ÙˆÙ† Ø¬Ø¯ÙŠØ¯.\n- Ø§Ø¬Ù…Ø¹ÙŠ Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø§Ù„Ø·Ù„Ø¨ Ø®Ø·ÙˆØ© Ø¨Ø®Ø·ÙˆØ©.\n\n[3. PRODUCT & ORDER RULES]\n- Ø§Ù„Ù…Ù‚Ø§Ø³Ø§Øª Ø§Ù„Ù…ØªÙˆÙØ±Ø©: 36-41 Ø£ÙˆØ±ÙˆØ¨ÙŠ.\n- Ø§Ù„ØªÙˆØµÙŠÙ„ Ø¹Ø¨Ø± ZR Express Ù„ÙƒÙ„ ÙˆÙ„Ø§ÙŠØ§Øª Ø§Ù„Ø¬Ø²Ø§Ø¦Ø±.\n- Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù….")
                with engine.connect() as _conn:
                    # Check if ai_settings for store=1 exists and has no model
                    _existing = _conn.execute(_sql_text("SELECT id, ai_model, system_prompt FROM ai_settings WHERE store_id = '1'")).fetchone()
                    if _existing:
                        _needs_update = not _existing[1] or not _existing[2]
                        if _needs_update:
                            _conn.execute(
                                _sql_text("UPDATE ai_settings SET ai_model = 'Qwen/Qwen3-VL-30B-A3B-Instruct', system_prompt = :prompt, language = 'ar', temperature = 0.7, max_tokens = 2048, greeting_enabled = TRUE, updated_at = :now WHERE store_id = '1'"),
                                {"prompt": _DEFAULT_PROMPT, "now": _dt.utcnow()}
                            )
                            _conn.commit()
                            logger.info("âœ… AI settings updated for store 1 (model + prompt)")
                        else:
                            logger.info("âœ… AI settings for store 1 already configured")
                    else:
                        _conn.execute(
                            _sql_text("INSERT INTO ai_settings (id, store_id, ai_model, system_prompt, language, temperature, max_tokens, greeting_enabled) VALUES (gen_random_uuid()::text, '1', 'Qwen/Qwen3-VL-30B-A3B-Instruct', :prompt, 'ar', 0.7, 2048, TRUE)"),
                            {"prompt": _DEFAULT_PROMPT}
                        )
                        _conn.commit()
                        logger.info("âœ… AI settings created for store 1")
            except Exception as ai_e:
                logger.warning(f"âš ï¸ AI settings seed (non-critical): {ai_e}")
        except Exception as e:
            logger.warning(f"âš ï¸ DB init (will retry on first request): {e}")

    # â”€â”€â”€ Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.route("/")
    def index():
        """Landing Page â€” the main entrance to RC Agents"""
        try:
            return render_template("landing.html")
        except Exception:
            return send_from_directory(app.static_folder, "landing.html")

    @app.route("/dashboard")
    def dashboard():
        """Dark Neon Cyberpunk Dashboard â€” full with AI Brain + Charts + Live Chat"""
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
        """Privacy Policy â€” required for Meta App Review"""
        try:
            return render_template("privacy.html")
        except Exception:
            return send_from_directory(app.static_folder, "privacy.html")

    @app.route("/terms")
    def terms():
        """Terms of Service â€” required for Meta App Review"""
        try:
            return render_template("terms.html")
        except Exception:
            return send_from_directory(app.static_folder, "terms.html")

    @app.route("/dashboard/orders")
    def dashboard_orders():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/clients")
    def dashboard_clients():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/products")
    def dashboard_products():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/chat")
    def dashboard_chat():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/settings")
    def dashboard_settings():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/shipments")
    def dashboard_shipments():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/constellation")
    def dashboard_constellation():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/auto-ship")
    def dashboard_autoship():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/agents")
    def dashboard_agents():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/analytics")
    def dashboard_analytics():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/inventory")
    def dashboard_inventory():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/dashboard/marketing")
    def dashboard_marketing():
        return send_from_directory(app.static_folder, "dashboard.html")

    # â”€â”€â”€ Webhook Endpoint (Messenger & Instagram) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

        # TEMP: Legacy flow â€” import from server.py
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

    # â”€â”€â”€ Import webhook handlers from root server.py â”€â”€â”€â”€â”€â”€â”€â”€
    import importlib.util
    _server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")
    _spec = importlib.util.spec_from_file_location("webhook_server", _server_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _legacy_process_messaging = _mod.process_messaging_entries
    _legacy_process_whatsapp = _mod.process_whatsapp_entries
    send_fb_reply = _mod.send_fb_reply
    send_ig_reply = _mod.send_ig_reply
    send_whatsapp_reply = _mod.send_whatsapp_reply

    # â”€â”€â”€ Multi-Tenant Webhook Processors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    from .database.crud import get_store_id_by_platform as _saas_get_store_id, get_store_id_by_whatsapp_phone as _saas_get_store_wa, get_or_create_conversation, save_message, get_or_create_ai_settings
    import importlib as _imp2
    _legacy_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "db.py")
    _legacy_db_spec = _imp2.util.spec_from_file_location("legacy_db", _legacy_db_path)
    _legacy_db_mod = _imp2.util.module_from_spec(_legacy_db_spec)
    try:
        _legacy_db_spec.loader.exec_module(_legacy_db_mod)
    except Exception:
        _legacy_db_mod = None

    def _get_store_id_from_entry(entry, channel_type):
        """Extract store_id from webhook entry based on channel type"""
        entry_id = entry.get("id", "")
        if entry_id:
            try:
                sid = _saas_get_store_id(channel_type, str(entry_id))
                if sid:
                    return sid
            except Exception:
                pass
            # Fallback to local SQLite DB if PostgreSQL fails
            if _legacy_db_mod:
                try:
                    sid = _legacy_db_mod.get_store_id_by_platform(channel_type, str(entry_id))
                    if sid and sid != 1 or True:  # use fallback result
                        return sid
                except Exception:
                    pass
        return None

    def _process_messaging_multi(entries, platform, send_func):
        """Multi-tenant: process Messenger/Instagram messages with store_id lookup"""
        logger.info(f"[MT] process_messaging: plat={platform} entries={len(entries)}")
        channel_type = "messenger" if platform == "FB" else "instagram"
        for entry in entries:
            store_id = _get_store_id_from_entry(entry, channel_type)
            if not store_id:
                logger.warning(f"[MT] No store for {channel_type} entry {entry.get('id','')}, falling back to legacy")
                _legacy_process_messaging([entry], platform, send_func)
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
                    try:
                        store_id = _saas_get_store_wa(str(phone_id))
                    except Exception:
                        pass
                    if not store_id and _legacy_db_mod:
                        try:
                            store_id = _legacy_db_mod.get_store_id_by_whatsapp_phone(str(phone_id))
                        except Exception:
                            pass
                if not store_id:
                    logger.warning(f"[MT] No store for WA phone {phone_id}, falling back to legacy")
                    _legacy_process_whatsapp([entry])
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
            "version": "2.0.1",
            "ai_model": os.getenv("AI_MODEL", "Qwen/Qwen3-VL-30B-A3B-Instruct"),
        })

    @app.route("/api/plans")
    def list_plans():
        return jsonify(Config.PLANS)

    # â”€â”€â”€ API: Tenant Onboard (Multi-Store Registration) â”€â”€â”€â”€â”€

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

            logger.info(f"âœ… New tenant registered: {store_name} (ID: {store_id})")

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

    # â”€â”€â”€ Error Handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/admin/migrate")
    def api_migrate():
        """Run DB migration + seed AI settings for store 1"""
        _seed_result = "skipped"
        try:
            from .database.models import Base, get_engine
            from sqlalchemy import text as _txt
            from datetime import datetime as _dt
            import uuid
            url = os.getenv("DATABASE_URL") or os.getenv("SAAS_DATABASE_URL")
            if not url:
                return jsonify({"error": "No DATABASE_URL in environment"}), 400
            engine = get_engine(url)
            Base.metadata.create_all(engine)
            inspector = __import__("sqlalchemy").inspect(engine)
            tables = inspector.get_table_names()

            # ðŸ§  Seed AI settings for store=1 (always runs)
            try:
                _ai_prompt = "[1. ROYAL IDENTITY]\nName: Louve\nRole: Sales assistant\nStore: Royal Chaussures\n\n[2. RULES]\n- Reply in Algerian Arabic\n- Use emojis\n- Never say you are AI\n\n[3. PRODUCTS]\n- Sizes: 36-41 EU\n- Delivery: ZR Express all Algeria\n- Payment: Cash on delivery"
                with engine.connect() as _conn:
                    _existing = _conn.execute(_txt("SELECT id FROM ai_settings WHERE store_id = '1'")).fetchone()
                    if _existing:
                        _conn.execute(_txt("UPDATE ai_settings SET ai_model = 'Qwen/Qwen3-VL-30B-A3B-Instruct', system_prompt = :p, language = 'ar', temperature = 0.7, max_tokens = 2048, greeting_enabled = TRUE, updated_at = :now WHERE store_id = '1'"), {"p": _ai_prompt, "now": _dt.utcnow()})
                        _seed_result = "updated"
                    else:
                        _conn.execute(_txt("INSERT INTO ai_settings (id, store_id, ai_model, system_prompt, language, temperature, max_tokens, greeting_enabled) VALUES (:id, '1', 'Qwen/Qwen3-VL-30B-A3B-Instruct', :p, 'ar', 0.7, 2048, TRUE)"), {"id": str(uuid.uuid4()), "p": _ai_prompt})
                        _seed_result = "created"
                    _conn.commit()
            except Exception as _se:
                _seed_result = f"error: {_se}"

            engine.dispose()
            return jsonify({"status": "ok", "tables": tables, "ai_seed": _seed_result, "model": "Qwen/Qwen3-VL-30B-A3B-Instruct"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# â”€â”€â”€ Entry Point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", Config.DASHBOARD_PORT))
    logger.info(f"RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
