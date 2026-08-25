#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - AI Agent Router v2.0
========================================
يدير التوجيه الذكي بين 5 وكلاء:
- customer_support  ← خدمة العملاء
- sales_agent       ← المبيعات المباشرة
- campaign_agent    ← الحملات التسويقية
- engagement_agent  ← التفاعل والولاء
- analytics_agent   ← التحليلات والتقارير
- shipping_tracking ← متابعة الشحنات
"""

from agents.config import AGENTS_CONFIG, detect_agent_from_message, get_auto_reply, get_agents_list
import logging

logger = logging.getLogger("royal-server")

# ----- المتغير العام لحالة الوكيل النشط -----
ACTIVE_AGENT = "customer_support"  # القيمة الافتراضية


def set_active_agent(agent_id):
    """تغيير الوكيل النشط"""
    global ACTIVE_AGENT
    if agent_id in AGENTS_CONFIG:
        ACTIVE_AGENT = agent_id
        return True
    return False


def get_active_agent():
    """إرجاع الوكيل النشط الحالي مع بياناته"""
    global ACTIVE_AGENT
    return ACTIVE_AGENT, AGENTS_CONFIG.get(ACTIVE_AGENT, AGENTS_CONFIG["customer_support"])


def route(message, platform="messenger", uid="unknown",
          openclaw_api_url=None, openclaw_token=None,
          image_url='', store_id=1):
    """
    توجيه الرسالة للوكيل المناسب
    ترجع: (response_text, agent_id, used_ai)
    """
    global ACTIVE_AGENT

    # 1. كشف الوكيل من الكلمات المفتاحية
    detected = detect_agent_from_message(message, ACTIVE_AGENT)

    # 2. جلب إعدادات الوكيل
    agent_config = AGENTS_CONFIG.get(detected, AGENTS_CONFIG["customer_support"])
    system_prompt = agent_config["system_prompt"]
    model = agent_config.get("openclaw_model", "openclaw/customer_support")

    # 3. محاولة استخدام OpenClaw AI إذا كان متاحاً
    if openclaw_api_url and openclaw_token:
        try:
            import requests
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            # If image exists, use vision format
            if isinstance(image_url, str) and image_url.strip():
                messages[1] = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message or "What is in this image?"},
                        {"type": "image_url", "image_url": {"url": image_url.strip()}}
                    ]
                }
            payload = {
                "model": model,
                "messages": messages,
                "user": f"customer:{platform}:{uid}",
                "max_tokens": 500,
                "temperature": 0.7
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openclaw_token}"
            }
            resp = requests.post(openclaw_api_url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                ai_reply = resp.json()['choices'][0]['message']['content']
                logger.info(f"[ROUTER] {detected} replied via AI to {uid[:20]}: {ai_reply[:60]}...")
                return ai_reply, detected, True
        except Exception as e:
            logger.warning(f"[ROUTER] AI call failed for {detected}, falling back: {e}")

    # 4. الرجوع للرد الآلي حسب الوكيل
    reply = get_auto_reply(detected, message)
    logger.info(f"[ROUTER] {detected} replied with auto-reply to {uid[:20]}")
    return reply, detected, False


def route_by_intent(message, platform="messenger", uid="unknown", image_url='', store_id=1):
    """
    توجيه أسرع يعتمد على النية فقط (للمكالمات الخفيفة)
    """
    detected = detect_agent_from_message(message, ACTIVE_AGENT)
    agent_config = AGENTS_CONFIG.get(detected, AGENTS_CONFIG["customer_support"])
    
    return {
        "agent_id": detected,
        "agent_name": agent_config["name"],
        "agent_emoji": agent_config["emoji"],
        "agent_color": agent_config["color"],
        "system_prompt": agent_config["system_prompt"]
    }


def get_route_stats():
    """إحصائيات التوجيه — للعرض في Dashboard"""
    global ACTIVE_AGENT
    config = AGENTS_CONFIG.get(ACTIVE_AGENT, AGENTS_CONFIG["customer_support"])
    return {
        "active_agent": ACTIVE_AGENT,
        "active_agent_name": config["name"],
        "active_agent_emoji": config["emoji"],
        "active_agent_color": config["color"],
        "available_agents": [
            {
                "id": aid,
                "name": ac["name"],
                "name_en": ac["name_en"],
                "description": ac["description"],
                "emoji": ac["emoji"],
                "color": ac["color"],
                "keywords": ac["keywords"][:8],  # Show first 8 keywords
                "active": aid == ACTIVE_AGENT
            }
            for aid, ac in AGENTS_CONFIG.items()
        ]
    }


def get_agent_config(agent_id):
    """إرجاع إعدادات وكيل معين"""
    return AGENTS_CONFIG.get(agent_id)
