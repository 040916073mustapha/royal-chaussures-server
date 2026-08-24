"""AI Handler — routes prompts to DeepSeek (or any OpenAI-compatible API)."""

import json
import logging
from typing import Optional, Union

import requests

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 40  # seconds


def generate_reply(
    user_message: str,
    system_prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Send a chat completion request and return the AI text response."""
    api_key = settings.AI_API_KEY
    api_base = settings.AI_API_BASE
    model_name = model or settings.AI_MODEL
    sys_prompt = system_prompt or settings.AI_SYSTEM_PROMPT or "[1. ROYAL IDENTITY] You are RC Agents AI."

    # ── Build messages ──────────────────────────────────
    messages = [{"role": "system", "content": sys_prompt}]

    if image_url and isinstance(image_url, str) and image_url.strip():
        user_content = [
            {"type": "text", "text": user_message or "What is in this image?"},
            {"type": "image_url", "image_url": {"url": image_url.strip()}},
        ]
    else:
        user_content = user_message or "Hello."

    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info(f"[AI] Sending to {model_name} | image={bool(image_url)}")
    try:
        resp = requests.post(api_base, json=payload, headers=headers, timeout=timeout)
        logger.info(f"[AI] Response {resp.status_code} | {resp.text[:200]}")
        if resp.status_code != 200:
            logger.error(f"[AI] API error: {resp.status_code} {resp.text[:500]}")
            return "عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي. الرجاء المحاولة لاحقاً."
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.Timeout:
        logger.error("[AI] Request timed out")
        return "عذراً، استغرق الرد وقتاً طويلاً. الرجاء إعادة المحاولة."
    except Exception as e:
        logger.exception(f"[AI] Request failed: {e}")
        return "عذراً، حدث خطأ غير متوقع. الرجاء المحاولة لاحقاً."
