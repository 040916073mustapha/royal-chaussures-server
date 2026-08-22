"""
RC Agents — Stats & Analytics API
Endpoints for dashboard: stats, store info, products, sales-by-channel, AI Brain
"""

import logging
from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import ProgrammingError, OperationalError

from ..database.models import (
    Store, Channel, Conversation, Message, AISettings,
    Invoice, get_global_session
)

logger = logging.getLogger("saas-core.api.stats")
stats_bp = Blueprint("stats", __name__, url_prefix="/api")


# ─── GET /api/store/<store_id> ────────────────────────────────

@stats_bp.route("/store/<store_id>", methods=["GET"])
def get_store(store_id):
    """Get store info by ID"""
    db = get_global_session()
    try:
        try:
            store = db.query(Store).filter(Store.id == store_id).first()
            if not store:
                return jsonify({"error": "Store not found"}), 404
        except (ProgrammingError, OperationalError) as e:
            logger.warning(f"Store table not ready: {e}")
            return jsonify({"id": store_id, "shopify_domain": "", "is_connected": False, "channels": []})

        channels_data = []
        try:
            channels = db.query(Channel).filter(Channel.store_id == store_id, Channel.is_active == True).all()
            for c in channels:
                channels_data.append({"type": c.channel_type, "name": c.platform_name, "active": c.is_active})
        except Exception:
            pass

        return jsonify({
            "id": store.id,
            "shopify_domain": store.shopify_domain,
            "is_connected": store.is_connected,
            "last_sync_at": store.last_sync_at.isoformat() if store.last_sync_at else None,
            "channels": channels_data,
            "created_at": store.created_at.isoformat() if store.created_at else None,
        })
    except Exception as e:
        logger.error(f"Get store error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ─── GET /api/stats?store_id=<store_id> ───────────────────────

@stats_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get store dashboard stats — total orders, revenue, customers, active channels"""
    store_id = request.args.get("store_id")
    if not store_id:
        return jsonify({"error": "store_id is required"}), 400

    db = get_global_session()
    try:
        # Store info — wrapped in try/except for tables that may not exist yet
        try:
            store = db.query(Store).filter(Store.id == store_id).first()
            if not store:
                return jsonify({"error": "Store not found"}), 404
        except (ProgrammingError, OperationalError) as e:
            logger.warning(f"Stats tables not ready yet: {e}")
            return jsonify({
                "store_name": "My Store", "store_id": store_id, "connected": False,
                "total_conversations": 0, "active_conversations": 0, "total_messages": 0,
                "messages_today": 0, "active_channels": [], "channel_counts": {},
                "messages_by_channel": {}, "ai_configured": False, "ai_model": None,
                "total_invoices": 0, "total_revenue_usd": 0
            })

        def safe_count(model, filters):
            try:
                q = db.query(func.count(model.id))
                for f in filters:
                    q = q.filter(f)
                return q.scalar() or 0
            except Exception:
                return 0

        # Conversation stats
        total_conversations = safe_count(Conversation, [Conversation.store_id == store_id])
        active_conversations = safe_count(Conversation, [
            Conversation.store_id == store_id, Conversation.is_active == True
        ])

        # Message stats
        total_messages = safe_count(Message, [Message.store_id == store_id])
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = safe_count(Message, [
            Message.store_id == store_id, Message.created_at >= today_start
        ])

        # Channel breakdown
        active_channels = []
        try:
            channels = db.query(Channel).filter(Channel.store_id == store_id, Channel.is_active == True).all()
            active_channels = [
                {"type": c.channel_type, "name": c.platform_name or c.channel_type}
                for c in channels
            ]
        except Exception:
            pass

        # Conversations per channel
        channel_counts = {}
        for ch in ["messenger", "instagram", "whatsapp"]:
            count = safe_count(Conversation, [Conversation.store_id == store_id, Conversation.channel == ch])
            if count > 0:
                channel_counts[ch] = count

        # Messages per channel (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        messages_by_channel = {}
        for ch in ["messenger", "instagram", "whatsapp"]:
            count = safe_count(Message, [
                Message.store_id == store_id, Message.channel == ch,
                Message.created_at >= seven_days_ago
            ])
            if count > 0:
                messages_by_channel[ch] = count

        # AI Brain status
        ai_configured = False
        ai_model = None
        try:
            ai_settings = db.query(AISettings).filter(AISettings.store_id == store_id).first()
            ai_configured = ai_settings is not None and bool(ai_settings.system_prompt)
            ai_model = ai_settings.ai_model if ai_settings else None
        except Exception:
            pass

        # Invoice / Revenue stats
        total_invoices = safe_count(Invoice, [Invoice.store_id == store_id])
        total_revenue_usd = 0.0
        try:
            total_revenue_usd = db.query(func.sum(Invoice.amount_usd)).filter(
                Invoice.store_id == store_id,
                Invoice.status == "paid"
            ).scalar() or 0.0
        except Exception:
            pass
            Invoice.status == "paid"
        ).scalar() or 0.0

        return jsonify({
            "store_name": store.shopify_domain.split(".")[0].capitalize() if store.shopify_domain else "My Store",
            "store_id": store.id,
            "connected": store.is_connected,

            # Core stats
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages,
            "messages_today": messages_today,

            # Channels
            "active_channels": active_channels,
            "channel_counts": channel_counts,
            "messages_by_channel": messages_by_channel,

            # AI
            "ai_configured": ai_configured,
            "ai_model": ai_settings.ai_model if ai_settings else None,

            # Revenue
            "total_invoices": total_invoices,
            "total_revenue_usd": float(total_revenue_usd),

            # Timestamps
            "last_sync_at": store.last_sync_at.isoformat() if store.last_sync_at else None,
            "created_at": store.created_at.isoformat() if store.created_at else None,
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ─── GET /api/products?store_id=<store_id> ────────────────────

@stats_bp.route("/products", methods=["GET"])
def get_products():
    """Get store product catalog from AI settings (cached)"""
    store_id = request.args.get("store_id")
    if not store_id:
        # Fallback: try to get from global list
        pass

    db = get_global_session()
    try:
        if store_id:
            ai_settings = db.query(AISettings).filter(AISettings.store_id == store_id).first()
            products = ai_settings.product_catalog if ai_settings and ai_settings.product_catalog else []
        else:
            # Return all products across stores (limited)
            all_settings = db.query(AISettings).all()
            products = []
            for s in all_settings:
                if s.product_catalog:
                    for p in s.product_catalog:
                        p["store_id"] = s.store_id
                        products.append(p)

        return jsonify({
            "products": products,
            "total": len(products)
        })
    except Exception as e:
        logger.error(f"Products error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ─── GET /api/clients?store_id=<store_id> ─────────────────────

@stats_bp.route("/clients", methods=["GET"])
def get_clients():
    """Get store customers from conversations (unique customers)"""
    store_id = request.args.get("store_id")
    if not store_id:
        return jsonify({"error": "store_id is required"}), 400

    db = get_global_session()
    try:
        try:
            conversations = db.query(Conversation).filter(
                Conversation.store_id == store_id,
                Conversation.customer_name.isnot(None),
                Conversation.customer_name != ""
            ).order_by(Conversation.updated_at.desc()).all()
        except (ProgrammingError, OperationalError):
            return jsonify({"clients": [], "total": 0})

        clients = []
        seen = set()
        for conv in conversations:
            key = conv.customer_platform_id or conv.customer_name
            if key and key not in seen:
                seen.add(key)
                clients.append({
                    "id": conv.id,
                    "name": conv.customer_name,
                    "platform_id": conv.customer_platform_id,
                    "channel": conv.channel,
                    "message_count": conv.message_count,
                    "last_active": conv.updated_at.isoformat() if conv.updated_at else None,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                })

        return jsonify({
            "clients": clients,
            "total": len(clients)
        })
    except Exception as e:
        logger.error(f"Clients error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ─── GET /api/stats/sales-by-channel?store_id=<store_id> ──────

@stats_bp.route("/stats/sales-by-channel", methods=["GET"])
def sales_by_channel():
    """Get sales/conversation breakdown by channel"""
    store_id = request.args.get("store_id")
    if not store_id:
        return jsonify({"error": "store_id is required"}), 400

    db = get_global_session()
    try:
        # Protect against missing tables
        try:
            db.query(Store).filter(Store.id == store_id).first()
        except (ProgrammingError, OperationalError):
            return jsonify({"channels": [], "total_conversations": 0})

        channels_list = ["messenger", "instagram", "whatsapp"]
        result = []

        def safe_count_v2(model, filters):
            try:
                q = db.query(func.count(model.id))
                for f in filters:
                    q = q.filter(f)
                return q.scalar() or 0
            except Exception:
                return 0

        for ch in channels_list:
            conv_count = safe_count_v2(Conversation, [
                Conversation.store_id == store_id, Conversation.channel == ch
            ])
            msg_count = safe_count_v2(Message, [
                Message.store_id == store_id, Message.channel == ch
            ])
            inv_count = safe_count_v2(Invoice, [Invoice.store_id == store_id])

            if conv_count > 0 or msg_count > 0:
                result.append({
                    "channel": ch,
                    "label": {"messenger": "Messenger", "instagram": "Instagram", "whatsapp": "WhatsApp"}.get(ch, ch),
                    "icon": {"messenger": "💬", "instagram": "📸", "whatsapp": "💚"}.get(ch, "📱"),
                    "conversations": conv_count,
                    "messages": msg_count,
                    "orders": inv_count,
                    "percentage": 0
                })

        total_conv = sum(r["conversations"] for r in result)
        for r in result:
            r["percentage"] = round((r["conversations"] / total_conv * 100), 1) if total_conv > 0 else 0

        return jsonify({
            "channels": result,
            "total_conversations": total_conv
        })
    except Exception as e:
        logger.error(f"Sales by channel error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ─── GET /api/stats/ai-brain?store_id=<store_id> ──────────────

@stats_bp.route("/stats/ai-brain", methods=["GET"])
def ai_brain_status():
    """Get AI Brain status for the store"""
    store_id = request.args.get("store_id")
    if not store_id:
        return jsonify({"error": "store_id is required"}), 400

    db = get_global_session()
    try:
        try:
            ai_settings = db.query(AISettings).filter(AISettings.store_id == store_id).first()
        except (ProgrammingError, OperationalError):
            ai_settings = None

        if not ai_settings:
            return jsonify({
                "configured": False, "model": None, "language": "ar",
                "greeting_enabled": True, "system_prompt": None,
                "product_count": 0, "faq_count": 0,
                "messages_handled": 0, "messages_pending": 0, "avg_response_time": None,
                "active_conversations": 0, "resolution_rate": 0
            })

        def safe_count_v3(model, filters):
            try:
                q = db.query(func.count(model.id))
                for f in filters:
                    q = q.filter(f)
                return q.scalar() or 0
            except Exception:
                return 0

        messages_handled = safe_count_v3(Message, [
            Message.store_id == store_id, Message.role == "assistant"
        ])
        total_user_msgs = safe_count_v3(Message, [
            Message.store_id == store_id, Message.role == "user"
        ])
        messages_pending = max(0, total_user_msgs - messages_handled)
        product_count = len(ai_settings.product_catalog) if ai_settings.product_catalog else 0
        faq_count = len(ai_settings.faq_entries) if ai_settings.faq_entries else 0
        active_conv_count = safe_count_v3(Conversation, [
            Conversation.store_id == store_id, Conversation.is_active == True
        ])

        return jsonify({
            "configured": True,
            "model": ai_settings.ai_model or "DeepSeek-V4-Flash",
            "language": ai_settings.language or "ar",
            "greeting_enabled": ai_settings.greeting_enabled,
            "system_prompt_length": len(ai_settings.system_prompt) if ai_settings.system_prompt else 0,
            "product_count": product_count, "faq_count": faq_count,
            "messages_handled": messages_handled, "messages_pending": messages_pending,
            "active_conversations": active_conv_count,
            "resolution_rate": round((messages_handled / max(total_user_msgs, 1)) * 100, 1),
            "temperature": ai_settings.temperature,
            "updated_at": ai_settings.updated_at.isoformat() if ai_settings.updated_at else None,
        })
    except Exception as e:
        logger.error(f"AI Brain error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ─── GET /api/orders?store_id=<store_id>&limit=N&status=X ────

@stats_bp.route("/orders", methods=["GET"])
def get_orders():
    """Get orders from invoices (as proxy for orders)"""
    store_id = request.args.get("store_id")
    limit = request.args.get("limit", 50, type=int)
    status_filter = request.args.get("status")

    db = get_global_session()
    try:
        try:
            q = db.query(Invoice).filter(Invoice.store_id == store_id)
            if status_filter and status_filter != "all":
                q = q.filter(Invoice.status == status_filter)
            invoices = q.order_by(Invoice.created_at.desc()).limit(limit).all()
        except (ProgrammingError, OperationalError):
            return jsonify({"orders": [], "total": 0})

        orders = []
        for inv in invoices:
            orders.append({
                "id": inv.id,
                "order_number": inv.payment_id or inv.id[:8],
                "customer": (inv.user_id or "Unknown")[:16],
                "total": inv.amount_usd,
                "currency": inv.currency,
                "status": inv.status,
                "plan": inv.plan,
                "payment_method": inv.payment_method,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            })

        return jsonify({
            "orders": orders,
            "total": len(orders)
        })
    except Exception as e:
        logger.error(f"Orders error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
