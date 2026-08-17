# fix_server.py
# Fix send_ig_reply function in server.py
import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Build the new function by constructing it safely
new_func_lines = []
new_func_lines.append("def send_ig_reply(sender_id, user_message):")
new_func_lines.append("    try:")
new_func_lines.append("        reply_text = generate_ai_reply(user_message, sender_id)")
new_func_lines.append("")
new_func_lines.append("        # Priority: Page Token (has MESSAGING permission)")
new_func_lines.append("        page_token = get_fb_page_token()")
new_func_lines.append("        if page_token:")
new_func_lines.append("            ig_token = page_token")
new_func_lines.append('            logger.info("Using Page Token for Instagram reply")')
new_func_lines.append("        else:")
new_func_lines.append("            ig_token = INSTAGRAM_ACCESS_TOKEN")
new_func_lines.append('            logger.warning("No page token, trying INSTAGRAM_ACCESS_TOKEN")')
new_func_lines.append("")
new_func_lines.append("        if not ig_token:")
new_func_lines.append('            logger.warning("No token available for Instagram reply")')
new_func_lines.append("            return")
new_func_lines.append("")
new_func_lines.append("        # Instagram DMs use /me/messages with a Page Token")
new_func_lines.append('        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ig_token}"')
new_func_lines.append('        payload = {"recipient": {"id": sender_id}, "message": {"text": reply_text}}')
new_func_lines.append('        headers = {"Content-Type": "application/json"}')
new_func_lines.append("        resp = requests.post(url, json=payload, headers=headers, timeout=10)")
new_func_lines.append("        if resp.status_code == 200:")
new_func_lines.append('            logger.info(f"IG reply sent to {sender_id}: {reply_text[:60]}...")')
new_func_lines.append("        else:")
new_func_lines.append("            err_body = resp.text[:300]")
new_func_lines.append('            logger.warning(f"IG send failed ({resp.status_code}): {err_body}")')
new_func_lines.append("            if 'does not exist' in err_body or 'capability' in err_body.lower():")
new_func_lines.append("                logger.info(\"Instagram reply needs 'Instagram Graph API' product.\")")
new_func_lines.append("                logger.info(\"Fix: Add Instagram Graph API in Meta Developer App.\")")
new_func_lines.append("    except Exception as e:")
new_func_lines.append('        logger.error(f"send_ig_reply error: {_safe_str(e)}")')
new_func_lines.append("")

new_func = '\n'.join(new_func_lines)

# Find the old function boundaries
lines = content.split('\n')
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'def send_ig_reply' in line:
        start_idx = i
    if start_idx is not None and i > start_idx + 1:
        stripped = line.strip()
        if stripped.startswith('def ') or stripped.startswith('# ---') or stripped.startswith('# ???') or stripped.startswith('# \u2500'):
            end_idx = i
            break

if end_idx is None:
    # Find next function or section
    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith('def ') or (stripped.startswith('#') and i > start_idx + 5):
            end_idx = i
            break

if end_idx is None:
    end_idx = len(lines)

print(f"Replacing lines {start_idx+1} to {end_idx}")

# Build new content
before = '\n'.join(lines[:start_idx])
after = '\n'.join(lines[end_idx:])

new_content = before + '\n' + new_func + after

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

# Verify syntax
try:
    compile(new_content, 'server.py', 'exec')
    print("SYNTAX: OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")

print("\nNew function:")
for line in new_func_lines:
    print(f"  {line}")
