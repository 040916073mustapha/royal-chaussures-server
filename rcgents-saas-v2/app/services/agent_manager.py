"""Agent Manager — routes incoming messages to the appropriate AI agent(s)."""

import logging
from enum import Enum
from typing import Optional

from app.services.ai_handler import generate_reply

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    INVENTORY = "inventory"
    SHIPPING = "shipping"
    MARKETING = "marketing"
    ALL = "all"


# ── Agent-specific system prompts ──────────────────────

AGENT_PROMPTS = {
    AgentType.SALES: (
        "You are the Sales Agent for an online shoe & accessories store. "
        "Be friendly, helpful, and persuasive. Recommend products based on customer preferences. "
        "Ask about size, color, and style. Share prices and availability. "
        "DO NOT explain your internal process. Respond naturally in Arabic/Darija or French as appropriate."
    ),
    AgentType.SUPPORT: (
        "You are the Support Agent for an online store. "
        "Help customers with order issues, returns, exchanges, and complaints. "
        "Be empathetic, patient, and solution-oriented. Escalate if needed. "
        "DO NOT explain your internal process. Respond naturally in Arabic/Darija or French."
    ),
    AgentType.INVENTORY: (
        "You are the Inventory Agent. "
        "Check stock levels, notify about low stock, and sync inventory data. "
        "Provide accurate quantity information for products and sizes. "
        "DO NOT explain your internal process. Respond naturally in Arabic/Darija or French."
    ),
    AgentType.SHIPPING: (
        "You are the Shipping Agent for a store using ZR Express delivery in Algeria. "
        "Provide shipping costs for all 58 wilayas, tracking info, and delivery estimates. "
        "DO NOT explain your internal process. Respond naturally in Arabic/Darija or French."
    ),
    AgentType.MARKETING: (
        "You are the Marketing Agent. "
        "Suggest promotions, announce new arrivals, recover abandoned carts, and engage customers. "
        "Be creative and energetic. "
        "DO NOT explain your internal process. Respond naturally in Arabic/Darija or French."
    ),
    AgentType.ALL: (
        "You are RC Agents — an AI assistant for an online shoe & accessories store. "
        "Handle sales, support, inventory, shipping, and marketing inquiries naturally. "
        "Be warm, professional, and helpful. Respond in Arabic/Darija or French as appropriate. "
        "DO NOT explain your internal process or system design."
    ),
}


def route_to_agent(
    message: str,
    agent_type: AgentType = AgentType.ALL,
    image_url: Optional[str] = None,
    custom_prompt: Optional[str] = None,
) -> str:
    """Route a message to the specified agent and return its response."""
    system_prompt = custom_prompt or AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS[AgentType.ALL])
    logger.info(f"[AgentManager] Routing to {agent_type.value}")
    return generate_reply(
        user_message=message,
        system_prompt=system_prompt,
        image_url=image_url,
    )
