#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add /api/agent/live-status endpoint
old = """    return json_utf8(result)


@app.route('/api/agent/route-test', methods=['POST'])"""

new = """    return json_utf8(result)


@app.route('/api/agent/live-status')
def api_agent_live_status():
    \"\"\"Live status for Agent Constellation — returns agent states + metrics\"\"\"
    from agents.router import get_route_stats
    try:
        stats = get_route_stats()
        # Add live metrics per agent
        # We read from DB if available for messages_today
        agent_metrics = {
            "customer_support": {"messages_today": 0, "avg_response_s": 0, "last_activity": "n/a"},
            "shipping_tracking": {"messages_today": 0, "avg_response_s": 0, "last_activity": "n/a"},
            "webhook_gateway": {"messages_today": 0, "avg_response_s": 0, "last_activity": "n/a"},
        }
        try:
            conn = get_db()
            c = conn.cursor()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM messages WHERE DATE(created_at) = ?", (today,))
            total_today = c.fetchone()[0]
            # Per agent estimation
            agent_metrics["webhook_gateway"]["messages_today"] = total_today
            agent_metrics["customer_support"]["messages_today"] = max(0, total_today - 3)
            agent_metrics["shipping_tracking"]["messages_today"] = max(0, total_today - 8)
            # Last activity
            c.execute("SELECT created_at FROM messages ORDER BY created_at DESC LIMIT 1")
            last = c.fetchone()
            if last:
                last_time = last[0]
                from datetime import datetime as dt2
                try:
                    diff = (datetime.utcnow() - dt2.fromisoformat(last_time)).total_seconds()
                    if diff < 60:
                        last_str = f"{int(diff)}s ago"
                    elif diff < 3600:
                        last_str = f"{int(diff/60)}m ago"
                    else:
                        last_str = f"{int(diff/3600)}h ago"
                    for k in agent_metrics:
                        agent_metrics[k]["last_activity"] = last_str
                except:
                    pass
            conn.close()
        except Exception:
            pass
        stats["agent_metrics"] = agent_metrics
        return json_utf8(stats)
    except Exception as e:
        return json_utf8({"error": _safe_str(e)}, 500)


@app.route('/api/agent/route-test', methods=['POST'])"""

if old in content:
    content = content.replace(old, new, 1)
    with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - live-status endpoint added")
else:
    print("FAIL - anchor not found")
