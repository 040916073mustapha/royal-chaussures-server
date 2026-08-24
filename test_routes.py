import sys
import os
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(p, "rcagents_saas_core"))
os.chdir(os.path.join(p, "rcagents_saas_core"))

# Monkey-patch: make relative imports work
__package__ = "rcagents_saas_core"
from app import create_app

app = create_app()
print("OK")
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    methods = r.methods - {"OPTIONS", "HEAD"}
    if methods and r.rule.startswith("/api/"):
        print(f"  {sorted(methods)} {r.rule}")
