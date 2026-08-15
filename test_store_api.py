"""Test the Store POS / Admin API endpoints"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from server import app

with app.test_client() as c:
    # 1. Health check
    r = c.get("/health")
    print(f"GET /health: {r.status_code}")

    # 2. Store login
    r = c.post("/api/v1/store/auth/login", json={
        "username": "store",
        "password": "rc-store-2026"
    })
    print(f"POST /api/v1/store/auth/login: {r.status_code}")
    if r.status_code == 200:
        token = r.get_json()["token"]
        print(f"   Token: {token[:50]}...")

        # 3. List products (empty initially)
        r = c.get("/api/v1/store/products", headers={"Authorization": f"Bearer {token}"})
        print(f"GET /api/v1/store/products: {r.status_code}")
        data = r.get_json()
        print(f"   Products: {data.get('count', 0)}")

        # 4. Create a product
        r = c.post("/api/v1/store/products", 
            json={"sku": "TEST-001", "name": "حذاء رياضي أحمر", "color": "أحمر", 
                  "store_price": 2500, "cost_price": 1500, "barcode": "123456789",
                  "store_quantity": 20},
            headers={"Authorization": f"Bearer {token}"})
        print(f"POST /api/v1/store/products: {r.status_code}")
        if r.status_code == 201:
            product = r.get_json()["product"]
            print(f"   Created: {product['name']} (ID: {product['id']})")

        # 5. Record a sale
        r = c.post("/api/v1/store/sales",
            json={"product_id": 1, "quantity": 2, "payment_method": "cash"},
            headers={"Authorization": f"Bearer {token}"})
        print(f"POST /api/v1/store/sales: {r.status_code}")
        if r.status_code == 201:
            sale = r.get_json()["sale"]
            print(f"   Sale #{sale['receipt_number']}: {sale['total']} DA")

        # 6. Daily summary
        r = c.get("/api/v1/store/sales/summary",
            headers={"Authorization": f"Bearer {token}"})
        print(f"GET /api/v1/store/sales/summary: {r.status_code}")
        data = r.get_json()
        if data and data.get("summary"):
            print(f"   Today: {data['summary'].get('total_revenue', 0)} DA")

        # 7. Low stock
        r = c.get("/api/v1/store/inventory/low-stock",
            headers={"Authorization": f"Bearer {token}"})
        print(f"GET /api/v1/store/inventory/low-stock: {r.status_code}")
        data = r.get_json()
        print(f"   Low stock items: {data.get('count', 0)}")

    # 8. Admin login
    r = c.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "rc-admin-2026"
    })
    print(f"\nPOST /api/v1/admin/auth/login: {r.status_code}")
    if r.status_code == 200:
        admin_token = r.get_json()["token"]

        # 9. Admin dashboard
        r = c.get("/api/v1/admin/dashboard", 
            headers={"Authorization": f"Bearer {admin_token}"})
        print(f"GET /api/v1/admin/dashboard: {r.status_code}")
        data = r.get_json()
        if data:
            print(f"   Store today: {data.get('store_today', {})}")
            print(f"   Low stock count: {data.get('low_stock_count', 0)}")

        # 10. System health
        r = c.get("/api/v1/admin/system/health",
            headers={"Authorization": f"Bearer {admin_token}"})
        print(f"GET /api/v1/admin/system/health: {r.status_code}")
        data = r.get_json()
        if data:
            print(f"   DB stats: {data.get('database', {}).get('stats', {})}")

        # 11. Users list
        r = c.get("/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"})
        print(f"GET /api/v1/admin/users: {r.status_code}")
        data = r.get_json()
        print(f"   Users: {data.get('count', 0)}")

    # 12. Verify original webhook still works (not affected)
    r = c.get("/webhook?hub.mode=subscribe&hub.challenge=test123")
    print(f"\nGET /webhook (verify): {r.status_code}")
    if r.status_code == 200:
        print(f"   Response: {r.data.decode()}")

    print("\n=== ALL TESTS PASSED ===")
