# 🗺️ RC Agents — خارطة الطريق الشاملة

> **آخر تحديث:** 19 أغسطس 2026  
> **الإصدار:** v2.5 (Multi-Tenant SaaS + Subdomains)  
> **الحالة:** 🟢 تشغيلية على rcagents.space + Render + Neon PostgreSQL

---

## 📌 1. الوضع الحالي (Current Status)

### ✅ المعالم المنشأة والجاهزة

| المعلم | الحالة | store_id | التفاصيل |
|--------|--------|----------|----------|
| **Royal Chaussures** (المتجر الرئيسي) | ✅ إنتاجي | 1 | أحذية نسائية + AI Agents + Messenger/WA/IG |
| **متجر ثانٍ (اختبار)** | ✅ منشأ | 2 | اختبار Onboarding API + Multi-Tenant |
| **Urban Moda** (متجر حقيقي ثالث) | ✅ منشأ | 3 | `urban-moda` — أول تاجر ثانٍ حقيقي |
| **صفحة Onboarding** (`/onboard`) | ✅ حية | — | واجهة تسجيل + Webhooks اختيارية + توجيه تلقائي |
| **تسجيل الدخول** (`/dashboard/login`) | ✅ حية | — | API + واجهة مع Session Token |
| **Dashboard Mult-Store** (`/dashboard/<store_id>/`) | ✅ حية | — | 5 صفحات لكل متجر على حدة |
| **🏪 Store Dashboard الجديد** (`store_dashboard.html`) | ✅ حية | — | بيانات حقيقية + AlpineJS + Subdomain Auto-Detect |
| **🌐 Subdomain لكل متجر** (`slug.rcagents.space`) | ✅ حية | — | ورل تلقائي بعد التسجيل |
| **🔐 Auth Bypass للـ Subdomains** | ✅ مكتمل | — | Basic Auth معطّل للـ *.rcagents.space |
| **📊 API Multi-Store** (`/api/stats, orders, clients, messages`) | ✅ معزّز | — | Subdomain Store_ID Auto-Detection |
| **Multi-Tenant DB** (PostgreSQL/Neon) | ✅ جاهز | — | عزل كامل للبيانات + sequences متزامنة |
| **AI Prompts لكل متجر** | ✅ جاهز | — | 4 وكلاء: customer_support, sales, shipping, inventory |
| **ZR Express** | ✅ جاهز | — | 58 ولاية مع أسعار مضبوطة |

### 🛠️ البنية التحتية

