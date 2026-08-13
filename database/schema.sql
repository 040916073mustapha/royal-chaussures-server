-- ============================================================
-- Nexus POS — Unified Multi-Tenant Database Schema
-- ============================================================
-- متعددة المتاجر (Multi-Tenant) مع عزل تام لبيانات كل تاجر
-- Royal Chaussures = store_id = 1 (الافتراضي)

-- 🔹 المتاجر (Nexus POS Multi-Tenant)
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    domain TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    address TEXT DEFAULT '',
    logo_url TEXT DEFAULT '',
    subscription_tier TEXT DEFAULT 'free',   -- free, basic, pro, enterprise
    subscription_status TEXT DEFAULT 'active', -- active, suspended, cancelled
    features JSON DEFAULT '{}',              -- enabled features per store
    settings JSON DEFAULT '{}',              -- store-specific settings
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 المستخدمين والأدوار
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'store_manager')),
    store_id INTEGER DEFAULT NULL REFERENCES stores(id), -- NULL للـ Super Admin
    display_name TEXT,
    permissions JSON DEFAULT '[]',           -- ["store:products:*", ...]
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, username)
);

-- 🔹 المنتجات الأساسية (مشتركة بين المحل و الأونلاين)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    sku TEXT NOT NULL,                        -- رمز المنتج (مع store_id يصبح UNIQUE)
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT '',
    color TEXT DEFAULT '',
    size TEXT DEFAULT '',
    cost_price DECIMAL(10,2) DEFAULT 0,      -- سعر الشراء (للمحل فقط)
    online_price DECIMAL(10,2) DEFAULT 0,     -- سعر البيع أونلاين
    store_price DECIMAL(10,2) DEFAULT 0,      -- سعر البيع في المحل
    supplier TEXT DEFAULT '',
    barcode TEXT,                             -- باركود المنتج (مع store_id يصبح UNIQUE)
    barcode_symbology TEXT DEFAULT 'CODE128', -- نوع الباركود
    image_url TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, sku),
    UNIQUE(store_id, barcode)
);

-- 🔹 المخزون (لحظي — sync بين المحل و الأونلاين)
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_quantity INTEGER DEFAULT 0,         -- مخزون المحل الفيزيائي
    online_quantity INTEGER DEFAULT 0,        -- مخزون الأونلاين (Shopify)
    warehouse_quantity INTEGER DEFAULT 0,     -- مخزون المستودع
    low_stock_threshold INTEGER DEFAULT 5,    -- حد التنبيه عند نفاد المخزون
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, product_id)
);

-- 🔹 مبيعات المحل (خاصة بـ POS)
CREATE TABLE IF NOT EXISTS store_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL REFERENCES stores(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    payment_method TEXT DEFAULT 'cash',       -- cash, card, bank_transfer
    notes TEXT DEFAULT '',
    cashier TEXT NOT NULL,                    -- اسم الكاشير (مدير المحل)
    customer_phone TEXT DEFAULT '',
    customer_name TEXT DEFAULT '',
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced INTEGER DEFAULT 1,                -- Offline sync flag
    receipt_number TEXT,
    UNIQUE(store_id, receipt_number)
);

-- 🔹 مصاريف المحل
CREATE TABLE IF NOT EXISTS store_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL REFERENCES stores(id),
    category TEXT NOT NULL,                   -- rent, utilities, salary, supply, other
    amount DECIMAL(10,2) NOT NULL,
    description TEXT DEFAULT '',
    recorded_by TEXT NOT NULL,
    expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 الطلبات الأونلاين (من Shopify)
CREATE TABLE IF NOT EXISTS online_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    shopify_order_id TEXT,
    order_number TEXT,
    customer_name TEXT DEFAULT '',
    customer_phone TEXT DEFAULT '',
    customer_email TEXT DEFAULT '',
    customer_address TEXT DEFAULT '',
    wilaya TEXT DEFAULT '',
    commune TEXT DEFAULT '',
    total DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) DEFAULT 0,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) DEFAULT 0,
    status TEXT DEFAULT 'pending',            -- pending, paid, shipped, delivered, cancelled
    payment_status TEXT DEFAULT 'pending',
    shipping_status TEXT DEFAULT 'pending',
    items JSON DEFAULT '[]',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, shopify_order_id)
);

-- 🔹 التزامن بين المحل و الأونلاين (سجل العمليات)
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    entity_type TEXT NOT NULL,                -- product, sale, inventory
    entity_id INTEGER,
    action TEXT NOT NULL,                     -- create, update, delete
    source TEXT NOT NULL,                     -- store, online, admin
    details JSON DEFAULT '{}',
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 مشتريات المحل (تموين المخزون)
CREATE TABLE IF NOT EXISTS store_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    supplier TEXT DEFAULT 'divers',
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0,
    notes TEXT DEFAULT '',
    recorded_by TEXT NOT NULL DEFAULT 'store',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 عناصر المشتريات (المنتجات المشتراة)
CREATE TABLE IF NOT EXISTS store_purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL REFERENCES store_purchases(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    barcode TEXT DEFAULT '',
    designation TEXT NOT NULL,
    prix_achat DECIMAL(10,2) NOT NULL,
    prix_vente DECIMAL(10,2) NOT NULL,
    quantite INTEGER NOT NULL DEFAULT 1,
    prix_total DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 باركود المنتجات (سجل الطباعة)
CREATE TABLE IF NOT EXISTS barcode_print_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    printed_by TEXT NOT NULL,
    printed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 رسائل العملاء (للتكامل مع الـ AI Agent)
CREATE TABLE IF NOT EXISTS saas_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL DEFAULT 1 REFERENCES stores(id),
    platform TEXT NOT NULL,                   -- telegram, messenger, whatsapp, instagram
    sender_id TEXT NOT NULL,
    sender_name TEXT DEFAULT '',
    message TEXT DEFAULT '',
    reply TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 جلسات التصفح/الـ API (اختياري)
CREATE TABLE IF NOT EXISTS api_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL REFERENCES stores(id),
    user_id INTEGER REFERENCES users(id),
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Indexes
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
CREATE INDEX IF NOT EXISTS idx_online_orders_created ON online_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_log_store ON sync_log(store_id);
CREATE INDEX IF NOT EXISTS idx_barcode_print_store ON barcode_print_log(store_id);
CREATE INDEX IF NOT EXISTS idx_saas_messages_store ON saas_messages(store_id);
CREATE INDEX IF NOT EXISTS idx_saas_messages_platform ON saas_messages(platform);
