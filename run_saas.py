"""
RC Agents â€” SaaS Core Entry Point (UNIVERSAL)
Works from any context: gunicorn, python run_saas.py, python -m run_saas
No assumptions about sys.path or PYTHONPATH needed.
"""

import os
import sys
import types
import importlib.util

__all__ = ["app"]

# â”€â”€â”€ Force AI_MODEL default before anything loads â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
os.environ.setdefault("AI_MODEL", "Qwen/Qwen3-VL-30B-A3B-Instruct")

# â”€â”€â”€ Force-load the package without relying on sys.path â”€â”€â”€â”€â”€â”€â”€â”€

def _bootstrap_package():
    """
    Bootstrap rcgents_saas_core as a proper Python package absolutely.
    Works regardless of sys.path, PYTHONPATH, or execution context.
    """
    # Find the package directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_dir = os.path.join(script_dir, "rcagents_saas_core")

    if not os.path.isdir(pkg_dir):
        # Fallback: try CWD
        pkg_dir = os.path.join(os.getcwd(), "rcagents_saas_core")

    if not os.path.isdir(pkg_dir):
        raise ImportError(
            f"Cannot find 'rcagents_saas_core' package directory. "
            f"Searched: {os.path.join(script_dir, 'rcagents_saas_core')}"
        )

    pkg_name = "rcagents_saas_core"

    # Already loaded?
    if pkg_name in sys.modules:
        return sys.modules[pkg_name]

    # Create the top-level package module
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [pkg_dir]
    pkg.__file__ = os.path.join(pkg_dir, "__init__.py")
    pkg.__package__ = pkg_name
    sys.modules[pkg_name] = pkg

    # Bootstrap sub-packages
    for sub in ("api", "database", "ai"):
        sub_dir = os.path.join(pkg_dir, sub)
        sub_name = f"{pkg_name}.{sub}"
        if os.path.isdir(sub_dir) and sub_name not in sys.modules:
            sub_mod = types.ModuleType(sub_name)
            sub_mod.__path__ = [sub_dir]
            sub_mod.__file__ = os.path.join(sub_dir, "__init__.py")
            sub_mod.__package__ = sub_name
            sys.modules[sub_name] = sub_mod

    # Now load __init__.py (which does `from .app import create_app`)
    init_path = os.path.join(pkg_dir, "__init__.py")
    spec = importlib.util.spec_from_file_location(pkg_name, init_path, submodule_search_locations=[pkg_dir])
    if spec and spec.loader:
        spec.loader.exec_module(pkg)

    return sys.modules[pkg_name]


# â”€â”€â”€ Bootstrap and create the Flask app â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_pkg = _bootstrap_package()
app = _pkg.create_app()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv("PORT", "5050"))
    logger = logging.getLogger("saas-core")
    logger.info(f"ðŸš€ RC Agents SaaS Core starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
