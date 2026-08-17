"""Test Phase 2 — POS PWA"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from server import app

# Count routes
store_routes = []
admin_routes = []
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
    if "/api/v1/store" in rule.rule:
        store_routes.append((methods, rule.rule))
    elif "/api/v1/admin" in rule.rule:
        admin_routes.append((methods, rule.rule))

print(f"Store POS Routes ({len(store_routes)}):")
for m, r in store_routes:
    print(f"  {m:8s} {r}")

print(f"\nAdmin Dashboard Routes ({len(admin_routes)}):")
for m, r in admin_routes:
    print(f"  {m:8s} {r}")

# Test POS page
with app.test_client() as c:
    r = c.get("/api/v1/store/pos")
    print(f"\nGET /api/v1/store/pos: {r.status_code}")
    if r.status_code == 200:
        html = r.data.decode("utf-8")
        print(f"  Content-Type: {r.content_type}")
        print(f"  Size: {len(r.data)} bytes")
        print(f"  Has login screen: {'login-screen' in html}")
        print(f"  Has pos-app: {'pos-app' in html}")
        print(f"  Has JS engine: {'pos.js' in html}")
        print(f"  Has manifest: {'manifest.json' in html}")
    
    # Health
    r = c.get("/health")
    print(f"\nGET /health: {r.status_code}")

    # Webhook still works
    r = c.get("/webhook?hub.mode=subscribe&hub.challenge=test123")
    print(f"GET /webhook: {r.status_code}")

print("\n=== Phase 2 Test Complete ===")