```
┌─────────────────────────────────────────────────────┐
│              RC Agents SERVER                       │
│  Host: rcagents.space | *.rcagents.space           │
│  ┌──────────┐  ┌─────────────────┐  ┌──────────┐   │
│  │  Webhook │  │   Dashboard     │  │    API   │   │
│  │ FB/WA/IG │  │  Store Dashboard│  │ Onboard/ │   │
│  │          │  │  (AlpineJS +    │  │ Login/   │   │
│  │          │  │   Real Data)    │  │ Settings │   │
│  └──────────┘  └─────────────────┘  └──────────┘   │
│         │                  │                         │
│  ┌──────┴──────────────────┴──────────────────┐     │
│  │       database/db.py + psql.py             │     │
│  │  • Auto-Reconnect (Neon Idle Fix)         │     │
│  │  • _get_store_id_from_subdomain()         │     │
│  │  • _sync_sequences() بعد كل Seed          │     │
│  │  • conn.status فحص قبل autocommit          │     │
│  └────────────────┬──────────────────────────┘     │
│  ┌────────────────┴──────────────────────────┐     │
│  │  PostgreSQL (Neon) + SQLite (Dev)         │     │
│  │  stores | users | store_prompts |         │     │
│  │  store_agent_config | store_webhooks      │     │
│  └───────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘


---

## 🗺️ 2. خريطة المراحل (Phases Roadmap)

### Phase 1: ✅ MVP Core & Multi-Tenant Infrastructure

| المهمة | الحالة | التفاصيل |
|--------|--------|----------|
| Golden Release v1.0 (Meta-Approved) | ✅ | Messenger + WhatsApp + Instagram |
| Golden Release v1.2 (Omnichannel) | ✅ | Live Chat Dashboard + AI Prompts |
| Golden Release v2.0 (Dark Neon Cyberpunk) | ✅ | تصميم كامل + Shopify + ZR |
| PostgreSQL Activation | ✅ | DB_ENGINE=postgres + Neon |
| Multi-Tenancy (Steps 1-5) | ✅ | stores, store_prompts, store_webhooks |
| Onboarding API (`/api/tenant/onboard`) | ✅ | إنشاء متجر + مستخدم + Prompts + Webhooks |
| Neon Connection Auto-Reconnect | ✅ | 3 مستويات: get_db() → execute() → commit() |
| Sequence Sync بعد الـ Seed | ✅ | `_sync_sequences()` لكل الجداول |
| Random Slug للأسماء العربية | ✅ | Fallback: `store-xxxxxxxx` |

### Phase 2: ✅ Frontend & Multi-Store Dashboard Integration (مكتملة)

| المهمة | الحالة | التفاصيل |
|--------|--------|----------|
| صفحة Onboarding (`/onboard`) | ✅ مكتملة | تسجيل + Webhooks + توجيه Subdomain |
| تسجيل الدخول (`/dashboard/login`) | ✅ مكتمل | API + Dashboard Login Page |
| Dashboard Multi-Store (`/dashboard/<store_id>/`) | ✅ مكتمل | 5 صفحات لكل متجر |
| **Store Dashboard الجديد** | ✅ مكتمل | `store_dashboard.html` مع بيانات حقيقية |
| **Subdomain Auth Bypass** | ✅ مكتمل | `_get_store_id_from_subdomain()` في كل APIs |
| **Safe Paths محسّنة** | ✅ مكتمل | /api/* و /dashboard/* مع store_id فحص |
| **Store Switcher (للمدير الرئيسي)** | 🔲 مفتوح | 🟡 متوسطة |
| حماية Dashboard بالـ Session Token | 🔲 مفتوح | 🟡 متوسطة |

### Phase 3: ⏳ AI Agents Configuration & Live Messaging

| المهمة | الحالة |
|--------|--------|
| UI لإدارة Prompts لكل متجر | 🔲 مفتوح |
| اختبار الـ Webhooks للمتجر الجديد | 🔲 مفتوح |
| تخصيص Agent Configs (الاسم + الإيموجي) عبر Dashboard | 🔲 مفتوح |
| إحصائيات المحادثات لكل متجر | 🔲 مفتوح |
| إشعارات عند تسجيل تاجر جديد | 🔲 مفتوح |

### Phase 4: 🚀 SaaS Domain & Production Launch

| المهمة | الحالة |
|--------|--------|
| نطاق مخصص للتاجر (store.royalchaussures.com) | 🔲 مفتوح |
| صفحة هبوط للمنصة (Landing Page) | 🔲 مفتوح |
| نظام الفوترة والاشتراكات | 🔲 مفتوح |
| دليل استخدام每位 تاجر | 🔲 مفتوح |
| ترقية الـ Dashboard بإحصائيات متقدمة | 🔲 مفتوح |

---

## 📋 3. لوحة المهام الحالية (Kanban Board)

### ✅ Done (تم الإنجاز)

- [x] `git tag v2.0-rc-agents-dark-neon-complete` (commit `e8da910`)
- [x] `git tag v1.2-omnichannel-production-ready` (commit `c62a9c7`)
- [x] `git tag v1.0-stable-meta-approved` (commit `51b0b78` → `12f9fc8`)
- [x] Multi-Tenant DB Architecture (stores + store_prompts + store_webhooks)
- [x] PostgreSQL Auto-Reconnect (3 مستويات ضد Neon Idle)
- [x] Onboarding API + Frontend Page (`/onboard`)
- [x] Tenant Login API + Dashboard Login Page (`/dashboard/login`)
- [x] Random Slug Fallback (`store-xxxxxxxx`) للأسماء العربية
- [x] `_sync_sequences()` لجميع جداول PostgreSQL بعد الـ Seed
- [x] فحص `conn.status` قبل تعيين `autocommit=False`
- [x] Subdomain Auth Bypass (4 طرق: safe paths, store_id param, Host check, regex)
- [x] `_get_store_id_from_subdomain()` لكل الـ APIs (stats, orders, clients, messages)
- [x] `/api/messages` + `/api/profile` في safe paths

### 🔄 In Progress (قيد التنفيذ الآن)

- [ ] Store Switcher Dropdown للمدير الرئيسي (مصطفى)
- [ ] حماية Dashboard بالـ Session Token

### ⏳ Backlog (المهام القادمة)

- [ ] UI تعديل Prompts من Dashboard
- [ ] اختبار Webhooks للمتجر الجديد
- [ ] إحصائيات المحادثات لكل متجر
- [ ] صفحة هبوط للمنصة (Landing Page)
- [ ] نظام الفوترة والاشتراكات

---

## ⚠️ 4. سجل القرارات البرمجية (ADR)

### ADR-001: Neon Connection Pool Auto-Reconnect

| الحقل | القيمة |
|-------|--------|
| **التاريخ** | 18 أغسطس 2026 |
| **المشكلة** | `InterfaceError: connection already closed` بعد Idle (Neon يغلق الاتصالات الخاملة) |
| **القرار** | إضافة Auto-Reconnect في 3 مستويات: `get_db()` (فحص SELECT 1 + 3 محاولات), `execute()` (فحص قبل كل استعلام), `commit()/rollback()` (إعادة اتصال عند الفشل) |
| **الملف** | `database/psql.py` |
| **الـ Commits** | `2d7d7f6`, `4ca2e86` |

### ADR-002: PostgreSQL Sequence Sync

| الحقل | القيمة |
|-------|--------|
| **التاريخ** | 18 أغسطس 2026 |
| **المشكلة** | `UniqueViolation: Key (id)=(1) already exists` عند محاولة إنشاء متجر جديد لأن الـ seed أدرج store_id=1 يدوياً دون تحديث الـ auto-increment |
| **القرار** | إضافة دالة `_sync_sequences(db)` تزامن 9 جداول (`stores`, `users`, `orders`, `products`, `clients`, `messages`, `store_agent_config`, `store_prompts`, `store_webhooks`) باستخدام `pg_get_serial_sequence` + `setval` |
| **الملف** | `database/psql.py` + `scripts/migrate_pg.py` |
| **الـ Commits** | `dea3994` |

### ADR-003: Random Slug للأسماء العربية

| الحقل | القيمة |
|-------|--------|
| **التاريخ** | 18 أغسطس 2026 |
| **المشكلة** | `re.sub(r"[^a-z0-9-]", "", slug)` يزيل كل الحروف العربية → يصبح الـ slug فارغاً ويظهر `--` |
| **القرار** | إضافة فحص: `if not slug or slug.strip("-") == ""` → استخدام `secrets.choice(string.ascii_lowercase, k=8)` مع بادئة `store-` |
| **الملف** | `server.py` (دالة `api_tenant_onboard`) |
| **الـ Commits** | `5703ba3` |

### ADR-004: set_session داخل Transaction

| الحقل | القيمة |
|-------|--------|
| **التاريخ** | 18 أغسطس 2026 |
| **المشكلة** | `psycopg2.ProgrammingError: set_session cannot be used inside a transaction` عند تعيين `conn.autocommit = False` على اتصال معاد استخدامه من الـ pool |
| **القرار** | فحص `conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION` قبل تعيين `autocommit` وعمل `conn.rollback()` إذا كانت Transaction نشطة |
| **الملف** | `database/psql.py` (دالة `get_db()` + دالة `_reconnect()`) |
| **الـ Commits** | `4ca2e86` |

### ADR-005: Subdomain Store-ID Auto-Detection

| الحقل | القيمة |
|-------|--------|
| **التاريخ** | 19 أغسطس 2026 |
| **المشكلة** | طلبات API من Subdomain (مثل `puma.rcagents.space/dashboard`) تعود ببيانات المتجر الرئيسي (store_id=1) بدلاً من بيانات المتجر الخاص بها |
| **القرار** | إضافة دالة `_get_store_id_from_subdomain()` تستخرج slug من Host header وتبحث عن store_id في DB + فحص 4 طبقات للـ Auth Bypass (safe paths, store_id param, Host regex, أصحاب subdomain) |
| **الملف** | `server.py` (دالة `require_auth_for_dashboard()` + دوال API) |
| **الـ Commits** | `a5ca089`, `a3709ea`, `89943cf`, `1d8c139` |

---

## 🔑 5. المفاتيح السريعة (Quick Reference)

### أوامر Git

```bash
# الرجوع للنسخ المستقرة
git checkout tags/v2.1-pos-stable       # POS Stable 🛡️
git checkout tags/v1.2-omnichannel-production-ready  # Omnichannel كاملة
git checkout tags/v1.0-stable-meta-approved           # النسخة الأساسية

