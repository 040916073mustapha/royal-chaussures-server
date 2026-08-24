import re

with open('rcagents_saas_core/frontend/templates/dashboard.html', 'r', encoding='utf-8') as f:
    tpl = f.read()

# Replace the x-data block and remove methods from it
# Strategy: find the full x-data span, pull out methods, put them in script

# Step 1: Replace x-init reference
tpl = tpl.replace('x-init="', 'x-init="dashInit(this)"')

# Step 2: The x-data="{ ... }" block - we just need to remove the methods from it
# Find the connectShopify(), connectMeta(), connectZR() methods inside x-data
# They start with "    connectShopify() {" and end with "    },"
# Replace them with just "    integrationStatus: {}"

old_block = """    integrationStatus: {},
    connectShopify() {
        const statusLog = document.getElementById('connectionStatusLog');
        const s = this.storeId || localStorage.getItem('rc_store_id');
        const shopify = this.integrations.shopify;
        statusLog.innerHTML = '<p class=\"text-neon-cyan\">\\u{1F504} Connecting to Shopify...</p>';
        fetch('/api/integrations/connect', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store_id:s, platform:'shopify', credentials:{shopify_domain:shopify.url, access_token:shopify.token}, sync:true}) })
        .then(r=>r.json()).then(data=>{ if(data.success){ statusLog.innerHTML='<p class=\"text-emerald-400\">\\u2705 '+data.message+'</p>'; this.integrationStatus.shopify=true; } else { statusLog.innerHTML='<p class=\"text-rose-400\">\\u274C '+data.error+'</p>'; } })
        .catch(err=>{ statusLog.innerHTML='<p class=\"text-rose-400\">\\u274C '+err.message+'</p>'; });
    },
    connectMeta() {
        const statusLog = document.getElementById('connectionStatusLog');
        const s = this.storeId || localStorage.getItem('rc_store_id');
        const meta = this.integrations.meta;
        statusLog.innerHTML = '<p class=\"text-neon-cyan\">\\u{1F504} Verifying Meta token...</p>';
        fetch('/api/integrations/connect', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store_id:s, platform:'meta', credentials:{access_token:meta.token, page_id:meta.pageId}}) })
        .then(r=>r.json()).then(data=>{ if(data.success){ statusLog.innerHTML='<p class=\"text-emerald-400\">\\u2705 '+data.message+'</p>'; this.integrationStatus.meta=true; } else { statusLog.innerHTML='<p class=\"text-rose-400\">\\u274C '+data.error+'</p>'; } })
        .catch(err=>{ statusLog.innerHTML='<p class=\"text-rose-400\">\\u274C '+err.message+'</p>'; });
    },
    connectZR() {
        const statusLog = document.getElementById('connectionStatusLog');
        const s = this.storeId || localStorage.getItem('rc_store_id');
        const zr = this.integrations.zr;
        statusLog.innerHTML = '<p class=\"text-neon-cyan\">\\u{1F504} Connecting to ZR Express...</p>';
        fetch('/api/integrations/connect', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store_id:s, platform:'zr_express', credentials:{api_key:zr.apiKey}}) })
        .then(r=>r.json()).then(data=>{ if(data.success){ statusLog.innerHTML='<p class=\"text-emerald-400\">\\u2705 '+data.message+'</p>'; this.integrationStatus.zr=true; } else { statusLog.innerHTML='<p class=\"text-rose-400\">\\u274C '+data.error+'</p>'; } })
        .catch(err=>{ statusLog.innerHTML='<p class=\"text-rose-400\">\\u274C '+err.message+'</p>'; });
    }
}"""

new_block = """    integrationStatus: {}
}"""

tpl = tpl.replace(old_block, new_block)

# Step 3: Remove old script and add new one
tpl = re.sub(
    r'<script>[\s\S]*?</script>\s*\n',
    '',
    tpl
)

print(f"Has x-data with methods: {old_block[:60] in tpl}")
print(f"Has new clean x-data: {new_block in tpl}")

