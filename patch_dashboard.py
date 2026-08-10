#!/usr/bin/env python3
"""
تحديث dashboard_server.py: استبدال DASHBOARD_HTML + إضافة API endpoints جديدة
"""

import os, shutil, re

SRC = r'C:\Users\Micro-Tech\.openclaw\workspace\dashboard_server.py'
BAK = SRC + '.bak'

# ==============================================================================
# NEW DASHBOARD_HTML
# ==============================================================================
NEW_HTML = r'''DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Royal Chaussures — لوحة التحكم</title>
    <!-- PWA -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#111111">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Royal Admin">
    <!-- Fonts: Playfair Display + Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Font Awesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <!-- html2pdf.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.2/html2pdf.bundle.min.js"></script>
    <style>
:root{
  --bg-primary:#0a0a0a;--bg-secondary:#111;--bg-card:#1a1a1a;--bg-glass:rgba(255,255,255,0.04);--bg-glass-hover:rgba(255,255,255,0.08);
  --text-primary:#f5f0eb;--text-secondary:#999490;--text-muted:#666360;
  --gold:#c9a96e;--gold-light:#e0c992;--gold-dark:#a88848;
  --border:rgba(255,255,255,0.08);--shadow:0 8px 32px rgba(0,0,0,0.4);
  --radius:16px;--radius-sm:10px;--radius-lg:24px;--sidebar-width:260px;
  --accent-red:#dc3545;--accent-green:#28a745;--accent-blue:#0d6efd;--accent-orange:#fd7e14;--accent-purple:#6f42c1;--accent-cyan:#17a2b8;
  --font-heading:'Playfair Display',Georgia,serif;--font-body:'Inter',-apple-system,sans-serif;
}
[data-theme="light"]{
  --bg-primary:#f5f0eb;--bg-secondary:#fff;--bg-card:#fff;--bg-glass:rgba(0,0,0,0.03);--bg-glass-hover:rgba(0,0,0,0.06);
  --text-primary:#1a1a1a;--text-secondary:#555;--text-muted:#999;
  --gold:#b8860b;--gold-light:#d4a843;--gold-dark:#8b6508;--border:rgba(0,0,0,0.08);--shadow:0 8px 32px rgba(0,0,0,0.1);
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-body);background:var(--bg-primary);color:var(--text-primary);min-height:100vh;transition:background .3s,color .3s}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-thumb{background:var(--gold-dark);border-radius:3px}

.sidebar{position:fixed;right:0;top:0;width:var(--sidebar-width);height:100vh;background:var(--bg-secondary);border-left:1px solid var(--border);padding:28px 20px;display:flex;flex-direction:column;z-index:100}
.sidebar .brand{display:flex;align-items:center;gap:12px;margin-bottom:4px}
.sidebar .brand-icon{width:40px;height:40px;background:linear-gradient(135deg,var(--gold),var(--gold-dark));border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px}
.sidebar .brand-text h2{font-family:var(--font-heading);font-size:18px;color:var(--text-primary);font-weight:600}
.sidebar .brand-text .subtitle{font-size:11px;color:var(--text-muted);letter-spacing:1px}
.sidebar .nav-section{margin-top:36px;flex:1}
.sidebar .nav-label{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);margin-bottom:12px;padding:0 12px}
.sidebar a.nav-item{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:var(--radius-sm);color:var(--text-secondary);text-decoration:none;margin-bottom:4px;transition:all .3s;font-size:14px}
.sidebar a.nav-item i{width:20px;text-align:center;font-size:16px;color:var(--text-muted)}
.sidebar a.nav-item:hover{background:var(--bg-glass-hover);color:var(--text-primary)}
.sidebar a.nav-item.active{background:var(--bg-glass);color:var(--gold);border:1px solid rgba(201,169,110,0.15)}
.sidebar .sidebar-footer{border-top:1px solid var(--border);padding-top:16px}
.sidebar .sidebar-footer a{display:flex;align-items:center;gap:12px;padding:10px 16px;border-radius:var(--radius-sm);color:var(--text-muted);text-decoration:none;font-size:13px;transition:all .3s}
.sidebar .sidebar-footer a:hover{color:var(--text-primary);background:var(--bg-glass)}
.sidebar-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:99}
.mobile-menu-btn{display:none;position:fixed;top:16px;right:16px;z-index:101;width:44px;height:44px;border-radius:12px;border:1px solid var(--border);background:var(--bg-card);color:var(--text-primary);font-size:20px;cursor:pointer;align-items:center;justify-content:center}

.main{margin-right:var(--sidebar-width);padding:32px 40px;min-height:100vh}
.page-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:32px;flex-wrap:wrap;gap:16px}
.page-header .header-left h1{font-family:var(--font-heading);font-size:28px;font-weight:600;color:var(--text-primary)}
.page-header .header-left p{color:var(--text-secondary);font-size:14px;margin-top:6px}
.page-header .header-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}

.theme-toggle{width:42px;height:42px;border-radius:12px;border:1px solid var(--border);background:var(--bg-glass);color:var(--text-secondary);font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .3s}
.theme-toggle:hover{background:var(--bg-glass-hover);color:var(--gold)}

.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:var(--radius-sm);border:none;cursor:pointer;font-family:var(--font-body);font-size:13px;font-weight:500;transition:all .3s;text-decoration:none}
.btn-gold{background:linear-gradient(135deg,var(--gold),var(--gold-dark));color:#fff}
.btn-gold:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(201,169,110,0.3)}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text-secondary)}
.btn-outline:hover{border-color:var(--gold);color:var(--gold)}
.btn-glass{background:var(--bg-glass);border:1px solid var(--border);color:var(--text-secondary)}
.btn-glass:hover{background:var(--bg-glass-hover);color:var(--text-primary)}
.btn-sm{padding:6px 14px;font-size:12px}

.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:32px}
.stat-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;position:relative;overflow:hidden;transition:all .3s}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--gold),var(--gold-light));opacity:0.6}
.stat-card:hover{transform:translateY(-4px);box-shadow:var(--shadow);border-color:var(--gold-dark)}
.stat-card .stat-icon{width:40px;height:40px;border-radius:12px;background:var(--bg-glass);display:flex;align-items:center;justify-content:center;font-size:18px;color:var(--gold);margin-bottom:16px}
.stat-card .number{font-family:var(--font-heading);font-size:32px;font-weight:700;color:var(--text-primary);line-height:1}
.stat-card .label{color:var(--text-muted);font-size:13px;margin-top:8px}
.stat-card .trend{font-size:11px;margin-top:8px;display:flex;align-items:center;gap:4px}
.trend-up{color:var(--accent-green)}

.glass-section{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px;margin-bottom:28px}
.glass-section .section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}
.glass-section .section-title{font-family:var(--font-heading);font-size:18px;font-weight:600;color:var(--text-primary);display:flex;align-items:center;gap:10px}
.glass-section .section-title i{color:var(--gold);font-size:20px}

.charts-grid{display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:28px}
.chart-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px}
.chart-card .chart-title{font-family:var(--font-heading);font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:16px;display:flex;align-items:center;gap:8px}
.chart-card .chart-title i{color:var(--gold)}
.chart-card canvas{max-height:250px}

.table-wrapper{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{text-align:right;padding:14px 16px;color:var(--text-muted);font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid var(--border)}
td{padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:14px;color:var(--text-primary)}
tr:hover td{background:var(--bg-glass)}
[data-theme="light"] td{border-bottom:1px solid rgba(0,0,0,0.04)}

.badge{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600}
.badge-pending{background:rgba(255,193,7,0.12);color:#ffc107}
.badge-confirmed{background:rgba(13,110,253,0.12);color:#0d6efd}
.badge-processing{background:rgba(111,66,193,0.12);color:#6f42c1}
.badge-shipped{background:rgba(23,162,184,0.12);color:#17a2b8}
.badge-delivered{background:rgba(40,167,69,0.12);color:#28a745}
.badge-cancelled{background:rgba(220,53,69,0.12);color:#dc3545}

.pwa-banner{display:none;align-items:center;gap:12px;background:linear-gradient(135deg,var(--gold-dark),var(--gold));color:#fff;padding:12px 20px;border-radius:var(--radius-sm);margin-bottom:16px;font-size:13px}
.pwa-banner.show{display:flex}
.pwa-banner .pwa-close{margin-right:auto;background:rgba(255,255,255,0.2);border:none;color:#fff;width:28px;height:28px;border-radius:50%;cursor:pointer}

.install-btn{display:none}
.install-btn.show{display:inline-flex}

.notif-badge{display:none;position:absolute;top:-4px;left:-4px;width:18px;height:18px;border-radius:50%;background:var(--accent-red);color:#fff;font-size:10px;font-weight:700;align-items:center;justify-content:center}
.notif-badge.show{display:flex}

.toast-container{position:fixed;bottom:24px;left:24px;z-index:9999;display:flex;flex-direction:column;gap:8px}
.toast{display:flex;align-items:center;gap:12px;padding:16px 20px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border);color:var(--text-primary);font-size:14px;min-width:280px;max-width:400px;animation:slideIn .3s ease}
.toast i{font-size:20px}
.toast-success i{color:var(--accent-green)}
.toast-error i{color:var(--accent-red)}
.toast-info i{color:var(--accent-blue)}
.toast-new-order i{color:var(--gold)}
@keyframes slideIn{from{transform:translateX(100px);opacity:0}to{transform:translateX(0);opacity:1}}

.empty-state{text-align:center;padding:48px 24px;color:var(--text-muted)}
.empty-state i{font-size:48px;color:var(--gold);opacity:0.4;margin-bottom:16px}
.spinner{display:inline-block;width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

@media(max-width:768px){
  .sidebar{transform:translateX(100%);transition:transform .3s}.sidebar.open{transform:translateX(0)}
  .sidebar-overlay.open{display:block}.mobile-menu-btn{display:flex}
  .main{margin-right:0;padding:16px;padding-top:72px}
  .stats-grid{grid-template-columns:repeat(2,1fr)}.charts-grid{grid-template-columns:1fr}
  .glass-section{padding:16px}.stat-card{padding:16px}.stat-card .number{font-size:24px}
}
@media(max-width:480px){.stats-grid{grid-template-columns:1fr 1fr;gap:10px}}
</style>
</head>
<body>
<button class="mobile-menu-btn" onclick="toggleSidebar()" id="menuBtn"><i class="fas fa-bars"></i></button>
<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
<div class="sidebar" id="sidebar">
  <div class="brand"><div class="brand-icon">👠</div><div class="brand-text"><h2>Royal Chaussures</h2><div class="subtitle">Admin Dashboard</div></div></div>
  <div class="nav-section">
    <div class="nav-label">القائمة الرئيسية</div>
    <a href="/" class="nav-item active"><i class="fas fa-chart-pie"></i> لوحة التحكم</a>
    <a href="/orders" class="nav-item"><i class="fas fa-box"></i> الطلبات</a>
    <a href="#" class="nav-item" onclick="showNotifHistory()"><i class="fas fa-bell"></i> الإشعارات <span class="notif-badge" id="notifBadge">0</span></a>
    <a href="/system/status" class="nav-item"><i class="fas fa-cog"></i> حالة النظام</a>
  </div>
  <div class="sidebar-footer">
    <a href="#" id="installAppBtn" class="install-btn" onclick="installPWA()"><i class="fas fa-download"></i> تثبيت التطبيق</a>
    <a href="/logout"><i class="fas fa-sign-out-alt"></i> تسجيل الخروج</a>
  </div>
</div>
<div class="main">
  <div class="pwa-banner" id="pwaBanner">
    <i class="fas fa-mobile-alt"></i> <span>قم بتثبيت تطبيق Royal Admin على جهازك</span>
    <button class="pwa-close" onclick="this.parentElement.classList.remove('show')">✕</button>
  </div>
  <div class="page-header">
    <div class="header-left">
      <h1>لوحة التحكم</h1>
      <p><i class="fas fa-user"></i> مرحباً {{ session.username }}! <span id="liveTime"></span></p>
    </div>
    <div class="header-actions">
      <button class="btn btn-outline btn-sm" onclick="exportPdf('stats','إحصائيات')"><i class="fas fa-file-pdf"></i> PDF</button>
      <button class="btn btn-outline btn-sm" onclick="exportPdf('orders','الطلبات')"><i class="fas fa-file-pdf"></i> تصدير PDF</button>
      <button class="btn btn-gold btn-sm" onclick="syncOrders()"><i class="fas fa-sync"></i> مزامنة</button>
      <button class="theme-toggle" onclick="toggleTheme()"><i class="fas fa-moon" id="themeIcon"></i></button>
    </div>
  </div>
  <button class="btn btn-gold btn-sm install-btn" onclick="installPWA()" style="margin-bottom:16px"><i class="fas fa-download"></i> تثبيت التطبيق</button>

  <div class="stats-grid" id="stats">
    <div class="stat-card"><div class="stat-icon"><i class="fas fa-shopping-bag"></i></div><div class="number">{{ stats.total_orders }}</div><div class="label">إجمالي الطلبات</div><div class="trend trend-up"><i class="fas fa-arrow-up"></i> {{ stats.today_orders }} جديد اليوم</div></div>
    <div class="stat-card"><div class="stat-icon"><i class="fas fa-clock"></i></div><div class="number">{{ stats.by_status.get('pending',0) }}</div><div class="label">قيد الانتظار</div></div>
    <div class="stat-card"><div class="stat-icon"><i class="fas fa-check-circle"></i></div><div class="number">{{ stats.by_status.get('confirmed',0) }}</div><div class="label">مؤكدة</div></div>
    <div class="stat-card"><div class="stat-icon"><i class="fas fa-truck"></i></div><div class="number">{{ stats.by_status.get('shipped',0)+stats.by_status.get('delivered',0) }}</div><div class="label">تم الشحن/التوصيل</div></div>
    <div class="stat-card"><div class="stat-icon"><i class="fas fa-calendar-day"></i></div><div class="number">{{ stats.today_orders }}</div><div class="label">طلبات اليوم</div></div>
    <div class="stat-card"><div class="stat-icon"><i class="fas fa-check-double"></i></div><div class="number">{{ stats.by_fulfillment.get('fulfilled',0) }}</div><div class="label">منفذة بالكامل</div></div>
  </div>

  <div class="charts-grid" id="charts">
    <div class="chart-card"><div class="chart-title"><i class="fas fa-chart-line"></i> المبيعات — آخر 30 يوم</div><canvas id="salesChart"></canvas></div>
    <div class="chart-card"><div class="chart-title"><i class="fas fa-chart-pie"></i> حالات الطلبات</div><canvas id="statusChart"></canvas></div>
    <div class="chart-card" style="grid-column:1/-1"><div class="chart-title"><i class="fas fa-chart-bar"></i> المنتجات الأكثر مبيعاً</div><canvas id="topProductsChart"></canvas></div>
  </div>

  <div class="glass-section" id="orders">
    <div class="section-header">
      <div class="section-title"><i class="fas fa-list"></i> آخر الطلبات</div>
      <div>
        <button class="btn btn-glass btn-sm" onclick="exportPdf('orders','الطلبات-الأخيرة')"><i class="fas fa-file-pdf"></i> PDF</button>
        <button class="btn btn-gold btn-sm" onclick="syncOrders()"><i class="fas fa-sync"></i> مزامنة</button>
      </div>
    </div>
    <div class="table-wrapper">
      {% if stats.recent_orders %}
      <table>
        <thead><tr><th>الطلب</th><th>الزبون</th><th>المبلغ</th><th>الحالة</th><th>التاريخ</th></tr></thead>
        <tbody>
          {% for order in stats.recent_orders %}
          <tr onclick="window.location='/orders/{{ order.id }}'" style="cursor:pointer">
            <td><strong>{{ order.order_name }}</strong></td>
            <td>{{ order.customer_name or '—' }}</td>
            <td>{{ order.total_amount }} د.ج</td>
            <td><span class="badge badge-{{ order.status }}">{{ order.status }}</span></td>
            <td>{{ order.created_at[:10] if order.created_at else '—' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% else %}
      <div class="empty-state"><i class="fas fa-inbox"></i><p>لا توجد طلبات بعد. قم بمزامنة Shopify أو انتظر وصول طلب جديد</p></div>
      {% endif %}
    </div>
  </div>
</div>
<div class="toast-container" id="toastContainer"></div>

<script>
let deferredPrompt=null,lastCheckTime=Math.floor(Date.now()/1000);
let salesChart=null,statusChart=null,productsChart=null;

// Theme
(function(){const s=localStorage.getItem('theme');if(s){document.documentElement.setAttribute('data-theme',s);document.getElementById('themeIcon').className=s==='light'?'fas fa-sun':'fas fa-moon';}})();
function toggleTheme(){const c=document.documentElement.getAttribute('data-theme'),n=c==='light'?'dark':'light';document.documentElement.setAttribute('data-theme',n);localStorage.setItem('theme',n);document.getElementById('themeIcon').className=n==='light'?'fas fa-sun':'fas fa-moon';}

// PWA
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;document.querySelectorAll('.install-btn').forEach(el=>el.classList.add('show'));document.getElementById('pwaBanner').classList.add('show');});
window.addEventListener('appinstalled',()=>{deferredPrompt=null;document.querySelectorAll('.install-btn').forEach(el=>el.classList.remove('show'));document.getElementById('pwaBanner').classList.remove('show');showToast('✅ تم تثبيت التطبيق بنجاح!','success');});
function installPWA(){if(!deferredPrompt){showToast('⚠️ يمكنك التثبيت من قائمة المتصفح','info');return;}deferredPrompt.prompt();deferredPrompt.userChoice.then(()=>{deferredPrompt=null;document.querySelectorAll('.install-btn').forEach(el=>el.classList.remove('show'));});}
if('serviceWorker'in navigator)navigator.serviceWorker.register('/service-worker.js').catch(()=>{});

// Sidebar
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open');document.getElementById('sidebarOverlay').classList.toggle('open');}

// Toast
function showToast(msg,type='info'){const c=document.getElementById('toastContainer'),t=document.createElement('div');const icons={success:'fa-check-circle',error:'fa-exclamation-circle',info:'fa-info-circle','new-order':'fa-cart-plus'};t.className='toast toast-'+type;t.innerHTML='<i class="fas '+(icons[type]||'fa-info-circle')+'"></i> '+msg;c.appendChild(t);setTimeout(()=>{t.style.opacity='0';setTimeout(()=>t.remove(),300);},4000);}

// Live Clock
function updateClock(){const d=new Date();const el=document.getElementById('liveTime');if(el)el.textContent='🕐 '+d.toLocaleTimeString('ar-DZ',{hour:'2-digit',minute:'2-digit'});}
updateClock();setInterval(updateClock,30000);

// New Order Check (every 30s)
function checkNewOrders(){fetch('/api/orders/new-check?since='+lastCheckTime).then(r=>r.json()).then(d=>{if(d.new_orders>0){document.getElementById('notifBadge').textContent=d.new_orders;document.getElementById('notifBadge').classList.add('show');showToast('🆕 '+d.new_orders+' طلب/طلبات جديدة!','new-order');}lastCheckTime=d.checked_at||Math.floor(Date.now()/1000);}).catch(()=>{});}
setInterval(checkNewOrders,30000);setTimeout(checkNewOrders,5000);

// Sync
function syncOrders(){const btn=event&&event.target?event.target.closest('button'):null;if(btn){btn.disabled=true;btn.innerHTML='<span class="spinner"></span>';}
fetch('/api/sync',{method:'POST'}).then(r=>r.json()).then(d=>{if(d.success){showToast('✅ تمت المزامنة!','success');setTimeout(()=>location.reload(),1500);}else showToast('❌ فشلت المزامنة','error');if(btn){btn.disabled=false;btn.innerHTML='<i class="fas fa-sync"></i> مزامنة';}}).catch(()=>{if(btn){btn.disabled=false;btn.innerHTML='<i class="fas fa-sync"></i> مزامنة';}});}

// Notif History
function showNotifHistory(){showToast('🔔 سجل الإشعارات قيد التطوير','info');}

// Charts
function initCharts(){
  fetch('/api/stats/chart-data').then(r=>r.json()).then(data=>{
    if(data.sales_30d&&document.getElementById('salesChart')){
      const labels=data.sales_30d.map(d=>d.date.slice(5)),values=data.sales_30d.map(d=>d.total);
      if(salesChart)salesChart.destroy();
      salesChart=new Chart('salesChart',{type:'line',data:{labels,datasets:[{label:'المبيعات (د.ج)',data,borderColor:'#c9a96e',backgroundColor:'rgba(201,169,110,0.1)',fill:true,tension:0.4,pointBackgroundColor:'#c9a96e',pointBorderColor:'#fff',pointRadius:3,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#999490',font:{family:'Inter'}}}},scales:{x:{ticks:{color:'#666360',font:{size:11}},grid:{color:'rgba(255,255,255,0.05)'}},y:{ticks:{color:'#666360',font:{size:11}},grid:{color:'rgba(255,255,255,0.05)'}}}}});
    }
    if(data.status_counts&&document.getElementById('statusChart')){
      const labels=Object.keys(data.status_counts),values=Object.values(data.status_counts);
      const colors={pending:'#ffc107',confirmed:'#0d6efd',processing:'#6f42c1',shipped:'#17a2b8',delivered:'#28a745',cancelled:'#dc3545'};
      if(statusChart)statusChart.destroy();
      statusChart=new Chart('statusChart',{type:'doughnut',data:{labels,datasets:[{data:values,backgroundColor:labels.map(l=>colors[l]||'#666'),borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{color:'#999490',font:{family:'Inter',size:11},padding:12}}}}});
    }
    if(data.top_products&&document.getElementById('topProductsChart')){
      const labels=data.top_products.map(p=>p.name),values=data.top_products.map(p=>p.count);
      if(productsChart)productsChart.destroy();
      productsChart=new Chart('topProductsChart',{type:'bar',data:{labels,datasets:[{label:'عدد المبيعات',data:values,backgroundColor:'rgba(201,169,110,0.6)',borderColor:'#c9a96e',borderWidth:1,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{labels:{color:'#999490',font:{family:'Inter'}}}},scales:{x:{ticks:{color:'#666360',font:{size:11}},grid:{color:'rgba(255,255,255,0.05)'}},y:{ticks:{color:'#999490',font:{size:11}},grid:{display:false}}}}});
    }
  }).catch(()=>{});
}

// PDF Export
function exportPdf(elementId,filename){
  const el=document.getElementById(elementId);
  if(!el){showToast('⚠️ القسم غير موجود','error');return;}
  showToast('📄 جاري إنشاء PDF...','info');
  html2pdf().set({margin:[10,10,10,10],filename:'Royal_'+filename+'.pdf',image:{type:'jpeg',quality:0.98},html2canvas:{scale:2,useCORS:true,backgroundColor:getComputedStyle(document.body).getPropertyValue('--bg-primary')||'#0a0a0a'},jsPDF:{unit:'mm',format:'a4',orientation:'portrait'}}).from(el).save().then(()=>showToast('✅ تم تصدير PDF!','success')).catch(()=>showToast('❌ فشل تصدير PDF','error'));
}

// Init
document.addEventListener('DOMContentLoaded',function(){setTimeout(initCharts,500);updateClock();});
</script>
</body>
</html>
"""'''

# ==============================================================================
# NEW API ENDPOINTS
# ==============================================================================
NEW_ENDPOINTS = r'''

# ========== API Endpoints جديدة (Dashboard Charts/Notifications) ==========

@app.route("/api/orders/new-check", methods=["GET"])
@require_auth
def api_new_orders_check():
    """فحص الطلبات الجديدة منذ آخر فحص (للإشعارات اللحظية)"""
    since = request.args.get("since", "0")
    try:
        since_ts = int(since)
    except:
        since_ts = 0

    # عدد الطلبات التي تم إنشاؤها في آخر دقيقتين
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE created_at >