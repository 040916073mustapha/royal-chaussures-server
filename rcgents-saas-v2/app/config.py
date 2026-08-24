"""pydantic-settings based configuration — single source of truth for all env vars."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "RC Agents v2"
    APP_ENV: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./test.db"  # Railway provides ${{DATABASE_URL}}

    # ── Shopify ──────────────────────────────────────────
    SHOPIFY_SHOP_URL: str = ""
    SHOPIFY_CATALOG_TOKEN: str = ""
    SHOPIFY_ORDERS_TOKEN: str = ""

    # ── Meta (Messenger / Instagram) ─────────────────────
    META_APP_SECRET: str = ""
    META_PAGE_ACCESS_TOKEN: str = ""
    META_VERIFY_TOKEN: str = ""
    META_BUSINESS_ACCOUNT_ID: str = ""

    # ── WhatsApp Cloud API ───────────────────────────────
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    # ── AI / DeepSeek ───────────────────────────────────
    AI_MODEL: str = "deepseek-ai/DeepSeek-V4-Flash"
    AI_API_KEY: str = ""
    AI_API_BASE: str = "https://api.deepinfra.com/v1/openai/chat/completions"
    AI_SYSTEM_PROMPT: Optional[str] = None

    # ── ZR Express Shipping ──────────────────────────────
    ZR_API_KEY: str = ""
    ZR_BASE_URL: str = "https://api.zrexpress.dz"

    # ── Domains ──────────────────────────────────────────
    BASE_URL: str = "https://rcagent.space"
    DOMAIN: str = "rcagent.space"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
