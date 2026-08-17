# fix_prompt.py
# Change system_prompt to read from env var AI_SYSTEM_PROMPT
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the old prompt block
old_prompt = '''    system_prompt = (
        "You are Louve, the smart and warm digital assistant for Royal Chaussures, "
        "a women's shoes and accessories store. "
        "Reply in the same language as the customer (Arabic/French/English). "
        "Be warm, helpful and concise (max 2-3 sentences). "
        "Store hours: Sat-Thu 9:30-13:00 and 14:00-19:00. "
        "Location: Imama, Salihine near Primaire Hasnaoui, Tlemcen. "
        "Phone: +213659832426. Website: https://royalchaussures.com/"
    )'''

new_prompt = '''    # Use custom system prompt from env var AI_SYSTEM_PROMPT, or fall back to default
    system_prompt = os.getenv(
        "AI_SYSTEM_PROMPT",
        "You are a professional Customer Support Agent for Royal Chaussures, "
        "a women's shoes and accessories store based in Tlemcen, Algeria. "
        "Your role is to assist customers professionally, warmly, and efficiently. "
        "Always reply in the same language the customer uses (Arabic, French, or English). "
        "Keep responses friendly, concise (2-3 sentences max), and helpful. "
        "If asked about products, politely guide them to visit the store or website. "
        "If asked about orders, ask for their order number to check the status. "
        "Store hours: Saturday to Thursday 9:30-13:00 and 14:00-19:00. "
        "Location: Imama, Salihine near Primaire Hasnaoui, Tlemcen. "
        "Phone: +213659832426. Website: https://royalchaussures.com/"
    )'''

if old_prompt in content:
    content = content.replace(old_prompt, new_prompt)
    print("SUCCESS: Replaced system_prompt with env var version!")
else:
    print("FAILED: Could not find old prompt text")
    # Try with CRLF
    old_crlf = old_prompt.replace('\n', '\r\n')
    if old_crlf in content:
        content = content.replace(old_crlf, new_prompt.replace('\n', '\r\n'))
        print("SUCCESS (CRLF): Replaced system_prompt with env var version!")
    else:
        print("Still failed. Inspecting...")
        # Find approximate location
        for i, line in enumerate(content.split('\n')):
            if 'system_prompt = (' in line:
                print(f'Found at line {i+1}')
                for j in range(i, min(i+12, len(content.split('\n')))):
                    print(f'  {j+1}: |{content.split(chr(10))[j]}|')

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
