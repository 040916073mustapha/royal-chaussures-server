#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Shipping Tracking Agent
===========================================
متابعة الشحنات والتوصيل مع ZR Express
"""

from agents.config import AGENTS_CONFIG
import logging

logger = logging.getLogger("royal-server")


def get_agent_info():
    """معلومات الوكيل للعرض"""
    return AGENTS_CONFIG.get("shipping_tracking", {})


def get_system_prompt():
    """الحصول على system prompt الخاص بمتابعة الشحنات"""
    return AGENTS_CONFIG["shipping_tracking"]["system_prompt"]


def format_tracking_reply(parcels, phone):
    """تنسيق رد التتبع بناءً على بيانات ZR Express"""
    if not parcels:
        return (
            f"🔍 لم أجد أي شحنة مرتبطة برقم {phone}.\n"
            "تأكد من أن الرقم صحيح، أو تواصل مع المدير على 0659832426 للتأكد من حالة طلبك."
        )

    if len(parcels) == 1:
        p = parcels[0]
        if isinstance(p, dict):
            status = p.get("status") or p.get("deliveryStatus") or "قيد المعالجة"
            ref = p.get("reference") or p.get("trackingNumber") or "غير محدد"
            return (
                f"📦 شحنتك موجودة!\n"
                f"🔖 المرجع: {ref}\n"
                f"📌 الحالة: {status}\n"
                f"🚚 وقت التوصيل المتوقع: 2-5 أيام عمل\n"
                f"شكراً لثقتك في Royal Chaussures! ❤️"
            )

    count = len(parcels)
    reply = f"📦 تم العثور على {count} شحنة مرتبطة برقمك:\n\n"
    for i, p in enumerate(parcels[:5], 1):
        if isinstance(p, dict):
            status = p.get("status") or p.get("deliveryStatus") or "قيد المعالجة"
            ref = p.get("reference") or p.get("trackingNumber") or f"شحنة {i}"
            reply += f"{i}. 🔖 {ref} — {status}\n"

    reply += "\n🚚 وقت التوصيل المتوقع: 2-5 أيام عمل"
    return reply


def extract_phone_from_message(message):
    """استخراج رقم الهاتف من الرسالة (للجزائر)"""
    import re
    # البحث عن أرقام جزائرية (05xx xx xx xx, 06xx xx xx xx, 07xx xx xx xx)
    phones = re.findall(r'(?:\+213|0)(?:5|6|7)\d{8}', message.replace(' ', '').replace('-', ''))
    if phones:
        return phones[0]
    # بحث أوسع: أي أرقام بطول 8-10 أرقام
    phones = re.findall(r'\d{8,10}', message)
    if phones:
        return phones[0]
    return None
