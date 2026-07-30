#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Customer Support Agent
==========================================
خدمة العملاء: مبيعات، منتجات، استفسارات عامة
"""

from agents.config import AGENTS_CONFIG


def get_agent_info():
    """معلومات الوكيل للعرض"""
    return AGENTS_CONFIG.get("customer_support", {})


def get_system_prompt():
    """الحصول على system prompt الخاص بخدمة العملاء"""
    return AGENTS_CONFIG["customer_support"]["system_prompt"]


def format_product_reply(products, query=None):
    """تنسيق رد يعرض المنتجات للزبون"""
    if not products:
        return "عذراً، لا توجد منتجات متوفرة حالياً. يرجى زيارة موقعنا: https://royalchaussures.com"

    reply = "🛍️ إليك بعض المنتجات المتوفرة:\n\n"
    for p in products[:5]:
        title = p.get("title", "منتج")
        price = "غير محدد"
        variants = p.get("variants", [])
        if variants:
            price = variants[0].get("price", "غير محدد")
        reply += f"👠 {title} - {price} DZD\n"

    reply += "\nتصفح المزيد: https://royalchaussures.com"
    return reply


def format_order_status(order):
    """تنسيق رد بحالة الطلب"""
    name = order.get("name", "طلب")
    financial = order.get("financial_status", "pending")
    fulfillment = order.get("fulfillment_status", "unfulfilled")

    status_map = {
        "paid": "مدفوع ✅",
        "pending": "قيد الانتظار ⏳",
        "refunded": "مسترجع ↩️",
        "partially_refunded": "مسترجع جزئياً ↩️",
        "voided": "ملغي ❌"
    }
    fulfillment_map = {
        "fulfilled": "تم الشحن ✅",
        "partial": "شحن جزئي 📦",
        "unfulfilled": "لم يتم الشحن بعد ⏳",
        "restocked": "تم إعادة التخزين 🔄"
    }

    return (
        f"📋 طلبك {name}\n"
        f"الحالة المالية: {status_map.get(financial, financial)}\n"
        f"حالة الشحن: {fulfillment_map.get(fulfillment, fulfillment)}"
    )
