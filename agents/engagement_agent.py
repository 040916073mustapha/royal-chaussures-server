#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Engagement Agent
===================================
وكيل التفاعل والتواصل: إعادة التفاعل، استطلاعات الرأي، برنامج الولاء
يدير العلاقة مع الزبائن بعد البيع ويعزز الولاء
"""

from agents.config import AGENTS_CONFIG
import logging

logger = logging.getLogger("royal-server")


def get_agent_info():
    """معلومات الوكيل للعرض"""
    return AGENTS_CONFIG.get("engagement_agent", {})


def get_system_prompt(store_id=1, store_name="Royal Chaussures"):
    """الحصول على system prompt للتفاعل والتواصل"""
    return (
        f"[ENGAGEMENT AGENT - {store_name}]\n"
        f"أنت وكيل تفاعل وعلاقات عامة في متجر {store_name} للأحذية والإكسسوارات النسائية.\n"
        "تتحدث باللهجة الجزائرية الدارجة والعربية الفصحى والفرنسية.\n\n"
        "مهمتك:\n"
        "1. إعادة التفاعل مع الزبائن السابقين (بعد أسبوع من الشراء)\n"
        "2. جمع التقييمات والمراجعات على المنتجات\n"
        "3. الترويج لبرنامج الولاء والمكافآت\n"
        "4. تهنئة الزبائن في المناسبات (عيد ميلاد، مناسبات خاصة)\n"
        "5. إرسال استبيانات رضا العملاء\n"
        "6. متابعة الطلبات بعد الاستلام للتأكد من الرضا\n\n"
        "قواعد:\n"
        "- كن ودوداً ودافئاً جداً ❤️🌸\n"
        "- استخدم أسماء الزبائن بطريقة لطيفة\n"
        "- لا تكن مزعجاً أو مكرراً — مرة واحدة لكل تفاعل\n"
        "- ركز على العلاقة طويلة المدى وليس البيع الفوري\n"
        "- قدم قيمة حقيقية: نصائح عناية، تنسيق ألوان، آخر الصيحات\n"
        "- استخدم الإيموجي الدافئ والحنون 💕✨🤍\n"
        "- ردود مختصرة ودافئة (2-4 جمل)"
    )


def format_followup_reply(customer_name, days_since_purchase, product_name):
    """تنسيق رد متابعة بعد الشراء"""
    if days_since_purchase <= 3:
        return (
            f"أهلاً {customer_name}! 💕\n"
            f"نتمنى أن تكوني استمتعتِ بـ {product_name}.\n"
            f"كيف وجدتِ المنتج؟ نحن مهتمون برأيك! 🤍"
        )
    elif days_since_purchase <= 7:
        return (
            f"مرحباً {customer_name}! 🌸\n"
            f"أسبوع مر على شرائكِ {product_name}، نتمنى أنه نال إعجابك!\n"
            f"هل تسمحين لنا بتقييم تجربتك؟ ⭐⭐⭐⭐⭐"
        )
    else:
        return (
            f"{customer_name} العزيزة! 💫\n"
            f"فاتنا أن نسمع رأيك في {product_name} الذي اشتريته مؤخراً.\n"
            f"نقدّر كثيراً مشاركتك تجربتك معنا! 🤍✨"
        )


def format_loyalty_reply(customer_name, points, rewards_available):
    """تنسيق رد برنامج الولاء"""
    return (
        f"🎉 {customer_name}! نقاط ولائك وصلت {points} نقطة!\n"
        f"يمكنك الاستفادة من:\n"
        + "\n".join([f"• {r}" for r in rewards_available[:3]]) +
        f"\n\nاستخدمي نقاطك الآن واستمتعي بالمكافآت! 💎✨"
    )


def format_review_request(customer_name, product_name):
    """تنسيق رد طلب تقييم"""
    return (
        f"{customer_name} العزيزة! 🤍\n"
        f"نحب نسمع رأيك في {product_name}.\n\n"
        f"⭐ تقييمك يساعد زبوناتنا الأخريات في الاختيار!\n"
        f"هل تشاركينا تقييمك؟ (1-5 نجوم) 🌟\n\n"
        f"رابط التقييم المباشر: https://royalchaussures.com/review"
    )


def format_birthday_reply(customer_name, discount_code, expiry):
    """تنسيق رد تهنئة عيد ميلاد"""
    return (
        f"🎂🎉 كل عام وأنتِ بخير يا {customer_name}! 🎉🎂\n\n"
        f"بمناسبة عيد ميلادك، تفضلي كود خصم خاص: **{discount_code}**\n"
        f"💰 خصم {discount_code}% على أي منتج!\n"
        f"📅 صالح حتى {expiry}\n\n"
        f"نتمنى لكِ يوم جميل! 💕🌸✨"
    )


def format_satisfaction_survey(customer_name):
    """تنسيق رد استبيان رضا"""
    return (
        f"مرحباً {customer_name}! 💫\n"
        f"هدفنا تحسين تجربتك دائماً.\n\n"
        f"📝 نرجو منكِ دقيقة واحدة لتعبئة استبيان الرضا:\n"
        f"1. كيف تقيمين تجربة التسوق؟ ___\n"
        f"2. هل وجدتِ ما تبحثين عنه؟ ___\n"
        f"3. ما الذي يمكننا تحسينه؟ ___\n\n"
        f"شكراً لوقتك الثمين! 🤍🌷"
    )
