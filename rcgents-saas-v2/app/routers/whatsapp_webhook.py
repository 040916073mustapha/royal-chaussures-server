"""WhatsApp Cloud API webhooks."""

import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.utils.security import verify_meta_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["whatsapp"])


@router.get("/whatsapp")
async def verify_whatsapp(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    """WhatsApp webhook verification (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("[WhatsApp] Webhook verified")
        return PlainTextResponse(hub_challenge)
    logger.warning(f"[WhatsApp] Verify failed: mode={hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def handle_whatsapp(request: Request):
    """Handle incoming WhatsApp messages."""
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(body, sig):
        logger.warning("[WhatsApp] Invalid signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    data = await request.json()
    logger.info(f"[WhatsApp] Webhook received: {str(data)[:300]}")
    # TODO: Process WhatsApp messages
    return {"status": "received"}
