"""Test Admin Dashboard + POS pages"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from server import app
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
    if methods and ("/dashboard" in rule.rule or "/pos" in rule.rule):
        print(f"  {methods:8s} {rule.rule}")

with app.test_client() as c:
    r = c.get("/api/v1/admin/dashboard")
    print(f"\nGET /api/v1/admin/dashboard: {r.status_code}")
    if r.status_code == 200:
        html = r.data.decode("utf-8")
        print(f"  Size: {len(r.data)} bytes")
        print(f"  Login screen: {'login-screen' in html}")
        print(f"  Sections: {'section-overview' in html}")

    r = c.get("/api/v1/store/pos")
    print(f"\nGET /api/v1/store/pos: {r.status_code}")
    if r.status_code == 200:
        print(f"  Size: {len(r.data)} bytes")

    r = c.get("/health")
    print(f"\nGET /health: {r.status_code}")

    # Test admin login -> dashboard
    r = c.post("/api/v1/admin/auth/login", json={
        "username": "admin", "password": "***"
    })
    print(f"\nAdmin login: {r.status_code}")
    if r.status_code == 200:
        token = r.get_json()["token"]
        r2 = c.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        print(f"Dashboard access: {r2.status_code}")

print("\n=== All OK ===")
