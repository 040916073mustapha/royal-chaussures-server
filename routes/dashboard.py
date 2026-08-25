#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Dashboard Blueprint v3.0
============================================
SINGLE ROUTE architecture: /dashboard?view=<section>
No sub-path routes — eliminates ALL Flak sub-path routing issues.
One route to rule them all. 🎯
"""

from flask import Blueprint, render_template, request
import logging

logger = logging.getLogger("royal-server")

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
    template_folder="../templates",
    static_folder="../static"
)


def _get_store_id():
    """Extract store_id from subdomain or query param"""
    host = request.headers.get("Host", "")
    if host.count(".") >= 2:
        slug = host.split(".")[0]
        try:
            from database.db import get_store_by_slug
            store = get_store_by_slug(slug)
            if store:
                return store["id"]
        except Exception:
            pass
    return request.args.get("store_id", 1, type=int)


@dashboard_bp.route("")
def dashboard():
    """
    SINGLE dashboard route. View is determined by ?view=<section> query param.
    Default view: overview
    Supported views: overview, orders, products, clients, settings, agents, chat,
                     analytics, marketing, inventory, shipments, auto-ship,
                     tracking, constellation
    """
    store_id = _get_store_id()
    view = request.args.get("view", "overview")
    logger.info(f"[DASHBOARD] dashboard() called. view={view}, store_id={store_id}")

    # Validate view — fallback to overview
    valid_views = [
        "overview", "orders", "products", "clients", "settings", "agents",
        "chat", "analytics", "marketing", "inventory", "shipments",
        "auto-ship", "tracking", "constellation"
    ]
    if view not in valid_views:
        logger.warning(f"[DASHBOARD] Invalid view: {view}. Falling back to overview")
        view = "overview"

    return render_template("dashboard.html", active=view, store_id=store_id, view=view)


@dashboard_bp.route("/")
def dashboard_slash():
    return dashboard()
