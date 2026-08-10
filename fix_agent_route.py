# fix_agent_route.py - Fix agent_route reference in server_complete.py

path = r'C:\Users\Micro-Tech\.openclaw\workspace\server_complete.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old get_atlas_response that still references agent_route
old_code = '''def get_atlas_response(msg, uid, platform="messenger"):
    """DeepSeek AI response via DeepInfra"""
    try:
        reply = get_ai_response(msg, uid, platform)
        if reply:
            return reply
        return get_auto_reply(msg)
    except Exception as e:
        _log_safe(logger.error, "AI response error", e)
        return get_auto_reply(msg)'''

new_code = '''def get_atlas_response(msg, uid, platform="messenger"):
    """DeepSeek AI response via DeepInfra"""
    try:
        reply = get_ai_response(msg, uid, platform)
        if reply:
            return reply
        return get_auto_reply(msg)
    except Exception as e:
        _log_safe(logger.error, "AI response error", e)
        return get_auto_reply(msg)'''

# البحث عن أي reference لـ agent_route غير المرغوب فيه
import re

# Check if the code has the OLD function (from original file)
old_original = '''def get_atlas_response(msg, uid, platform="messenger"):
    """??????? ??? router ????? ?????? ??????? ?????? ???????"""
    try:
        reply, agent_id, used_ai = agent_route(
            message=msg,
            platform=platform,
            uid=uid,
            openclaw_api_url=OPENCLAW_API_URL,
            openclaw_token=OPENCLAW_TOKEN
        )
        logger.info(f"[Agent:{agent_id}] AI={used_ai} Platform={platform} UID={uid[:20]}")
        return reply
    except Exception as e:
        _log_safe(logger.error, "Agent route error", e)
        return get_auto_reply(msg)'''

if old_original in content:
    content = content.replace(old_original, new_code)
    print("Replaced old get_atlas_response (original version)")
else:
    print("Old get_atlas_response NOT found - checking for other agent_route refs...")
    # Search for any remaining agent_route references
    if 'agent_route' in content:
        positions = [(m.start(), m.group()) for m in re.finditer(r'agent_route', content)]
        print(f"Found {len(positions)} references to agent_route")
        for pos, match in positions:
            line_num = content[:pos].count('\n') + 1
            print(f"  Line {line_num}: ...{content[max(0,pos-20):pos+30]}...")
        
        # Find and replace the function that uses agent_route
        # Remove the import line
        content = content.replace('from agents.router import route as agent_route, set_active_agent, get_active_agent, get_route_stats\n', '')
        # Replace agent_route calls with empty
        content = content.replace('agent_route(', 'get_ai_response(')
    else:
        print("No agent_route references found - maybe already fixed")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Final syntax check
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('\nSyntax: OK')
except py_compile.PyCompileError as e:
    print(f'\nSyntax error: {e}')
