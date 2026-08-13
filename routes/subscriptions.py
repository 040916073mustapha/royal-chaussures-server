"""
Nexus POS — Subscription & Payment Module
============================================
نظام الاشتراكات والدفع الإلكتروني عبر Chargily و BaridiMob

الخطط:
- Free: مجاني (30 يوم تجريبي)
- Basic: 1,500 دج/شهر
- Pro: 3,500 دج/شهر
- Enterprise: مخصص

طرق الدفع:
- Chargily: البطاقات البنكية (CIB/Dahabia)
- BaridiMob: تحويل بريدي موب (يدوي)
"""

import os
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, render_template, g, current_app
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, dict_from_row, dicts_from_rows, get_current_store_id

subs_bp = Blueprint("subscriptions", __name__, template_folder="../templates", url_prefix="/api/v1/subscription")


# ============================================================
# 🔐 Chargily Configuration
# ============================================================

CHARGILY_API_KEY = os.getenv("CHARGILY_API_KEY", "sandbox")
CHARGILY_SECRET = os.getenv("CHARGILY_SECRET", "sandbox")
CHARGILY_SANDBOX = CHARGILY_API_KEY == "sandbox" or not CHARGILY_API_KEY

CHARGILY_BASE = "https://api.chargily.com" if not CHARGILY_SANDBOX else "https://sandbox.api.chargily.com"


# ============================================================
# 💎 Plans & Pricing
# ============================================================

