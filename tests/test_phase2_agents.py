#!/usr/bin/env python3
"""Test Phase 2 Agents"""
import sys
sys.path.insert(0, r'C:\Users\Micro-Tech\.openclaw\workspace')

from agents.router import get_route_stats, route_by_intent
from agents.campaign_agent import get_active_campaigns, format_campaign_reply
from agents.sales_agent import format_upsell_reply, format_urgency_reply
from agents.engagement_agent import format_followup_reply
from agents.analytics_agent import format_sales_report

# Test 1: Route stats has all 6 agents
stats = get_route_stats()
agent_ids = [a['id'] for a in stats['available_agents']]
print(f'Agents count: {len(agent_ids)}')
print(f'Agents: {agent_ids}')
assert len(agent_ids) == 6, f"Expected 6, got {len(agent_ids)}"

# Test 2: Intent detection
tests = [
    ('أريد شراء حذاء كعب', 'sales_agent'),
    ('شنو عندكم عروض', 'campaign_agent'),
    ('وين طلبي', 'shipping_tracking'),
    ('مرحبا كيفكم', 'customer_support'),
    ('عندي شكوى', 'engagement_agent'),
    ('أريد تقرير المبيعات', 'analytics_agent'),
]
all_ok = True
for msg, expected in tests:
    result = route_by_intent(msg)
    ok = result['agent_id'] == expected
    status = 'OK' if ok else 'FAIL'
    print(f'{status}: "{msg[:25]}..." -> {result["agent_id"]} (expected {expected})')
    all_ok = all_ok and ok

# Test 3: Campaign agent
campaigns = get_active_campaigns()
print(f'Active campaigns: {len(campaigns)}')
for c in campaigns:
    print(f'  - {c["name"]}: {c["description"]}')

# Test 4: Format helpers
print(f'Sales upsell: {format_upsell_reply("Test", "3000-5000", "جودة عالية")[:60]}...')
print(f'Engagement: {format_followup_reply("مريم", 3, "حذاء")[:60]}...')

assert all_ok, "Some intent detection tests failed!"
print('\nAll tests passed!')
