# fix_conversation.py
# Fix: 1) Conversation history 2) Shopify pre-call before AI reply
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# === FIX 1: Add conversation history dict ===
# Before generate_ai_reply, add a conversation store
conv_store = '''

# --- Conversation Memory (Thread Storage) ---
# Stores last N messages per sender_id for continuity
CONVERSATION_MEMORY = {}
MAX_HISTORY = 10  # keep last 10 exchanges per user


def get_conversation(sender_id):
    """Get or create conversation history for a sender."""
    if sender_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[sender_id] = []
    return CONVERSATION_MEMORY[sender_id]


def add_to_conversation(sender_id, role, text):
    """Add a message to conversation history."""
    conv = get_conversation(sender_id)
    conv.append({"role": role, "content": text})
    # Keep only last MAX_HISTORY*2 messages (user + assistant pairs)
    if len(conv) > MAX_HISTORY * 2:
        conv[:] = conv[-(MAX_HISTORY * 2):]


def detect_product_query(user_message):
    """Detect if user is asking about products and return search query."""
    keywords = ["منتج", "حذاء", "صندل", "بوت", "باليرينا", "اسكربين",
                "escarpin", "ballerine", "botte", "sandale", "mule",
                "product", "shoe", "size", "price", "سعر", "مقاس",
                "لون", "color", "متوفر", "disponible", "stock",
                "عندكم", "عندك", "شنو", "واش", "product"]
    msg_lower = user_message.lower()
    for kw in keywords:
        if kw in msg_lower:
            return user_message  # return the full query to search
    return None
'''

# Find where to insert - right before FB_SYSTEM_USER_TOKEN section
marker_fb = '\nFB_SYSTEM_USER_TOKEN = os.getenv("FB_SYSTEM_USER_TOKEN", "")'
if marker_fb in content:
    content = content.replace(marker_fb, conv_store + marker_fb)
    print("SUCCESS: Added conversation memory!")
else:
    print("FAILED: Could not find insertion point for conversation memory")
    # Find alternative
    if 'SHOPIFY_STORE' in content:
        # Insert after the Shopify functions
        insert_after = 'check_product_inventory() to verify stock availability.\\n"'
        if insert_after in content:
            content = content.replace(insert_after, insert_after + conv_store)
            print("Inserted after Shopify prompt line")
        else:
            print("Alternative insertion point not found")

