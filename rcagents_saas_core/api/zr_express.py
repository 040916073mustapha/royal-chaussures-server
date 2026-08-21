"""
SaaS Core — ZR Express API (Shipping Integration)
Automatic shipment creation from orders & conversations
"""

import os
import re
import logging
import requests as http_requests
from flask import Blueprint, request, jsonify

from ..database.models import Store, get_session
from .auth import require_auth

logger = logging.getLogger("saas-core.zr")

zr_bp = Blueprint("zr", __name__)


# ─── Helpers ──────────────────────────────────────────────────

def _get_zr_credentials():
    """Get ZR Express API credentials from environment"""
    return {
        "api_key": os.getenv("ZR_API_KEY", ""),
        "base_url": os.getenv("ZR_BASE_URL", "https://api.zrexpress.app/api/v1"),
        "tenant_id": os.getenv("ZR_TENANT_ID", ""),
        "secret_key": os.getenv("ZR_SECRET_KEY", ""),
    }


def _clean_phone(phone):
    """Normalize phone to Algerian international format (213...)"""
    if phone is None:
        return ""
    if not isinstance(phone, str):
        phone = str(int(phone)) if isinstance(phone, float) else str(phone)
    phone = phone.strip()
    if not phone:
        return ""
    clean = re.sub(r"[^0-9]", "", phone)
    if not clean.startswith("213"):
        if clean.startswith("0"):
            clean = "213" + clean[1:]
        else:
            clean = "213" + clean
    return clean


# ─── Routes ──────────────────────────────────────────────────

@zr_bp.route("/api/zr/test", methods=["GET"])
@require_auth
def test_connection():
    """Test ZR Express API connection"""
    creds = _get_zr_credentials()
    if not creds["api_key"] or not creds["tenant_id"]:
        return jsonify({"error": "ZR API not configured", "configured": False}), 400

    try:
        url = f"{creds['base_url']}/tenant/{creds['tenant_id']}/parcels?page=1&limit=1"
        headers = {
            "x-api-key": creds["api_key"],
            "Content-Type": "application/json",
        }
        resp = http_requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return jsonify({"status": "ok", "message": "ZR Express connected successfully"})
        else:
            return jsonify({
                "status": "error",
                "message": f"ZR API returned {resp.status_code}",
                "detail": resp.text[:200],
            }), 502
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502


