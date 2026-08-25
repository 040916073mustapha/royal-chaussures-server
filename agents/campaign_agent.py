#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Campaign Agent
=================================
وكيل الحملات التسويقية: إدارة العروض، التخفيضات، الموسمية، الإعلانات
يدير الترويج للمنتجات حسب المناسبات والفصول
"""

from agents.config import AGENTS_CONFIG
from datetime import datetime
import logging

logger = logging.getLogger("royal-server")


# ----- العروض الموسمية والحالية -----
CAMPAIGNS = {
    "back_to_school": {
        "name": "🎒 العودة إلى الدراسة",
        "active": False,
        "start_date": "2026-09-01",
        "end_date": "2026-10-15",
        "description": "خصم 15% على الأحذية الرياضية والمدرسية",
        "discount": 15,
        "target_products": ["sneakers", "ballerines", "school"],
    },
    "ramadan": {
        "name": "🌙 رمضان كريم",
        "active": False,
        "start_date": "2027-01-01",
        "end_date": "2027-02-01",
        "description": "عروض خاصة لشهر رمضان: خصم حتى 25%",
        "discount": 25,
        "target_products": ["sandals", "heels", "bags"],
    },
    "eid": {
        "name": "🕌 عيد الأضحى",
        "active": False,
        "start_date": "2027-03-01",
        "end_date": "2027-03-20",
        "description": "تشكيلة العيد: أحذية فاخرة + إكسسوارات",
        "discount": 20,
        "target_products": ["heels", "formal", "accessories"],
    },
    "winter_clearance": {
        "name": "☃️ التصفية الشتوية",
        "active": True,
        "start_date": "2026-08-15",
        "end_date": "2026-09-30",
        "description": "تصفية نهاية الموسم: خصم حتى 40%",
        "discount": 40,
        "target_products": ["boots", "winter"],
    },
    "new_arrivals": {
        "name": "🌟 وصل حديثاً",
        "active": True,
        "start_date": "2026-08-20",
        "end_date": "2026-10-01",
        "description": "تشكيلة خريف 2026 — أحدث الصيحات",
        "discount": 0,
        "target_products": ["new", "autumn", "trendy"],
    },
    "flash_sale": {
        "name": "⚡ فلاش سيل",
        "active": True,
        "start_date": "2026-08-22",
        "end_date": "2026-08-26",
        "description": "تخفيضات البرق: خصم فوري 30% لمدة 48 ساعة",
        "discount": 30,
        "target_products": ["all"],
    },
}


def get_agent_info():
    """معلومات الوكيل للعرض"""
    return AGENTS_CONFIG.get("campaign_agent", {})


def get_system_prompt(store_id=1, store_name="Royal Chaussures"):
    """الحصول على system prompt مخصص للحملات التسويقية"""
    active_campaigns = get_active_campaigns()
    campaigns_text = "\n".join(
        [f"• {c['name']}: {c['description']} (حتى {c['end_date']})"
         for c in active_campaigns]
    ) if active_campaigns else "لا توجد حملات نشطة حالياً."

    return (
        f"[CAMPAIGN AGENT - {store_name}]\n"
        f"أنت وكيل حملات تسويقية في متجر {store_name} للأحذية والإكسسوارات النسائية.\n"
        f"تتحدث باللهجة الجزائرية الدارجة والعربية الفصحى والفرنسية.\n\n"
        f"الحملات النشطة حالياً:\n{campaigns_text}\n\n"
        "مهمتك:\n"
        "1. عرض العروض والتخفيضات الحالية للزبائن\n"
        "2. إقناع الزبائن بالاستفادة من العروض قبل انتهائها\n"
        "3. توجيه الزبائن للمنتجات المشمولة بالتخفيض\n"
        "4. خلق شعور بالإلحاح لتحفيز الشراء\n"
        "5. الرد على استفسارات العروض والخصومات\n\n"
        "قواعد:\n"
        "- تحدث بحماس عن العروض 🔥💥\n"
        "- اذكر تاريخ انتهاء العرض لخلق الإلحاح\n"
        "- إذا سألت الزبونة عن منتج غير مشمول، أخبرها بلطف واقترح البديل المخفض\n"
        "- ردود مختصرة وجذابة (2-4 جمل)\n"
        "- لا تتحدث عن نفسك كذكاء اصطناعي\n"
        "- استخدم الإيموجي الناري والملفت 🔥🎉💫"
    )


def get_active_campaigns():
    """إرجاع الحملات النشطة حالياً"""
    now = datetime.now().date()
    active = []
    for cid, campaign in CAMPAIGNS.items():
        if not campaign["active"]:
            continue
        start = datetime.strptime(campaign["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(campaign["end_date"], "%Y-%m-%d").date()
        if start <= now <= end:
            active.append({"id": cid, **campaign})
    return active


def format_campaign_reply(campaigns=None):
    """تنسيق رد يعرض الحملات النشطة"""
    if campaigns is None:
        campaigns = get_active_campaigns()
    if not campaigns:
        return (
            "عذراً، لا توجد عروض حالياً. 😊\n"
            "لكن لا تترددي في زيارة موقعنا لمشاهدة أحدث التشكيلات!\n"
            "https://royalchaussures.com"
        )
    reply = "🎯 **العروض الحالية في Royal Chaussures:**\n\n"
    for c in campaigns:
        badge = f"🔥 خصم {c['discount']}%" if c['discount'] > 0 else "🌟 جديد"
        reply += (
            f"{c['name']} {badge}\n"
            f"📅 حتى {c['end_date']}\n"
            f"{c['description']}\n\n"
        )
    reply += "استفيدي من العروض قبل انتهائها! 🚀💫"
    return reply


def format_countdown_reply(days_left, campaign_name, discount):
    """تنسيق رد بعداد تنازلي للحملة"""
    return (
        f"⏰ {campaign_name} — متبقي {days_left} أيام فقط!\n"
        f"🔥 خصم {discount}% على منتجات مختارة\n"
        f"لا تفوتي الفرصة! ☄️"
    )


def format_product_campaign_reply(product_name, campaign_name, discount, price_before, price_after):
    """تنسيق رد منتج مع خصم الحملة"""
    return (
        f"🔥 **{product_name}** مشمول في {campaign_name}!\n"
        f"💰 كان: ~~{price_before} د.ج~~ → الآن: **{price_after} د.ج**\n"
        f"✅ وفر {discount}%\n"
        f"العرض سارٍ لفترة محدودة! ⏳"
    )