# === FIX 2: Replace generate_ai_reply with conversation-aware version ===
old_generate = '''def generate_ai_reply(user_message, sender_id):
    if not AI_API_KEY:
        logger.warning("AI_API_KEY not set, returning default greeting")
        return "Merhaba, Royal Chaussures'a hos geldiniz! Nasil yardimci olabiliriz?"
    # Use custom system prompt from env var AI_SYSTEM_PROMPT, or fall back to default
    system_prompt = os.getenv(
        "AI_SYSTEM_PROMPT",
        "[1. About Us & Core Identity]\\n"
        "You are the official AI Customer Support Agent for Royal Chaussures (\u0631\u0648\u064a\u0627\u0644 \u0634\u0648\u0633\u064a\u0631), a premium, minimalist women's footwear and accessories boutique based in Tlemcen, Algeria.\\n"
        "- Business Name: Royal Chaussures\\n"
        "- Website: https://royalchaussures.com/\\n"
        "- Phone: 0659832426\\n"
        "- Email: royalchaussures2@gmail.com\\n"
        "- Physical Store Address: Imama, a cote de la CNAS & Primaire Hasnaoui, Tlemcen, Algeria.\\n"
        "- Google Maps: https://maps.app.goo.gl/7MSZMzkHtbR29eMa7\\n\\n"
        "[2. Scope of Authority & Shopify Integration]\\n"
        "- Products & Pricing: You are fully authorized to answer inquiries about products, prices, available sizes, colors, and stock using the connected Shopify API.\\n"
        "- Visuals & Links: When customers ask for product details or photos, provide accurate information and store links retrieved from Shopify.\\n"
        "- Real-Time Check: You have direct Shopify API access. When a customer asks about any product, availability, size, color, or price, call search_shopify_products() to look up the latest data in real-time. Before confirming an order, call check_product_inventory() to verify stock availability.\\n"
        "- Communication Channels: Customers can purchase via Direct Messages (FB/IG/WhatsApp), the website (RoyalChaussures.com), or in-store.\\n\\n"
        "[3. Master Interaction Rules]\\n"
        "1. Strict Arabic Language Policy: Always reply 100% in professional, elegant, and welcoming Arabic (or respectful Algerian Darija), regardless of the language used by the customer. Never mix languages.\\n"
        "2. Premium & Minimalist Tone: Keep responses concise, helpful, and polite. Avoid unnecessary length.\\n"
        "3. No Name Repetition: Address the customer by name once in the initial greeting, then proceed naturally without overusing their name.\\n\\n"
        "[4. Store Location & Contact Inquiries]\\n"
        "If a customer asks about the physical store or contact info, respond with:\\n"
        "- Address: \u0625\u0645\u0627\u0645\u0629\u060c \u0628\u062c\u0627\u0646\u0628 CNAS \u0648\u0645\u062f\u0631\u0633\u0629 \u062d\u0633\u0646\u0627\u0648\u064a \u0627\u0644\u0627\u0628\u062a\u062f\u0627\u0626\u064a\u0629 - \u062a\u0644\u0645\u0633\u0627\u0646.\\n"
        "- Google Maps: https://maps.app.goo.gl/7MSZMzkHtbR29eMa7\\n"
        "- Phone: 0659832426\\n"
        "- Website: https://royalchaussures.com/\\n\\n"
        "[5. Shipping & Delivery Rules (ZR Express - 58 Wilayas)]\\n"
        "Delivery Time: 1 to 2 days across all 58 Wilayas via ZR Express.\\n"
        "Methods Available: Home Delivery OR Stop Desk (Desk Pickup).\\n\\n"
        "Shipping Fees Table (DZD):\\n"
        "- Tlemcen (All communes/Ghazaouet/Maghnia/Remchi): Home 500 / Desk 350\\n"
        "- Alger: Home 650 / Desk 450\\n"
        "- Ain Temouchent: Home 650 / Desk 500\\n"
        "- Oran, Mascara, Mostaganem, Sidi Bel Abbes: Home 700 / Desk 500\\n"
        "- Blida, Tiaret, Medea, Tissemsilt, Chlef, Ain Defla, Relizane: Home 750 / Desk 500\\n"
        "- Saida: Home 750 / Desk 500\\n"
        "- Oum El Bouaghi, Batna, Bejaia, Bouira, Tizi Ouzou, Jijel, Setif, Skikda, Guelma, Constantine, BBArreridj, Boumerdes, Khenchela, Souk Ahras, Tipaza, Mila: Home 800 / Desk 500\\n"
        "- Annaba, El Tarf: Home 850 / Desk 500\\n"
        "- Tebessa: Home 900 / Desk 500\\n"
        "- M'Sila, Laghouat, Biskra, Djelfa, Ouled Djellal: Home 950 / Desk 650\\n"
        "- El Bayadh, Naama, Ghardaia: Home 1000 / Desk 600\\n"
        "- Ouargla, El Oued, Touggourt, El Menia, El Meghaier: Home 1000 / Desk 700\\n"
        "- Bechar: Home 1100 / Desk 700\\n"
        "- Beni Abbes: Home 1200 / Desk 950\\n"
        "- Adrar, Timimoun: Home 1400 / Desk 950\\n"
        "- Tamanrasset, In Salah, In Guezzam: Home 1600 / Desk 1110\\n\\n"
        "[6. Lead & Order Collection Protocol]\\n"
        "To process an order via messaging, collect the following details:\\n"
        "1. Full Name (\u0627\u0644\u0627\u0633\u0645 \u0627\u0644\u0643\u0627\u0645\u0644)\\n"
        "2. Phone Number (\u0631\u0642\u0645 \u0627\u0644\u0647\u0627\u062a\u0641)\\n"
        "3. Wilaya & Municipality (\u0627\u0644\u0648\u0644\u0627\u064a\u0629 \u0648\u0627\u0644\u0628\u0644\u062f\u064a\u0629)\\n"
        "4. Product Name & Color (\u0627\u0633\u0645 \u0627\u0644\u0645\u0646\u062a\u062c \u0648\u0627\u0644\u0644\u0648\u0646)\\n"
        "5. Size & Quantity (\u0627\u0644\u0645\u0642\u0627\u0633 \u0648\u0627\u0644\u0643\u0645\u064a\u0629)\\n"
        "6. Delivery Preference (\u062a\u0648\u0635\u064a\u0644 \u0644\u0644\u0645\u0646\u0632\u0644 \u0623\u0648 \u0627\u0644\u0645\u0643\u062a\u0628)\\n\\n"
        "Order Confirmation Step:\\n"
        "Once all info is gathered, display a clear vertical summary:\\n"
        "- \u0627\u0644\u0645\u0646\u062a\u062c: [Product Name]\\n"
        "- \u0627\u0644\u0645\u0642\u0627\u0633 \u0648\u0627\u0644\u0644\u0648\u0646: [Size / Color]\\n"
        "- \u0627\u0644\u0643\u0645\u064a\u0629: [Qty]\\n"
        "- \u0627\u0644\u062a\u0648\u0635\u064a\u0644: [Home / Desk via ZR Express - Fee DZD]\\n"
        "- \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a: [Total Price DZD]\\n\\n"
        "Then ask: \u0647\u0644 \u062a\u0624\u0643\u062f\u064a\u0646 \u0647\u0630\u0647 \u0627\u0644\u0637\u0644\u0628\u064a\u0629 \u0644\u0646\u0633\u062c\u0644\u0647\u0627 \u0644\u0643\u0650\u061f \U0001f49b\\n\\n"
        "Upon confirmation (\u0646\u0639\u0645), respond:\\n"
        "\u0645\u0645\u062a\u0627\u0632! \u0644\u0642\u062f \u062a\u0645 \u062a\u0633\u062c\u064a\u0644 \u0637\u0644\u0628\u064a\u062a\u0643\u0650 \u0628\u0646\u062c\u0627\u062d. \u0633\u064a\u062a\u0635\u0644 \u0628\u0643\u0650 \u0623\u062d\u062f \u0623\u0639\u0636\u0627\u0621 \u0641\u0631\u064a\u0642\u0646\u0627 \u0647\u0627\u062a\u0641\u064a\u0627\u064b \u0644\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0637\u0644\u0628\u064a\u0629 \u0648\u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0634\u062d\u0646 \u0627\u0644\u0646\u0647\u0627\u0626\u064a\u0629. \u0634\u0643\u0631\u0627\u064b \u0644\u0627\u062e\u062a\u064a\u0627\u0631\u0643 \u0631\u0648\u064a\u0627\u0644 \u0634\u0648\u0633\u064a\u0631! \U0001f49b\\n\\n"
        "[7. Policies (Exchanges & Discounts)]\\n"
        "- Returns & Size Exchange: Size exchange is allowed if the product does not fit.\\n"
        "  Conditions: Product must be completely unused, in its original condition, and requested as soon as possible after delivery. Requests are reviewed individually by our support team.\\n"
        "- Promotions: All discounts and special offers are announced exclusively via our official social pages and website (RoyalChaussures.com).\\n\\n"
        "[8. Human Agent Hand-off Protocol]\\n"
        "If a customer encounters an issue outside these instructions, insists on speaking to a human, or requests custom support, reply with:\\n"
        "\u0633\u0623\u0642\u0648\u0645 \u0628\u062a\u062d\u0648\u064a\u0644\u0643\u0650 \u0627\u0644\u0622\u0646 \u0625\u0644\u0649 \u0623\u062d\u062f \u0623\u0639\u0636\u0627\u0621 \u0641\u0631\u064a\u0642\u0646\u0627 \u0644\u064a\u0633\u0627\u0639\u062f\u0643\u0650 \u0628\u0634\u0643\u0644 \u0623\u0641\u0636\u0644 \U0001f49b\\n"
        "and flag the conversation for human takeover."
    )
    try:
        headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }
        resp = requests.post(AI_API_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            reply = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if reply:
                return reply
            logger.warning("Empty AI reply content")
        else:
            logger.error(f"AI API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"AI reply error: {_safe_str(e)}")
    return "Merci de nous contacter! Nous reviendrons vers vous bientot."'''

