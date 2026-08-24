"""
SaaS Core â€” CRUD Operations for Multi-Tenant Schema
RC Agents Platform
"""

import logging
from sqlalchemy.orm import Session
from .models import (
    User, Store, Channel, Conversation, Message,
    AISettings, Invoice, get_global_session
)

logger = logging.getLogger("saas-core.db.crud")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# USERS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# STORES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CHANNELS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CONVERSATIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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
        _err_str = str(e)
        if "ForeignKeyViolation" in _err_str or "foreign key" in _err_str.lower() or "is not present in table 'stores'" in _err_str:
            # Auto-create the store if it doesn't exist
            logger.warning(f"[DB] Store {store_id} not found, attempting to create it")
            try:
                from sqlalchemy import text
                from datetime import datetime
                from .models import get_engine
                eng = get_engine()
                with eng.connect() as conn:
                    # Ensure a user exists
                    user_r = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
                    if not user_r:
                        import uuid
                        uid = str(uuid.uuid4())
                        conn.execute(
                            text("INSERT INTO users (id, email, name, created_at, updated_at) VALUES (:id, :email, :name, :now, :now)"),
                            {"id": uid, "email": "auto@rcagents.space", "name": "Auto User", "now": datetime.now()}
                        )
                        user_r = (uid,)
                    conn.execute(
                        text("""INSERT INTO stores (id, user_id, shopify_domain, shopify_access_token, is_connected, created_at, updated_at)
                               VALUES (:sid, :uid, 'auto.myshopify.com', 'auto', TRUE, :now, :now)
                               ON CONFLICT (id) DO NOTHING"""),
                        {"sid": _store_id_str, "uid": user_r[0], "now": datetime.now()}
                    )
                    conn.commit()
                logger.info(f"[DB] Store {store_id} auto-created successfully, retrying...")
                # Retry: recursively call self (one level only)
                return get_or_create_conversation(store_id, channel, platform_conversation_id, customer_name, customer_platform_id)
            except Exception as retry_err:
                logger.error(f"[DB] Auto-create store failed: {retry_err}")
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


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# AI SETTINGS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def get_or_create_ai_settings(store_id, db=None):
    """Get AI settings for a store, create default if not exists"""
    if db is None:
        db = get_global_session()
    try:
        settings = db.query(AISettings).filter(AISettings.store_id == store_id).first()
        if settings:
            # Ensure model is set even if previously null/empty
            _changed = False
            if not settings.ai_model:
                settings.ai_model = "meta-llama/Llama-3.3-70B-Instruct"
                _changed = True
            if not settings.system_prompt:
                settings.system_prompt = DEFAULT_SYSTEM_PROMPT
                _changed = True
            if not settings.language:
                settings.language = "ar"
                _changed = True
            if _changed:
                db.commit()
                logger.info(f"[AI] Default AI settings seeded for store {store_id}: DeepSeek-V4-Flash")
            return settings
        settings = AISettings(
            store_id=store_id,
            ai_model="meta-llama/Llama-3.3-70B-Instruct",
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=2048,
            language="ar",
            greeting_enabled=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
        logger.info(f"[AI] Default AI settings created for store {store_id}: DeepSeek-V4-Flash")
        return settings
    except Exception as e:
        db.rollback()
        logger.error(f"Get/create AI settings failed: {e}")
        raise
    finally:
        db.close()


# â”€â”€â”€ Default System Prompt â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

DEFAULT_SYSTEM_PROMPT = """[1. ROYAL IDENTITY]
Ø§Ù„Ø§Ø³Ù…: Ù„ÙˆÙ (Louve)
Ø§Ù„Ø¯ÙˆØ±: Ø´Ø±ÙŠÙƒØ© Ù…Ø¨ÙŠØ¹Ø§Øª Ø°ÙƒÙŠØ©ØŒ Ù…Ø³Ø§Ø¹Ø¯Ø© ØªÙ†ÙÙŠØ°ÙŠØ©ØŒ ÙˆÙ…Ø¯ÙŠØ±Ø© Ø±Ù‚Ù…ÙŠØ©.
Ø§Ù„Ø´Ø®ØµÙŠØ©: Ø¯Ø§ÙØ¦Ø©ØŒ Ù…Ø±Ø­Ø©ØŒ Ø°ÙƒÙŠØ©ØŒ ÙˆÙ…Ø­ØªØ±ÙØ©.
Ø§Ù„Ù…ØªØ¬Ø±: Royal Chaussures â€” Ø£Ø­Ø°ÙŠØ© ÙˆØ¥ÙƒØ³Ø³ÙˆØ§Ø±Ø§Øª Ù†Ø³Ø§Ø¦ÙŠØ© ÙØ§Ø®Ø±Ø©.

[2. COMMUNICATION RULES]
- Ø§Ù„Ø±Ø¯ÙˆØ¯ ØªÙƒÙˆÙ† Ø¯Ø§Ø¦Ù…Ø§Ù‹ Ø¨Ø§Ù„Ù„Ù‡Ø¬Ø© Ø§Ù„Ø¬Ø²Ø§Ø¦Ø±ÙŠØ© Ø§Ù„Ø¯Ø§Ø±Ø¬Ø© Ø£Ùˆ Ø§Ù„Ø¹Ø±Ø¨ÙŠØ© Ø§Ù„ÙØµØ­Ù‰ Ø§Ù„Ø¨Ø³ÙŠØ·Ø©.
- Ø§Ø³ØªØ®Ø¯Ù…ÙŠ Ø§Ù„Ø¥ÙŠÙ…ÙˆØ¬ÙŠ Ø§Ù„Ù…Ù†Ø§Ø³Ø¨ âœ¨ðŸ›ï¸ðŸ’ª.
- Ù„Ø§ ØªØ´Ø±Ø­ÙŠ Ø£Ø¨Ø¯Ø§Ù‹ Ø£Ù†Ùƒ Ù†Ø¸Ø§Ù… Ø£Ùˆ AI Ø£Ùˆ Ø±ÙˆØ¨ÙˆØª. Ø£Ù†Øª Ø¨Ø¨Ø³Ø§Ø·Ø© Ù…Ø³Ø§Ø¹Ø¯Ø© Ø§Ù„Ù…ØªØ¬Ø±.
- Ù„Ø§ ØªÙƒØ±Ø±ÙŠ Ø§Ù„ØªØ¹Ù„ÙŠÙ…Ø§Øª Ø£Ùˆ Ø§Ù„Ù…Ù†Ø´ÙˆØ± ÙÙŠ Ø±Ø¯ÙˆØ¯Ùƒ.
- Ø±Ø­Ø¨ÙŠ ØªØ±Ø­ÙŠØ¨Ø© Ø¨Ø³ÙŠØ·Ø© ÙÙ‚Ø· ÙÙŠ Ø£ÙˆÙ„ Ø±Ø³Ø§Ù„Ø© Ù„ÙƒÙ„ Ø²Ø¨ÙˆÙ† Ø¬Ø¯ÙŠØ¯.
- Ø§Ø¬Ù…Ø¹ÙŠ Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø§Ù„Ø·Ù„Ø¨ Ø®Ø·ÙˆØ© Ø¨Ø®Ø·ÙˆØ©.

[3. PRODUCT & ORDER RULES]
- Ø§Ù„Ù…Ù‚Ø§Ø³Ø§Øª Ø§Ù„Ù…ØªÙˆÙØ±Ø©: 36-41 Ø£ÙˆØ±ÙˆØ¨ÙŠ.
- Ø¥Ø°Ø§ Ø³Ø£Ù„ Ø¹Ù† Ø§Ù„ØªÙˆÙØ±: ØªØ­Ù‚Ù‚ÙŠ Ù…Ù† Ø§Ù„Ù‚Ø§Ø¦Ù…Ø© Ø£Ø¹Ù„Ø§Ù‡.
- Ø¥Ø°Ø§ Ø·Ù„Ø¨ Ù…Ù‚Ø§Ø³ ØºÙŠØ± Ù…ØªÙˆÙØ±: Ø§Ø¹Ø±Ø¶ÙŠ Ø§Ù„Ù…Ù‚Ø§Ø³Ø§Øª Ø§Ù„Ù…ØªØ§Ø­Ø©.
- Ø§Ù„ØªÙˆØµÙŠÙ„ Ø¹Ø¨Ø± ZR Express Ù„ÙƒÙ„ ÙˆÙ„Ø§ÙŠØ§Øª Ø§Ù„Ø¬Ø²Ø§Ø¦Ø±.
- Ø£Ø³Ø¹Ø§Ø± Ø§Ù„ØªÙˆØµÙŠÙ„ Ø­Ø³Ø¨ Ø§Ù„ÙˆÙ„Ø§ÙŠØ©.
- Ø§Ù„Ø¯ÙØ¹ Ø¹Ù†Ø¯ Ø§Ù„Ø§Ø³ØªÙ„Ø§Ù…."""


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# WEBHOOK HELPERS â€” Platform â†’ Store lookup
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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
