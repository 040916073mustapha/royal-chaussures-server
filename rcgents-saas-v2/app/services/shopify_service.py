"""Shopify API service — product and order sync for a given tenant."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SHOPIFY_API_VERSION = "2024-10"
REQUEST_TIMEOUT = 10


class ShopifyService:
    """Lightweight Shopify client scoped to one tenant's credentials."""

    def __init__(self, shop_url: str, catalog_token: str, orders_token: str):
        self.shop_url = shop_url.rstrip("/").replace("https://", "")
        self.catalog_token = catalog_token
        self.orders_token = orders_token
        self.base = f"https://{self.shop_url}/admin/api/{SHOPIFY_API_VERSION}"

    def _headers(self, token: str) -> dict:
        return {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }

    # ── Products ────────────────────────────────────────

    def get_products(self, limit: int = 50) -> list:
        url = f"{self.base}/products.json?limit={limit}"
        try:
            resp = requests.get(url, headers=self._headers(self.catalog_token), timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("products", [])
        except Exception as e:
            logger.error(f"[Shopify] get_products failed: {e}")
            return []

    def get_product(self, product_id: str) -> Optional[dict]:
        url = f"{self.base}/products/{product_id}.json"
        try:
            resp = requests.get(url, headers=self._headers(self.catalog_token), timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("product")
        except Exception as e:
            logger.error(f"[Shopify] get_product({product_id}) failed: {e}")
            return None

    # ── Parse product → our schema ─────────────────────

    @staticmethod
    def parse_product(raw: dict) -> dict:
        """Convert Shopify product to our normalized format."""
        variants = raw.get("variants", [])
        sizes = sorted(set(
            v.get("title", "").strip()
            for v in variants
            if v.get("title", "").strip()
        ))
        colors = []
        for opt in raw.get("options", []):
            if opt.get("name", "").lower() in ("color", "colour", "لون", "couleur"):
                colors = opt.get("values", [])
                break
        first_variant = variants[0] if variants else {}
        return {
            "shopify_product_id": str(raw["id"]),
            "title": raw.get("title", ""),
            "price": float(first_variant.get("price", 0)),
            "compare_at_price": float(first_variant.get("compare_at_price", 0)) if first_variant.get("compare_at_price") else None,
            "sizes": sizes,
            "colors": colors,
            "image_url": raw.get("image", {}).get("src") if raw.get("image") else None,
            "inventory_quantity": sum(int(v.get("inventory_quantity", 0)) for v in variants),
        }

    # ── Orders ──────────────────────────────────────────

    def get_orders(self, status: str = "any", limit: int = 20) -> list:
        url = f"{self.base}/orders.json?status={status}&limit={limit}"
        try:
            resp = requests.get(url, headers=self._headers(self.orders_token), timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("orders", [])
        except Exception as e:
            logger.error(f"[Shopify] get_orders failed: {e}")
            return []
