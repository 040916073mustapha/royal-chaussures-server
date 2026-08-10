# fix_prompt_shopify.py
# Update system prompt to mention Shopify real-time lookup
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find [2. Scope of Authority & Shopify Integration] section
old_prompt_line = (
    '        "- Visuals & Links: When customers ask for product details or photos,'
    ' provide accurate information and store links retrieved from Shopify.\\n"'
)

new_prompt_line = (
    '        "- Visuals & Links: When customers ask for product details or photos,'
    ' provide accurate information and store links retrieved from Shopify.\\n"\n'
    '        "- Real-Time Check: You have direct Shopify API access. '
    'When a customer asks about any product, availability, size, color, or price, '
    'call search_shopify_products() to look up the latest data in real-time. '
    'Before confirming an order, call check_product_inventory() to verify stock availability.\\n"'
)

if old_prompt_line in content:
    content = content.replace(old_prompt_line, new_prompt_line)
    print("SUCCESS: Updated prompt with Shopify real-time instructions")
else:
    # Try exact version from file
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Visuals & Links' in line:
            print(f"Found at line {i+1}: |{line}|")
            lines[i] = lines[i].rstrip() + '\n' + new_prompt_line.split('\n')[1]
            content = '\n'.join(lines)
            print("Updated inline")
            break

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
