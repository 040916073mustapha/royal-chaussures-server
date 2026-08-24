"""SQLAlchemy models — Multi-tenant schema (store_id on every business table)."""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Tenant(Base):
    """Each tenant = one store/business."""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(255), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)  # e.g. "royal-chaussures"
    domain = Column(String(255), nullable=True)  # custom domain if any
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # ── Per-tenant credentials ─────────────────────────
    shopify_shop_url = Column(String(255), default="")
    shopify_catalog_token = Column(String(255), default="")
    shopify_orders_token = Column(String(255), default="")
    meta_page_access_token = Column(String(255), default="")
    meta_business_account_id = Column(String(128), default="")
    whatsapp_token = Column(String(255), default="")
    whatsapp_phone_number_id = Column(String(64), default="")
    ai_system_prompt = Column(Text, nullable=True)
    zr_api_key = Column(String(255), default="")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)  # FK → tenants.id
    shopify_order_id = Column(String(64), nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(64), nullable=True)
    customer_email = Column(String(255), nullable=True)
    total_price = Column(Float, default=0.0)
    currency = Column(String(8), default="DZD")
    financial_status = Column(String(64), default="pending")
    fulfillment_status = Column(String(64), default="unfulfilled")
    shipping_city = Column(String(128), nullable=True)
    shipping_wilaya = Column(String(64), nullable=True)
    items = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        # Each store has its own unique shopify_order_id space
        {"sqlite_autoincrement": True},  # ignored by PostgreSQL
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    platform = Column(String(32), nullable=False)  # messenger | whatsapp | instagram | shopify
    platform_user_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    shopify_product_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    price = Column(Float, default=0.0)
    compare_at_price = Column(Float, nullable=True)
    currency = Column(String(8), default="DZD")
    sizes = Column(JSON, default=list)  # ["36","37","38","39","40","41"]
    colors = Column(JSON, default=list)
    image_url = Column(Text, nullable=True)
    inventory_quantity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, nullable=False, index=True)
    platform = Column(String(32), nullable=False)
    platform_conversation_id = Column(String(128), nullable=False)
    customer_id = Column(Integer, nullable=True)
    messages_count = Column(Integer, default=0)
    last_message = Column(Text, nullable=True)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)
    agent_handled = Column(String(64), default="all")  # sales|support|shipping|inventory|marketing|all
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
