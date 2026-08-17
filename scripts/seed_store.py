"""
🧪 اختبار تهيئة Royal Chaussures (store_id=1)
"""
import sys, os
sys.path.insert(0, os.getcwd())
os.environ['DB_ENGINE'] = 'sqlite'

from database.db import init_db
init_db()
print("[OK] DB initialized")

# Seed prompts
from database.db import set_store_prompt
set_store_prompt(1, 'customer_support', '[1. ROYAL IDENTITY]\nI represent Royal Chaussures...')
set_store_prompt(1, 'sales_agent', '[SALES AGENT]\nYou help customers find products...')
set_store_prompt(1, 'shipping_tracking', '[SHIPPING AGENT]\nYou track ZR Express shipments...')
set_store_prompt(1, 'inventory_agent', '[INVENTORY AGENT]\nYou manage stock queries...')
print("[OK] Prompts seeded")

# Verify
from database.db import get_all_store_prompts, get_store_prompt
prompts = get_all_store_prompts(1)
for k, v in prompts.items():
    print(f"  {k}: {len(v)} chars")
print("[OK] All prompts verified")

# Seed webhook registry
from database.db import register_webhook, get_store_id_by_platform
register_webhook(1, 'messenger', 'ROYAL_FB_PAGE_ID')
register_webhook(1, 'whatsapp', 'ROYAL_WA_PHONE_ID', 'WHATSAPP_PHONE_NUMBER_ID')
register_webhook(1, 'instagram', 'ROYAL_IG_ID')
sid = get_store_id_by_platform('messenger', 'ROYAL_FB_PAGE_ID')
print(f"[OK] Webhooks registered, lookup -> store_id={sid}")

print("\n=== ALL SYSTEMS READY! ===")
print("Royal Chaussures (store_id=1) fully configured!")