PLANS = {
    "free": {
        "name": "Free",
        "name_ar": "مجاني",
        "price_dzd": 0,
        "price_label": "مجاني",
        "max_products": 50,
        "max_employees": 1,
        "ai_agent": False,
        "shopify_sync": False,
        "reports": "basic",
        "trial_days": 30,
        "features": [
            "نظام POS أساسي",
            "حتى 50 منتج",
            "تقارير بسيطة",
            "مستخدم واحد"
        ]
    },
    "basic": {
        "name": "Basic",
        "name_ar": "أساسي",
        "price_dzd": 1500,
        "price_label": "1,500 دج/شهر",
        "max_products": 500,
        "max_employees": 3,
        "ai_agent": True,
        "shopify_sync": False,
        "reports": "advanced",
        "trial_days": 0,
        "features": [
            "كل ميزات المجاني",
            "حتى 500 منتج",
            "حتى 3 موظفين",
            "AI Agent للمخزون",
            "تقارير متقدمة",
            "دعم فني"
        ]
    },
    "pro": {
        "name": "Pro",
        "name_ar": "احترافي",
        "price_dzd": 3500,
        "price_label": "3,500 دج/شهر",
        "max_products": -1,  # غير محدود
        "max_employees": 10,
        "ai_agent": True,
        "shopify_sync": True,
        "reports": "full",
        "trial_days": 0,
        "features": [
            "كل ميزات الأساسي",
            "منتجات غير محدودة",
            "حتى 10 موظفين",
            "AI Agent كامل",
            "ربط Shopify تلقائي",
            "تقارير شاملة",
            "أولوية الدعم"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "name_ar": "مؤسسات",
        "price_dzd": 0,
        "price_label": "مخصص",
        "max_products": -1,
        "max_employees": -1,
        "ai_agent": True,
        "shopify_sync": True,
        "reports": "full",
        "trial_days": 0,
        "features": [
            "كل ميزات الاحترافي",
            "API كامل للتخصيص",
            "عدد غير محدود من الموظفين",
            "خادم خاص (اختياري)",
            "دعم VIP على مدار الساعة",
            "تدريب الفريق"
        ]
    }
}

BARIDI_CCP = "28439208 Clé 69"
BARIDI_RIP = "00799999002843920896"
BARIDI_OWNER = "CHABNI REDA ELMUSTAPHA"


# ============================================================
# 🧠 Helper Functions
# ============================================================

def get_store_subscription(store_id=None):
    """جلب حالة اشتراك متجر"""
    db = get_db()
    if store_id is None:
        store_id = get_current_store_id()
    store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = %s", [store_id]).fetchone())
    if not store:
        return None

    now = datetime.utcnow()
    trial_ends = store.get("trial_ends_at")
    if trial_ends and isinstance(trial_ends, str):
        trial_ends = datetime.fromisoformat(trial_ends.replace("Z", ""))

    next_billing = store.get("next_billing_at")
    if next_billing and isinstance(next_billing, str):
        next_billing = datetime.fromisoformat(next_billing.replace("Z", ""))

    tier = store.get("subscription_tier", "free")
    status = store.get("subscription_status", "active")
    plan = PLANS.get(tier, PLANS["free"])

    # حساب الفترة التجريبية
    is_trial = False
    trial_remaining_days = 0
    if tier == "free" and trial_ends:
        is_trial = True
        trial_remaining_days = max(0, (trial_ends - now).days)

    # هل الاشتراك منتهي؟
    is_expired = False
    if status == "active" and tier != "free" and next_billing:
        if now > next_billing:
            is_expired = True

    return {
        "store_id": store_id,
        "store_name": store["name"],
        "tier": tier,
        "tier_name": plan["name_ar"],
        "status": status,
        "is_trial": is_trial,
        "trial_remaining_days": trial_remaining_days,
        "is_expired": is_expired,
        "next_billing": next_billing.isoformat() if next_billing else None,
        "plan": plan,
        "can_use": status == "active" and not is_expired
    }


def subscription_required(f):
    """Decorator: يمنع الوصول إذا الاشتراك منتهي"""
    @wraps(f)
    def decorated(*args, **kwargs):
        store_id = getattr(g, "store_id", None) or get_current_store_id()
        sub = get_store_subscription(store_id)
        if not sub or not sub["can_use"]:
            return jsonify({
                "error": "Subscription expired or inactive",
                "subscription": sub,
                "upgrade_url": "/api/v1/subscription/plans"
            }), 402  # Payment Required
        return f(*args, **kwargs)
    return decorated


def _generate_invoice_number(store_id, tier):
    """توليد رقم فاتورة فريد"""
    ts = int(time.time())
    return f"NXP-{store_id}-{ts}-{tier.upper()}"


# ============================================================
# 🔓 Free Trial — تفعيل الفترة التجريبية
# ============================================================

@subs_bp.route("/activate-trial", methods=["POST"])
def activate_trial():
    """تفعيل الفترة التجريبية المجانية لمتجر (30 يوم)"""
    try:
        data = request.get_json() or {}
        store_id = data.get("store_id") or getattr(g, "store_id", None) or get_current_store_id()

        db = get_db()
        store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = %s", [store_id]).fetchone())
        if not store:
            return jsonify({"error": "Store not found"}), 404

        # إذا كان الاشتراك ليس free أو trial منتهي
        if store["subscription_tier"] != "free":
            return jsonify({"error": "Store already has a paid subscription"}), 400

        now = datetime.utcnow()
        trial_end = now + timedelta(days=30)

        db.execute(
            "UPDATE stores SET trial_ends_at = %s, subscription_status = 'active', updated_at = NOW() WHERE id = %s",
            [trial_end.isoformat(), store_id]
        )
        db.commit()

        return jsonify({
            "success": True,
            "message": "تم تفعيل الفترة التجريبية لمدة 30 يوم",
            "trial_ends_at": trial_end.isoformat()
        })

    except Exception as e:
        import traceback
        print(f"[Subs] Activate trial error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# 💳 Chargily Payment — إنشاء رابط دفع
# ============================================================

@subs_bp.route("/chargily/create-checkout", methods=["POST"])
def chargily_create_checkout():
    """إنشاء رابط دفع عبر Chargily للاشتراك"""
    try:
        data = request.get_json() or {}
        store_id = data.get("store_id") or getattr(g, "store_id", None) or get_current_store_id()
        tier = data.get("tier", "basic")
        period = data.get("period", "monthly")  # monthly, yearly

        if tier not in PLANS or tier == "free" or tier == "enterprise":
            return jsonify({"error": "Invalid tier. Choose: basic, pro"}), 400

        plan = PLANS[tier]
        price = plan["price_dzd"]

        # خصم 20% للاشتراك السنوي
        if period == "yearly":
            price = int(price * 12 * 0.8)

        # توليد رقم الفاتورة
        invoice_id = _generate_invoice_number(store_id, tier)

        # Chargily Checkout URL (Sandbox/Production)
        if CHARGILY_SANDBOX:
            checkout_url = f"{CHARGILY_BASE}/checkout/public/{CHARGILY_SECRET}"
        else:
            checkout_url = f"{CHARGILY_BASE}/checkout/public/{CHARGILY_API_KEY}"

        # تخزين معلومات الدفع مؤقتاً
        pending = {
            "invoice_id": invoice_id,
            "store_id": store_id,
            "tier": tier,
            "period": period,
            "amount": price,
            "currency": "DZD",
            "created_at": datetime.utcnow().isoformat()
        }

        # حفظ في قاعدة البيانات (جدول invoices اختياري — مؤقتاً في JSON)
        db = get_db()
        db.execute(
            "UPDATE stores SET features = jsonb_set(COALESCE(features, '{}'::jsonb), '{pending_payment}', %s::jsonb) WHERE id = %s",
            [json.dumps(pending), store_id]
        )
        db.commit()

        return jsonify({
            "success": True,
            "checkout_url": checkout_url,
            "invoice_id": invoice_id,
            "amount": price,
            "plan": plan["name_ar"],
            "period": "شهري" if period == "monthly" else "سنوي",
            "message": f"تم إنشاء رابط الدفع. المبلغ: {price:,} دج"
        })

    except Exception as e:
        import traceback
        print(f"[Subs] Chargily checkout error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# 📨 Chargily Webhook — استقبال تأكيد الدفع
# ============================================================

@subs_bp.route("/chargily/webhook", methods=["POST"])
def chargily_webhook():
    """استقبال Webhook من Chargily لتأكيد الدفع"""
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get("X-Chargily-Signature", "")

        # التحقق من التوقيع (HMAC-SHA256)
        if not CHARGILY_SANDBOX and CHARGILY_SECRET:
            expected_sig = hmac.new(
                CHARGILY_SECRET.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected_sig, signature):
                return jsonify({"error": "Invalid signature"}), 403

        data = request.get_json() or {}
        event = data.get("event", "")
        invoice_id = data.get("invoice_id") or data.get("metadata", {}).get("invoice_id")

        if event == "payment.success" and invoice_id:
            # البحث عن المتجر المرتبط بالفاتورة
            db = get_db()
            stores = dicts_from_rows(db.execute(
                "SELECT id, features FROM stores WHERE features->'pending_payment'->>'invoice_id' = %s",
                [invoice_id]
            ).fetchall())

            for store in stores:
                pending = store.get("features", {}).get("pending_payment", {})
                if pending.get("invoice_id") == invoice_id:
                    tier = pending["tier"]
                    period = pending.get("period", "monthly")
                    now = datetime.utcnow()

                    # تحديد تاريخ التجديد
                    if period == "yearly":
                        next_billing = now + timedelta(days=365)
                    else:
                        next_billing = now + timedelta(days=30)

                    db.execute(
                        "UPDATE stores SET subscription_tier = %s, subscription_status = 'active', "
                        "subscribed_at = %s, next_billing_at = %s, "
                        "features = features - 'pending_payment', updated_at = NOW() "
                        "WHERE id = %s",
                        [tier, now.isoformat(), next_billing.isoformat(), store["id"]]
                    )
                    print(f"[Subs] Payment confirmed: Store #{store['id']} upgraded to {tier}")

            db.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"[Subs] Chargily webhook error: {e}")
        return jsonify({"status": "error"}), 500


# ============================================================
# 💰 BaridiMob — تأكيد الدفع يدوي
# ============================================================

@subs_bp.route("/baridi/confirm", methods=["POST"])
def baridi_confirm():
    """تأكيد دفع BaridiMob يدوياً (يتطلب مراجعة من الأدمن)"""
    try:
        data = request.get_json() or {}
        store_id = data.get("store_id") or getattr(g, "store_id", None) or get_current_store_id()
        tier = data.get("tier", "basic")
        period = data.get("period", "monthly")
        transfer_ref = data.get("transfer_ref", "").strip()

        if not transfer_ref:
            return jsonify({"error": "رقم التحويل مطلوب"}), 400

        db = get_db()
        store = dict_from_row(db.execute("SELECT * FROM stores WHERE id = %s", [store_id]).fetchone())
        if not store:
            return jsonify({"error": "Store not found"}), 404

        # تخزين طلب التأكيد للانتظار (pending confirmation)
        pending = {
            "type": "baridi",
            "tier": tier,
            "period": period,
            "transfer_ref": transfer_ref,
            "status": "pending_review",
            "created_at": datetime.utcnow().isoformat()
        }

        db.execute(
            "UPDATE stores SET features = jsonb_set(COALESCE(features, '{}'::jsonb), '{pending_payment}', %s::jsonb) WHERE id = %s",
            [json.dumps(pending), store_id]
        )
        db.commit()

        return jsonify({
            "success": True,
            "message": "تم استلام طلب الاشتراك. سيتم تأكيد الدفع بعد التحقق من التحويل.",
            "baridi_info": {
                "ccp": BARIDI_CCP,
                "rip": BARIDI_RIP,
                "owner": BARIDI_OWNER,
                "amount": PLANS[tier]["price_dzd"] if period == "monthly" else PLANS[tier]["price_dzd"] * 12 * 0.8,
                "transfer_ref": transfer_ref
            }
        })

    except Exception as e:
        import traceback
        print(f"[Subs] Baridi confirm error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# 📋 Plans & Pricing — صفحة الخطط
# ============================================================

@subs_bp.route("/plans", methods=["GET"])
def pricing_page():
    """صفحة خطط الاشتراك"""
    return render_template("nexus_pricing.html", plans=PLANS, baridi={
        "ccp": BARIDI_CCP,
        "rip": BARIDI_RIP,
        "owner": BARIDI_OWNER
    })


# ============================================================
# 📊 Subscription Status API
# ============================================================

@subs_bp.route("/status", methods=["GET"])
def subscription_status():
    """حالة الاشتراك الحالية"""
    try:
        store_id = request.args.get("store_id", type=int) or getattr(g, "store_id", None) or get_current_store_id()
        sub = get_store_subscription(store_id)
        if not sub:
            return jsonify({"error": "Store not found"}), 404
        return jsonify(sub)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# 🛠️ Admin: تأكيد الدفع يدوياً (للأدمن)
# ============================================================

@subs_bp.route("/admin/confirm-subscription", methods=["POST"])
def admin_confirm_subscription():
    """تأكيد الاشتراك يدوياً من لوحة الأدمن"""
    try:
        data = request.get_json() or {}
        store_id = data.get("store_id")
        tier = data.get("tier", "basic")
        period = data.get("period", "monthly")

        if not store_id:
            return jsonify({"error": "store_id required"}), 400

        db = get_db()
        now = datetime.utcnow()
        next_billing = now + timedelta(days=30 if period == "monthly" else 365)

        db.execute(
            "UPDATE stores SET subscription_tier = %s, subscription_status = 'active', "
            "subscribed_at = %s, next_billing_at = %s, "
            "features = features - 'pending_payment', updated_at = NOW() "
            "WHERE id = %s",
            [tier, now.isoformat(), next_billing.isoformat(), store_id]
        )
        db.commit()

        return jsonify({
            "success": True,
            "message": f"Store #{store_id} confirmed as {tier}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
