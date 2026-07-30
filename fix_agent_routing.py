#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\agents\\config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add latin keyword variants to shipping_tracking
old1 = '"express", "livraison", "suivi"'
new1 = '"express", "livraison", "suivi", "tlahi", "talahi", "plasi", "track", "order", "shipment", "where is", "find"'
if old1 in content:
    content = content.replace(old1, new1, 1)
    print("OK - keywords updated")
else:
    print("FAIL - keywords not found")

# 2. Replace the detect_agent function
old2 = '''def detect_agent_from_message(message, active_agent_id="customer_support"):
    """تحديد أي وكيل يجب أن يرد بناءً على الرسالة والكلمات المفتاحية"""
    msg_lower = message.lower()
    scores = {}

    for agent_id, config in AGENTS_CONFIG.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in msg_lower:
                score += 1
        scores[agent_id] = score

    # إذا ما لقى كلمات مفتاحية — استعمل الوكيل النشط
    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return active_agent_id

    # ابحث عن الوكيل صاحب أعلى score
    best_agent = max(scores, key=lambda k: scores[k])

    # إذا shipping له نقاط أكتر من customer_support — حول للشحنات
    if scores.get("shipping_tracking", 0) > scores.get("customer_support", 0):
        return "shipping_tracking"

    return best_agent'''

new2 = '''def detect_agent_from_message(message, active_agent_id="customer_support"):
    """تحديد أي وكيل يجب أن يرد بناءً على الرسالة والكلمات المفتاحية"""
    msg_lower = message.lower()
    scores = {}

    for agent_id, config in AGENTS_CONFIG.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in msg_lower:
                score += 1
        scores[agent_id] = score

    max_score = max(scores.values()) if scores else 0

    # Shipping preference: if any shipping keyword matches AND >= customer
    shipping_score = scores.get("shipping_tracking", 0)
    customer_score = scores.get("customer_support", 0)
    if shipping_score > 0 and shipping_score >= customer_score:
        return "shipping_tracking"

    if max_score == 0:
        return active_agent_id

    return max(scores, key=lambda k: scores[k])'''

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("OK - detect_agent function updated")
else:
    print("FAIL - detect_agent function not found")
    # debug: find approximate location
    idx = content.find("def detect_agent")
    if idx >= 0:
        print(f"Found at {idx}, first 200 chars:")
        print(repr(content[idx:idx+200]))

with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\agents\\config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE")
