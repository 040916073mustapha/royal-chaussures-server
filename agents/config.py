#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - AI Agent Configuration
==========================================
تكوين الوكيلين الذكيين:
1. customer_support  — خدمة العملاء ورعاية مبيعات المنتجات
2. shipping_tracking — متابعة الشحنات والتوصيل مع ZR Express
"""

# ----- تعريف الوكيلين -----
AGENTS_CONFIG = {
    "customer_support": {
        "id": "customer_support",
        "name": "🤝 خدمة العملاء",
        "name_en": "Customer Support",
        "description": "خدمة العملاء ورعاية مبيعات المنتجات",
        "emoji": "🤝",
        "color": "#0d6efd",
        "active_by_default": True,
        "keywords": [
            "مرحبا", "السلام", "سلام", "صباح", "مساء", "hello", "hi", "bonjour",
            "سعر", "كم", "ثمن", "بكم", "prix", "combien",
            "مقاس", "قياس", "taille",
            "استرجاع", "تبديل", "إرجاع", "مرجوع", "retour",
            "مدير", "المالك", "مصطفى", "مسؤول",
            "افتتاح", "ساعات", "عنوان", "موقع", "adresse",
            "منتج", "حذاء", "صندل", "حقيبة", "إكسسوارات",
            "متوفر", "لون", "طلب"
        ],
        "auto_reply_map": {
            "مرحبا": "مرحباً بك في Royal Chaussures! 🎀 كيف نقدر نخدمك؟ 👠✨",
            "السلام": "مرحباً بك في Royal Chaussures! 🎀 كيف نقدر نخدمك؟ 👠✨",
            "سلام": "مرحباً بك في Royal Chaussures! 🎀 كيف نقدر نخدمك؟ 👠✨",
            "صباح": "صباح الخير! 🌅 كيف نقدر نخدمك اليوم؟ 👠✨",
            "مساء": "مساء الخير! 🌙 كيف نقدر نخدمك؟ 👠✨",
            "hello": "Welcome to Royal Chaussures! 🎀 How can we help you? 👠✨",
            "hi": "Welcome to Royal Chaussures! 🎀 How can we help you? 👠✨",
            "bonjour": "Bienvenue chez Royal Chaussures! 🎀 Comment pouvons-nous vous aider? 👠✨",
            "سعر": "أهلاً! الأسعار تختلف حسب المنتج. تقدر تتصفح المجموعة كاملة على موقعنا: https://royalchaussures.com",
            "كم": "أهلاً! الأسعار تختلف حسب المنتج. تقدر تتصفح المجموعة كاملة على موقعنا: https://royalchaussures.com",
            "prix": "Les prix varient selon le produit. Vous pouvez parcourir notre collection: https://royalchaussures.com",
            "مقاس": "المقاسات متوفرة من 36 إلى 42 👠 نحن هنا لمساعدتك في اختيار المقاس المناسب!",
            "قياس": "المقاسات متوفرة من 36 إلى 42 👠 نحن هنا لمساعدتك في اختيار المقاس المناسب!",
            "taille": "Les tailles disponibles: 36 à 42 👠 Nous sommes là pour vous aider!",
            "استرجاع": "نوفر خدمة الاسترجاع والتبديل خلال 7 أيام من الاستلام 📋 للتواصل مع المدير: 0659832426",
            "تبديل": "نوفر خدمة الاسترجاع والتبديل خلال 7 أيام من الاستلام 📋 للتواصل مع المدير: 0659832426",
            "مدير": "يمكنك التواصل مع الأستاذ مصطفى على الرقم 0659832426",
            "مصطفى": "يمكنك التواصل مع الأستاذ مصطفى على الرقم 0659832426",
            "افتتاح": "📍 إمامة، صالحين بجانب ابتدائية حسانوي، تلمسان 🕐 9:00 صباحاً إلى 20:00 مساءً",
            "عنوان": "📍 إمامة، صالحين بجانب ابتدائية حسانوي، تلمسان 🕐 9:00 صباحاً إلى 20:00 مساءً",
            "موقع": "📍 إمامة، صالحين بجانب ابتدائية حسانوي، تلمسان 🕐 9:00 صباحاً إلى 20:00 مساءً"
        },
        "openclaw_model": "openclaw/customer_support",
        "system_prompt": (
            "أنت موظف خدمة عملاء في متجر Royal Chaussures، متجر جزائري للأحذية والإكسسوارات النسائية. "
            "تتحدث باللهجة الجزائرية الدارجة. ردودك مختصرة (2-4 جمل). "
            "لا تتحدث عن نفسك كذكاء اصطناعي. "
            "مهمتك: مساعدة الزبائن في اختيار المنتجات، الأسعار، المقاسات، "
            "سياسة الاسترجاع، معلومات المتجر. "
            "إذا سألك عن الشحن أو التتبع، حوله إلى وكيل الشحنات بطريقة لطيفة. "
            "كن ودوداً، محترفاً، ومفيداً."
        ),
        "needs_shopify_data": True,
        "needs_zr_data": False
    },
    "shipping_tracking": {
        "id": "shipping_tracking",
        "name": "📦 متابعة الشحنات",
        "name_en": "Shipping Tracking",
        "description": "متابعة الشحنات والتوصيل مع ZR Express",
        "emoji": "📦",
        "color": "#198754",
        "active_by_default": False,
        "keywords": [
            "تتبع", "تتبع", "شحن", "وين طلبي", "ZR",
            "tracking", "delivery", "shipment",
            "متى يوصل", "وقت التوصيل", "الطلب",
            "أين طلبي", "فين طلبي",
            "كود", "رقم التتبع", "بارسيل",
            "express", "livraison", "suivi"
        ],
        "auto_reply_map": {
            "تتبع": "📦 نوفر خدمة التتبع لشحنات ZR Express. يرجى إرسال رقم هاتفك للتحقق من حالة الشحنة.",
            "شحن": "📦 نقدم خدمة التوصيل لكل ولايات الجزائر عبر ZR Express. للتتبع، أرسل رقم هاتفك.",
            "وين طلبي": "📦 للتحقق من حالة طلبك، يرجى إرسال رقم هاتفك وسأبحث عن الشحنة فوراً!",
            "tracking": "For tracking your ZR Express shipment, please send your phone number and I will check the status.",
            "delivery": "We offer delivery to all Algerian wilayas via ZR Express. Typically 2-5 business days.",
            "livraison": "Nous livrons dans toutes les wilayas algériennes via ZR Express. Généralement 2-5 jours ouvrés.",
            "suivi": "Pour suivre votre colis ZR Express, veuillez envoyer votre numéro de téléphone."
        },
        "openclaw_model": "openclaw/shipping_tracking",
        "system_prompt": (
            "أنت موظف متابعة شحنات في متجر Royal Chaussures. تتحدث باللهجة الجزائرية الدارجة. "
            "ردودك مختصرة (2-4 جمل). لا تتحدث عن نفسك كذكاء اصطناعي. "
            "مهمتك: مساعدة الزبائن في تتبع شحناتهم عبر ZR Express، "
            "تقديم معلومات عن وقت التوصيل المتوقع (2-5 أيام عمل)، "
            "الاستعلام عن حالة الشحنة باستخدام رقم الهاتف. "
            "إذا سألك عن منتجات أو أسعار، حوله إلى وكيل خدمة العملاء بطريقة لطيفة. "
            "كن مهذياً، محترفاً، وسريعاً في الرد."
        ),
        "needs_shopify_data": False,
        "needs_zr_data": True
    }
}

# ----- دالة المساعدة للبحث عن الوكيل المناسب -----
def detect_agent_from_message(message, active_agent_id="customer_support"):
    """تحديد أي وكيل يجب أن يرد بناءً على الرسالة والكلمات المفتاحية"""
    msg_lower = message.lower()
    scores = {}

    for agent_id, config in AGENTS_CONFIG.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in msg_lower:
                score += 1
        scores[agent_id] = score

    # إذا ما لقى كلمات مفتاحية — استعمل الوكيل النشط
    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return active_agent_id

    # ابحث عن الوكيل صاحب أعلى score
    best_agent = max(scores, key=lambda k: scores[k])

    # إذا shipping له نقاط أكتر من customer_support — حول للشحنات
    if scores.get("shipping_tracking", 0) > scores.get("customer_support", 0):
        return "shipping_tracking"

    return best_agent


def get_auto_reply(agent_id, message):
    """الحصول على رد آلي سريع للوكيل المحدد"""
    msg_lower = message.lower()
    config = AGENTS_CONFIG.get(agent_id, AGENTS_CONFIG["customer_support"])
    auto_map = config.get("auto_reply_map", {})

    # ابحث عن أول كلمة مفتاحية تطابق الرسالة
    for keyword, reply in auto_map.items():
        if keyword in msg_lower:
            return reply

    # رد افتراضي حسب الوكيل
    if agent_id == "shipping_tracking":
        return (
            "📦 مرحباً بك في خدمة متابعة شحنات Royal Chaussures! "
            "للتتبع، يرجى إرسال رقم هاتفك وسأبحث عن شحنتك فوراً. "
            "أو يمكنك استخدام صفحة التتبع: https://royal-chaussures-server.onrender.com/dashboard/tracking"
        )

    return (
        "مرحباً بك في Royal Chaussures! 🎀 شكراً لتواصلك. "
        "سيتم الرد عليك في أقرب وقت. 👠✨ "
        "للتحدث مع المدير: 0659832426"
    )
