"""ZR Express shipping service — rates, labels, and tracking."""

import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)

# 58 wilayas fixed pricing
WILAYA_SHIPPING = {
    "أدرار": 1200, "الشلف": 800, "الأغواط": 900, "أم البواقي": 1000,
    "باتنة": 1000, "بجاية": 900, "بسكرة": 1000, "بشار": 1200,
    "البليدة": 700, "البويرة": 800, "تمنراست": 1500, "تبسة": 1100,
    "تلمسان": 600, "تيارت": 800, "تيزي وزو": 800, "الجزائر": 600,
    "الجلفة": 900, "جيجل": 900, "سطيف": 800, "سعيدة": 900,
    "سكيكدة": 900, "سيدي بلعباس": 700, "عنابة": 900, "قالمة": 1000,
    "قسنطينة": 800, "المدية": 700, "مستغانم": 800, "المسيلة": 900,
    "معسكر": 800, "ورقلة": 1200, "وهران": 700, "البيض": 1000,
    "إليزي": 1500, "برج بوعريريج": 800, "بومرداس": 700, "الطارف": 1000,
    "تندوف": 1500, "تيسمسيلت": 800, "الوادي": 1100, "خنشلة": 1000,
    "سوق أهراس": 1000, "تيبازة": 700, "ميلة": 900, "عين الدفلى": 700,
    "النعامة": 1000, "عين تموشنت": 700, "غرداية": 1100, "غليزان": 800,
    "المغير": 1100, "المنيعة": 1200, "أولاد جلال": 1000,
    "بني عباس": 1300, "عين صالح": 1400, "عين قزام": 1600,
    "تقرت": 1100, "جانت": 1600, "البرج": 1100, "الأبيض سيدي الشيخ": 1200,
}


def get_shipping_cost(wilaya: str) -> Optional[int]:
    """Return shipping cost in DZD for a given wilaya name."""
    return WILAYA_SHIPPING.get(wilaya.strip())


def list_wilayas() -> dict:
    """Return all supported wilayas and their shipping costs."""
    return dict(WILAYA_SHIPPING)
