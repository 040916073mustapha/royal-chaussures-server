"""
RC Agents — SaaS Core Runner (Entry Point)
Clean, minimal launcher — adds the workspace root to sys.path,
then imports and runs the app.
"""

import os
import sys

# Ensure the workspace root is on sys.path so relative imports work
_workspace = os.path.dirname(os.path.abspath(__file__))
if _workspace not in sys.path:
    sys.path.insert(0, _workspace)

# Now import the app module (it uses relative imports internally)
from rcgents_saas_core import create_app

app = create_app()

if __name__ == "__main__":
    import logging
    from rcgents_saas_core.config import Config

    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv("PORT", Config.DASHBOARD_PORT))
    logging.getLogger("saas-core").info(f"🚀 RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
