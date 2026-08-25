#!/usr/bin/env python3
"""Test Phase 2 Integration: generate_ai_reply routing"""
import sys, os
sys.path.insert(0, r'C:\Users\Micro-Tech\.openclaw\workspace')

# Test router integration into server.py logic
from agents.router import route_by_intent, get_route_stats

print("=" * 60)
print("TEST: Phase 2 Agent Routing Integration")
print("=" * 60)

# Test 1: Route stats
stats = get_route_stats()
print(f"\n[1] Agents available: {len(stats['available_agents'])}")
assert len(stats['available_agents']) == 6, f"Expected 6 agents, got {len(stats['available_agents'])}"

# Test 2: Intent detection with image URL (vision support)
test_cases = [
    # (message, image_url, expected_agent)
    ("أريد شراء حذاء كعب عالي", "", "sales_agent"),
    ("شنو عندكم عروض وتخفيضات", "", "campaign_agent"),
    ("وين طلبي من ZR Express", "", "shipping_tracking"),
    ("كيف كانت تجربتي في التقييم", "", "engagement_agent"),
    ("أريد تقرير مبيعات الأسبوع", "", "analytics_agent"),
    ("مرحبا كم سعر هذا الحذاء", "", "customer_support"),
    ("", "https://example.com/shoe.jpg", "customer_support"),  # image only
    ("ما هذا الحذاء؟", "https://example.com/shoe.jpg", "customer_support"),
]

all_ok = True
for msg, img_url, expected in test_cases:
    result = route_by_intent(msg or "image", "messenger", "test_user", img_url, 1)
    ok = result["agent_id"] == expected
    status = "OK" if ok else "FAIL"
    if not ok:
        all_ok = False
    print(f"[{status}] msg='{msg[:30]:30s}' img={bool(img_url)} -> {result['agent_id']:20s} (expected {expected})")

# Test 3: Verify auto-reply map works for each agent
from agents.config import get_auto_reply
agent_ids = ["customer_support", "shipping_tracking", "sales_agent", "campaign_agent", "engagement_agent", "analytics_agent"]
print(f"\n[3] Auto-reply fallback test:")
for aid in agent_ids:
    reply = get_auto_reply(aid, "اختبار random message")
    print(f"  {aid}: {reply[:50]}...")
    assert len(reply) > 10, f"Auto-reply too short for {aid}"

print(f"\n{'='*60}")
if all_ok:
    print("ALL TESTS PASSED! Phase 2 routing is operational.")
else:
    print("Some tests FAILED - check output above.")
print(f"{'='*60}")
