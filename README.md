# Royal Chaussures Server 👑👠

**AI Customer Support Bot** لمتجر **Royal Chaussures** — أحذية وإكسسوارات نسائية فاخرة في تلمسان، الجزائر.

## 🏷️ النسخة المستقرة الحالية

**Tag:** `v1.0.0-stable-qwen3vl`  
**Commit:** `4b1ab83`  
**النموذج:** `Qwen/Qwen3-VL-30B-A3B-Instruct` (عبر DeepInfra)

## ✅ الميزات

- 🤖 **AI Vision** — قراءة صور الأحذية مع الأسعار والألوان والتفاصيل بدقة
- 💬 **ردود ذكية** — بالعربية والدارجة والفرنسية
- 📱 **دعم المنصات:** Facebook Messenger · Instagram · WhatsApp
- 🛍️ **Shopify متكامل** — استعلام عن المنتجات، المخزون، الطلبات
- 🚚 **ZR Express** — متابعة الشحن عبر 58 ولاية
- 📊 **Dashboard** — لوحة تحكم للإدارة (طلبات، منتجات، عملاء)
- 🧪 **Logging كامل** — تشخيص كل طلب AI مع الـ Response/Status Code

## ⚙️ متغيرات البيئة (Render)

| المتغير | الوصف |
|---|---|
| `AI_MODEL` | نموذج AI (حالياً `Qwen/Qwen3-VL-30B-A3B-Instruct`) |
| `AI_API_URL` | DeepInfra endpoint: `https://api.deepinfra.com/v1/openai/chat/completions` |
| `AI_API_KEY` | مفتاح DeepInfra API |
| `SHOPIFY_CATALOG_TOKEN` | Token قراءة المنتجات والمخزون |
| `SHOPIFY_ORDERS_TOKEN` | Token إدارة الطلبات |
| `FB_PAGE_ACCESS_TOKEN` | Token صفحة فيسبوك |
| `FB_VERIFY_TOKEN` | Token التحقق من Webhook |
| `WHATSAPP_ACCESS_TOKEN` | Token واتساب API |

## 🔧 التطوير

### تجربة نموذج AI جديد
1. غيّر `AI_MODEL` في Render Environment Variables فقط
2. تأكد من الـ Logs: `[AI]` يطبع Status و Response
3. إذا تعطل → `git reset --hard ee335fc` والعودة للنسخة الأساسية

### إضافة منصة جديدة
- أضف دالة `process_xxx_entries` مماثلة لـ `process_whatsapp_entries`
- أضف endpoint في Flask (`/xxx/webhook`)
- أضف دالة إرسال مماثلة لـ `send_whatsapp_reply`

## 📜 ملفات مهمة

- `server.py` — السيرفر الرئيسي (بوت + ويبهوك + Dashboard)
- `webhook_server.py` — ويبهوك Shopify
- `render_deploy/` — إعدادات Render

## 🔒 الأمان

- الكود لا يلمس دوال Webhook الأساسية
- قاعدة Payload الصحيح: `isinstance(image_url, str) and image_url.strip()`
- لا فلاتر thinking/regex
- Logging كامل لكل طلب API
