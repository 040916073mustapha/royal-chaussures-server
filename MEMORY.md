# 🧠 Long-Term Memory — Royal Chaussures System

> آخر تحديث: 7 أغسطس 2026

## 🏆 GOLDEN RELEASE v3 — RC Agent v2.0 (Dark Neon Cyberpunk Complete)

| العنصر | القيمة |
|--------|--------|
| **Tag** | `v2.0-rc-agents-dark-neon-complete` |
| **Commit** | `e8da910` |
| **التاريخ** | 7 أغسطس 2026 |
| **الحالة** | ✅ Production — Dashboard + Messenger + WhatsApp + Instagram |

### ✨ ميزات v2.0 (Dark Neon Cyberpunk)
- **تصميم RC AGENTS Dark Neon Cyberpunk** — واجهة مبهرة كاملة
- **لوحة تحكم (Dashboard)**: إحصائيات المبيعات، إدارة الطلبات، المنتجات
- **Live Chat Inbox**: محادثات حية من جميع القنوات مع auto-refresh
- **Sidebar ذكي**: AlpineJS x-for مع dynamic navItems
- **System Prompt من ملف**: `prompt.txt` يُقرأ بدل Environment Variable (لا انكسار بعد الآن)
- **ذكاء المحادثة**: ترحيب فقط في أول رسالة، جمع بيانات Step-by-Step
- **مقاسات أوروبية**: 36-41 من Shopify Options (لا تظهر كميات المخزون كمقاسات)
- **لا Meta-Explanation**: الـ AI يرد طبيعياً بدون شرح خطوات النظام
- **Dashboard Basic Auth**: before_request يحمي `/dashboard/*` و `/api/*`
- **Settings page**: يعرض `Qwen/Qwen3-VL-30B-A3B-Instruct`
- **إصلاح خطأ 500**: {{ item.label }} → x-text="item.label" (Jinja2/AlpineJS conflict)
- **🔐 X-Hub-Signature-256**: التحقق من HMAC-SHA256 للتوقيع (Meta App Secret)

### ✅ اختبار شامل — 7 أغسطس 2026
- 📱 **Messenger**: ✅
- 💚 **WhatsApp**: ✅
- 📸 **Instagram**: ✅
- 🖥️ **Live Chat Dashboard**: ✅
- 🛍️ **Shopify**: ✅
- 🏙️ **ZR Express**: ✅ 58 ولاية
- **Settings Page**: ✅ تعرض الموديل الصحيح
- **🔐 Webhook Security**: ✅ X-Hub-Signature-256 verification

---

## 🏆 GOLDEN RELEASE v2 — RC Agent v1.2 (Omnichannel Production Ready)

| العنصر | القيمة |
|--------|--------|
| **Tag** | `v1.2-omnichannel-production-ready` |
| **Commit** | `c62a9c7` |
| **التاريخ** | 7 أغسطس 2026 |
| **الحالة** | ✅ Production — Messenger, WhatsApp, Instagram + Live Dashboard |

### ✨ ميزات جديدة في v1.2 (بالإضافة إلى v1.0)
- **Live Chat Dashboard**: `/dashboard/chat` — عرض المحادثات الحية من جميع القنوات
- **save_message_db()**: تخزين كل رسالة ورد في SQLite (`messages` table) فورياً
- **/api/messages**: API لجلب المحادثات مع فلترة بالمنصة والبحث
- **/api/profile**: جلب اسم المستخدم من Facebook Graph API (يعرض اسم العميل بدل ID)
- **fetchNames()**: AlpineJS يطلب أسماء المستخدمين تلقائياً بعد تحميل المحادثات
- **Logging محسّن**: `[DB]` markers + traceback كامل عند الخطأ
- **Intervention Mode**: تفعيل/إيقاف الردود التلقائية لكل محادثة
- **Auto-refresh**: تحديث المحادثات كل 10 ثوانٍ

### ✅ اختبار شامل — 7 أغسطس 2026
- 📱 **Messenger**: ✅ وصول + رد + حفظ في Dashboard
- 💚 **WhatsApp**: ✅ وصول + رد + حفظ في Dashboard
- 📸 **Instagram**: ✅ وصول + رد + حفظ في Dashboard
- 🖥️ **Live Chat**: ✅ أسماء العملاء + نص الرسائل + توقيت
- 🛍️ **Shopify**: ✅ جلب المنتجات والأسعار قبل كل رد
- 🏙️ **ZR Express**: ✅ 58 ولاية بأسعار مضبوطة

---

## 🏆 GOLDEN RELEASE v1 — RC Agent v1.0 (Meta-Approved)

| العنصر | القيمة |
|--------|--------|
| **Tag** | `v1.0-stable-meta-approved` |
| **Commit** | `51b0b78` (Rollback إلى `12f9fc8` المستقرة) |
| **التاريخ** | 7 أغسطس 2026 |
| **الحالة** | ✅ Production — Messenger, WhatsApp, Instagram |

