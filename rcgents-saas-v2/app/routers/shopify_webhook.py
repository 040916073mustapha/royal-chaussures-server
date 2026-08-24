"""Shopify webhooks — orders/create, orders/updated, products/sync."""

import logging

from fastapi import APIRouter, Request, HTTPException

from app.config import settings
from app.utils.security import verify_shopify_hmac

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["shopify"])


@router.post("/shopify")
async def handle_shopify_webhook(request: Request):
    """Handle Shopify order/product webhooks."""
    body = await request.body()
    topic = request.headers.get("x-shopify-topic", "")
    hmac_header = request.headers.get("x-shopify-hmac-sha256", "")
    
    if not verify_shopify_hmac(body, hmac_header):
        logger.warning("[Shopify] Invalid HMAC signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    data = await request.json()
    logger.info(f"[Shopify] Webhook topic={topic}: {str(data)[:300]}")
    
    if topic == "orders/create":
        # TODO: Upsert order
        pass
    elif topic == "orders/updated":
        # TODO: Update order
        pass
    elif topic == "products/update":
        # TODO: Sync product
        pass
    
    return {"status": "received"}
