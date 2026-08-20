"""
SaaS Core — Settings API (AI per-store configuration)
"""

from flask import Blueprint, request, jsonify

from ..database.models import AISettings, Store, get_session
from .auth import require_auth

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/api/settings/<store_id>", methods=["GET"])
@require_auth
def get_settings(store_id):
    """Get AI settings for a store"""
    session = get_session()
    try:
        # Verify store ownership
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()
        if not store:
            return jsonify({"error": "Store not found"}), 404

        settings = session.query(AISettings).filter_by(store_id=store_id).first()
        if not settings:
            return jsonify({
                "system_prompt": "",
                "ai_model": "",
                "temperature": 0.7,
                "max_tokens": 2048,
                "language": "ar",
                "greeting_enabled": True,
                "greeting_message": "",
                "product_catalog_count": 0,
                "faq_count": 0,
            })

        return jsonify({
            "system_prompt": settings.system_prompt or "",
            "ai_model": settings.ai_model or "",
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "language": settings.language,
            "greeting_enabled": settings.greeting_enabled,
            "greeting_message": settings.greeting_message or "",
            "product_catalog_count": len(settings.product_catalog) if settings.product_catalog else 0,
            "faq_count": len(settings.faq_entries) if settings.faq_entries else 0,
        })

    finally:
        session.close()


@settings_bp.route("/api/settings/<store_id>", methods=["PUT"])
@require_auth
def update_settings(store_id):
    """Update AI settings for a store"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    session = get_session()
    try:
        # Verify store ownership
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()
        if not store:
            return jsonify({"error": "Store not found"}), 404

        settings = session.query(AISettings).filter_by(store_id=store_id).first()
        if not settings:
            settings = AISettings(store_id=store_id)
            session.add(settings)

        # Update fields
        if "system_prompt" in data:
            settings.system_prompt = data["system_prompt"]
        if "ai_model" in data:
            settings.ai_model = data["ai_model"]
        if "temperature" in data:
            settings.temperature = float(data["temperature"])
        if "max_tokens" in data:
            settings.max_tokens = int(data["max_tokens"])
        if "language" in data:
            settings.language = data["language"]
        if "greeting_enabled" in data:
            settings.greeting_enabled = bool(data["greeting_enabled"])
        if "greeting_message" in data:
            settings.greeting_message = data["greeting_message"]
        if "faq_entries" in data:
            settings.faq_entries = data["faq_entries"]

        session.commit()

        return jsonify({"success": True, "message": "Settings updated"})

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@settings_bp.route("/api/settings/<store_id>/sync-catalog", methods=["POST"])
@require_auth
def refresh_catalog(store_id):
    """Manually refresh product catalog from Shopify"""
    from .stores import sync_store
    return sync_store(store_id)
