"""Meta webhooks — Messenger & Instagram (Facebook Graph API)."""

import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.utils.security import verify_meta_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["meta"])


@router.get("/messenger")
async def verify_messenger(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    """Facebook Messenger webhook verification (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("[Meta] Messenger webhook verified")
        return PlainTextResponse(hub_challenge)
    logger.warning(f"[Meta] Messenger verify failed: mode={hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.get("/instagram")
async def verify_instagram(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    """Instagram webhook verification (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("[Meta] Instagram webhook verified")
        return PlainTextResponse(hub_challenge)
    logger.warning(f"[Meta] Instagram verify failed: mode={hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/messenger")
async def handle_messenger(request: Request):
    """Handle incoming Messenger messages."""
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(body, sig):
        logger.warning("[Meta] Invalid Messenger signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    data = await request.json()
    logger.info(f"[Meta] Messenger webhook received: {str(data)[:300]}")
    # TODO: Process messaging entries
    return {"status": "received"}


@router.post("/instagram")
async def handle_instagram(request: Request):
    """Handle incoming Instagram messages."""
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256")
    if not verify_meta_signature(body, sig):
        logger.warning("[Meta] Invalid Instagram signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    data = await request.json()
    logger.info(f"[Meta] Instagram webhook received: {str(data)[:300]}")
    # TODO: Process messaging entries
    return {"status": "received"}
