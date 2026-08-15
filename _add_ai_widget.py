#!/usr/bin/env python3
"""إضافة AI Agent Chat Widget في POS"""
with open('templates/pos/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add AI nav button before sidebar-spacer
old_nav = 'button class="nav-item" data-view="purchases-list"'
ai_nav_btn = 'button class="nav-item" data-view="ai-agent" onclick="switchView(\'ai-agent\')" title="AI Inventory Agent"><i class="fas fa-robot" style="color:#00e5ff"></i></button>'

# Find purchases-list button and add AI button after it
marker = 'title="Liste achats"><i class="fas fa-file-import"></i></button>'
replace_idx = content.find(marker)
if replace_idx == -1:
    print("ERROR: Could not find marker for purchases-list button")
    exit(1)
end_of_button = replace_idx + len(marker)
# Insert AI button after purchases-list button, before sidebar-spacer
spacer_marker = 'div class="sidebar-spacer"'
content = content[:end_of_button] + '\n            <' + ai_nav_btn + '\n            <' + spacer_marker + content[end_of_button:]

print(f"1. Added AI nav button (len={len(content)})")

# 2. Add AI agent view-container before purchases-list view
old_purchases = '<!-- PURCHASE LIST (LISTE DES ACHATS) -->'
ai_view_html = '''            <!-- AI AGENT CHAT WIDGET -->
            <div class="view-container" id="view-ai-agent" style="flex-direction:row;">
                <div class="ai-agent-chat">
                    <div class="ai-header">
                        <i class="fas fa-robot"></i>
                        <span>Inventory AI Agent</span>
                        <span class="ai-status">Online</span>
                    </div>
                    <div class="ai-messages" id="ai-messages">
                        <div class="ai-msg ai-bot">
                            <div class="ai-msg-bubble">
                                Bonjour! Je suis l\'Agent d\'inventaire. Je peux vous aider:<br>
                                Ajouter un produit<br>
                                Verifier le stock<br>
                                Modifier les prix<br>
                                Lister les produits<br>
                                Produits en rupture
                            </div>
                        </div>
                    </div>
                    <div class="ai-input-area">
                        <input type="text" id="ai-input" class="ai-input" placeholder="Ex: zid hwaya rouge taille 38 b 2500 DA..." onkeydown="if(event.key==='Enter') aiSendMessage()">
                        <button class="ai-send-btn" onclick="aiSendMessage()"><i class="fas fa-paper-plane"></i></button>
                    </div>
                </div>
                <div class="ai-logs">
                    <div class="ai-logs-header">
                        <i class="fas fa-history"></i>
                        <span>Actions log</span>
                    </div>
                    <div id="ai-logs-content" class="ai-logs-content">
                        <div class="ai-log-empty">Aucune action pour l\'instant</div>
                    </div>
                </div>
            </div>

            ''' + old_purchases

content = content.replace('<!-- PURCHASE LIST (LISTE DES ACHATS) -->', ai_view_html)

print(f"2. Added AI view container (len={len(content)})")

# 3. Add AI Agent CSS and JavaScript
css_marker = '</style>'
ai_css = '''

        /* ===== AI Agent Chat Widget ===== */
        .ai-agent-chat {
            width: 380px; min-width: 380px;
            display: flex; flex-direction: column;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
        }
        .ai-header {
            display: flex; align-items: center; gap: 10px;
            padding: 14px 18px;
            background: #1a1a2e;
            color: #fff;
            font-weight: 600;
            border-bottom: 1px solid #16213e;
        }
        .ai-header .fa-robot { color: #00e5ff; font-size: 18px; }
        .ai-status {
            margin-left: auto;
            font-size: 11px; color: #4ade80;
            background: rgba(74,222,128,0.15);
            padding: 2px 10px; border-radius: 10px;
        }
        .ai-messages {
            flex: 1; overflow-y: auto; padding: 14px;
            display: flex; flex-direction: column; gap: 10px;
            background: #f8f9fc;
        }
        .ai-msg { display: flex; flex-direction: column; }
        .ai-msg.ai-bot { align-items: flex-start; }
        .ai-msg.ai-user { align-items: flex-end; }
        .ai-msg-bubble {
            max-width: 90%; padding: 10px 14px;
            border-radius: 12px; font-size: 13px; line-height: 1.5;
        }
        .ai-bot .ai-msg-bubble {
            background: #fff; color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        .ai-user .ai-msg-bubble {
            background: #2563eb; color: #fff;
            border-bottom-right-radius: 4px;
        }
        .ai-msg-time {
            font-size: 10px; color: #999; margin-top: 2px;
        }
        .ai-input-area {
            display: flex; gap: 8px; padding: 10px 14px;
            background: #fff; border-top: 1px solid #e0e0e0;
        }
        .ai-input {
            flex: 1; padding: 10px 14px;
            border: 1px solid #ddd; border-radius: 24px;
            font-size: 13px; outline: none;
            background: var(--bg-input);
        }
        .ai-input:focus { border-color: #2563eb; }
        .ai-send-btn {
            width: 40px; height: 40px; border: none;
            background: #2563eb; color: #fff;
            border-radius: 50%; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: 0.15s;
        }
        .ai-send-btn:hover { background: #1d4ed8; }
        .ai-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .ai-typing .ai-msg-bubble::after {
            content: ''; display: inline-block;
            width: 8px; height: 8px; background: #999;
            border-radius: 50%; animation: ai-blink 1s infinite;
        }
        @keyframes ai-blink { 50% { opacity: 0; } }

        /* AI Logs (side panel) */
        .ai-logs {
            flex: 1; display: flex; flex-direction: column;
            background: #fff; min-width: 200px;
        }
        .ai-logs-header {
            display: flex; align-items: center; gap: 8px;
            padding: 14px 18px;
            background: #f8f9fc; border-bottom: 1px solid #e0e0e0;
            font-weight: 600; font-size: 13px; color: #555;
        }
        .ai-logs-content {
            flex: 1; overflow-y: auto; padding: 10px 14px;
        }
        .ai-log-item {
            padding: 8px 10px; margin-bottom: 6px;
            border-radius: 6px; font-size: 12px;
            border-left: 3px solid #2563eb;
            background: #f8f9fc;
        }
        .ai-log-item.success { border-left-color: #4ade80; background: #f0fdf4; }
        .ai-log-item.error { border-left-color: #ef4444; background: #fef2f2; }
        .ai-log-item .log-action { font-weight: 600; color: #333; }
        .ai-log-item .log-detail { color: #666; margin-top: 2px; }
        .ai-log-empty { color: #999; font-size: 12px; text-align: center; padding: 30px 10px; }
'''

content = content.replace('</style>', ai_css + '\n</style>')

print(f"3. Added AI CSS (len={len(content)})")

# 4. Add AI JavaScript before closing </body>
js_marker = '</body>'
ai_js = '''
<script>
/* ===== AI Agent Chat ===== */
function aiSendMessage() {
    var input = document.getElementById('ai-input');
    var text = input.value.trim();
    if (!text) return;
    
    input.value = '';
    var msgs = document.getElementById('ai-messages');
    
    // Add user message
    var userDiv = document.createElement('div');
    userDiv.className = 'ai-msg ai-user';
    userDiv.innerHTML = '<div class="ai-msg-bubble">' + escapeHtml(text) + '</div><div class="ai-msg-time">' + new Date().toLocaleTimeString() + '</div>';
    msgs.appendChild(userDiv);
    msgs.scrollTop = msgs.scrollHeight;
    
    // Show typing indicator
    var typingDiv = document.createElement('div');
    typingDiv.className = 'ai-msg ai-bot ai-typing';
    typingDiv.id = 'ai-typing';
    typingDiv.innerHTML = '<div class="ai-msg-bubble">...</div>';
    msgs.appendChild(typingDiv);
    msgs.scrollTop = msgs.scrollHeight;
    
    var sBtn = document.querySelector('.ai-send-btn');
    sBtn.disabled = true;
    
    // Call API
    fetch('/api/v1/agent/process', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        // Remove typing
        var typing = document.getElementById('ai-typing');
        if (typing) typing.remove();
        
        var botDiv = document.createElement('div');
        botDiv.className = 'ai-msg ai-bot';
        var msg = data.message || '';
        botDiv.innerHTML = '<div class="ai-msg-bubble">' + escapeHtml(msg).replace(/\\n/g, '<br>') + '</div><div class="ai-msg-time">' + new Date().toLocaleTimeString() + '</div>';
        msgs.appendChild(botDiv);
        msgs.scrollTop = msgs.scrollHeight;
        
        // Add action log
        if (data.action && data.action !== 'unknown') {
            addAiLog(data.action, data.message || 'Action executed', data.success);
        }
    })
    .catch(function(err) {
        var typing = document.getElementById('ai-typing');
        if (typing) typing.remove();
        var errDiv = document.createElement('div');
        errDiv.className = 'ai-msg ai-bot';
        errDiv.innerHTML = '<div class="ai-msg-bubble" style="background:#fef2f2;color:#dc2626;border-color:#fca5a5;">Erreur de connexion au serveur</div>';
        msgs.appendChild(errDiv);
    })
    .finally(function() {
        sBtn.disabled = false;
    });
}

function addAiLog(action, detail, success) {
    var logContent = document.getElementById('ai-logs-content');
    var empty = logContent.querySelector('.ai-log-empty');
    if (empty) empty.remove();
    
    var item = document.createElement('div');
    item.className = 'ai-log-item' + (success ? ' success' : ' error');
    item.innerHTML = '<div class="log-action">' + action + '</div><div class="log-detail">' + escapeHtml(detail).substring(0, 80) + '</div>';
    logContent.insertBefore(item, logContent.firstChild);
}

function escapeHtml(s) {
    if (!s) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(s));
    return div.innerHTML;
}
</script>
'''

content = content.replace('</body>', ai_js + '\n</body>')

print(f"4. Added AI JavaScript (len={len(content)})")

with open('templates/pos/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE! AI Agent Chat Widget added to POS.")
