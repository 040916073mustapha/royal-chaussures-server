"""Test app imports and routes"""
from app import create_app
app = create_app()
print("✅ App loaded successfully")
print("Routes:")
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    methods = r.methods - {"OPTIONS", "HEAD"}
    if methods:
        print(f"  {sorted(methods)} {r.rule}")
