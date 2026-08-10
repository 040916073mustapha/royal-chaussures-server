"""
Royal Chaussures — Inventory Agent
===================================
Inventory Agent API: إدارة المنتجات والمخزون عبر الرسائل النصية
يستقبل أوامر بالعربية/الدارجة وينفذها تلقائياً في النظام

مثال:
- "زيد حذاء رياضي أحمر مقاس 38 ب 2500 دج"
- "نقص 5 من مخزون الحذاء الرياضي"
- "غير سعر الحذاء الرياضي ل 3000"
- "شنو عندك في المخزون؟"
"""

import json
import re
from flask import Blueprint, request, jsonify

from database.db import (
    get_products, get_product, get_product_by_sku,
    create_product, update_product, search_products,
    get_inventory, update_inventory, get_low_stock_items
)

inv_agent_bp = Blueprint("inv_agent", __name__)


# ============================================================
# 🔧 NLP Parsers — فهم الأوامر العربية والدارجة
# ============================================================

# كلمات مفتاحية للكشف عن النية
INTENT_PATTERNS = {
    "add_product": [
        r"زيد\s+", r"أضف\s+", r"اضف\s+", r"إضافة\s+", r"ضيف\s+",
        r"new\s+product", r"add\s+product", r"create\s+product",
        r"دخّل\s+", r"دخل\s+", r"حط\s+", r"نوّد\s+"
    ],
    "update_price": [
        r"غيّر\s+", r"غير\s+", r"بدّل\s+", r"عدّل\s+", r"تعديل\s+",
        r"update\s+price", r"change\s+price", r"سعر\s+"
    ],
    "update_stock": [
        r"نقص\s+", r"زود\s+", r"أضف مخزون\s+", r"ضيف مخزون\s+",
        r"update\s+stock", r"زيادة\s+مخزون", r"إنقاص\s+مخزون"
    ],
    "check_stock": [
        r"شنو\s+عندك", r"واش\s+عندك", r"عندك\s+شنو", r"المخزون\s+",
        r"stock\s+check", r"inventory\s+", r"available\s+",
        r"شحال\s+", r"قداش\s+", r"واش\s+كاين"
    ],
    "list_products": [
        r"جميع\s+المنتجات", r"كل\s+المنتجات", r"المنتجات\s+",
        r"list\s+products", r"show\s+products", r"products\s+list"
    ],
    "low_stock": [
        r"المنتجات\s+المنخفضة", r"نفاد\s+المخزون", r"low\s+stock",
        r"المخزون\s+الضعيف", r"راح\s+يكمل"
    ]
}


def detect_intent(text):
    """تحليل النص واكتشاف النية (القصد) من الرسالة"""
    text_lower = text.lower().strip()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent
    
    return "unknown"


