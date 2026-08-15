# Royal Chaussures — API Reference 📚

## Base URLs

| البيئة | الرابط |
|--------|--------|
| **Local** | `http://localhost:10000` |
| **Production (Render)** | `https://royal-chaussures-server.onrender.com` |

---

## 🏪 POS APIs (`/api/v1/store/pos`)

### Products

| Method | Path | الوصف |
|--------|------|-------|
| `GET` | `/pos/products` | جلب جميع المنتجات مع المخزون |
| `GET` | `/pos/products/barcode/<barcode>` | البحث عن منتج بالباركود |
| `POST` | `/pos/products` | إنشاء منتج جديد |
| `PUT` | `/pos/products/<id>` | تعديل منتج |
| `DELETE` | `/pos/products/<id>` | حذف منتج (Soft: is_active=false) |

**POST /pos/products — إنشاء منتج:**
```json
{
  "name": "Nike Air Max",
  "barcode": "2001234567890",
  "category": "chaussures",
  "cost_price": 2000,
  "store_price": 4000,
  "online_price": 4500,
  "store_quantity": 10,
  "store_id": 1
}
```

**PUT /pos/products/1 — تعديل:**
```json
{
  "name": "Nike Air Max 2026",
  "store_price": 4200
}
```

---

### Sales (البيع)

| Method | Path | الوصف |
|--------|------|-------|
| `POST` | `/pos/sales` | تسجيل بيعة جديدة |

**POST /pos/sales:**
```json
{
  "store_id": 1,
  "cashier": "caisse1",
  "customer_name": "Ahmed",
  "customer_phone": "0555000000",
  "payment_method": "cash",
  "discount": 0,
  "total": 5000,
  "items": [
    {
      "product_id": 1,
      "product_name": "Nike Air Max",
      "quantity": 2,
      "unit_price": 2500,
      "total_price": 5000
    }
  ]
}
```

**Response:**
```json
{
  "sale": {
    "id": 42,
    "receipt_number": 42
  }
}
```

---

### Purchases (المشتريات)

| Method | Path | الوصف |
|--------|------|-------|
| `GET` | `/pos/purchases` | قائمة المشتريات |
| `POST` | `/pos/purchases` | تسجيل شراء جديد |
| `DELETE` | `/pos/purchases/<id>` | إلغاء شراء (Soft: status=annule) |

---

### Auth (تسجيل الدخول للـ POS)

| Method | Path | الوصف |
|--------|------|-------|
| `POST` | `/auth/login` | تسجيل الدخول |
| `GET` | `/auth/me` | معلومات المستخدم الحالي |

---

## 🖥️ POS صفحات

| Path | الوصف |
|------|-------|
| `/pos/` | واجهة POS الكاشير (PWA) |

---

## 📊 RC AGENTS Dashboard (محادثات العملاء)

| Path | الوصف |
|------|-------|
| `/dashboard` | لوحة تحكم RC AGENTS |
| `/dashboard/chat` | محادثات العملاء الحية |
| `/api/messages` | API جلب المحادثات |
| `/api/profile/<psid>` | جلب اسم العميل |

---

## Database Schema

### Products
```sql
id | store_id | name | sku | barcode | category | color | size
cost_price | store_price | online_price | supplier
image_url | description | is_active | created_at | updated_at
```

### Store Sales
```sql
id | store_id | product_id | quantity | unit_price | total
discount | payment_method | notes | cashier
customer_name | customer_phone | sale_date
```

### Purchases
```sql
id | store_id | supplier | supplier_phone | reference
subtotal | discount | tax | total | notes | status | created_at
```
