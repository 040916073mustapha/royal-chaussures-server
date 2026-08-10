# create_templates.py
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
os.makedirs(templates_dir, exist_ok=True)

templates = {
    "dashboard_base.html": """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Royal Chaussures - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script>
        tailwind.config = { darkMode: "class", theme: { extend: { colors: { royal: { 50: "#fdf2f8", 100: "#fce7f3", 200: "#fbcfe8", 300: "#f9a8d4", 400: "#f472b6", 500: "#db2777", 600: "#be185d", 700: "#9d174d", 800: "#831843", 900: "#500724" } } } } }
        document.documentElement.classList.add("dark");
    </script>
</head>
<body class="bg-[#0f0f13] text-gray-100 font-sans" x-data="app()">
    <div class="flex h-screen">
        <aside class="w-64 bg-[#1a1a23] border-l border-[#2a2a35] p-4 flex flex-col">
            <div class="text-center mb-6 py-3">
                <h1 class="text-xl font-bold bg-gradient-to-r from-royal-400 to-pink-400 bg-clip-text text-transparent">Royal Chaussures</h1>
                <p class="text-xs text-gray-500">SaaS Dashboard</p>
            </div>
            <nav class="space-y-1 flex-1">
                <a href="/dashboard" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition {{ 'bg-royal-600/20 text-royal-300 border border-royal-500/30' if active == 'dashboard' else 'text-gray-400 hover:bg-[#252530] hover:text-white' }}">
                    <span>📊</span> <span>لوحة التحكم</span>
                </a>
                <a href="/dashboard/orders" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition {{ 'bg-royal-600/20 text-royal-300 border border-royal-500/30' if active == 'orders' else 'text-gray-400 hover:bg-[#252530] hover:text-white' }}">
                    <span>📦</span> <span>الطلبات</span>
                </a>
                <a href="/dashboard/products" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition {{ 'bg-royal-600/20 text-royal-300 border border-royal-500/30' if active == 'products' else 'text-gray-400 hover:bg-[#252530] hover:text-white' }}">
                    <span>👟</span> <span>المنتجات</span>
                </a>
                <a href="/dashboard/clients" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition {{ 'bg-royal-600/20 text-royal-300 border border-royal-500/30' if active == 'clients' else 'text-gray-400 hover:bg-[#252530] hover:text-white' }}">
                    <span>👥</span> <span>العملاء</span>
                </a>
                <a href="/dashboard/settings" class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition {{ 'bg-royal-600/20 text-royal-300 border border-royal-500/30' if active == 'settings' else 'text-gray-400 hover:bg-[#252530] hover:text-white' }}">
                    <span>⚙️</span> <span>الإعدادات</span>
                </a>
            </nav>
            <div class="text-center text-xs text-gray-600 mt-4 pt-4 border-t border-[#2a2a35]">RC Agent v2.0</div>
        </aside>
        <main class="flex-1 overflow-y-auto p-6 bg-[#0f0f13]">
            {% block content %}{% endblock %}
        </main>
    </div>
    <script>function app(){return{init(){}}}</script>
</body>
</html>
""",

    "dashboard_stats.html": """{% extends "dashboard_base.html" %}
{% block content %}
<div x-data="{ stats: {}, orders: [] }" x-init="fetch('/api/stats').then(r=>r.json()).then(d=>stats=d); fetch('/api/orders').then(r=>r.json()).then(d=>orders=d.orders||[])">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-[#1a1a23] rounded-xl p-5 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">إجمالي الطلبات</p>
            <p class="text-3xl font-bold text-white mt-1" x-text="stats.total_orders || 0"></p>
        </div>
        <div class="bg-[#1a1a23] rounded-xl p-5 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">المؤكدة</p>
            <p class="text-3xl font-bold text-emerald-400 mt-1" x-text="stats.confirmed || 0"></p>
        </div>
        <div class="bg-[#1a1a23] rounded-xl p-5 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">الإيرادات</p>
            <p class="text-3xl font-bold text-royal-400 mt-1" x-text="(stats.revenue||0).toLocaleString() + ' د.ج'"></p>
        </div>
        <div class="bg-[#1a1a23] rounded-xl p-5 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">معدل التوصيل</p>
            <p class="text-3xl font-bold text-blue-400 mt-1" x-text="(stats.delivery_rate||0) + '%'"></p>
        </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-[#1a1a23] rounded-xl p-4 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">قيد الانتظار</p>
            <p class="text-2xl font-bold text-yellow-400" x-text="stats.pending || 0"></p>
        </div>
        <div class="bg-[#1a1a23] rounded-xl p-4 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">تم التوصيل</p>
            <p class="text-2xl font-bold text-green-400" x-text="stats.delivered || 0"></p>
        </div>
        <div class="bg-[#1a1a23] rounded-xl p-4 border border-[#2a2a35]">
            <p class="text-gray-400 text-sm">العملاء</p>
            <p class="text-2xl font-bold text-purple-400" x-text="stats.clients_count || 0"></p>
        </div>
    </div>
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] p-5">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">آخر الطلبات</h2>
            <a href="/dashboard/orders" class="text-royal-400 text-sm hover:underline">عرض الكل →</a>
        </div>
        <template x-if="orders.length === 0"><p class="text-gray-500 text-center py-8">لا توجد طلبات بعد</p></template>
        <template x-for="o in orders.slice(0,10)" :key="o.id">
            <div class="flex items-center justify-between py-3 border-b border-[#2a2a35] last:border-0">
                <div>
                    <p class="font-medium" x-text="o.customer||'زبون'"></p>
                    <p class="text-sm text-gray-400" x-text="o.product + (o.variant?' - '+o.variant:'')"></p>
                </div>
                <div class="text-left">
                    <span class="text-xs px-2 py-1 rounded" :class="{'bg-emerald-500/20 text-emerald-400':o.status=='Confirme','bg-yellow-500/20 text-yellow-400':o.status=='Nouveau','bg-red-500/20 text-red-400':o.status=='Annule','bg-blue-500/20 text-blue-400':o.status=='Livre'}" x-text="o.status"></span>
                    <p class="text-sm text-gray-400 mt-1" x-text="(o.total||0).toLocaleString() + ' د.ج'"></p>
                </div>
            </div>
        </template>
    </div>
</div>
{% endblock %}""",

    "dashboard_orders.html": """{% extends "dashboard_base.html" %}
{% block content %}
<div x-data="{ orders:[], statusFilter:'', searchQuery:'', loadOrders(){ let u='/api/orders?'; if(this.statusFilter) u+='status='+this.statusFilter; if(this.searchQuery) u+=(this.statusFilter?'&':'')+'search='+encodeURIComponent(this.searchQuery); fetch(u).then(r=>r.json()).then(d=>this.orders=d.orders||[]) }, updateStatus(id,status){ fetch('/api/orders/'+id+'/status',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})}).then(r=>r.json()).then(d=>{ if(d.success) this.loadOrders() }) } }" x-init="loadOrders()">
    <div class="flex justify-between items-center mb-4">
        <h1 class="text-2xl font-bold">📦 إدارة الطلبات</h1>
        <div class="flex gap-2">
            <select x-model="statusFilter" @change="loadOrders()" class="bg-[#1a1a23] border border-[#2a2a35] rounded-lg px-3 py-2 text-sm">
                <option value="">الكل</option>
                <option value="Nouveau">جديد</option>
                <option value="Confirme">مؤكد</option>
                <option value="Livre">تم التوصيل</option>
                <option value="Annule">ملغي</option>
            </select>
            <input type="text" x-model="searchQuery" @keyup.enter="loadOrders()" placeholder="بحث..." class="bg-[#1a1a23] border border-[#2a2a35] rounded-lg px-3 py-2 text-sm w-48">
        </div>
    </div>
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] overflow-hidden">
        <table class="w-full text-sm">
            <thead class="bg-[#252530] text-gray-400">
                <tr><th class="p-3 text-right">الزبون</th><th class="p-3 text-right">المنتج</th><th class="p-3 text-right">الولاية</th><th class="p-3 text-right">المجموع</th><th class="p-3 text-right">الحالة</th><th class="p-3 text-right">التاريخ</th><th class="p-3 text-center">إجراءات</th></tr>
            </thead>
            <tbody>
                <template x-for="o in orders" :key="o.id">
                    <tr class="border-t border-[#2a2a35] hover:bg-[#252530]/50">
                        <td class="p-3"><p x-text="o.customer||'-'" class="font-medium"></p><p x-text="o.phone||''" class="text-xs text-gray-500"></p></td>
                        <td class="p-3"><p x-text="o.product"></p><p x-text="o.variant" class="text-xs text-gray-500"></p></td>
                        <td class="p-3 text-gray-400" x-text="o.wilaya||'-'"></td>
                        <td class="p-3" x-text="(o.total||0).toLocaleString()+' د.ج'"></td>
                        <td class="p-3"><span class="text-xs px-2 py-1 rounded" :class="{'bg-emerald-500/20 text-emerald-400':o.status=='Confirme','bg-yellow-500/20 text-yellow-400':o.status=='Nouveau','bg-red-500/20 text-red-400':o.status=='Annule','bg-blue-500/20 text-blue-400':o.status=='Livre'}" x-text="o.status"></span></td>
                        <td class="p-3 text-gray-400 text-xs" x-text="o.date"></td>
                        <td class="p-3 text-center">
                            <select @change="updateStatus(o.id, $event.target.value)" class="bg-[#1a1a23] border border-[#2a2a35] rounded text-xs px-2 py-1">
                                <option value="Nouveau">جديد</option>
                                <option value="Confirme">تأكيد</option>
                                <option value="Livre">توصيل</option>
                                <option value="Annule">إلغاء</option>
                            </select>
                        </td>
                    </tr>
                </template>
                <tr x-show="orders.length===0"><td colspan="7" class="p-8 text-center text-gray-500">لا توجد طلبات</td></tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "dashboard_products.html": """{% extends "dashboard_base.html" %}
{% block content %}
<div x-data="{ products:[] }" x-init="fetch('/api/products').then(r=>r.json()).then(d=>products=d.products||[])">
    <h1 class="text-2xl font-bold mb-4">👟 المنتجات والمخزون</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <template x-for="p in products" :key="p.id">
            <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] overflow-hidden">
                <div class="h-40 bg-[#252530] flex items-center justify-center">
                    <img :src="p.image" :alt="p.title" class="h-full w-full object-cover" x-show="p.image">
                    <span x-show="!p.image" class="text-gray-600 text-4xl">👟</span>
                </div>
                <div class="p-4">
                    <h3 class="font-semibold" x-text="p.title"></h3>
                    <p class="text-sm text-gray-400 mt-1"><span x-text="p.variants + ' مقاس'"></span> <span x-text="p.stock + ' مخزون'"></span></p>
                    <p class="text-royal-400 font-bold mt-2" x-text="(p.price_min==p.price_max ? p.price_min.toLocaleString() : p.price_min.toLocaleString()+' - '+p.price_max.toLocaleString()) + ' د.ج'"></p>
                </div>
            </div>
        </template>
    </div>
    <div x-show="products.length===0" class="text-center py-12 text-gray-500">جاري تحميل المنتجات...</div>
