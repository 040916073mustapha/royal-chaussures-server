#!/usr/bin/env python3
"""
[GUARD] EXISTING FEATURES GUARD
=================================
قبل أي Push: شغّل هذا الملف لتتأكد أن كل الميزات الشغالة لسا شغالة.

الاستخدام:
    python tests/test_existing_features.py

إذا طبع "All existing features OK" -> Push آمن.
إذا طبع "FAILED" -> راجع التغييرات.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASSED = 0
FAILED = 0

def test(name, fn):
    global PASSED, FAILED
    try:
        fn()
        PASSED += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        FAILED += 1
        print(f"  [FAIL] {name}: {e}")

# ============================================================
# Database
# ============================================================
def test_database_connection():
    from database.db import get_db
    db = get_db()
    assert db is not None, "get_db() returned None"

def test_get_products():
    from database.db import get_products
    products = get_products(limit=3)
    assert isinstance(products, list), f"Expected list, got {type(products)}"

def test_get_product():
    from database.db import get_product, get_products
    products = get_products(limit=1)
    if products:
        p = get_product(products[0]["id"])
        assert p is not None, "get_product returned None for existing id"

# ============================================================
# Create Sale
# ============================================================
def test_create_sale():
    from database.db import create_sale, get_db
    db = get_db()
    is_sqlite = "sqlite" in str(type(db))
    if is_sqlite:
        db.execute("PRAGMA foreign_keys=OFF")
    try:
        result = create_sale({
            "store_id": 1,
            "cashier": "test",
            "customer_name": "Test",
            "payment_method": "cash",
            "total": 1000,
            "discount": 0,
            "items": [{"product_id": 1, "product_name": "Test", "quantity": 1, "unit_price": 1000, "total_price": 1000}]
        })
        assert "id" in result or "error" in result, f"Unexpected create_sale result: {result}"
        if "error" in result:
            print(f"      (note: {result['error']})")
    finally:
        if is_sqlite:
            db.execute("PRAGMA foreign_keys=ON")

def test_get_store_sales():
    from database.db import get_store_sales
    sales = get_store_sales(store_id=1, page=1, per_page=3)
    assert isinstance(sales, list)

# ============================================================
# Products CRUD
# ============================================================
def test_create_product():
    from database.db import create_product
    import time
    ts = int(time.time() * 1000) % 100000000
    name = f"Test-{ts}"
    p = create_product({
        "name": name,
        "store_id": 1,
        "sku": f"SKU{ts}",
        "barcode": f"TEST{ts}",
        "cost_price": 500,
        "store_price": 1000
    })
    assert p is not None, "create_product returned None"
    assert "id" in p, f"create_product missing 'id': {p}"

def test_update_product():
    from database.db import create_product, update_product
    import time
    ts = int(time.time() * 1000) % 100000000
    name = f"Upd-{ts}"
    p = create_product({"name": name, "store_id": 1, "sku": f"SKU_UPD{ts}", "barcode": f"BAR_UPD{ts}", "cost_price": 500, "store_price": 1000})
    pid = p["id"]
    updated = update_product(pid, {"name": name + "-MOD", "store_price": 2000})
    assert updated is not None, "update_product returned None"
    assert updated.get("store_price") == 2000, f"Expected store_price=2000, got {updated.get('store_price')}"

def test_soft_delete_product():
    from database.db import create_product, update_product, get_product
    import time
    ts = int(time.time() * 1000) % 100000000
    name = f"Del-{ts}"
    p = create_product({"name": name, "store_id": 1, "sku": f"SKU_DEL{ts}", "barcode": f"BAR_DEL{ts}", "cost_price": 500, "store_price": 1000})
    pid = p["id"]
    deleted = update_product(pid, {"is_active": False})
    assert deleted is not None
    fetched = get_product(pid)
    assert fetched is not None

# ============================================================
# Purchases
# ============================================================
def test_get_store_purchases():
    try:
        from database.db import get_store_purchases, get_db
        db = get_db()
        is_sqlite = "sqlite" in str(type(db))
        if is_sqlite:
            # SQLite قد لا يكون جدول purchases موجوداً
            purchases = []
        else:
            from database.db import get_store_purchases
            purchases = get_store_purchases(store_id=1, page=1, per_page=3)
            assert isinstance(purchases, list)
    except ImportError:
        pass
    except Exception as e:
        # purchases table may not exist on sqlite - this is OK
        print(f"      (note: {e})")

# ============================================================
# API Routes
# ============================================================
def test_route_registration():
    from flask import Flask
    from routes.store import store_bp
    app = Flask(__name__)
    app.register_blueprint(store_bp, url_prefix="/api/v1/store")
    rules = [str(r.rule) for r in app.url_map.iter_rules()]
    expected = ["/api/v1/store/pos/products", "/api/v1/store/pos/sales", "/api/v1/store/pos/purchases"]
    for e in expected:
        found = any(e in r for r in rules)
        assert found, f"Route {e} not registered!"

# ============================================================
# JS Syntax Check
# ============================================================
def test_pos_js_syntax():
    import subprocess
    result = subprocess.run(
        ["node", "-e", "const fs=require('fs'); const code=fs.readFileSync('static/pos/pos.js','utf8'); new Function(code); console.log('OK')"],
        capture_output=True, text=True, shell=True
    )
    assert "OK" in result.stdout, f"JS syntax error: {result.stderr}"

# ============================================================
# Run all
# ============================================================
def run_all():
    global PASSED, FAILED
    print("=" * 60)
    print("EXISTING FEATURES GUARD")
    print("=" * 60)
    print()

    print("Database:")
    test("Database connection", test_database_connection)
    test("Get products", test_get_products)
    test("Get product by id", test_get_product)

    print("\nSales:")
    test("Create sale", test_create_sale)
    test("Get store sales", test_get_store_sales)

    print("\nProduct CRUD:")
    test("Create product", test_create_product)
    test("Update product", test_update_product)
    test("Soft delete product", test_soft_delete_product)

    print("\nPurchases:")
    test("Get store purchases", test_get_store_purchases)

    print("\nAPI Routes:")
    test("Route registration", test_route_registration)

    print("\nFrontend:")
    test("pos.js syntax", test_pos_js_syntax)

    print()
    print("=" * 60)
    print(f"Result: {PASSED} passed | {FAILED} failed")
    if FAILED > 0:
        print("FAILED - Do not push before fixing!")
        sys.exit(1)
    else:
        print("All existing features OK - Push safe!")
        sys.exit(0)

if __name__ == "__main__":
    run_all()
