# 🧠 Long-Term Memory — Royal Chaussures System

> آخر تحديث: 7 أغسطس 2026

## 🏆 GOLDEN RELEASE — RC Agent v1.0 (Meta-Approved)

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

في حالة حدوث خطأ مستقبلاً:
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
- دوال الإرسال `send_*_reply` — فقط تمرير `image_url`

**لا تلمس أبداً:**
- دوال Webhook الأساسية (`/webhook`, `/whatsapp/webhook`)
- `process_messaging_entries` الأساسية (غير استخراج الصور)
- `upsert_order_from_shopify`
- كود قاعدة البيانات
- كود التعامل مع Shopify API

## 🏪 Royal Chaussures
- متجر أحذية وإكسسوارات نسائية
- الموقع: Imama, Tlemcen
- التوصيل: ZR Express عبر 58 ولاية
- Shopify live: https://royalchaussures.com/
