"""
[pos] POS Blueprint Module
================================
كل ما يخص POS موجود هنا:
- المسار /pos → عرض الصفحة
- APIs: /pos/products, /pos/sales, /pos/purchases
- static files: pos/static/pos/
- template: pos/templates/pos/index.html
"""

import os
from flask import Blueprint, render_template, jsonify, request

_pos_bp = Blueprint(
    "pos",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/pos-static",
    url_prefix="/pos"
)


@_pos_bp.route("/")
def pos_page():
    """POS PWA - صفحة الكاشير"""
    return render_template("pos/index.html")


# ✅ تسجيل جميع مسارات POS من store.py يمكن إضافتها هنا مستقبلاً
# لكن الآن المسارات (products, sales, purchases) تبقى في store.py
# عبر نفس الـ url_prefix /api/v1/store/pos

# هذا الملف يحافظ على التنظيم ويسمح بفصل POS كامل إذا احتجنا