### 🎯 الميزات المثبتة
- قراءة صور الأحذية + الأسعار + الألوان + التفاصيل بدقة
- ردود بالعربية والدارجة عبر AI (DeepSeek-V4-Flash)
- دعم FB Messenger، Instagram، WhatsApp
- دعم صور FB (`attachments[].payload.url`), WA (`image.id`/`link`)
- Logging كامل: `[AI]` request/response/status/timeout
- جلب live inventory من Shopify تلقائياً قبل كل رد
- أسعار التوصيل ZR Express لـ 58 ولاية
- **System Prompt** قابل للتعديل عبر `AI_SYSTEM_PROMPT` في Render Environment Variables

### 🧠 System Prompt (في Render Env منذ 7 أغسطس 2026)
- المتغير: `AI_SYSTEM_PROMPT`
- Fallback: النص الثابت في `server.py` إن لم يوجد المتغير
- آلية العمل: `os.getenv("AI_SYSTEM_PROMPT", "[1. ROYAL IDENTITY]...")`

**ملاحظة مهمة:** لا نستخدم فلاتر thinking/regex! النموذج مباشر.

---

## ✅ النسخة المستقرة السابقة (أرشيف)

## 🔑 المبادئ الهندسية (Royal System)

### قاعدة Payload الصحيح
```python
if isinstance(image_url, str) and image_url.strip():
    user_content = [
        {"type": "text", "text": user_message or "What is in this image?"},
        {"type": "image_url", "image_url": {"url": image_url.strip()}}
    ]
else:
    user_content = user_message
```

## 🔄 كيفية الرجوع للنسخة الذهبية في أي وقت

### للرجوع لـ v1.2 (Omnichannel كاملة):
```bash
git checkout tags/v1.2-omnichannel-production-ready -- server.py templates/chat_console.html
git commit -m "[HOTFIX] Revert to golden release v1.2 omnichannel"
git push
# ثم Deploy على Render (Manual Deploy → Deploy latest commit)
```

### للرجوع لـ v1.0 (النسخة الأساسية المستقرة):
```bash
git checkout tags/v1.0-stable-meta-approved -- server.py
git commit -m "[HOTFIX] Revert to golden release v1.0"
git push
# ثم Deploy على Render (Manual Deploy → Deploy latest commit)
```

### عند تعديل System Prompt
1. اذهب إلى **Render Dashboard** → Environment Variables
2. عدل قيمة `AI_SYSTEM_PROMPT`
3. **لا داعي لتعديل الكود**
4. Render يعيد التشغيل تلقائياً

---

### عند إضافة Vision لنموذج جديد
1. جرب `timeout=40` أولاً
2. أضف `[AI]` logging قبل/بعد `requests.post`
3. تأكد من استجابة DeepInfra أولاً بـ `resp.text[:800]`
4. اختبر محلياً:
   - نص فقط → `str`
   - نص + صورة → `list` مع `image_url`
   - صورة فقط → `list` مع `"What is in this image?"`
   - `None`/`""`/`"   "` → `str`

### عند فشل النموذج
1. غير `AI_MODEL` في Render Environment Variables (بدون تعديل كود)
2. تحقق من Logs: `[AI] Sending to` يطبع؟ `[AI] Response` يطبع؟
3. إذا طبع "Sending" وما طبع "Response" → المشكلة في الاتصال/توقف DeepInfra
4. إذا طبع "Response 4XX" → المشكلة في المفتاح/الرصيد/Payload
5. **Revert** إلى `git reset --hard ee335fc` والبدء من جديد

### آخر تعديلات الـ `server.py`
- `generate_ai_reply` — يبني الـ payload (نص/صورة)
- `process_messaging_entries` — استخراج صور FB/IG
- `process_whatsapp_entries` — استخراج صور WA
- `save_message_db()` — حفظ الرسائل في SQLite للـ Dashboard
- `send_fb_reply` / `send_ig_reply` / `send_whatsapp_reply` — مع `save_message_db()` بعد الرد
- `/api/messages` — API جلب المحادثات (فلترة + بحث)
- `/api/profile` — API جلب اسم FB Profile
- دوال الإرسال `send_*_reply` — تمرير `image_url` + حفظ في DB

**لا تلمس أبداً:**
- دوال Webhook الأساسية (`/webhook`, `/whatsapp/webhook`)
- `process_messaging_entries` الأساسية (غير استخراج الصور)
- `upsert_order_from_shopify`
- كود قاعدة البيانات (`init_db`, `upsert_order_from_shopify`)
- كود التعامل مع Shopify API
- **تذكر**: `save_message_db()` كتبتها لخدمة الـ Dashboard فقط — لا تخلطها مع `CONVERSATION_MEMORY` (RAM)

## 🏪 Royal Chaussures
- متجر أحذية وإكسسوارات نسائية
- الموقع: Imama, Tlemcen
- التوصيل: ZR Express عبر 58 ولاية
- Shopify live: https://royalchaussures.com/
