"""Security utilities: HMAC verification, signatures, rate limiting."""

import hashlib
import hmac
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def verify_meta_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """Verify X-Hub-Signature-256 from Meta (Messenger, Instagram, WhatsApp)."""
    if not signature_header:
        logger.warning("[SECURITY] Missing Meta signature header")
        return False
    expected_signature = "sha256=" + hmac.new(
        settings.META_APP_SECRET.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)


def verify_shopify_hmac(payload_body: bytes, hmac_header: Optional[str]) -> bool:
    """Verify Shopify HMAC-SHA256 webhook signature."""
    if not hmac_header:
        logger.warning("[SECURITY] Missing Shopify HMAC header")
        return False
    digest = hmac.new(
        settings.SHOPIFY_ORDERS_TOKEN.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, hmac_header)