</div>
{% endblock %}""",

    "dashboard_clients.html": """{% extends "dashboard_base.html" %}
{% block content %}
<div x-data="{ clients:[] }" x-init="fetch('/api/clients').then(r=>r.json()).then(d=>clients=d.clients||[])">
    <h1 class="text-2xl font-bold mb-4">👥 العملاء</h1>
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] overflow-hidden">
        <table class="w-full text-sm">
            <thead class="bg-[#252530] text-gray-400">
                <tr><th class="p-3 text-right">الاسم</th><th class="p-3 text-right">رقم الهاتف</th><th class="p-3 text-right">الولاية</th><th class="p-3 text-right">الطلبات</th><th class="p-3 text-right">الإجمالي</th><th class="p-3 text-right">آخر طلب</th></tr>
            </thead>
            <tbody>
                <template x-for="c in clients" :key="c.id">
                    <tr class="border-t border-[#2a2a35] hover:bg-[#252530]/50">
                        <td class="p-3 font-medium" x-text="c.name||'-'"></td>
                        <td class="p-3 text-gray-400" x-text="c.phone||'-'"></td>
                        <td class="p-3 text-gray-400" x-text="c.wilaya||'-'"></td>
                        <td class="p-3"><span class="text-royal-400 font-bold" x-text="c.orders"></span></td>
                        <td class="p-3" x-text="(c.spent||0).toLocaleString()+' د.ج'"></td>
                        <td class="p-3 text-xs text-gray-500" x-text="c.last_order ? c.last_order.slice(0,10) : '-'"></td>
                    </tr>
                </template>
                <tr x-show="clients.length===0"><td colspan="6" class="p-8 text-center text-gray-500">لا يوجد عملاء بعد</td></tr>
            </tbody>
        </table>
    </div>
