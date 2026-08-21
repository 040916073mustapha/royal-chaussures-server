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

        if obj == "page":
            process_messaging_entries(data.get("entry", []), "FB", send_fb_reply)
        elif obj == "instagram":
            process_messaging_entries(data.get("entry", []), "IG", send_ig_reply)
        elif obj == "whatsapp_business_account":
            process_whatsapp_entries(data.get("entry", []))
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
            process_whatsapp_entries(data.get("entry", []))
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
