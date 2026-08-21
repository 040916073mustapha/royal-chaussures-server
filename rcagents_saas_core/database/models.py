"""
SaaS Core — Database Models (SQLAlchemy ORM)
Multi-Tenant Schema for RC Agents Platform
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, String, Text, Integer, Float,
    Boolean, DateTime, ForeignKey, JSON, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


# ─── Users (Tenant Owners) ─────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    company = Column(String(255), default="")

    # Subscription
    plan = Column(String(50), default="free", nullable=False)  # free|starter|business|enterprise
    plan_status = Column(String(20), default="active")  # active|past_due|canceled
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))

    # Meta Business Manager
    meta_bm_id = Column(String(255))
    meta_system_user_token = Column(Text)

    # Limits tracking
    conversations_this_month = Column(Integer, default=0)
    billing_period_start = Column(DateTime, default=utcnow)

    # Timestamps
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    stores = relationship("Store", back_populates="user", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_email", "email"),
    )


# ─── Stores (Shopify Stores) ──────────────────────────────────

class Store(Base):
    __tablename__ = "stores"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Shopify
    shopify_domain = Column(String(255), nullable=False)
    shopify_access_token = Column(String(255), nullable=False)
    shopify_store_id = Column(String(255))
    shopify_location_id = Column(String(50), default="")

    # Status
    is_connected = Column(Boolean, default=True)
    last_sync_at = Column(DateTime)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="stores")

    __table_args__ = (
        UniqueConstraint("user_id", "shopify_domain", name="uq_user_store"),
    )


# ─── Channels (Messaging Platforms) ───────────────────────────

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)

    channel_type = Column(String(50), nullable=False)  # messenger|instagram|whatsapp|telegram
    platform_id = Column(String(255), nullable=False)   # Page ID / Phone ID / Bot ID
    platform_name = Column(String(255))                  # Display name
    access_token = Column(Text)
    webhook_secret = Column(String(255))

    # Intervention mode (manual override per channel)
    intervention_mode = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="channels")

    __table_args__ = (
        UniqueConstraint("user_id", "channel_type", "platform_id", name="uq_user_channel"),
    )


# ─── Conversations ────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)            # messenger|instagram|whatsapp
    platform_conversation_id = Column(String(255))          # PSID / IG ID / WA ID
    customer_name = Column(String(255))
    customer_platform_id = Column(String(255))              # Sender PSID etc.

    # Last AI context
    last_ai_reply = Column(Text)
    last_user_message = Column(Text)
    conversation_state = Column(JSON, default=dict)         # Step-by-step state

    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("store_id", "platform_conversation_id", name="uq_store_conversation"),
        Index("idx_conversation_channel", "store_id", "channel"),
    )


# ─── Messages ─────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=False)

    role = Column(String(20), nullable=False)               # user|assistant|system
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")       # text|image|quick_reply
    image_url = Column(Text)

    platform_message_id = Column(String(255))
    channel = Column(String(50), nullable=False)

    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id", "created_at"),
    )


# ─── AI Settings (Per Store) ──────────────────────────────────

class AISettings(Base):
    __tablename__ = "ai_settings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    store_id = Column(String(36), ForeignKey("stores.id"), unique=True, nullable=False)

    system_prompt = Column(Text, default="")                 # Custom prompt for this store
    ai_model = Column(String(100), default="")               # Override model
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)

    # Knowledge base
    product_catalog = Column(JSON, default=list)             # Cached product info
    faq_entries = Column(JSON, default=list)                 # Custom FAQs

    # Language
    language = Column(String(10), default="ar")              # ar|fr|en
    greeting_enabled = Column(Boolean, default=True)
    greeting_message = Column(Text, default="")

    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


# ─── Subscription Invoices ────────────────────────────────────

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)

    plan = Column(String(50), nullable=False)
    amount_usd = Column(Float, nullable=False)
    amount_dzd = Column(Float)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="pending")           # pending|paid|failed|canceled
    payment_method = Column(String(50))                       # stripe|baridimob|transfer
    payment_id = Column(String(255))                         # Stripe ID / reference

    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=utcnow)
    paid_at = Column(DateTime)


# ─── Factory ──────────────────────────────────────────────────

def get_engine(database_url=None):
    """Create SQLAlchemy engine"""
    # Read from multiple env var names for flexibility
    url = database_url or os.getenv("SAAS_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///./rcagents.db"
    if url.startswith("postgres"):
        return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)
    return create_engine(url, connect_args={"check_same_thread": False})


def init_db(engine=None):
    """Create all tables"""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """Get a new session"""
    if engine is None:
        engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# ─── Helper: Get engine via Session maker ─────────────────────

_session_factory = None
_session_lock = object()


def get_global_engine():
    """Get or create the global engine (singleton)"""
    global _session_factory
    if _session_factory is None:
        _session_factory = get_engine()
    return _session_factory


def get_global_session():
    """Get a new session from the global engine"""
    engine = get_global_engine()
    s = sessionmaker(bind=engine)
    return s()
