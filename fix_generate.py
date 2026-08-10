# fix_generate.py
# Replace generate_ai_reply with Shopify-aware + conversation history version
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact old function by locating `def generate_ai_reply`
start = content.find('def generate_ai_reply(user_message, sender_id):')
if start < 0:
    start = content.find('def generate_ai_reply')
if start < 0:
    print("FATAL: Could not find generate_ai_reply")
    sys.exit(1)

# Find end - the next `def` after line
rest = content[start+1:]
# Skip the function body, find next def or end-of-file
# We know the function ends at: return "Merci de nous contacter..."
end_marker = 'return "Merci de nous contacter! Nous reviendrons vers vous bientot."'
end_idx = rest.find(end_marker)
if end_idx < 0:
    print("FATAL: Could not find function end")
    sys.exit(1)

end_idx = start + end_idx + len(end_marker)
old_func = content[start:end_idx]

print(f"Found function at pos {start}-{end_idx}, length {len(old_func)}")

# Build new function using code object to avoid escape issues
NEW_FUNC_CODE = """
def generate_ai_reply(user_message, sender_id):
    if not AI_API_KEY:
        logger.warning("AI_API_KEY not set, returning default greeting")
        return "Merhaba, Royal Chaussures'a hos geldiniz! Nasil yardimci olabiliriz?"
    system_prompt = os.getenv(
        "AI_SYSTEM_PROMPT",
        "[1. About Us & Core Identity]\\n"
        "You are the AI Customer Support Agent for Royal Chaussures, a premium women's footwear boutique in Tlemcen, Algeria.\\n"
        "- Website: https://royalchaussures.com/\\n"
        "- Phone: 0659832426\\n"
        "- Location: Imama, Tlemcen.\\n\\n"
        "[2. Shopify]\\n"
        "- Real-time access to products, prices, sizes, stock via Shopify API.\\n"
        "- When a customer asks about products, ALWAYS call search_shopify_products() first.\\n"
        "- Before confirming an order, call check_product_inventory() to verify stock.\\n\\n"
        "[3. Language & Tone]\\n"
        "- Reply in professional Arabic or Algerian Darija only.\\n"
        "- Be concise, polite, and welcoming.\\n\\n"
        "[4. Shipping]\\n"
        "Delivery 1-2 days across 58 wilayas via ZR Express. Home or Desk pickup.\\n\\n"
        "[5. Order Protocol]\\n"
        "Collect: name, phone, wilaya, product+color, size+qty, delivery preference.\\n"
        "Confirm then register.\\n\\n"
        "[6. Policies & Hand-off]\\n"
        "Size exchange allowed if unused. Promotions on social media only.\\n"
        "If outside scope, transfer to human team."
    )

    # Pre-call Shopify if product-related
    shopify_context = ""
    if detect_product_query(user_message):
        logger.info("Product query detected, calling Shopify API...")
        shopify_data = search_shopify_products(user_message)
        shopify_context = "\\n\\n--- SHOPIFY DATA ---\\n" + shopify_data + "\\n--- END SHOPIFY ---\\n"

    # Build messages with conversation history
    history = get_conversation(sender_id)
    messages = [{"role": "system", "content": system_prompt + shopify_context}]
    for msg in history[-8:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    try:
        headers = {"Authorization": "Bearer " + AI_API_KEY, "Content-Type": "application/json"}
        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7
        }
        resp = requests.post(AI_API_URL, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            reply = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if reply:
                add_to_conversation(sender_id, "user", user_message)
                add_to_conversation(sender_id, "assistant", reply)
                return reply
            logger.warning("Empty AI reply content")
        else:
            logger.error("AI API error: " + str(resp.status_code) + " " + resp.text[:200])
    except Exception as e:
        logger.error("AI reply error: " + _safe_str(e))
    return "Merci de nous contacter! Nous reviendrons vers vous bientot."
"""

content_new = content[:start] + NEW_FUNC_CODE + content[end_idx:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

try:
    compile(content_new, 'server.py', 'exec')
    print("SYNTAX: 100% OK!")
    
    # Verify key features
    checks = [
        ("search_shopify_products()", "Shopify pre-call"),
        ("get_conversation(sender_id)", "Conversation history"),
        ("add_to_conversation", "History storage"),
        ("detect_product_query", "Product detection"),
        ("max_tokens\": 300", "Extended tokens"),
    ]
    for pattern, desc in checks:
        print(f"  {desc}: {'YES' if pattern in NEW_FUNC_CODE else 'MISSING!'}")
    
    # Count total lines
    total = len(content_new.split('\n'))
    print(f"\nTotal lines: {total}")
    
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