def extract_product_info(text):
    """
    استخراج معلومات المنتج من النص العربي/الدارجي
    مثل: الاسم، السعر، اللون، المقاس، الكمية
    """
    info = {
        "name": "",
        "price": None,
        "color": "",
        "size": "",
        "quantity": 1,
        "sku": "",
        "barcode": ""
    }
    
    # استخراج السعر (رقم يتبعه دج أو DA أو دينار)
    price_match = re.search(r'(\d+[\d,.]*)\s*(دج|د\.ج|da|دينار|dinars?)', text, re.IGNORECASE)
    if price_match:
        info["price"] = float(price_match.group(1).replace(",", ""))
    
    # استخراج المقاس (رقم بعد "مقاس" أو "size" أو رقم من 36-46)
    size_match = re.search(r'مقاس\s*(\d{2}(?:\.\d)?)', text)
    if not size_match:
        size_match = re.search(r'size\s*(\d{2}(?:\.\d)?)', text, re.IGNORECASE)
    if not size_match:
        # أي رقم بين 32 و 48
        size_match = re.search(r'\b(3[2-9]|4[0-8])\b', text)
    if size_match:
        info["size"] = size_match.group(1)
    
    # استخراج اللون (كلمات ألوان معروفة)
    colors = {
        "أحمر": "أحمر", "حمرة": "أحمر", "rouge": "أحمر", "red": "أحمر",
        "أسود": "أسود", "كحل": "أسود", "khal": "أسود", "noir": "أسود", "black": "أسود",
        "أبيض": "أبيض", "بيض": "أبيض", "blanc": "أبيض", "white": "أبيض",
        "أزرق": "أزرق", "زرق": "أزرق", "bleu": "أزرق", "blue": "أزرق",
        "أخضر": "أخضر", "خضر": "أخضر", "vert": "أخضر", "green": "أخضر",
        "أصفر": "أصفر", "صفر": "أصفر", "jaune": "أصفر", "yellow": "أصفر",
        "وردي": "وردي", "ورد": "وردي", "rose": "وردي", "pink": "وردي",
        "بني": "بني", "marron": "بني", "brown": "بني",
        "رمادي": "رمادي", "gris": "رمادي", "grey": "رمادي", "gray": "رمادي",
        "بنفسجي": "بنفسجي", "violet": "بنفسجي", "purple": "بنفسجي",
        "بيج": "بيج", "beige": "بيج",
        "ذهبي": "ذهبي", "doré": "ذهبي", "gold": "ذهبي",
        "فضي": "فضي", "argent": "فضي", "silver": "فضي",
        "نحاسي": "نحاسي", "cuivre": "نحاسي", "copper": "نحاسي"
    }
    for ar_word, normalized in colors.items():
        if ar_word in text.lower():
            info["color"] = normalized
            break
    
    # استخراج الكمية (رقم قبل "زوج" أو "قطعة" أو "حبة" أو بعد كمية/quantity)
    qty_match = re.search(r'(\d+)\s*(أزواج|زوج|زوجين|قطع|قطعة|حبات|حبة|pairs?|pieces?)', text)
    if qty_match:
        info["quantity"] = int(qty_match.group(1))
    
    # استخراج الاسم (الكلمات المتبقية التي ليست أرقام/ألوان/مقاسات)
    name_text = text
    
    # إزالة الكلمات المفتاحية المعروفة
    remove_patterns = [
        r'زيد\s+', r'أضف\s+', r'اضف\s+', r'إضافة\s+', r'ضيف\s+',
        r'new\s+product', r'add\s+product',
        r'مقاس\s+\d+', r'size\s+\d+',
        r'\d+[\d,.]*\s*(دج|د\.ج|da|دينار)',
        r'\d+\s*(أزواج|زوج|زوجين|قطع|قطعة|حبات|حبة)',
        r'ب\s+', r'بـ\s+',
    ]
    for pat in remove_patterns:
        name_text = re.sub(pat, "", name_text, flags=re.IGNORECASE)
    
    # تنظيف المسافات الزائدة
    name_text = re.sub(r'\s+', ' ', name_text).strip()
    
    # إزالة الألوان من الاسم
    for color_word in colors:
        name_text = re.sub(r'\b' + color_word + r'\b', '', name_text)
    
    name_text = re.sub(r'\s+', ' ', name_text).strip()
    
    if name_text and len(name_text) > 2:
        info["name"] = name_text
    
    return info


# ============================================================
# 🤖 Agent Endpoints
# ============================================================

@inv_agent_bp.route("/process", methods=["POST"])
def process_command():
    """
    الـ Endpoint الرئيسي للـ Inventory Agent
    يستقبل رسالة نصية وينفذ الأمر المناسب
    
    Input: {"message": "زيد حذاء رياضي أحمر مقاس 38 ب 2500 دج"}
    Output: {"success": true, "action": "add_product", "product": {...}, "message": "..."}
    """
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required", "code": "INVALID_INPUT"}), 400
    
    text = data["message"].strip()
    intent = detect_intent(text)
    
    if intent == "add_product":
        return _handle_add_product(text)
    elif intent == "update_price":
        return _handle_update_price(text)
    elif intent == "update_stock":
        return _handle_update_stock(text)
    elif intent == "check_stock":
        return _handle_check_stock(text)
    elif intent == "list_products":
        return _handle_list_products(text)
    elif intent == "low_stock":
        return _handle_low_stock()
    else:
        return jsonify({
            "success": False,
            "action": "unknown",
            "message": "لم أفهم الأمر. حاول بصيغة مثل:\n"
                       "• 'زيد حذاء رياضي أحمر مقاس 38 ب 2500 دج'\n"
                       "• 'شنو عندك في المخزون؟'\n"
                       "• 'المنتجات المنخفضة المخزون'\n"
                       "• 'غير سعر الحذاء الرياضي ل 3000 دج'"
        }), 200