new_generate = '''def generate_ai_reply(user_message, sender_id):
    if not AI_API_KEY:
        logger.warning("AI_API_KEY not set, returning default greeting")
        return "Merhaba, Royal Chaussures\\'a hos geldiniz! Nasil yardimci olabiliriz?"
    # Use custom system prompt from env var AI_SYSTEM_PROMPT, or fall back to default
    system_prompt = os.getenv(
        "AI_SYSTEM_PROMPT",
        "[1. About Us & Core Identity]\\n"
        "You are the official AI Customer Support Agent for Royal Chaussures, a premium women\\'s footwear boutique in Tlemcen, Algeria.\\n"
        "- Website: https://royalchaussures.com/\\n"
        "- Phone: 0659832426\\n"
        "- Location: Imama, Tlemcen, Algeria.\\n\\n"
        "[2. Shopify Access]\\n"
        "- You have real-time access to products, prices, sizes, colors, and stock via Shopify API.\\n"
        "- When a customer asks about any product/availability, ALWAYS call search_shopify_products() first.\\n"
        "- Before confirming an order, call check_product_inventory() to verify stock.\\n\\n"
        "[3. Language & Tone]\\n"
        "- Reply in professional Arabic or Algerian Darija. Never use other languages.\\n"
        "- Be concise, polite, and welcoming.\\n\\n"
        "[4. Shipping - ZR Express (58 Wilayas)]\\n"
        "Delivery: 1-2 days. Home/Desk options with fees by wilaya.\\n\\n"
        "[5. Order Protocol]\\n"
        "Collect: name, phone, wilaya, product+color, size+qty, delivery preference.\\n"
        "Show summary then ask: \\"\\u0647\\u0644 \\u062a\\u0624\\u0643\\u062f\\u064a\\u0646 \\u0647\\u0630\\u0647 \\u0627\\u0644\\u0637\\u0644\\u0628\\u064a\\u0629\\u061f\\"\\n"
        "On confirmation, register the order and inform them a team member will call.\\n\\n"
        "[6. Policies]\\n"
        "- Size exchange allowed if unused and in original condition.\\n"
        "- Promotions via official social pages only.\\n\\n"
        "[7. Human Hand-off]\\n"
        "If outside scope, transfer to human team."
    )
    
    # --- Pre-call Shopify if customer asks about products ---
    shopify_context = ""
    query = detect_product_query(user_message)
    if query:
        logger.info(f"Product query detected, searching Shopify: {user_message[:60]}...")
        shopify_data = search_shopify_products(user_message)
        shopify_context = "\\n\\n--- SHOPIFY REAL-TIME DATA ---\\n" + shopify_data + "\\n--- END SHOPIFY DATA ---\\n"
    
    # --- Build conversation history ---
    history = get_conversation(sender_id)
    messages = [{"role": "system", "content": system_prompt + shopify_context}]
    # Add last few exchanges for context
    for msg in history[-8:]:  # last 4 exchanges
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    
    try:
        headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
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
            logger.error(f"AI API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"AI reply error: {_safe_str(e)}")
    return "Merci de nous contacter! Nous reviendrons vers vous bientot."'''

# Replace
if old_generate in content:
    content = content.replace(old_generate, new_generate)
    print("SUCCESS: Replaced generate_ai_reply with conversation-aware version!")
else:
    print("FAILED: Could not find old generate_ai_reply")
    # Find approximate location
    idx = content.find('def generate_ai_reply')
    if idx > 0:
        print(f"Found at position {idx}")
        # Show context
        print(content[idx:idx+100])

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: 100% OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
