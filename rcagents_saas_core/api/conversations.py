"""
SaaS Core — Conversations API (Message history & management)
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from ..database.models import Conversation, Message, Store, get_session
from .auth import require_auth

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/api/conversations/<store_id>", methods=["GET"])
@require_auth
def list_conversations(store_id):
    """List conversations for a store"""
    session = get_session()
    try:
        # Verify store ownership
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()
        if not store:
            return jsonify({"error": "Store not found"}), 404

        channel = request.args.get("channel")  # optional filter
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))
        search = request.args.get("search", "").strip()

        query = session.query(Conversation).filter_by(store_id=store_id)

        if channel:
            query = query.filter_by(channel=channel)

        if search:
            query = query.filter(
                Conversation.customer_name.ilike(f"%{search}%")
            )

        total = query.count()
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).offset(offset).limit(limit).all()

        return jsonify({
            "total": total,
            "conversations": [
                {
                    "id": c.id,
                    "channel": c.channel,
                    "customer_name": c.customer_name or "Unknown",
                    "customer_platform_id": c.customer_platform_id,
                    "last_message": c.last_user_message or "",
                    "last_reply": c.last_ai_reply or "",
                    "message_count": c.message_count,
                    "is_active": c.is_active,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in conversations
            ]
        })

    finally:
        session.close()


@conversations_bp.route("/api/conversations/<store_id>/<conv_id>/messages", methods=["GET"])
@require_auth
def get_messages(store_id, conv_id):
    """Get messages for a specific conversation"""
    session = get_session()
    try:
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()
        if not store:
            return jsonify({"error": "Store not found"}), 404

        conv = session.query(Conversation).filter_by(
            id=conv_id,
            store_id=store_id,
        ).first()
        if not conv:
            return jsonify({"error": "Conversation not found"}), 404

        limit = min(int(request.args.get("limit", 100)), 500)

        messages = session.query(Message).filter_by(
            conversation_id=conv_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).all()

        return jsonify({
            "conversation": {
                "id": conv.id,
                "channel": conv.channel,
                "customer_name": conv.customer_name,
                "is_active": conv.is_active,
            },
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "content_type": m.content_type,
                    "image_url": m.image_url,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ]
        })

    finally:
        session.close()


@conversations_bp.route("/api/conversations/<store_id>/<conv_id>/intervention", methods=["POST"])
@require_auth
def toggle_intervention(store_id, conv_id):
    """Toggle intervention mode for a conversation"""
    session = get_session()
    try:
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()
        if not store:
            return jsonify({"error": "Store not found"}), 404

        # Intervention is per-channel, not per-conversation
        from ..database.models import Channel
        data = request.get_json(silent=True) or {}
        channel_type = data.get("channel")

        if not channel_type:
            return jsonify({"error": "Channel type required"}), 400

        channel = session.query(Channel).filter_by(
            store_id=store_id,
            channel_type=channel_type,
        ).first()

        if not channel:
            return jsonify({"error": "Channel not found"}), 404

        channel.intervention_mode = not channel.intervention_mode
        session.commit()

        return jsonify({
            "success": True,
            "intervention_mode": channel.intervention_mode,
            "channel": channel_type,
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