def _handle_add_product(text):
    """إضافة منتج جديد من النص"""
    info = extract_product_info(text)
    
    if not info["name"]:
        return jsonify({
            "success": False,
            "action": "add_product",
            "message": "لم أتمكن من تحديد اسم المنتج. حاول مثلاً:\n"
                       "زيد حذاء رياضي أحمر مقاس 38 ب 2500 دج"
        }), 200
    
    # توليد SKU تلقائي
    from datetime import datetime
    sku = f"ROYAL-{datetime.now().strftime('%y%m%d%H%M%S')}"
    
    # البحث عن منتج مشابه
    similar = search_products(info["name"], limit=3)
    
    product_data = {
        "sku": sku,
        "name": info["name"],
        "color": info["color"],
        "size": info["size"],
        "store_price": info["price"] or 0,
        "online_price": info["price"] or 0,
        "cost_price": 0,  # يحتاج تحديث يدوي لسعر الشراء
        "category": "أحذية" if any(w in info["name"] for w in ["حذاء", "boot", "sneaker", "pump"]) else "عام",
        "barcode": sku  # مؤقت
    }
    
    try:
        product = create_product(product_data)
        
        # تعيين المخزون الابتدائي
        update_inventory(product["id"], store_qty=info["quantity"])
        
        response_parts = [f"✅ تمت إضافة **{info['name']}** بنجاح!"]
        if info["price"]:
            response_parts.append(f"💰 السعر: {int(info['price'])} دج")
        if info["color"]:
            response_parts.append(f"🎨 اللون: {info['color']}")
        if info["size"]:
            response_parts.append(f"📏 المقاس: {info['size']}")
        response_parts.append(f"📦 المخزون: {info['quantity']} قطعة")
        response_parts.append(f"🔖 SKU: `{sku}`")
        
        return jsonify({
            "success": True,
            "action": "add_product",
            "product": product,
            "message": "\n".join(response_parts)
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "action": "add_product",
            "message": f"❌ خطأ في إضافة المنتج: {str(e)}"
        }), 500


def _handle_update_price(text):
    """تحديث سعر منتج"""
    # استخراج السعر الجديد
    price_match = re.search(r'(?:ل|إلى|بـ|ب)\s*(\d+[\d,.]*)\s*(دج|د\.ج|da|دينار)?', text, re.IGNORECASE)
    if not price_match:
        price_match = re.search(r'(\d+[\d,.]*)\s*(دج|د\.ج|da|دينار)', text, re.IGNORECASE)
    new_price = float(price_match.group(1).replace(",", "")) if price_match else None
    
    if not new_price:
        return jsonify({
            "success": False,
            "action": "update_price",
            "message": "لم أتمكن من تحديد السعر الجديد. حاول:\nغير سعر الحذاء الرياضي ل 3000 دج"
        }), 200
    
    # استخراج اسم المنتج (إزالة السعر والأرقام وكلمات التعديل)
    name_text = re.sub(r'(?:غير|غيّر|بدّل|عدّل|تعديل)\s+سعر\s+', '', text, flags=re.IGNORECASE)
    name_text = re.sub(r'سعر\s+', '', name_text, flags=re.IGNORECASE)
    name_text = re.sub(r'(?:ل|إلى|بـ|ب)\s*\d+[\d,.]*\s*(دج|د\.ج|da|دينار)?', '', name_text, flags=re.IGNORECASE)
    name_text = re.sub(r'\d+[\d,.]*\s*(دج|د\.ج|da|دينار)?', '', name_text, flags=re.IGNORECASE)
    name_text = name_text.strip().rstrip("?؟").strip()
    
    if not name_text or len(name_text) < 2:
        return jsonify({
            "success": False,
            "action": "update_price",
            "message": "لم أتمكن من تحديد اسم المنتج. حاول:\nغير سعر الحذاء الرياضي ل 3000 دج"
        }), 200
    
    # البحث عن المنتج
    matched = search_products(name_text, limit=5)
    if not matched:
        # Fuzzy search in all products
        all_products = get_products(active_only=True)
        matched = [p for p in all_products if name_text.lower() in p["name"].lower()]
    
    if not matched:
        return jsonify({
            "success": False,
            "action": "update_price",
            "message": f"لم أجد منتجاً باسم '{name_text}'"
        }), 200
    
    product = matched[0]
    update_product(product["id"], {"store_price": new_price, "online_price": new_price})
    
    return jsonify({
        "success": True,
        "action": "update_price",
        "product": get_product(product["id"]),
        "message": f"✅ تم تحديث سعر **{product['name']}** إلى {int(new_price)} دج"
    }), 200


