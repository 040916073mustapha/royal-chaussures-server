#!/usr/bin/env python3
"""
🤖 RC Agents — PostgreSQL Migration Script (Neon)
==================================================
ينفذ كل الـ Schema Statements على قاعدة بيانات PostgreSQL الخارجية (Neon).

الاستخدام:
    python scripts/migrate_pg.py               # ينفذ المخطط بالكامل
    python scripts/migrate_pg.py --seed         # ينفذ + يضيف المتجر الافتراضي
    python scripts/migrate_pg.py --check        # يفحص حالة الجداول فقط
    
متطلبات البيئة:
    DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
"""

import os
import sys
import json

# Read DATABASE_URL from env
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set in environment")
    print("   Set: DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require")
    sys.exit(1)

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "database", "nexus_schema_pg.sql"
)

SEED_SQL = """
-- ============================================================
-- 🌱 Seed: Default Store (Royal Chaussures)
-- ============================================================
INSERT INTO stores (id, name, slug, domain, email, phone, subscription_tier, subscription_status, is_active)
VALUES (1, 'Royal Chaussures', 'royal-chaussures', 'https://royalchaussures.com/',
        'royalchaussures2@gmail.com', '+213659832426', 'pro', 'active', TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    phone = EXCLUDED.phone;

-- Default store prompts for Royal Chaussures (store_id=1)
INSERT INTO store_prompts (store_id, prompt_type, prompt_text, is_active)
VALUES
    (1, 'customer_support',
     '[1. ROYAL IDENTITY]\nI represent Royal Chaussures...\n[2. MULTILINGUAL]\n[3. BEHAVIOR]\n[4. SHOPIFY INTEGRATION]\n[5. SHIPPING (ZR Express)]\n[6. CONTACT INFO]\n[7. CRM COMMANDS]',
     TRUE),
    (1, 'sales_agent',
     '[SALES AGENT]\nYou are a sales consultant for Royal Chaussures...\nHelp customers choose shoes and accessories.',
     TRUE),
    (1, 'shipping_tracking',
     '[SHIPPING AGENT]\nYou track shipments via ZR Express...\nProvide timely delivery updates.',
     TRUE),
    (1, 'inventory_agent',
     '[INVENTORY AGENT]\nYou manage stock queries for Royal Chaussures...\nCheck availability and notify restocks.',
     TRUE)
ON CONFLICT (store_id, prompt_type) DO NOTHING;

-- Default agent configs
INSERT INTO store_agent_config (store_id, agent_type, agent_name, agent_emoji, is_enabled)
VALUES
    (1, 'customer_support', 'Customer Support', '🎧', TRUE),
    (1, 'sales_agent', 'Sales Consultant', '🛍️', TRUE),
    (1, 'shipping_tracking', 'Shipping Tracker', '🚚', TRUE),
    (1, 'inventory_agent', 'Inventory Manager', '📦', TRUE)
ON CONFLICT (store_id, agent_type) DO NOTHING;

-- Default webhook registration for Royal Chaussures
INSERT INTO store_webhooks (store_id, platform, platform_account_id, platform_phone_id)
VALUES
    (1, 'messenger', 'ROYAL_FB_PAGE_ID', NULL),
    (1, 'whatsapp', 'ROYAL_WA_PHONE_ID', 'WHATSAPP_PHONE_NUMBER_ID'),
    (1, 'instagram', 'ROYAL_IG_ID', NULL)
ON CONFLICT (store_id, platform) DO NOTHING;
"""

CHECK_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"""


def run_migration(seed=False, check_only=False):
    """تنفيذ الـ Migration على PostgreSQL"""
    print("=" * 60)
    print("🔷 RC Agents — PostgreSQL Migration (Neon)")
    print("=" * 60)

    if check_only:
        print("\n🔍 Checking database tables...\n")
    else:
        print(f"\n📋 Schema: {SCHEMA_PATH}")
        print(f"🔌 Database: {DATABASE_URL[:40]}...\n")

    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    try:
        if check_only:
            cur.execute(CHECK_SQL)
            tables = cur.fetchall()
            print(f"📊 Found {len(tables)} tables:\n")
            for t in sorted(tables):
                # Get row counts
                try:
                    cur.execute(f"SELECT count(*) FROM {t[0]}")
                    count = cur.fetchone()[0]
                    print(f"   ✅ {t[0]:30s}  ({count} rows)")
                except Exception:
                    print(f"   🔶 {t[0]:30s}  (unknown)")
            return

        # === Read and execute nexus_schema_pg.sql ===
        print("📄 Reading schema file...")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        print("⚡ Executing schema statements...")
        statements = []
        current = ""
        for line in schema_sql.split("\n"):
            stripped = line.strip()
            if stripped.startswith("--") or stripped.startswith("/*"):
                continue
            if stripped == "":
                continue
            current += line + "\n"
            if stripped.endswith(";"):
                statements.append(current.strip())
                current = ""

        executed = 0
        errors = 0
        for stmt in statements:
            try:
                cur.execute(stmt)
                executed += 1
            except Exception as e:
                err_str = str(e)
                if "already exists" in err_str:
                    executed += 1
                    continue
                if "duplicate key" in err_str:
                    executed += 1
                    continue
                print(f"   ⚠️  Statement error (skipped): {err_str[:80]}")
                errors += 1

        print(f"\n✅ Schema executed: {executed} statements ({errors} errors)")

        # === Seed default store ===
        if seed:
            print("\n🌱 Seeding default store (Royal Chaussures)...")
            for stmt in SEED_SQL.split(";"):
                stmt = stmt.strip()
                if stmt and not stmt.startswith("--"):
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        print(f"   ℹ️  Seed: {str(e)[:80]}")

        # === Sync sequences after seed ===
        if seed:
            print("\n🔄 Syncing PostgreSQL sequences...")
            sync_tables = [
                ("stores", "id"),
                ("users", "id"),
                ("orders", "id"),
                ("products", "id"),
                ("clients", "id"),
                ("messages", "id"),
                ("store_agent_config", "id"),
                ("store_prompts", "id"),
                ("store_webhooks", "id"),
            ]
            for table, col in sync_tables:
                try:
                    cur.execute(
                        f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), "
                        f"COALESCE(MAX({col}), 1)) FROM {table}"
                    )
                    print(f"   ✅ {table}.{col} synced")
                except Exception as e:
                    print(f"   ℹ️  {table}.{col}: {str(e)[:60]}")

        print("\n" + "=" * 60)
        print("✅ Migration complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed = "--seed" in sys.argv
    check_only = "--check" in sys.argv
    run_migration(seed=seed, check_only=check_only)
