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

from flask import Flask, jsonify, send_from_directory, request, Response
from flask_cors import CORS

from .config import Config
from .database.models import init_db

# Import API Blueprints
from .api.auth import auth_bp
from .api.stores import stores_bp
from .api.settings import settings_bp
from .api.conversations import conversations_bp

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
        return send_from_directory(app.static_folder, "login.html")

    @app.route("/dashboard")
    def dashboard():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/onboarding")
    def onboarding():
        return send_from_directory(app.static_folder, "onboarding.html")

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

    # ─── Error Handlers ──────────────────────────────────────

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    return app


# ─── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", Config.DASHBOARD_PORT))
    logger.info(f"🚀 RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
