# verify_final.py
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print("Lines:", len(lines))

# Check all required components
checks = {
    "Conversation memory": 'CONVERSATION_MEMORY' in content,
    "get_conversation()": 'def get_conversation' in content,
    "add_to_conversation()": 'def add_to_conversation' in content,
    "detect_product_query()": 'def detect_product_query' in content,
    "shopify_api()": 'def shopify_api' in content,
    "search_shopify_products()": 'def search_shopify_products' in content,
    "check_product_inventory()": 'def check_product_inventory' in content,
    "generate_ai_reply with history": 'get_conversation(sender_id)' in content,
    "generate_ai_reply with Shopify pre-call": 'detect_product_query' in content,
    "add_to_conversation in generate": 'add_to_conversation(sender_id' in content,
    "FB_SYSTEM_USER_TOKEN": 'FB_SYSTEM_USER_TOKEN = os.getenv' in content,
    "FB_VERIFY_TOKEN": 'FB_VERIFY_TOKEN = os.getenv' in content,
    "INSTAGRAM_ACCESS_TOKEN": 'INSTAGRAM_ACCESS_TOKEN = os.getenv' in content,
    "WHATSAPP_ACCESS_TOKEN": 'WHATSAPP_ACCESS_TOKEN = os.getenv' in content,
    "send_fb_reply": 'def send_fb_reply' in content,
    "send_ig_reply": 'def send_ig_reply' in content,
    "send_whatsapp_reply": 'def send_whatsapp_reply' in content,
    "Webhook handler": "def webhook()" in content,
    "Instagram webhook": "object='instagram'" in content or 'object == "instagram"' in content,
    "WhatsApp webhook": "whatsapp_business_account" in content,
}

all_ok = True
for name, ok in checks.items():
    status = "YES" if ok else "MISSING!"
    if not ok:
        all_ok = False
    print(f"  {name}: {status}")

# Check no corruption
corrupted = sum(1 for l in lines if '***' in l)
print(f"  *** corruption: {corrupted}")
if corrupted > 0:
    all_ok = False

# Syntax check
try:
    compile(content, 'server.py', 'exec')
    print("  SYNTAX: 100% OK!")
except SyntaxError as e:
    print(f"  SYNTAX ERROR: {e}")
    all_ok = False

print(f"\nOverall: {'ALL GOOD! 🎉' if all_ok else 'SOME ISSUES!'}")
