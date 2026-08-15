"""Debug: Check why store endpoints return 401"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from server import app

with app.test_client() as c:
    # Login first
    r = c.post("/api/v1/store/auth/login", json={
        "username": "store", "password": "rc-store-2026"
    })
    print(f"Login: {r.status_code}")
    if r.status_code == 200:
        token = r.get_json()["token"]
        
        # Try getting products with token as Bearer
        r = c.get("/api/v1/store/products", 
            headers={"Authorization": f"Bearer {token}"})
        print(f"  Products with Bearer: {r.status_code}")
        print(f"  Response: {r.get_json()}")
        
        # Try with different header format
        r = c.get("/api/v1/store/products",
            headers={"authorization": f"Bearer {token}"})
        print(f"  Products with lowercase: {r.status_code}")
        
        # Check if its the before_request blocking
        r = c.get("/api/v1/store/products",
            headers={"Authorization": f"Bearer {token}"},
            environ_base={"REMOTE_ADDR": "127.0.0.1"})
        print(f"  With environ_base: {r.status_code}")

    # Check what the before_request sees
    with app.test_request_context("/api/v1/store/products", 
            headers={"Authorization": f"Bearer {token if r.status_code == 200 else ''}"}):
        from flask import request, g
        print(f"\n  Path: {request.path}")
        print(f"  Auth header: {request.headers.get('Authorization', '(none)')[:30]}...")
        print(f"  _AUTH_SAFE_PATHS check...")
        
        # Manually check what the before_request does
        path = request.path.rstrip("/")
        for safe in ("/health", "/webhook", "/whatsapp/webhook", "/", "/api/chatbot", "/api/v1"):
            if path == safe or path.startswith(safe + "/"):
                print(f"  MATCHED safe: {safe}")