# Add script at the end
SCRIPT = """<script>
// Dashboard state factory
function dashData() {
    return {
        stats: {}, orders: [], orderList: [], msgs: [], products: [], 
        loading: true, convCount: 0, msgCount: 0, 
        storeId: 'royal-main', storeName: 'Royal Chaussures', page: 'overview',
        integrations: { shopify: { url: '', token: '' }, meta: { token: '', pageId: '' }, zr: { apiKey: '' } },
        integrationStatus: {}
    };
}
// Dashboard init (called from x-init)
function dashInit(el) {
    try {
        var d = el.__x.$data;
        d.storeId = localStorage.getItem('rc_store_id') || 'royal-main';
        var tp = '{{ active_page | default("overview") }}';
        if (tp && ['overview','orders','products','clients','chat','settings','analytics','marketing','inventory','shipments','integrations','agents','auto-ship','constellation'].indexOf(tp) >= 0) {
            d.page = tp;
        }
    } catch(e) { if(el.__x && el.__x.$data) el.__x.$data.page = 'overview'; }
    
    var d = el.__x.$data;
    
    function loadOverview() {
        Promise.all([
            fetch('/api/stats?store_id=' + d.storeId).then(function(r){return r.json()}).then(function(d2){ d.stats=d2; d.storeName=d2.store_name||'Royal Chaussures' }).catch(function(){}).then(function(){ return fetch('/api/orders?store_id=' + d.storeId + '&limit=10').then(function(r){return r.json()}).then(function(d2){d.orders=d2.orders||[]}).catch(function(){}) }),
            fetch('/api/messages?limit=200').then(function(r){return r.json()}).then(function(d2){ if(d2.success){ d.msgs=d2.messages; d.msgCount=d2.count; var s=new Set(); d2.messages.forEach(function(m){s.add(m.sender_id+'|'+m.platform)}); d.convCount=s.size } }).catch(function(){})
        ]).finally(function(){d.loading=false});
    }
    function loadOrdersPage() {
        fetch('/api/orders?store_id=' + d.storeId + '&limit=50').then(function(r){return r.json()}).then(function(d2){ d.orderList=d2.orders||[] }).catch(function(){}).finally(function(){d.loading=false});
    }
    function loadProductsPage() {
        fetch('/api/products?store_id=' + d.storeId).then(function(r){return r.json()}).then(function(d2){ d.products=d2.products||[] }).catch(function(){}).finally(function(){d.loading=false});
    }
    
    try {
        if (d.page === 'overview') { setTimeout(loadOverview, 50); }
        else if (d.page === 'orders') { setTimeout(loadOrdersPage, 50); }
        else if (d.page === 'products') { setTimeout(loadProductsPage, 50); }
        else { d.loading = false; }
    } catch(e) { d.loading = false; }
}

// Global connect functions (called from @click in integrations.html)
function connectShopify() {
    var el = document.querySelector('[x-data]');
    if (!el || !el.__x) return;
    var d = el.__x.$data;
    var log = document.getElementById('connectionStatusLog');
    var shopify = d.integrations.shopify;
    log.innerHTML = 'Connecting to Shopify...';
    fetch('/api/integrations/connect', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store_id:d.storeId, platform:'shopify', credentials:{shopify_domain:shopify.url, access_token:shopify.token}, sync:true}) })
    .then(function(r){return r.json()}).then(function(data){ if(data.success){ log.innerHTML='Connected!'; d.integrationStatus.shopify=true; } else { log.innerHTML='Error: '+data.error; } })
    .catch(function(err){ log.innerHTML='Failed: '+err.message; });
}
function connectMeta() {
    var el = document.querySelector('[x-data]');
    if (!el || !el.__x) return;
    var d = el.__x.$data;
    var log = document.getElementById('connectionStatusLog');
    var meta = d.integrations.meta;
    log.innerHTML = 'Verifying Meta token...';
    fetch('/api/integrations/connect', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store_id:d.storeId, platform:'meta', credentials:{access_token:meta.token, page_id:meta.pageId}}) })
    .then(function(r){return r.json()}).then(function(data){ if(data.success){ log.innerHTML='Meta connected!'; d.integrationStatus.meta=true; } else { log.innerHTML='Error: '+data.error; } })
    .catch(function(err){ log.innerHTML='Failed: '+err.message; });
}
function connectZR() {
    var el = document.querySelector('[x-data]');
    if (!el || !el.__x) return;
    var d = el.__x.$data;
    var log = document.getElementById('connectionStatusLog');
    var zr = d.integrations.zr;
    log.innerHTML = 'Connecting to ZR Express...';
    fetch('/api/integrations/connect', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({store_id:d.storeId, platform:'zr_express', credentials:{api_key:zr.apiKey}}) })
    .then(function(r){return r.json()}).then(function(data){ if(data.success){ log.innerHTML='ZR connected!'; d.integrationStatus.zr=true; } else { log.innerHTML='Error: '+data.error; } })
    .catch(function(err){ log.innerHTML='Failed: '+err.message; });
}
</script>
{% endblock %}"""

tpl = tpl.replace('{% endblock %}', SCRIPT)

with open('rcagents_saas_core/frontend/templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(tpl)

print('Done! File updated.')
