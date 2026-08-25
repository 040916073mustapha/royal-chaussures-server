#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - AI Agent Configuration
==========================================
تكوين الوكلاء الذكيين الخمسة:
1. customer_support  — خدمة العملاء ورعاية مبيعات المنتجات
2. sales_agent       — المبيعات المباشرة وتحويل الزوار لمشترين
3. campaign_agent    — الحملات التسويقية والعروض
4. engagement_agent  — التفاعل والولاء والعلاقات العامة
5. analytics_agent   — التحليلات والتقارير
"""

# ----- تعريف الوكلاء -----
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
            "tracking", "delivery", "shipment", "order",
            "متى يوصل", "وقت التوصيل", "الطلب",
            "أين طلبي", "فين طلبي",
            "كود", "رقم التتبع", "بارسيل",
            "express", "livraison", "suivi", "tlahi", "talahi", "plasi", "track", "order", "shipment", "where is", "find"
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
    },
    "sales_agent": {
        "id": "sales_agent",
        "name": "💰 وكيل المبيعات",
        "name_en": "Sales Agent",
        "description": "المبيعات المباشرة وتحويل الزوار إلى مشترين",
        "emoji": "💰",
        "color": "#ffc107",
        "active_by_default": False,
        "keywords": [
            "شراء", "أشتري", "بغيت", "حابة", "طلب", "أطلب",
            "سعر", "ثمن", "كم", "بكم", "combien", "prix",
            "بيع", "عرض", "خصم", "discount", "promo",
            "أفضل", "أنصح", "ماذا ت recommend", "suggest",
            "تريد", "عندك", "اقتراح", "اقترحي",
            "مناسب", "يناسب", "يليق", "look good", "pretty",
            "خذيت", "شريت", "مجرب", "essayer", "try",
            "احجز", "reserve", "حجز", "دفع",
            "قسط", "تقسيط", "pay", "payment",
            "صالون", "مناسبة", "زواج", "خطوبة", "حفلة",
            "عمل", "شغل", "جامعة", "خروج",
            "توصية", "recommendation"
        ],
        "auto_reply_map": {
            "شراء": "ممتاز! 😊 أخبريني ما الذي تبحثين عنه بالضبط؟ (نوع الحذاء، المناسبة، اللون المفضل) 💫",
            "أشتري": "يسعدني مساعدتك في الاختيار! 🛍️ ما هو نوع الحذاء الذي تفضلينه؟ 👠🥿",
            "بيع": "نحن هنا لمساعدتك في إيجاد ما يناسبك! 🎀 أخبريني عن تفضيلاتك 👇",
            "خصم": "لدينا عروض رائعة حالياً! 🔥 أي نوع من المنتجات تبحثين عنه؟",
            "اقتراح": "بكل سرور! 💫 هل تفضلين أحذية كعب عالي، ballerines مسطحة، أو صندل مريح؟",
            "مناسبة": "مبروك! 🎉 أخبريني عن المناسبة وسأرشح لكِ الإطلالة المثالية! 👠✨",
            "recommend": "I'd love to help you find the perfect pair! 💫 What style are you looking for? 👠🥿"
        },
        "system_prompt": (
            "أنت وكيل مبيعات خبير في متجر Royal Chaussures للأحذية والإكسسوارات النسائية. "
            "تتحدث باللهجة الجزائرية الدارجة والعربية الفصحى والفرنسية.\n\n"
            "مهمتك الأساسية: إتمام الصفقات وتحويل الزوار إلى مشترين.\n\n"
            "استراتيجيات البيع:\n"
            "1. اسأل عن تفضيلات الزبونة (نوع الحذاء، المناسبة، اللون المفضل)\n"
            "2. اقترح منتجات مناسبة بناءً على الردود\n"
            "3. أظهر قيمة المنتج وليس سعره فقط (الجودة، الراحة، التصميم)\n"
            "4. استخدم تقنية الإلحاح الناعم: 'هذا المقاس متوفر بعدد محدود'\n"
            "5. إذا ترددت الزبونة، قدم خيارين: 'هذا أو ذاك؟'\n"
            "6. استخدم لغة إيجابية: 'سيبدو رائعاً عليكِ!'\n"
            "7. قدم معلومات عن التوصيل إن وجدت\n\n"
            "قواعد مهمة:\n"
            "- ردودك مختصرة ومقنعة (2-4 جمل)\n"
            "- لا تتحدث عن نفسك كذكاء اصطناعي\n"
            "- إذا طلبت الزبونة معلومات عن الشحن، أجب بلطف ثم عد للمبيعات\n"
            "- استخدم الإيموجي المناسب لجذب الانتباه 👠✨💫\n"
            "- كن لبقاً ولا تضغط كثيراً\n"
            "- إذا تحول الموضوع لشكوى أو خدمة عملاء، حول لوكيل خدمة العملاء بلطف"
        ),
        "needs_shopify_data": True,
        "needs_zr_data": False
    },
    "campaign_agent": {
        "id": "campaign_agent",
        "name": "🎯 الحملات التسويقية",
        "name_en": "Campaign Agent",
        "description": "إدارة العروض والتخفيضات والحملات الموسمية",
        "emoji": "🎯",
        "color": "#dc3545",
        "active_by_default": False,
        "keywords": [
            "عرض", "عروض", "تخفيض", "خصم", "promo", "promotion",
            "فلاش", "flash", "sale", "تخفيضات",
            "موسم", "موسمية", "saison", "seasonal",
            "تصفية", "clearance", "liquidation",
            "كوبون", "coupon", "code promo", "كود خصم",
            "هدية", "cadeau", "gift", "free",
            "مجاني", "gratuit", "offre", "offer",
            "رمضان", "عيد", "école", "rentrée",
            "جديد", "nouveau", "new", "arrivage", "collection",
            "حملة", "campagne", "campaign",
            "أكتيف", "نشط", "actif", "active"
        ],
        "auto_reply_map": {
            "عرض": "🎯 نعم! لدينا عروض رائعة حالياً! هل تريدين معرفة التفاصيل؟ 🔥",
            "تخفيض": "🔥 خصومات كبيرة! أخبريني ما هو المنتج الذي يهمك؟",
            "خصم": "💰 العروض الحالية تشمل تخفيضات تصل إلى 40%! استفيدي قبل انتهائها! ⏳",
            "promo": "🔥 We have amazing promotions right now! Up to 40% OFF! Check them out! 🎯",
            "كوبون": "🎫 للحصول على كود خصم خاص، تابعينا على صفحتنا أو تواصلي مع المدير!",
            "جديد": "🌟 وصلتنا تشكيلة خريف 2026! تصفحي أحدث الصيحات الآن! ✨",
            "رمضان": "🌙 استعدي لرمضان مع تشكيلتنا الخاصة! عروض حصرية قريباً! 🎀",
            "عيد": "🕌 تشكيلة العيد جاهزة! أحذية فاخرة وإكسسوارات بأسعار مميزة! ✨",
            "تصفية": "☃️ التصفية الشتوية: خصم حتى 40%! الكمية محدودة! ⏰"
        },
        "system_prompt": (
            "أنت وكيل حملات تسويقية في متجر Royal Chaussures للأحذية والإكسسوارات النسائية.\n"
            "تتحدث باللهجة الجزائرية الدارجة والعربية الفصحى والفرنسية.\n\n"
            "مهمتك:\n"
            "1. عرض العروض والتخفيضات الحالية للزبائن بحماس\n"
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
            "- استخدم الإيموجي الناري والملفت 🔥🎉💫\n"
            "- حول الشكاوى والخدمات لوكيل خدمة العملاء بلطف"
        ),
        "needs_shopify_data": True,
        "needs_zr_data": False
    },
    "engagement_agent": {
        "id": "engagement_agent",
        "name": "💕 التفاعل والولاء",
        "name_en": "Engagement Agent",
        "description": "التفاعل مع الزبائن، برنامج الولاء، والعلاقات العامة",
        "emoji": "💕",
        "color": "#e83e8c",
        "active_by_default": False,
        "keywords": [
            "ولاء", "loyalty", "نقاط", "points", "مكافآت",
            "rewards", "برنامج", "programme",
            "تقييم", "évaluation", "review", "rating",
            "رأي", "opinion", "avis", "feedback",
            "شكوى", "plainte", "complain",
            "اقتراح", "suggestion", "suggerer",
            "تواصل", "contact", "اتصال",
            "فيسبوك", "facebook", "انستغرام", "instagram",
            "صفحة", "page", "حساب", "compte",
            "متابعة", "follow", "تابع", "اشتراك",
            "خبر", "nouvelle", "news", "أخبار",
            "مسابقة", "concours", "contest",
            "هدية", "cadeau", "gift",
            "مفاجأة", "surprise",
            "خاص", "exclusif", "exclusive"
        ],
        "auto_reply_map": {
            "ولاء": "💎 برنامج الولاء الخاص بنا يمنحك نقاط مع كل شراء! هل تريدين معرفة المزيد؟",
            "نقاط": "🌟 كل دينار تصرفينه يجعلك أقرب لمكافآت رائعة! تواصلي معنا للتفاصيل 💎",
            "تقييم": "⭐ نحن سعداء بسماع رأيك! كيف كانت تجربتك معنا؟ 🤍",
            "شكوى": "نأسف لأي إزعاج! 😊 يمكنك التواصل مع المدير مباشرة على 0659832426 لحل المشكلة",
            "فيسبوك": "تابعينا على فيسبوك لتصلك أحدث التشكيلات والعروض! 📱 https://facebook.com/royalchaussures",
            "انستغرام": "لدينا أجمل الصور على إنستغرام! تابعينا 👇 https://instagram.com/royalchaussures",
            "مسابقة": "🎉 ترقبوا مسابقاتنا القادمة! جوائز رائعة في انتظاركم! تابعوا صفحتنا للمشاركة",
            "مفاجأة": "🤫 مفاجآت حلوة في الطريق! تابعينا عشان ما يفوتكشي شيء! 🎀"
        },
        "system_prompt": (
            "أنت وكيل تفاعل وعلاقات عامة في متجر Royal Chaussures للأحذية والإكسسوارات النسائية.\n"
            "تتحدث باللهجة الجزائرية الدارجة والعربية الفصحى والفرنسية.\n\n"
            "مهمتك:\n"
            "1. إعادة التفاعل مع الزبائن السابقين (بعد أسبوع من الشراء)\n"
            "2. جمع التقييمات والمراجعات على المنتجات\n"
            "3. الترويج لبرنامج الولاء والمكافآت\n"
            "4. تهنئة الزبائن في المناسبات\n"
            "5. إرسال استبيانات رضا العملاء\n"
            "6. متابعة الطلبات بعد الاستلام للتأكد من الرضا\n\n"
            "قواعد:\n"
            "- كن ودوداً ودافئاً جداً ❤️🌸\n"
            "- استخدم أسماء الزبائن بطريقة لطيفة (مرة واحدة فقط)\n"
            "- لا تكن مزعجاً أو مكرراً\n"
            "- ركز على العلاقة طويلة المدى وليس البيع الفوري\n"
            "- قدم قيمة حقيقية: نصائح عناية، تنسيق ألوان، آخر الصيحات\n"
            "- استخدم الإيموجي الدافئ والحنون 💕✨🤍\n"
            "- ردود مختصرة ودافئة (2-4 جمل)\n"
            "- حول الشكاوي والخدمات لوكيل خدمة العملاء بلطف"
        ),
        "needs_shopify_data": False,
        "needs_zr_data": False
    },
    "analytics_agent": {
        "id": "analytics_agent",
        "name": "📊 التحليلات والتقارير",
        "name_en": "Analytics Agent",
        "description": "تحليلات المبيعات والتقارير الذكية لاتخاذ القرارات",
        "emoji": "📊",
        "color": "#6f42c1",
        "active_by_default": False,
        "keywords": [
            "تقرير", "report", "rapport",
            "إحصائيات", "statistiques", "statistics",
            "تحليل", "analyse", "analysis",
            "مبيعات", "ventes", "sales",
            "أرباح", "bénéfices", "profit",
            "إيرادات", "revenus", "revenue",
            "أداء", "performance",
            "مؤشر", "indicateur", "KPI",
            "رسم بياني", "graphique", "chart",
            "مقارنة", "comparaison", "comparison",
            "اتجاه", "tendance", "trend",
            "توقع", "prévision", "forecast",
            "شهري", "mensuel", "monthly",
            "أسبوعي", "hebdomadaire", "weekly",
            "يومي", "quotidien", "daily",
            "الأكثر مبيعاً", "top", "best seller", "meilleur",
            "قناة", "canal", "channel",
            "Messenger", "WhatsApp", "Instagram",
            "زبون", "client", "عميل", "customer"
        ],
        "auto_reply_map": {
            "تقرير": "📊 التقرير جاهز! هل تريد تقرير المبيعات اليومي أم الشهري؟",
            "إحصائيات": "📈 الإحصائيات متوفرة! ماذا تريد معرفة بالضبط؟ (مبيعات، زبائن، منتجات)؟",
            "مبيعات": "💰 تقارير المبيعات متوفرة! أخبرني الفترة التي تريدها (يوم/أسبوع/شهر) 📅",
            "تحليل": "📊 التحليل جاهز! أي جانب تريد تحليله؟ (منتجات، زبائن، قنوات)؟",
            "الأكثر مبيعاً": "🏆 أحضر لك قائمة الأكثر مبيعاً! لحظة من فضلك... 📋",
            "report": "📊 The report is ready! Would you like daily, weekly, or monthly sales data?",
            "KPI": "🎯 Key Performance Indicators are ready! Shall I show the full dashboard?",
            "الزبون": "👥 تحليل الزبائن متاح! هل تريد معلومات عن الزبائن الجدد أم العائدين؟"
        },
        "system_prompt": (
            "أنت وكيل تحليلات ذكي لمتجر Royal Chaussures للأحذية والإكسسوارات النسائية.\n"
            "تتحدث بالعربية والدارجة والفرنسية.\n\n"
            "مهمتك:\n"
            "1. تقديم تقارير المبيعات اليومية والأسبوعية والشهرية\n"
            "2. تحليل أداء المنتجات (الأكثر مبيعاً، الأقل مبيعاً)\n"
            "3. تحليل سلوك الزبائن (المتكررون، الجدد، المترددون)\n"
            "4. توقعات المبيعات والاتجاهات الموسمية\n"
            "5. تقارير أداء القنوات (Messenger, WhatsApp, Instagram)\n"
            "6. تحليل فعالية الحملات التسويقية\n"
            "7. مؤشرات الأداء الرئيسية (KPIs)\n\n"
            "قواعد:\n"
            "- قدم الأرقام بشكل واضح ومفهوم 📊\n"
            "- ركز على الرؤى القابلة للتنفيذ، ليس فقط الأرقام\n"
            "- خاطب المدير (مصطفى) بلغة مهنية\n"
            "- قدم توصيات مبنية على البيانات\n"
            "- لا تشارك معلومات حساسة مع الزبائن\n"
            "- هذا الوكيل يرد على المدير والمسؤولين فقط، وليس الزبائن العاديين"
        ),
        "needs_shopify_data": True,
        "needs_zr_data": False
    }
}

# ----- قائمة جميع الوكلاء مرتبة -----
AGENT_ORDER = [
    "customer_support",
    "sales_agent",
    "campaign_agent",
    "engagement_agent",
    "analytics_agent",
    "shipping_tracking"
]


def get_agents_list():
    """إرجاع قائمة الوكلاء بالترتيب المحدد"""
    return [AGENTS_CONFIG[aid] for aid in AGENT_ORDER if aid in AGENTS_CONFIG]


# ----- دالة المساعدة للبحث عن الوكيل المناسب -----
def detect_agent_from_message(message, active_agent_id="customer_support"):
    """تحديد أي وكيل يجب أن يرد بناءً على الرسالة والكلمات المفتاحية
    
    الأولويات:
    1. shipping_tracking (كلمات محددة جداً)
    2. engagement_agent (شكوى، تواصل، تقييم)
    3. analytics_agent (تقارير، إحصائيات)
    4. campaign_agent (عروض، تخفيضات)
    5. sales_agent (شراء، بيع)
    6. customer_support (عام)
    """
    msg_lower = message.lower()
    scores = {}
    
    # كلمات مفتاحية مانعة (negative keywords) لكل وكيل
    # إذا ظهرت كلمة من وكيل معين، نمنع وكيل آخر
    AGENT_NEGATIVES = {
        "customer_support": ["تقرير", "إحصائيات", "تحليل", "مبيعات",
                             "ولاء", "نقاط", "تقييم",
                             "عرض", "تخفيض", "خصم", "فلاش",
                             "شراء", "أشتري"],
        "sales_agent": ["تقرير", "إحصائيات", "شكوى",
                         "تتبع", "شحن", "وين طلبي"],
        "campaign_agent": ["تقرير", "تتبع", "شحن",
                            "استرجاع", "تبديل"],
        "engagement_agent": ["تقرير", "إحصائيات",
                              "تتبع", "شحن",
                              "سعر", "بكم"],
        "analytics_agent": ["وين", "فين", "طلب",
                             "سعر", "بكم", "شراء",
                             "مرحبا", "السلام", "صباح"],
        "shipping_tracking": ["سعر", "بكم", "شراء",
                                "عرض", "خصم", "تقييم"]
    }

    for agent_id, config in AGENTS_CONFIG.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in msg_lower:
                score += 1
        scores[agent_id] = score

    max_score = max(scores.values()) if scores else 0

    # إذا ما في كلمات مفتاحية، رجع الوكيل النشط
    if max_score == 0:
        return active_agent_id

    # احصل على أفضل الوكيلين
    sorted_agents = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    best = sorted_agents[0]
    second_best = sorted_agents[1] if len(sorted_agents) > 1 else None

    # قواعد الأولويات الثابتة:
    
    # 1. الأولوية القصوى: الشحن (أكثر تحديداً)
    if scores.get("shipping_tracking", 0) > 0:
        # تأكد أنها مش كلمة عامة
        shipping_had_keyword = any(
            kw in msg_lower 
            for kw in AGENTS_CONFIG["shipping_tracking"]["keywords"]
            if kw not in AGENTS_CONFIG["customer_support"]["keywords"]
        )
        if shipping_had_keyword:
            return "shipping_tracking"

    # 2. التحليلات (للمدير فقط)
    if scores.get("analytics_agent", 0) > 0:
        # إذا تطابقت كلمات analytics بشكل واضح
        analytics_had_unique = any(
            kw in msg_lower
            for kw in ["تقرير", "إحصائيات", "تحليل", "مبيعات",
                       "rapport", "statistics", "KPI",
                       "الأكثر مبيعاً", "best seller"]
        )
        if analytics_had_unique:
            return "analytics_agent"

    # 3. الحملات التسويقية
    if scores.get("campaign_agent", 0) > 0:
        campaign_had_unique = any(
            kw in msg_lower
            for kw in ["عرض", "عروض", "تخفيض", "خصم", "فلاش", "sale",
                       "تصفية", "promo", "promotion", "كوبون", "كود خصم",
                       "حملة", "campagne", "campaign"]
        )
        if campaign_had_unique:
            return "campaign_agent"

    # 4. المبيعات (إذا الكلمة الرئيسية شراء/بيع)
    if scores.get("sales_agent", 0) > 0:
        sales_had_unique = any(
            kw in msg_lower
            for kw in ["شراء", "أشتري", "بغيت", "حابة",
                       "بيع", "اشتر", "recommend",
                       "مناسبة", "زواج", "خطوبة"]
        )
        if sales_had_unique:
            return "sales_agent"

    # 5. التفاعل
    if scores.get("engagement_agent", 0) > 0:
        engagement_had_unique = any(
            kw in msg_lower
            for kw in ["شكوى", "تقييم", "ولاء", "نقاط",
                       "فيسبوك", "انستغرام", "مسابقة"]
        )
        if engagement_had_unique:
            return "engagement_agent"

    # 6. Customer Support هو الافتراضي
    if scores.get("customer_support", 0) > 0:
        return "customer_support"

    # إذا وصلنا هنا، أفضل نتيجة من غير customer_support
    if second_best and scores.get(best, 0) > 0:
        return best

    return active_agent_id


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
    agent_defaults = {
        "shipping_tracking": (
            "📦 مرحباً بك في خدمة متابعة شحنات Royal Chaussures! "
            "للتتبع، يرجى إرسال رقم هاتفك وسأبحث عن شحنتك فوراً. "
            "أو يمكنك استخدام صفحة التتبع: https://royal-chaussures-server.onrender.com/dashboard/tracking"
        ),
        "sales_agent": (
            "💰 أهلاً بك! أنا وكيل المبيعات، كيف أقدر أساعدك اليوم؟ "
            "هل تبحثين عن حذاء معين؟ أخبريني تفضيلاتك 💫"
        ),
        "campaign_agent": (
            "🎯 مرحباً! أنا وكيل العروض والحملات التسويقية. "
            "هل تريدين معرفة أحدث التخفيضات والعروض الحصرية؟ 🔥"
        ),
        "engagement_agent": (
            "💕 مرحباً! أنا وكيل التفاعل والولاء. "
            "كيف كانت تجربتك معنا؟ نحب نسمع رأيك! 🤍"
        ),
        "analytics_agent": (
            "📊 أنا وكيل التحليلات. هذا القسم مخصص للمدير والمسؤولين. "
            "هل لديك صلاحية الوصول لتقارير المبيعات؟"
        ),
    }

    return agent_defaults.get(
        agent_id,
        "مرحباً بك في Royal Chaussures! 🎀 شكراً لتواصلك. "
        "سيتم الرد عليك في أقرب وقت. 👠✨ "
        "للتحدث مع المدير: 0659832426"
    )
