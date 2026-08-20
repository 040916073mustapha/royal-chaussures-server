"""
SaaS Core — Stores API (Shopify Connect / OAuth / Sync)
"""

from flask import Blueprint, request, jsonify, redirect
from sqlalchemy import text

from ..config import Config
from ..database.models import Store, Channel, get_session
from .auth import require_auth

stores_bp = Blueprint("stores", __name__)

SHOPIFY_SCOPES = "read_products,write_products,read_inventory,read_orders,write_orders"


@stores_bp.route("/api/stores/shopify/auth-url", methods=["GET"])
@require_auth
def get_auth_url():
    """Get Shopify OAuth URL for this user's store"""
    shop = (request.args.get("shop") or "").strip()
    if not shop:
        return jsonify({"error": "Shop parameter is required (e.g. mystore.myshopify.com)"}), 400

    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"

    # Generate unique state token
    import uuid
    state = str(uuid.uuid4())

    # Store state temporarily (in production: use Redis/cache)
    session = get_session()
    try:
        session.execute(
            text("INSERT INTO temp_oauth_states (state, user_id, shop, created_at) "
                 "VALUES (:state, :user_id, :shop, NOW())"),
            {"state": state, "user_id": request.current_user_id, "shop": shop}
        )
        session.commit()
    except Exception:
        # Table may not exist — we'll handle state in app memory for now
        pass
    finally:
        session.close()

    auth_url = (
        f"https://{shop}/admin/oauth/authorize"
        f"?client_id={Config.SHOPIFY_CLIENT_ID}"
        f"&scope={SHOPIFY_SCOPES}"
        f"&redirect_uri=https://app.rcagents.space/api/stores/shopify/callback"
        f"&state={state}"
    )

    return jsonify({"auth_url": auth_url, "state": state})


@stores_bp.route("/api/stores/shopify/callback", methods=["GET"])
def shopify_callback():
    """Handle Shopify OAuth callback"""
    code = request.args.get("code")
    shop = request.args.get("shop")
    state = request.args.get("state")

    if not code or not shop:
        return jsonify({"error": "Missing code or shop parameter"}), 400

    # Exchange code for access token
    import requests as http_requests

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": Config.SHOPIFY_CLIENT_ID,
        "client_secret": Config.SHOPIFY_CLIENT_SECRET,
        "code": code,
    }

    try:
        resp = http_requests.post(token_url, json=payload, timeout=10)
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return jsonify({"error": "Failed to get access token"}), 400

        # Get store info
        store_resp = http_requests.get(
            f"https://{shop}/admin/api/{Config.SHOPIFY_API_VERSION}/shop.json",
            headers={"X-Shopify-Access-Token": access_token},
            timeout=10,
        )
        store_resp.raise_for_status()
        shop_data = store_resp.json().get("shop", {})
        store_id = str(shop_data.get("id", ""))

        # Save to database
        db_session = get_session()
        try:
            existing = db_session.query(Store).filter_by(
                user_id=request.current_user_id,
                shopify_domain=shop,
            ).first()

            if existing:
                existing.shopify_access_token = access_token
                existing.shopify_store_id = store_id
                existing.is_connected = True
                existing.updated_at = None  # triggers onupdate
            else:
                # For now, link to first user (multi-tenant will be improved)
                from ..database.models import User
                first_user = db_session.query(User).first()
                new_store = Store(
                    user_id=first_user.id if first_user else request.current_user_id,
                    shopify_domain=shop,
                    shopify_access_token=access_token,
                    shopify_store_id=store_id,
                )
                db_session.add(new_store)

            db_session.commit()

        except Exception as e:
            db_session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            db_session.close()

        # Redirect to dashboard success page
        return redirect(f"https://app.rcagents.space/onboarding?shop={shop}&connected=true")

    except Exception as e:
        return jsonify({"error": f"OAuth error: {str(e)}"}), 500


@stores_bp.route("/api/stores", methods=["GET"])
@require_auth
def list_stores():
    """List user's connected stores"""
    session = get_session()
    try:
        stores = session.query(Store).filter_by(
            user_id=request.current_user_id
        ).all()

        return jsonify({
            "stores": [
                {
                    "id": s.id,
                    "shopify_domain": s.shopify_domain,
                    "is_connected": s.is_connected,
                    "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in stores
            ]
        })
    finally:
        session.close()


@stores_bp.route("/api/stores/<store_id>/sync", methods=["POST"])
@require_auth
def sync_store(store_id):
    """Sync products from Shopify store"""
    session = get_session()
    try:
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()

        if not store:
            return jsonify({"error": "Store not found"}), 404

        if not store.is_connected:
            return jsonify({"error": "Store is not connected"}), 400

        # Fetch products from Shopify
        import requests as http_requests

        resp = http_requests.get(
            f"https://{store.shopify_domain}/admin/api/{Config.SHOPIFY_API_VERSION}/products.json?limit=250",
            headers={"X-Shopify-Access-Token": store.shopify_access_token},
            timeout=15,
        )
        resp.raise_for_status()
        products = resp.json().get("products", [])

        # Update cached catalog in AI settings
        from ..database.models import AISettings
        ai_settings = session.query(AISettings).filter_by(store_id=store.id).first()
        if ai_settings:
            ai_settings.product_catalog = products
        else:
            ai_settings = AISettings(
                store_id=store.id,
                system_prompt="",
                product_catalog=products,
            )
            session.add(ai_settings)

        # Update last sync
        from datetime import datetime, timezone
        store.last_sync_at = datetime.now(timezone.utc)
        session.commit()

        return jsonify({
            "success": True,
            "products_count": len(products),
            "store": store.shopify_domain,
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@stores_bp.route("/api/stores/<store_id>", methods=["DELETE"])
@require_auth
def disconnect_store(store_id):
    """Disconnect a store"""
    session = get_session()
    try:
        store = session.query(Store).filter_by(
            id=store_id,
            user_id=request.current_user_id,
        ).first()

        if not store:
            return jsonify({"error": "Store not found"}), 404

        store.is_connected = False
        session.commit()

        return jsonify({"success": True, "message": "Store disconnected"})

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