# Pre-push hook
git config core.hooksPath .githooks
```

### المتغيرات البيئية (Environment Variables)

| المتغير | الوصف |
|---------|-------|
| `DATABASE_URL` | PostgreSQL connection string (Neon) |
| `DB_ENGINE` | `postgres` (إنتاج) / `sqlite` (تطوير) |
| `AI_MODEL` | موديل AI (مثل `Qwen/Qwen3-VL-30B-A3B-Instruct`) |
| `AI_API_KEY` | مفتاح AI API |
| `AI_SYSTEM_PROMPT` | System Prompt (يُقرأ من Environment Variable) |
| `DASHBOARD_USER` / `DASHBOARD_PASS` | Basic Auth للـ Dashboard |
| `SHOPIFY_CATALOG_TOKEN` | Token الـ Shopify للـ Products |
| `SHOPIFY_ORDERS_TOKEN` | Token الـ Shopify للـ Orders |
| `PLATFORM_DOMAIN` | الدومين الرئيسي للمنصة (مثل `rcagents.space`) |
| `NOTION_TOKEN` | Token الـ Notion لمزامنة ROADMAP |
| `NOTION_PAGE_ID` | ID صفحة Notion للـ Roadmap |

### المسارات العامة (Public API — لا تحتاج Auth)

| المسار | الوصف |
|--------|-------|
| `GET /health` | فحص صحة السيرفر |
| `POST /api/tenant/onboard` | تسجيل تاجر جديد (بدون Auth) |
| `POST /api/tenant/login` | تسجيل دخول التاجر (بدون Auth) |
| `GET /onboard` | صفحة تسجيل التاجر |
| `GET /dashboard/login` | صفحة تسجيل الدخول |
| `GET /dashboard/<id>` | Dashboard المتجر (بدون Auth) |
| `GET /dashboard` | Dashboard عبر Subdomain (بدون Auth) |
| `GET /api/stats?store_id=` | إحصائيات المتجر (بدون Auth مع store_id) |
| `GET /api/orders?store_id=` | طلبات المتجر (بدون Auth مع store_id) |
| `GET /api/clients?store_id=` | عملاء المتجر (بدون Auth مع store_id) |
| `GET /api/messages?store_id=` | رسائل المتجر (بدون Auth مع store_id) |
| `GET /api/store/<id>` | معلومات المتجر (بدون Auth) |
| `POST /webhook` | Webhook Facebook/Instagram |
| `POST /whatsapp/webhook` | Webhook WhatsApp |

---

> **🚀 هذه الخارطة هي مرجعنا الدائم. كل جلسة جديدة نبدأ بقراءتها ونحدثها بعد أي إنجاز أو قرار مهم.**

> _صنع بـ ❤️ بواسطة Louve لـ RC Mustapha و Royal Chaussures_
