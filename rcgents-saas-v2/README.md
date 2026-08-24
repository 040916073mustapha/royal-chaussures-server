# 🚀 RC Agents v2 — Multi-Tenant AI Automation Platform

**5 AI Agents** powering e-commerce stores across Messenger, WhatsApp, Instagram, and Shopify.

## 🏗️ Architecture

```
rcagents-saas-v2/
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # pydantic-settings env management
│   ├── database/         # SQLAlchemy models + CRUD (multi-tenant)
│   ├── routers/          # Webhooks: Meta, WhatsApp, Shopify, Dashboard API
│   ├── services/         # AI Handler, Shopify client, Shipping, Agent Manager
│   └── utils/            # Security (HMAC, signatures)
├── templates/            # Landing, Privacy, Terms, Dashboard
├── static/               # CSS/JS assets
├── .env.example
├── requirements.txt
├── Procfile
└── README.md
```

## 🤖 The 5 Agents

| Agent | Role |
|-------|------|
| 🛒 Sales | Product inquiries, recommendations, closing sales |
| 🆘 Support | Returns, exchanges, order issues |
| 📦 Inventory | Real-time stock tracking, low-stock alerts |
| 🚚 Shipping | ZR Express rates, labels, tracking (58 wilayas) |
| 📢 Marketing | Campaigns, abandoned cart recovery, promotions |

## 🔐 Multi-Tenant

Every table is scoped by `store_id`. Isolated data per tenant.
Tenant #1: **Royal Chaussures** (slug: `royal-chaussures`)

## 🚀 Deploy

```bash
# 1. Clone & install
pip install -r requirements.txt

# 2. Copy env
cp .env.example .env

# 3. Run
uvicorn app.main:app --reload
```

## 📦 Deploy to Railway

1. Push to GitHub
2. Connect Railway project → repo
3. Set `DATABASE_URL` via Railway PostgreSQL plugin (`${{DATABASE_URL}}`)
4. Set all env vars from `.env.example`
5. Deploy 🚀

## 🔗 Channels

- **Messenger**: `/webhooks/messenger`
- **Instagram**: `/webhooks/instagram`
- **WhatsApp**: `/webhooks/whatsapp`
- **Shopify**: `/webhooks/shopify`

---

© 2026 RC Agents — A Royal Chaussures Technology