@zr_bp.route("/api/zr/shipments", methods=["GET"])
@require_auth
def list_shipments():
    """List recent ZR Express shipments"""
    store_id = request.args.get("store_id")
    if store_id:
        # Verify store ownership
        session = get_session()
        try:
            store = session.query(Store).filter_by(
                id=store_id,
                user_id=request.current_user_id,
            ).first()
            if not store:
                return jsonify({"error": "Store not found"}), 404
        finally:
            session.close()

    creds = _get_zr_credentials()
    if not creds["api_key"] or not creds["tenant_id"]:
        return jsonify({"error": "ZR API not configured"}), 400

    try:
        page = request.args.get("page", 1)
        limit = request.args.get("limit", 20)
        url = f"{creds['base_url']}/tenant/{creds['tenant_id']}/parcels?page={page}&limit={limit}"
        headers = {
            "x-api-key": creds["api_key"],
            "Content-Type": "application/json",
        }
        resp = http_requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            parcels = data.get("data", data.get("parcels", []))[:int(limit)]
            return jsonify({"success": True, "shipments": parcels, "count": len(parcels)})
        else:
            return jsonify({"error": f"ZR API error: {resp.status_code}", "detail": resp.text[:300]}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@zr_bp.route("/api/zr/create-shipment", methods=["POST"])
@require_auth
def create_shipment():
    """Create a new shipment in ZR Express from order data"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    creds = _get_zr_credentials()
    if not creds["api_key"] or not creds["tenant_id"]:
        return jsonify({"error": "ZR API not configured"}), 400

    # Build payload
    addr = data.get("shipping_address") or data.get("billing_address") or {}
    customer = data.get("customer") or {}
    phone = _clean_phone(addr.get("phone", "") or customer.get("phone", "") or "")
    items = data.get("line_items", [])
    total = float(data.get("total_price", data.get("total_amount", 0)))

    payload = {
        "reference": data.get("name", f"ORDER-{data.get('order_id', '')}"),
        "shopify_order_id": str(data.get("order_id", data.get("id", ""))),
        "customer_name": (
            f"{customer.get('first_name', '') or ''} "
            f"{customer.get('last_name', '') or ''}"
        ).replace("None", "").strip() or data.get("customer_name", ""),
        "customer_phone": phone,
        "customer_address": (
            f"{addr.get('address1', '')} {addr.get('address2', '')}"
        ).strip() or data.get("customer_address", ""),
        "city": addr.get("city", data.get("city", "")),
        "wilaya": addr.get("province", data.get("wilaya", "")),
        "total_amount": total,
        "items": [
            {
                "sku": i.get("sku", ""),
                "name": i.get("title", i.get("name", "")),
                "qty": i.get("quantity", 1),
                "price": float(i.get("price", 0)),
            }
            for i in items
        ],
        "currency": "DZD",
        "notes": data.get("note", data.get("notes", "")),
    }

    try:
        url = f"{creds['base_url']}/parcels/create"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": creds["api_key"],
            "X-TENANT-ID": creds["tenant_id"],
        }
        resp = http_requests.post(url, json=payload, headers=headers, timeout=30)

        if resp.status_code in (200, 201):
            result = resp.json()
            return jsonify({
                "success": True,
                "parcel_id": result.get("id", ""),
                "tracking_number": result.get("tracking_number", ""),
                "response": result,
            })
        else:
            return jsonify({
                "success": False,
                "error": f"ZR API returned {resp.status_code}",
                "detail": resp.text[:300],
            }), 502

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


@zr_bp.route("/api/zr/wilayas", methods=["GET"])
def list_wilayas():
    """Get ZR Express wilaya list and shipping prices"""
    creds = _get_zr_credentials()
    if not creds["api_key"] or not creds["base_url"]:
        return jsonify({
            "wilayas": [
                {"id": 1, "name": "Adrar", "price": 600},
                {"id": 2, "name": "Chlef", "price": 600},
                {"id": 3, "name": "Laghouat", "price": 600},
                {"id": 4, "name": "Oum El Bouaghi", "price": 600},
                {"id": 5, "name": "Batna", "price": 600},
                {"id": 6, "name": "Béjaïa", "price": 600},
                {"id": 7, "name": "Biskra", "price": 600},
                {"id": 8, "name": "Béchar", "price": 600},
                {"id": 9, "name": "Blida", "price": 400},
                {"id": 10, "name": "Bouira", "price": 600},
                {"id": 11, "name": "Tamanrasset", "price": 600},
                {"id": 12, "name": "Tébessa", "price": 600},
                {"id": 13, "name": "Tlemcen", "price": 400},
                {"id": 14, "name": "Tiaret", "price": 600},
                {"id": 15, "name": "Tizi Ouzou", "price": 500},
                {"id": 16, "name": "Alger", "price": 400},
                {"id": 17, "name": "Djelfa", "price": 600},
                {"id": 18, "name": "Jijel", "price": 600},
                {"id": 19, "name": "Sétif", "price": 500},
                {"id": 20, "name": "Saïda", "price": 600},
                {"id": 21, "name": "Skikda", "price": 600},
                {"id": 22, "name": "Sidi Bel Abbès", "price": 500},
                {"id": 23, "name": "Annaba", "price": 600},
                {"id": 24, "name": "Guelma", "price": 600},
                {"id": 25, "name": "Constantine", "price": 500},
                {"id": 26, "name": "Médéa", "price": 500},
                {"id": 27, "name": "Mostaganem", "price": 500},
                {"id": 28, "name": "M'Sila", "price": 600},
                {"id": 29, "name": "Mascara", "price": 600},
                {"id": 30, "name": "Ouargla", "price": 600},
                {"id": 31, "name": "Oran", "price": 400},
                {"id": 32, "name": "El Bayadh", "price": 600},
                {"id": 33, "name": "Illizi", "price": 600},
                {"id": 34, "name": "Bordj Bou Arreridj", "price": 600},
                {"id": 35, "name": "Boumerdès", "price": 400},
                {"id": 36, "name": "El Tarf", "price": 600},
                {"id": 37, "name": "Tindouf", "price": 600},
                {"id": 38, "name": "Tissemsilt", "price": 600},
                {"id": 39, "name": "El Oued", "price": 600},
                {"id": 40, "name": "Khenchela", "price": 600},
                {"id": 41, "name": "Souk Ahras", "price": 600},
                {"id": 42, "name": "Tipaza", "price": 400},
                {"id": 43, "name": "Mila", "price": 600},
                {"id": 44, "name": "Aïn Defla", "price": 500},
                {"id": 45, "name": "Naâma", "price": 600},
                {"id": 46, "name": "Aïn Témouchent", "price": 500},
                {"id": 47, "name": "Ghardaïa", "price": 600},
                {"id": 48, "name": "Relizane", "price": 500},
                {"id": 49, "name": "Timimoun", "price": 600},
                {"id": 50, "name": "Bordj Badji Mokhtar", "price": 600},
                {"id": 51, "name": "Ouled Djellal", "price": 600},
                {"id": 52, "name": "Béni Abbès", "price": 600},
                {"id": 53, "name": "In Salah", "price": 600},
                {"id": 54, "name": "In Guezzam", "price": 600},
                {"id": 55, "name": "Touggourt", "price": 600},
                {"id": 56, "name": "Djanet", "price": 600},
                {"id": 57, "name": "El M'Ghair", "price": 600},
                {"id": 58, "name": "El Menia", "price": 600},
            ]
        })

    try:
        url = f"{creds['base_url']}/wilayas"
        headers = {"x-api-key": creds["api_key"]}
        resp = http_requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({"wilayas": data.get("data", data.get("wilayas", []))})
        else:
            # Fallback to static list
            return jsonify({"wilayas": [
                {"id": i, "name": f"Wilaya {i}", "price": 600}
                for i in range(1, 59)
            ]})
    except Exception:
        return jsonify({"wilayas": [
            {"id": i, "name": f"Wilaya {i}", "price": 600}
            for i in range(1, 59)
        ]})
