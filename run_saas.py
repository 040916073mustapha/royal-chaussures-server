"""
RC Agents — SaaS Core Runner (Entry Point)
Works from any execution context: gunicorn, python run_saas.py, python -m run_saas
"""

import os
import sys

# Always ensure the workspace root is on sys.path
_cwd = os.getcwd()
_script_dir = os.path.dirname(os.path.abspath(__file__))

for _p in (_script_dir, _cwd, os.path.abspath(".")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

__all__ = ["app"]

from rcgents_saas_core import create_app

app = create_app()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv("PORT", "5050"))
    logger = logging.getLogger("saas-core")
    logger.info(f"🚀 RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