def _handle_update_stock(text):
    """تحديث المخزون (نقص/زيادة)"""
    # تحديد هل هي زيادة أم نقصان
    is_increase = bool(re.search(r'زود\s+|أضف مخزون|ضيف مخزون|زيادة\s+مخزون|زيد\s+مخزون', text))
    
    # استخراج الكمية
    qty_match = re.search(r'(\d+)', text)
    quantity = int(qty_match.group(1)) if qty_match else 1
    
    # استخراج اسم المنتج (إزالة الكلمات المفتاحية والرقم)
    name_text = re.sub(r'\d+', '', text)
    name_text = re.sub(r'نقص\s+|زود\s+|أضف مخزون|ضيف مخزون|زيادة\s+مخزون|زيد\s+مخزون|من\s+مخزون\s+|من\s+', '', name_text, flags=re.IGNORECASE)
    name_text = name_text.strip().rstrip("?؟").strip()
    
    if not name_text or len(name_text) < 2:
        return jsonify({
            "success": False,
            "action": "update_stock",
            "message": "لم أتمكن من تحديد اسم المنتج. حاول:\نقص 5 من الحذاء الرياضي"
        }), 200
    
    matched = search_products(name_text, limit=5) if name_text else []
    if not matched:
        # Fuzzy search in all products
        all_products = get_products(active_only=True)
        matched = [p for p in all_products if name_text.lower() in p["name"].lower()]
    
    if not matched:
        return jsonify({
            "success": False,
            "action": "update_stock",
            "message": f"لم أجد منتجاً باسم '{name_text}'"
        }), 200
    
    product = matched[0]
    inv = get_inventory(product["id"])
    current_qty = inv.get("store_quantity", 0) if inv else 0
    
    if is_increase:
        new_qty = current_qty + quantity
        action_word = "زيادة"
    else:
        new_qty = max(0, current_qty - quantity)
        action_word = "نقص"
    
    update_inventory(product["id"], store_qty=new_qty)
    
    return jsonify({
        "success": True,
        "action": "update_stock",
        "product": get_product(product["id"]),
        "message": f"✅ {action_word} مخزون **{product['name']}**: {int(current_qty)} → {int(new_qty)} قطعة"
    }), 200


def _handle_check_stock(text):
    """التحقق من المخزون"""
    # بحث في النص عن اسم منتج
    name_text = text
    for word in ["شنو عندك", "واش عندك", "عندك شنو", "المخزون", "stock", "inventory", "available", "شحال", "قداش", "كاين", "واش كاين"]:
        name_text = name_text.replace(word, "")
    name_text = name_text.strip().rstrip("؟?")
    
    if name_text and len(name_text) > 1:
        # البحث عن منتج معين
        matched = search_products(name_text, limit=5)
        if matched:
            results = []
            for p in matched:
                inv = get_inventory(p["id"])
                qty = inv.get("store_quantity", 0) if inv else 0
                results.append(f"• **{p['name']}**: {int(qty)} قطعة ({int(p.get('store_price', 0))} دج)")
            return jsonify({
                "success": True,
                "action": "check_stock",
                "products": matched,
                "message": "📦 **المخزون المطلوب:**\n" + "\n".join(results)
            }), 200
    
    # عرض ملخص المخزون
    all_inv = get_inventory()
    total_items = sum(i.get("store_quantity", 0) for i in all_inv)
    total_products = len(all_inv)
    low_stock = get_low_stock_items()
    
    return jsonify({
        "success": True,
        "action": "check_stock",
        "summary": {
            "total_products": total_products,
            "total_items": total_items,
            "low_stock_count": len(low_stock)
        },
        "message": f"📊 **ملخص المخزون:**\n"
                   f"• إجمالي المنتجات: {total_products}\n"
                   f"• إجمالي القطع: {int(total_items)}\n"
                   f"{'⚠️ منتجات منخفضة المخزون: ' + str(len(low_stock)) if low_stock else '✅ كل المنتجات متوفرة'}"
    }), 200


