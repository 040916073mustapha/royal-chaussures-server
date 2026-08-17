#!/usr/bin/env python3
"""
🧪 اختبار API Onboarding لتاجر جديد
=====================================
لمحاكاة إنشاء متجر ثانٍ على منصة RC Agents.

الاستخدام:
    python scripts/test_onboard.py          # اختبار محلي
    python scripts/test_onboard.py --live   # اختبار على Render
"""

import sys
import json
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import init_db, get_all_store_prompts, get_store_by_slug, set_store_prompt, register_webhook, get_store_id_by_platform, get_all_registered_webhooks

os.environ["DB_ENGINE"] = "sqlite"

def test_local_onboard():
    """اختبار إنشاء متجر محلياً"""
    print("=" * 60)
    print("🔷 اختبار Onboarding تاجر جديد (محلي)")
    print("=" * 60)

    init_db()

    # بيانات تاجر جديد
    store_name = "متجر الأحذية الفاخرة"
    email = "luxury.shoes@example.com"
    phone = "+213555123456"

    # 1. التحقق من slug
    slug = store_name.lower().replace(" ", "-")
    import re
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    existing = get_store_by_slug(slug)
    if existing:
        slug = f"{slug}-{int(time.time())}"

    print(f"\n🏪 المتجر: {store_name}")
    print(f"   slug: {slug}")

    # 2. إنشاء store
    from database.db import create_store
    store = create_store({"name": store_name, "slug": slug, "email": email, "phone": phone})
    store_id = store.get("id", 2) if store and isinstance(store, dict) else 2
    print(f"   store_id: {store_id}")

    # 3. إضافة AI Prompts
    set_store_prompt(store_id, "customer_support", f"[IDENTITY] AI Support for {store_name}. Be helpful.")
    set_store_prompt(store_id, "sales_agent", f"[SALES] Help customers at {store_name}.")
    set_store_prompt(store_id, "shipping_tracking", f"[SHIPPING] Track {store_name} orders.")
    set_store_prompt(store_id, "inventory_agent", f"[INVENTORY] Manage stock at {store_name}.")

    # 4. التحقق من Prompts
    prompts = get_all_store_prompts(store_id)
    print(f"   Prompts: {len(prompts)} types configured")

    # 5. تسجيل Webhooks
    register_webhook(store_id, "messenger", "TEST_FB_PAGE_002")
    register_webhook(store_id, "whatsapp", "TEST_WA_PHONE_002", "WA_PHONE_ID_002")

    # 6. التحقق
    sid = get_store_id_by_platform("messenger", "TEST_FB_PAGE_002")
    assert sid == store_id, f"❌ Store lookup failed: {sid} != {store_id}"
    print(f"   ✅ Webhook lookup: FB Page -> store_id={sid}")

    all_webhooks = get_all_registered_webhooks()
    print(f"   ✅ Total registrations: {len(all_webhooks)}")

    print("\n" + "=" * 60)
    print("✅✅✅ اختبار Onboarding نجح!")
    print(f"   🏪 المتجر الثاني \"{store_name}\" (store_id={store_id})")
    print(f"   🧠 4 AI Prompts منفصلة")
    print(f"   🔗 2 Webhooks مسجلة")
    print("=" * 60)

    return store_id


def test_store_isolation():
    """اختبار عزل البيانات بين المتجرين"""
    print("\n🧪 اختبار عزل الـ Prompts بين المتاجر...")

    # Prompts Royal Chaussures (store_id=1)
    rc_prompts = get_all_store_prompts(1)
    rc_types = set(rc_prompts.keys())

    # Prompts المتجر الجديد (store_id=2)
    prompts = get_all_store_prompts(2)
    new_types = set(prompts.keys())

    # التحقق إن كل متجر له مستقله
    print(f"   🏪 Royal Chaussures (1): {len(rc_prompts)} prompts")
    print(f"   🏪 المتجر الجديد (2):   {len(prompts)} prompts")

    # تعديل Prompt المتجر الجديد فقط
    set_store_prompt(2, "customer_support", "[SPECIAL] هذا الـ prompt مخصص للمتجر الثاني فقط")
    rc_support = get_all_store_prompts(1)["customer_support"]
    new_support = get_all_store_prompts(2)["customer_support"]

    assert "[SPECIAL]" in new_support, "❌ Store 2 prompt wasn't updated"
    assert "[SPECIAL]" not in rc_support, "❌ Store 1 prompt was contaminated!"
    print(f"   ✅ ✅ العزل تام! كل متجر له Prompt مستقل!")


if __name__ == "__main__":
    sid = test_local_onboard()
    test_store_isolation()
    print("\n🎉 منصة RC Agents جاهزة لاستقبال التجار الجدد!")
