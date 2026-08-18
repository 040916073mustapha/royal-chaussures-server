#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📤 Syncer — RC Agents → Notion
================================
سكريبت سريع لمزامنة ROADMAP.md مع Notion.

الاستخدام:
    python scripts/sync_notion.py                  # مزامنة عادية
    python scripts/sync_notion.py --verbose         # مع تفاصيل أكثر
    python scripts/sync_notion.py --check           # فحص الإعدادات فقط بدون Sync

متغيرات البيئة المطلوب ضبطها في Render:
    NOTION_TOKEN
    NOTION_PAGE_ID

# أنشئ ملف .env محلي:
#   NOTION_TOKEN=ntn_your_token_here
#   NOTION_PAGE_ID=your_page_id_here
# ثم: python scripts/sync_notion.py --check
"""

import os
import sys

# إضافة جذر المشروع للمسار
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from dotenv import load_dotenv
load_dotenv()


def check_config():
    """فحص الإعدادات"""
    token = os.getenv("NOTION_TOKEN", "")
    page_id = os.getenv("NOTION_PAGE_ID", "")

    print("=" * 50)
    print("🔍 RC Agents → Notion Sync — فحص الإعدادات")
    print("=" * 50)

    if token:
        print(f"✅ NOTION_TOKEN: موجود ({token[:8]}...{token[-4:]})")
    else:
        print("❌ NOTION_TOKEN: غير موجود")

    if page_id:
        print(f"✅ NOTION_PAGE_ID: موجود ({page_id})")
    else:
        print("❌ NOTION_PAGE_ID: غير موجود")

    roadmap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ROADMAP.md")
    if os.path.exists(roadmap_path):
        size = os.path.getsize(roadmap_path)
        print(f"✅ ROADMAP.md: موجود ({size:,} bytes)")
    else:
        print("❌ ROADMAP.md: غير موجود")

    print("=" * 50)

    return bool(token and page_id)


def main():
    """تشغيل المزامنة"""
    verbose = "--verbose" in sys.argv
    check_only = "--check" in sys.argv

    if check_only:
        check_config()
        return

    if not check_config():
        print("\n⚠️  الإعدادات غير مكتملة. أضف المتغيرات البيئية.")
        sys.exit(1)

    print("\n🚀 جاري مزامنة ROADMAP.md → Notion...\n")

    import logging
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    from services.notion_sync import sync_roadmap_quick
    success = sync_roadmap_quick()

    if success:
        print("\n🎉 تمت المزامنة بنجاح!")
        print("   افتح صفحة Notion لرؤية التحديثات.")
    else:
        print("\n❌ فشلت المزامنة. تحقق من السجلات و الـ logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
