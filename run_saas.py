"""
RC Agents — SaaS Core Runner (Entry Point)
Use this file to run the SaaS Core application.
"""

import os
import sys

# Add the workspace root to Python path
workspace_root = os.path.dirname(os.path.abspath(__file__))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from rcgents_saas_core.app import app, Config
import logging

logger = logging.getLogger("saas-core")

if __name__ == "__main__":
    port = int(os.getenv("PORT", Config.DASHBOARD_PORT))
    logger.info(f"🚀 RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
