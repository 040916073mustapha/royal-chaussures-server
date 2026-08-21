"""
SaaS Core — Configuration Module
RC Agents Platform — Multi-Tenant AI Agent Backend
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Load .env from parent workspace


# Helper: read from primary env name first, fallback to secondary
_env = os.getenv


class Config:
    """Central configuration for SaaS Core"""

    # ─── Database ────────────────────────────────────────────
    DB_ENGINE = _env("SAAS_DB_ENGINE", _env("DB_ENGINE", "postgresql"))
    DATABASE_URL = _env("SAAS_DATABASE_URL", _env("DATABASE_URL", ""))
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://saas_user:saas_password@localhost:5432/rcagents"

    # ─── Auth ────────────────────────────────────────────────
    JWT_SECRET = _env("SAAS_JWT_SECRET", _env("JWT_SECRET", "change-me-in-production-v3"))
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = 72

    # ─── Shopify ─────────────────────────────────────────────
    SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
    SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "")
    SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "")

    # ─── AI (DeepInfra) ──────────────────────────────────────
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "openai/deepseek-ai/DeepSeek-V4-Flash")
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "4096"))
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))

    # ─── Meta Platforms ──────────────────────────────────────
    META_APP_SECRET = os.getenv("META_APP_SECRET", "")

    # ─── Dashboard ───────────────────────────────────────────
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5050"))
    DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
    DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "change-me")

    # ─── Plans & Limits ──────────────────────────────────────
    PLANS = {
        "free": {
            "name": "Free",
            "monthly_conversations": 50,
            "max_channels": 1,
            "price_usd": 0,
        },
        "starter": {
            "name": "Starter",
            "monthly_conversations": 500,
            "max_channels": 3,
            "price_usd": 19,
        },
        "business": {
            "name": "Business",
            "monthly_conversations": 2000,
            "max_channels": 10,
            "price_usd": 49,
        },
        "enterprise": {
            "name": "Enterprise",
            "monthly_conversations": 99999,
            "max_channels": 99,
            "price_usd": 199,
        },
    }
