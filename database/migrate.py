"""
Nexus POS — Alembic Configuration
====================================
لتوليد وتطبيق التغييرات على قاعدة PostgreSQL بسلاسة

الاستخدام:
    alembic init alembic          # أول مرة — تم
    alembic revision --autogenerate -m "init"
    alembic upgrade head
"""

import os
from alembic.config import Config
from alembic import command


ALEMBIC_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "alembic.ini")


def get_alembic_config():
    """Get Alembic config with database URL from env"""
    cfg = Config(ALEMBIC_CFG_PATH)
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def run_migrations():
    """تشغيل الترحيلات التلقائية"""
    cfg = get_alembic_config()
    command.upgrade(cfg, "head")
    print("[Alembic] Migrations applied successfully")


def create_revision(message="auto"):
    """إنشاء مراجعة جديدة"""
    cfg = get_alembic_config()
    command.revision(cfg, autogenerate=True, message=message)
    print(f"[Alembic] Revision created: {message}")