</div>
{% endblock %}""",

    "dashboard_settings.html": """{% extends "dashboard_base.html" %}
{% block content %}
<h1 class="text-2xl font-bold mb-4">⚙️ الإعدادات</h1>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] p-5">
        <h2 class="text-lg font-semibold mb-3">🚚 ZR Express</h2>
        <div class="space-y-3">
            <div><p class="text-sm text-gray-400">حالة الاتصال</p><p class="text-emerald-400 font-medium">🟢 متصل</p></div>
            <div><p class="text-sm text-gray-400">Tenant ID</p><p class="font-mono text-xs text-gray-300">d2217f31-20f1-43c6-abd4-c420788a63ed</p></div>
        </div>
    </div>
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] p-5">
        <h2 class="text-lg font-semibold mb-3">🤖 AI Agent</h2>
        <div><p class="text-sm text-gray-400">النموذج: <span class="text-white">DeepSeek-V4-Flash</span></p></div>
        <div class="mt-2"><p class="text-sm text-gray-400">المنصات: <span class="text-emerald-400">Messenger, WhatsApp, Instagram</span></p></div>
    </div>
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] p-5">
        <h2 class="text-lg font-semibold mb-3">📱 Automations</h2>
        <p class="text-sm text-gray-400">سيتم إضافة إرسال رسائل WhatsApp التلقائية قريباً</p>
    </div>
    <div class="bg-[#1a1a23] rounded-xl border border-[#2a2a35] p-5">
        <h2 class="text-lg font-semibold mb-3">🛍️ Shopify</h2>
        <p class="text-sm text-gray-400">المتجر: <span class="text-white">rwqchh-na.myshopify.com</span></p>
        <p class="text-sm text-gray-400 mt-1">المزامنة: <span class="text-emerald-400">تلقائية</span></p>
    </div>
</div>
{% endblock %}"""
}

for filename, content in templates.items():
    path = os.path.join(templates_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f"Created: {filename}")

print(f"\nAll {len(templates)} templates created in {templates_dir}")
