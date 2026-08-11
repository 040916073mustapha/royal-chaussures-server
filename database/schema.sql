-- ============================================================
-- Royal Chaussures — Unified Database Schema
-- ============================================================
-- المخزون الموحد بين المحل الفيزيائي و المتجر الإلكتروني

-- 🔹 المستخدمين والأدوار
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'store_manager')),
    store_id INTEGER DEFAULT NULL,          -- NULL للـ Super Admin
    display_name TEXT,
    permissions JSON DEFAULT '[]',           -- ["store:products:*", ...]
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 المنتجات الأساسية (مشتركة بين المحل و الأونلاين)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,                 -- رمز المنتج (بين المحل و الأونلاين)
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT '',
    color TEXT DEFAULT '',
    size TEXT DEFAULT '',
    cost_price DECIMAL(10,2) DEFAULT 0,      -- سعر الشراء (للمحل فقط)
    online_price DECIMAL(10,2) DEFAULT 0,     -- سعر البيع أونلاين
    store_price DECIMAL(10,2) DEFAULT 0,      -- سعر البيع في المحل
    supplier TEXT DEFAULT '',
    barcode TEXT UNIQUE,                      -- باركود المنتج
    barcode_symbology TEXT DEFAULT 'CODE128', -- نوع الباركود
    image_url TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 المخزون (لحظي — sync بين المحل و الأونلاين)
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    store_quantity INTEGER DEFAULT 0,         -- مخزون المحل الفيزيائي
    online_quantity INTEGER DEFAULT 0,        -- مخزون الأونلاين (Shopify)
    warehouse_quantity INTEGER DEFAULT 0,     -- مخزون المستودع
    low_stock_threshold INTEGER DEFAULT 5,    -- حد التنبيه عند نفاد المخزون
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id)
);

-- 🔹 مبيعات المحل (خاصة بـ POS)
CREATE TABLE IF NOT EXISTS store_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    payment_method TEXT DEFAULT 'cash',       -- cash, card, bank_transfer
    notes TEXT DEFAULT '',
    store_id INTEGER NOT NULL,
    cashier TEXT NOT NULL,                    -- اسم الكاشير (مدير المحل)
    customer_phone TEXT DEFAULT '',
    customer_name TEXT DEFAULT '',
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced INTEGER DEFAULT 1,                -- Offline sync flag
    receipt_number TEXT UNIQUE
);

-- 🔹 مصاريف المحل
CREATE TABLE IF NOT EXISTS store_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,                   -- rent, utilities, salary, supply, other
    amount DECIMAL(10,2) NOT NULL,
    description TEXT DEFAULT '',
    store_id INTEGER NOT NULL,
    recorded_by TEXT NOT NULL,
    expense_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 الطلبات الأونلاين (من Shopify)
CREATE TABLE IF NOT EXISTS online_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shopify_order_id TEXT UNIQUE,
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 التزامن بين المحل و الأونلاين (سجل العمليات)
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,                -- product, sale, inventory
    entity_id INTEGER,
    action TEXT NOT NULL,                     -- create, update, delete
    source TEXT NOT NULL,                     -- store, online, admin
    details JSON DEFAULT '{}',
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 باركود المنتجات (سجل الطباعة)
-- 🔹 مشتريات المحل (تموين المخزون)
CREATE TABLE IF NOT EXISTS store_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier TEXT DEFAULT 'divers',
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0,
    notes TEXT DEFAULT '',
    store_id INTEGER NOT NULL DEFAULT 1,
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
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    printed_by TEXT NOT NULL,
    printed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_store_sales_date ON store_sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_store_sales_store ON store_sales(store_id);
CREATE INDEX IF NOT EXISTS idx_store_purchases_date ON store_purchases(purchase_date);
CREATE INDEX IF NOT EXISTS idx_store_purchase_items_purchase ON store_purchase_items(purchase_id);
CREATE INDEX IF NOT EXISTS idx_online_orders_status ON online_orders(status);
CREATE INDEX IF NOT EXISTS idx_online_orders_created ON online_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
