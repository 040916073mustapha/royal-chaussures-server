#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Dashboard Blueprint v2.0
============================================
Clean rebuild: each route renders its template directly.
No middleware interference. Halal routes only. 🕌✨
"""

from flask import Blueprint, render_template, request
import logging

logger = logging.getLogger("royal-server")

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _get_store_id():
    """استخراج store_id من subdomain أو query param"""
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


# ============================================================
# HOMEPAGE
# ============================================================
@dashboard_bp.route("")
def overview():
    """Main dashboard overview"""
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] overview() called. store_id={store_id}")
    return render_template("dashboard.html", active="dashboard", store_id=store_id)


@dashboard_bp.route("/")
def overview_slash():
    return overview()


# ============================================================
# CORE PAGES
# ============================================================
@dashboard_bp.route("/orders")
def orders():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] orders() called. store_id={store_id}")
    return render_template("orders.html", active="orders", store_id=store_id)


@dashboard_bp.route("/products")
def products():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] products() called. store_id={store_id}")
    return render_template("products.html", active="products", store_id=store_id)


@dashboard_bp.route("/clients")
def clients():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] clients() called. store_id={store_id}")
    return render_template("clients.html", active="clients", store_id=store_id)


@dashboard_bp.route("/settings")
def settings():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] settings() called. store_id={store_id}")
    settings_data = {
        "zr_express": {
            "status": "متصل",
            "tenant_id": "d2217f31-20f1-43c6-abd4-c420788a63ed",
            "last_sync": "منذ دقيقة",
            "server_status": "نشط"
        },
        "automations": {
            "status": "نشط",
            "items": [
                {"icon": "💬", "name": "WhatsApp - تأكيد الطلبات", "badge": "تلقائي"},
                {"icon": "📦", "name": "إشعارات الشحن", "badge": "تلقائي"},
                {"icon": "📊", "name": "تقرير الصباح اليومي", "badge": "09:00 صباحاً"}
            ]
        },
        "ai_agent": {
            "status": "متصل",
            "model": "DeepSeek-V4-Flash",
            "platforms": [
                {"name": "Messenger", "cls": "bg-blue-500/15 text-blue-400"},
                {"name": "WhatsApp", "cls": "bg-green-500/15 text-green-400"},
                {"name": "Instagram", "cls": "bg-pink-500/15 text-pink-400"}
            ],
            "agents_link": "/dashboard/agents"
        },
        "shopify": {
            "status": "متصل",
            "store": "rwqchh-na.myshopify.com",
            "auto_sync": "مفعلة",
            "last_sync": "منذ دقيقة",
            "products": 47
        }
    }
    return render_template(
        "settings.html", active="settings", store_id=store_id, **settings_data
    )


# ============================================================
# AI & COMMUNICATION
# ============================================================
@dashboard_bp.route("/agents")
def agents():
    """AI Agents Management Dashboard"""
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] agents() called. store_id={store_id}")
    try:
        rendered = render_template("agents_dashboard.html", store_id=store_id)
        logger.info(
            f"[DASHBOARD] agents_dashboard.html rendered: {len(rendered)} bytes"
        )
        if len(rendered) < 5000:
            logger.warning(f"[DASHBOARD] agents page too small! First 200: {rendered[:200]}")
        return rendered
    except Exception as e:
        logger.error(f"[DASHBOARD] agents() error: {e}")
        return f"<h1>Template Error: {e}</h1>", 500


@dashboard_bp.route("/chat")
def chat():
    """Live Chat Console"""
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] chat() called. store_id={store_id}")
    try:
        return render_template("chat_console.html", store_id=store_id)
    except Exception as e:
        logger.error(f"[DASHBOARD] chat() error: {e}")
        return f"<h1>Template Error: {e}</h1>", 500


# ============================================================
# INTELLIGENCE
# ============================================================
@dashboard_bp.route("/analytics")
def analytics():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] analytics() called. store_id={store_id}")
    return render_template("dashboard.html", active="analytics", store_id=store_id)


@dashboard_bp.route("/marketing")
def marketing():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] marketing() called. store_id={store_id}")
    return render_template("dashboard.html", active="marketing", store_id=store_id)


@dashboard_bp.route("/inventory")
def inventory():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] inventory() called. store_id={store_id}")
    return render_template("dashboard.html", active="inventory", store_id=store_id)


# ============================================================
# OPERATIONS
# ============================================================
@dashboard_bp.route("/shipments")
def shipments():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] shipments() called. store_id={store_id}")
    return render_template("dashboard.html", active="shipping", store_id=store_id)


@dashboard_bp.route("/auto-ship")
def auto_ship():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] auto_ship() called. store_id={store_id}")
    return render_template("dashboard.html", active="auto-ship", store_id=store_id)


@dashboard_bp.route("/tracking")
def tracking():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] tracking() called. store_id={store_id}")
    return render_template("tracking.html", store_id=store_id)


# ============================================================
# SYSTEM
# ============================================================
@dashboard_bp.route("/constellation")
def constellation():
    store_id = _get_store_id()
    logger.info(f"[DASHBOARD] constellation() called. store_id={store_id}")
    return render_template("dashboard.html", active="integrations", store_id=store_id)


@dashboard_bp.route("/login")
def login():
    return render_template("dashboard_login.html")
