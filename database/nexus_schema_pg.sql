-- ============================================================
-- Nexus POS — PostgreSQL Schema (Neon-Ready)
-- ============================================================
-- Multi-Tenant SaaS Schema for PostgreSQL
-- متوافق مع SQLite schema.sql لكن مع ميزات PostgreSQL

-- لضمان UUID generation إذا احتجنا
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 🔹 المتاجر (Nexus POS Multi-Tenant)
-- ============================================================
CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255) DEFAULT '',
    email VARCHAR(255) DEFAULT '',
    phone VARCHAR(50) DEFAULT '',
    address TEXT DEFAULT '',
    logo_url TEXT DEFAULT '',
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    features JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    trial_ends_at TIMESTAMP,                          -- تاريخ انتهاء الفترة التجريبية
    subscribed_at TIMESTAMP,                           -- تاريخ بداية الاشتراك المدفوع
    next_billing_at TIMESTAMP,                         -- تاريخ التجديد القادم
    billing_period VARCHAR(20) DEFAULT 'monthly',      -- monthly, yearly
    baridi_ccp VARCHAR(50) DEFAULT '',                 -- رقم CCP للتاجر
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 المستخدمين والأدوار
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'store_manager')),
    store_id INTEGER DEFAULT NULL REFERENCES stores(id) ON DELETE CASCADE,
    display_name VARCHAR(255),
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(store_id, username)
);

-- ============================================================
-- 🔹 المنتجات الأساسية (مشتركة بين المحل و الأونلاين)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    sku VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    category VARCHAR(100) DEFAULT '',
    color VARCHAR(100) DEFAULT '',
    size VARCHAR(50) DEFAULT '',
    cost_price DECIMAL(10,2) DEFAULT 0,
    online_price DECIMAL(10,2) DEFAULT 0,
    store_price DECIMAL(10,2) DEFAULT 0,
    supplier VARCHAR(255) DEFAULT '',
    barcode VARCHAR(255),
    barcode_symbology VARCHAR(50) DEFAULT 'CODE128',
    image_url TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(store_id, sku),
    UNIQUE(store_id, barcode)
);

-- ============================================================
-- 🔹 المخزون (لحظي — sync بين المحل و الأونلاين)
-- ============================================================
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_quantity INTEGER DEFAULT 0,
    online_quantity INTEGER DEFAULT 0,
    warehouse_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 5,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(store_id, product_id)
);

-- ============================================================
-- 🔹 مبيعات المحل (خاصة بـ POS)
-- ============================================================
CREATE TABLE IF NOT EXISTS store_sales (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    payment_method VARCHAR(50) DEFAULT 'cash',
    notes TEXT DEFAULT '',
    cashier VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50) DEFAULT '',
    customer_name VARCHAR(255) DEFAULT '',
    sale_date TIMESTAMP DEFAULT NOW(),
    synced BOOLEAN DEFAULT TRUE,
    receipt_number VARCHAR(255),
    UNIQUE(store_id, receipt_number)
);

-- ============================================================
-- 🔹 مصاريف المحل
-- ============================================================
CREATE TABLE IF NOT EXISTS store_expenses (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT DEFAULT '',
    recorded_by VARCHAR(255) NOT NULL,
    expense_date TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 الطلبات الأونلاين (من Shopify)
-- ============================================================
CREATE TABLE IF NOT EXISTS online_orders (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    shopify_order_id VARCHAR(255),
    order_number VARCHAR(255),
    customer_name VARCHAR(255) DEFAULT '',
    customer_phone VARCHAR(50) DEFAULT '',
    customer_email VARCHAR(255) DEFAULT '',
    customer_address TEXT DEFAULT '',
    wilaya VARCHAR(100) DEFAULT '',
    commune VARCHAR(100) DEFAULT '',
    total DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) DEFAULT 0,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    payment_status VARCHAR(50) DEFAULT 'pending',
    shipping_status VARCHAR(50) DEFAULT 'pending',
    items JSONB DEFAULT '[]',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(store_id, shopify_order_id)
);

-- ============================================================
-- 🔹 التزامن (سجل العمليات)
-- ============================================================
CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    action VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}',
    synced_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 مشتريات المحل (تموين المخزون)
-- ============================================================
CREATE TABLE IF NOT EXISTS store_purchases (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    supplier VARCHAR(255) DEFAULT 'divers',
    purchase_date TIMESTAMP DEFAULT NOW(),
    total DECIMAL(12,2) DEFAULT 0,
    notes TEXT DEFAULT '',
    recorded_by VARCHAR(255) NOT NULL DEFAULT 'store',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 عناصر المشتريات
-- ============================================================
CREATE TABLE IF NOT EXISTS store_purchase_items (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL REFERENCES store_purchases(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    barcode VARCHAR(255) DEFAULT '',
    designation VARCHAR(255) NOT NULL,
    prix_achat DECIMAL(10,2) NOT NULL,
    prix_vente DECIMAL(10,2) NOT NULL,
    quantite INTEGER NOT NULL DEFAULT 1,
    prix_total DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 باركود — سجل الطباعة
-- ============================================================
CREATE TABLE IF NOT EXISTS barcode_print_log (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    printed_by VARCHAR(255) NOT NULL,
    printed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 رسائل العملاء (للتكامل مع الـ AI Agent)
-- ============================================================
CREATE TABLE IF NOT EXISTS saas_messages (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    sender_id VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255) DEFAULT '',
    message TEXT DEFAULT '',
    reply TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🔹 جلسات الـ API (اختياري)
-- ============================================================
CREATE TABLE IF NOT EXISTS api_sessions (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 🏆 Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_stores_slug ON stores(slug);
CREATE INDEX IF NOT EXISTS idx_users_store_id ON users(store_id);
CREATE INDEX IF NOT EXISTS idx_products_store ON products(store_id);
CREATE INDEX IF NOT EXISTS idx_products_store_sku ON products(store_id, sku);
CREATE INDEX IF NOT EXISTS idx_products_store_barcode ON products(store_id, barcode);
CREATE INDEX IF NOT EXISTS idx_inventory_store ON inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_inventory_store_product ON inventory(store_id, product_id);
CREATE INDEX IF NOT EXISTS idx_store_sales_store ON store_sales(store_id);
CREATE INDEX IF NOT EXISTS idx_store_sales_date ON store_sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_store_expenses_store ON store_expenses(store_id);
CREATE INDEX IF NOT EXISTS idx_store_purchases_store ON store_purchases(store_id);
CREATE INDEX IF NOT EXISTS idx_store_purchase_items_purchase ON store_purchase_items(purchase_id);
CREATE INDEX IF NOT EXISTS idx_online_orders_store ON online_orders(store_id);
CREATE INDEX IF NOT EXISTS idx_online_orders_status ON online_orders(status);
CREATE INDEX IF NOT EXISTS idx_sync_log_store ON sync_log(store_id);
CREATE INDEX IF NOT EXISTS idx_barcode_print_store ON barcode_print_log(store_id);
CREATE INDEX IF NOT EXISTS idx_saas_messages_store ON saas_messages(store_id);
CREATE INDEX IF NOT EXISTS idx_saas_messages_platform ON saas_messages(platform);
