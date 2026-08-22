"""
SaaS Core — CRUD Operations for Multi-Tenant Schema
RC Agents Platform
"""

import logging
from sqlalchemy.orm import Session
from .models import (
    User, Store, Channel, Conversation, Message,
    AISettings, Invoice, get_global_session
)

logger = logging.getLogger("saas-core.db.crud")


# ═══════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════

def create_user(email, password_hash, name, company="", db=None):
    """Create a new user"""
    if db is None:
        db = get_global_session()
    try:
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            company=company
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User created: {email}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Create user failed: {e}")
        raise
    finally:
        db.close()


def get_user_by_email(email, db=None):
    """Get user by email"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def get_user_by_id(user_id, db=None):
    """Get user by ID"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# STORES
# ═══════════════════════════════════════════════════════════════

def create_store(user_id, shopify_domain, shopify_access_token, shopify_store_id="", db=None):
    """Create a new store"""
    if db is None:
        db = get_global_session()
    try:
        store = Store(
            user_id=user_id,
            shopify_domain=shopify_domain,
            shopify_access_token=shopify_access_token,
            shopify_store_id=shopify_store_id
        )
        db.add(store)
        db.commit()
        db.refresh(store)
        logger.info(f"Store created: {shopify_domain}")
        return store
    except Exception as e:
        db.rollback()
        logger.error(f"Create store failed: {e}")
        raise
    finally:
        db.close()


def get_store_by_id(store_id, db=None):
    """Get store by ID"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(Store).filter(Store.id == store_id).first()
    finally:
        db.close()


def get_store_by_shopify_domain(shopify_domain, db=None):
    """Get store by Shopify domain"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(Store).filter(Store.shopify_domain == shopify_domain).first()
    finally:
        db.close()


def get_stores_by_user(user_id, db=None):
    """Get all stores for a user"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(Store).filter(Store.user_id == user_id).all()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# CHANNELS
# ═══════════════════════════════════════════════════════════════

def create_channel(user_id, channel_type, platform_id, platform_name="", access_token="", store_id=None, db=None):
    """Create a new channel (messenger/instagram/whatsapp)"""
    if db is None:
        db = get_global_session()
    try:
        channel = Channel(
            user_id=user_id,
            store_id=store_id,
            channel_type=channel_type,
            platform_id=platform_id,
            platform_name=platform_name,
            access_token=access_token
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        logger.info(f"Channel created: {channel_type}/{platform_id}")
        return channel
    except Exception as e:
        db.rollback()
        logger.error(f"Create channel failed: {e}")
        raise
    finally:
        db.close()


def get_channel_by_platform(channel_type, platform_id, db=None):
    """Get channel by type and platform ID (e.g. messenger + Page ID)"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(Channel).filter(
            Channel.channel_type == channel_type,
            Channel.platform_id == platform_id
        ).first()
    finally:
        db.close()


def get_channels_by_store(store_id, db=None):
    """Get all channels for a store"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(Channel).filter(Channel.store_id == store_id).all()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# CONVERSATIONS
# ═══════════════════════════════════════════════════════════════

def get_or_create_conversation(store_id, channel, platform_conversation_id, customer_name="", customer_platform_id="", db=None):
    """Get existing conversation or create new one"""
    if db is None:
        db = get_global_session()
    try:
        from sqlalchemy import cast, String as _SA_Str
        _store_id_str = str(store_id) if not isinstance(store_id, str) else store_id
        conv = db.query(Conversation).filter(
            cast(Conversation.store_id, _SA_Str) == _store_id_str,
            Conversation.platform_conversation_id == platform_conversation_id
        ).first()
        if conv:
            # Update name if provided
            if customer_name and not conv.customer_name:
                conv.customer_name = customer_name
                db.commit()
            return conv

        conv = Conversation(
            store_id=store_id,
            channel=channel,
            platform_conversation_id=platform_conversation_id,
            customer_name=customer_name,
            customer_platform_id=customer_platform_id
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        logger.info(f"New conversation: {channel}/{platform_conversation_id[:20]}")
        return conv
    except Exception as e:
        db.rollback()
        logger.error(f"Get/create conversation failed: {e}")
        raise
    finally:
        db.close()


def save_message(conversation_id, store_id, role, content, channel, content_type="text", image_url="", platform_message_id="", db=None):
    """Save a message to the database"""
    if db is None:
        db = get_global_session()
    try:
        _store_id_str = str(store_id) if not isinstance(store_id, str) else store_id
        msg = Message(
            conversation_id=str(conversation_id),
            store_id=_store_id_str,
            role=role,
            content=content,
            content_type=content_type,
            image_url=image_url,
            channel=channel,
            platform_message_id=platform_message_id
        )
        db.add(msg)
        # Update conversation
        db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).update({
            Conversation.message_count: Conversation.message_count + 1,
            Conversation.last_user_message: content if role == "user" else Conversation.last_user_message,
            Conversation.last_ai_reply: content if role == "assistant" else Conversation.last_ai_reply,
            Conversation.updated_at: __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        })
        db.commit()
        return msg
    except Exception as e:
        db.rollback()
        logger.error(f"Save message failed: {e}")
        raise
    finally:
        db.close()


def get_conversation_messages(conversation_id, limit=50, db=None):
    """Get messages for a conversation"""
    if db is None:
        db = get_global_session()
    try:
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).limit(limit).all()
    finally:
        db.close()


def get_store_conversations(store_id, channel=None, limit=20, db=None):
    """Get all conversations for a store"""
    if db is None:
        db = get_global_session()
    try:
        q = db.query(Conversation).filter(Conversation.store_id == store_id)
        if channel:
            q = q.filter(Conversation.channel == channel)
        return q.order_by(Conversation.updated_at.desc()).limit(limit).all()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# AI SETTINGS
# ═══════════════════════════════════════════════════════════════

def get_or_create_ai_settings(store_id, db=None):
    """Get AI settings for a store, create default if not exists"""
    if db is None:
        db = get_global_session()
    try:
        settings = db.query(AISettings).filter(AISettings.store_id == store_id).first()
        if settings:
            return settings
        settings = AISettings(store_id=store_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    except Exception as e:
        db.rollback()
        logger.error(f"Get/create AI settings failed: {e}")
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# WEBHOOK HELPERS — Platform → Store lookup
# ═══════════════════════════════════════════════════════════════

def get_store_id_by_platform(channel_type, platform_id, db=None):
    """
    Find store_id by channel type + platform ID (FB Page ID, IG ID, WhatsApp Phone ID)
    Returns store_id string or None
    """
    if db is None:
        db = get_global_session()
    try:
        channel = db.query(Channel).filter(
            Channel.channel_type == channel_type,
            Channel.platform_id == platform_id,
            Channel.is_active == True
        ).first()
        if channel and channel.store_id:
            return channel.store_id
        return None
    finally:
        db.close()


def get_store_id_by_whatsapp_phone(phone_number_id, db=None):
    """Find store_id by WhatsApp Phone Number ID"""
    return get_store_id_by_platform("whatsapp", phone_number_id, db)


def get_system_prompt_for_store(store_id, db=None):
    """Get the AI system prompt for a store"""
    if db is None:
        db = get_global_session()
    try:
        settings = get_or_create_ai_settings(store_id, db)
        return settings.system_prompt or ""
    finally:
        db.close()