def _handle_list_products(text):
    """عرض قائمة المنتجات"""
    products = get_products(active_only=True, limit=30)
    
    if not products:
        return jsonify({
            "success": True,
            "action": "list_products",
            "products": [],
            "message": "📭 لا توجد منتجات في النظام بعد. أضف منتجاً أولاً!"
        }), 200
    
    lines = ["📋 **المنتجات المتوفرة:**\n"]
    for p in products[:20]:
        inv = get_inventory(p["id"])
        qty = inv.get("store_quantity", 0) if inv else 0
        price = int(p.get("store_price", 0))
        stock_icon = "✅" if qty > 5 else ("⚠️" if qty > 0 else "❌")
        lines.append(f"{stock_icon} **{p['name']}** — {price} دج ({int(qty)} قطعة)")
    
    if len(products) > 20:
        lines.append(f"\n... و {len(products) - 20} منتج آخر")
    
    return jsonify({
        "success": True,
        "action": "list_products",
        "products": products[:20],
        "message": "\n".join(lines)
    }), 200


def _handle_low_stock():
    """المنتجات المنخفضة المخزون"""
    items = get_low_stock_items()
    
    if not items:
        return jsonify({
            "success": True,
            "action": "low_stock",
            "items": [],
            "message": "✅ كل المنتجات متوفرة بكميات جيدة!"
        }), 200
    
    lines = ["⚠️ **المنتجات المنخفضة المخزون:**\n"]
    for item in items:
        qty = item.get("store_quantity", 0)
        lines.append(f"• **{item['name']}** — {int(qty)} قطعة فقط!")
    
    return jsonify({
        "success": True,
        "action": "low_stock",
        "items": items,
        "message": "\n".join(lines)
    }), 200


# ============================================================
# 🔌 System Prompt Generator for AI Agent
# ============================================================

@inv_agent_bp.route("/system-prompt", methods=["GET"])
def get_system_prompt():
    """
    توليد System Prompt للـ AI Agent لتفعيل الـ Inventory Agent
    يُستخدم هذا الـ prompt في تكوين AI_SYSTEM_PROMPT أو prompt.txt
    """
    prompt = """## 🤖 Inventory Agent — إدارة المخزون بالرسائل

يمكنك إدارة منتجات ومخزون المتجر عبر الرسائل النصية فقط!

### الأوامر المدعومة:

#### 1️⃣ إضافة منتج جديد
أرسل رسالة تحتوي على:
- كلمة "زيد" أو "أضف" أو "ضيف"
- اسم المنتج
- السعر (رقم + دج)
- المقاس (اختياري)
- اللون (اختياري)

**مثال:** "زيد حذاء رياضي أحمر مقاس 38 ب 2500 دج"

#### 2️⃣ التحقق من المخزون
- "شنو عندك في المخزون؟" — عرض ملخص
- "المخزون" — عرض كل المنتجات
- "شحال من حذاء رياضي؟" — بحث في منتج معين

#### 3️⃣ تحديث المخزون
- "نقص 5 من الحذاء الرياضي"
- "زود 10 من الصنادل"

#### 4️⃣ تغيير السعر
- "غير سعر الحذاء الرياضي ل 3000 دج"

#### 5️⃣ المنتجات المنخفضة
- "المنتجات المنخفضة المخزون"
- "واش راح يكمل؟"

### ملاحظات مهمة:
- أدخل سعر الشراء (cost_price) لاحقاً من Dashboard
- SKU يتولد تلقائياً
- لإضافة صورة للمنتج، استخدم Dashboard
"""
    return jsonify({
        "success": True,
        "prompt": prompt,
        "prompt_length": len(prompt)
    }), 200
