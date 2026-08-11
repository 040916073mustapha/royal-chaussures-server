/**
 * Royal POS — JavaScript Engine
 * ShopLine Classic Light Theme
 */

// ==============================================
//  GLOBAL STATE
// ==============================================
var STATE = {
    token: null,
    user: null,
    cart: [],
    products: [],
    allProducts: [],
    categories: new Set(),
    selectedPayment: 'cash',
    lastSale: null,
    isOffline: false,
    pendingSales: JSON.parse(localStorage.getItem('pos_pending') || '[]'),
    _lastBarcodeTime: 0,
    _barcodeBuffer: ''
};

// ==============================================
//  GLOBAL API CONFIG
// ==============================================
var API = (() => {
    const base = '/api/v1/store';
    return {
        headers: () => ({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${STATE.token || ''}`
        }),
        async login(username, password) {
            const r = await fetch(`${base}/auth/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            return r.json();
        },
        async getProducts() {
            const r = await fetch(`${base}/products`, {headers: this.headers()});
            return r.json();
        },
        async searchProducts(q) {
            const r = await fetch(`${base}/products/search?q=${encodeURIComponent(q)}&limit=50`, 
                {headers: this.headers()});
            return r.json();
        },
        async getByBarcode(code) {
            const r = await fetch(`${base}/products/barcode/${encodeURIComponent(code)}`,
                {headers: this.headers()});
            return r.json();
        },
        async recordSale(data) {
            if (STATE.isOffline) {
                return this._saveOffline(data);
            }
            const r = await fetch(`${base}/sales`, {
                method: 'POST',
                headers: this.headers(),
                body: JSON.stringify(data)
            });
            const result = await r.json();
            if (!r.ok && result.error && (result.error.includes('timeout') || r.status >= 500)) {
                return this._saveOffline(data);
            }
            return result;
        },
        async _saveOffline(data) {
            const pending = JSON.parse(localStorage.getItem('pos_pending') || '[]');
            pending.push({...data, _offlineId: Date.now(), _createdAt: new Date().toISOString()});
            localStorage.setItem('pos_pending', JSON.stringify(pending));
            return {sale: {receipt_number: `OFFLINE-${Date.now()}`, total: data.total || 0}, _offline: true};
        },
        async syncPending() {
            const pending = JSON.parse(localStorage.getItem('pos_pending') || '[]');
            if (pending.length === 0) return;
            const stillPending = [];
            for (const sale of pending) {
                try {
                    const r = await fetch(`${base}/sales`, {
                        method: 'POST', headers: this.headers(), body: JSON.stringify(sale)
                    });
                    if (!r.ok) stillPending.push(sale);
                } catch { stillPending.push(sale); }
            }
            localStorage.setItem('pos_pending', JSON.stringify(stillPending));
        }
    };
})();

// ==============================================
//  DIGITAL CLOCK
// ==============================================
function startClock() {
    function update() {
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        const el = document.getElementById('digital-clock');
        if (el) el.textContent = `${h}:${m}:${s}`;
    }
    update();
    setInterval(update, 1000);
}

// ==============================================
//  LOGIN
// ==============================================
async function login() {
    const user = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-pass').value.trim();
    const btn = document.getElementById('login-btn');
    const err = document.getElementById('login-error');

    if (!user || !pass) { err.textContent = 'يرجى إدخال اسم المستخدم وكلمة السر'; err.style.display = 'block'; return; }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> جاري تسجيل الدخول...';
    err.style.display = 'none';

    const result = await API.login(user, pass);
    
    if (result.token) {
        STATE.token = result.token;
        STATE.user = result.user;
        localStorage.setItem('pos_token', result.token);
        localStorage.setItem('pos_user', JSON.stringify(result.user));
        showApp();
        loadProducts();
        updateConnectionStatus();
        startClock();
    } else {
        err.textContent = result.error || 'خطأ في تسجيل الدخول';
        err.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> تسجيل الدخول';
    }
}

// ---- Auto-login from localStorage ----
(function autoLogin() {
    const token = localStorage.getItem('pos_token');
    const user = localStorage.getItem('pos_user');
    if (token && user) {
        STATE.token = token;
        STATE.user = JSON.parse(user);
        showApp();
        loadProducts();
        updateConnectionStatus();
        startClock();
    }
})();

function showApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('pos-app').classList.add('active');
    
    const displayName = STATE.user?.display_name || STATE.user?.username || 'مدير المحل';
    const role = STATE.user?.role === 'admin' ? 'Admin' : 'Store';
    
    // Sidebar
    document.getElementById('sidebar-name').textContent = displayName;
    document.getElementById('sidebar-role').textContent = role;
    document.getElementById('sidebar-avatar').textContent = displayName.charAt(0).toUpperCase();
    
    document.getElementById('page-title').textContent = '🛒 مبيعة جديدة';
    document.getElementById('barcode-input').focus();
}

function logout() {
    STATE.token = null;
    STATE.user = null;
    STATE.cart = [];
    localStorage.removeItem('pos_token');
    localStorage.removeItem('pos_user');
    document.getElementById('pos-app').classList.remove('active');
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('login-user').value = '';
    document.getElementById('login-pass').value = '';
    document.getElementById('login-btn').disabled = false;
    document.getElementById('login-btn').innerHTML = '<i class="fas fa-sign-in-alt"></i> تسجيل الدخول';
}

// ==============================================
//  VIEW SWITCHER (Sidebar Navigation)
// ==============================================
function switchView(viewId) {
    // Update sidebar active
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewId);
    });
    
    // Update view containers
    document.querySelectorAll('.view-container').forEach(v => {
        v.classList.remove('active');
    });
    
    const target = document.getElementById('view-' + viewId);
    if (target) {
        target.classList.add('active');
    }
    
    // Update page title
    const titles = {
        'sale': '🛒 مبيعة جديدة',
        'purchase': '🛍️ شراء جديد',
        'products': '📦 قائمة المنتجات',
        'sales-list': '📜 قائمة المبيعات',
        'purchases-list': '📁 قائمة المشتريات'
    };
    document.getElementById('page-title').textContent = titles[viewId] || viewId;
    
    // Special handling
    if (viewId === 'products') {
        renderProductsTable();
    }
}

// ==============================================
//  PRODUCTS
// ==============================================
async function loadProducts() {
    try {
        const data = await API.getProducts();
        STATE.allProducts = data.products || [];
        
        // Extract categories
        STATE.categories = new Set();
        STATE.allProducts.forEach(p => {
            if (p.category) STATE.categories.add(p.category);
        });
        
        renderCategories();
        STATE.products = [...STATE.allProducts];
        renderProducts(STATE.products);
        renderProductsTable();
    } catch (e) {
        showToast('فشل تحميل المنتجات: ' + e.message, 'error');
    }
}

function renderCategories() {
    const container = document.getElementById('categories');
    container.innerHTML = '<button class="cat-btn active" onclick="filterCategory(\'all\')">الكل</button>';
    STATE.categories.forEach(cat => {
        container.innerHTML += `<button class="cat-btn" onclick="filterCategory('${cat}')">${cat}</button>`;
    });
}

function filterCategory(cat) {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    
    if (cat === 'all') STATE.products = [...STATE.allProducts];
    else STATE.products = STATE.allProducts.filter(p => p.category === cat);
    renderProducts(STATE.products);
}

function renderProducts(products) {
    const grid = document.getElementById('products-grid');
    if (!grid) return;
    if (!products || products.length === 0) {
        grid.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:40px;">لا توجد منتجات</div>';
        return;
    }
    
    grid.innerHTML = products.map(p => {
        const stock = p.store_quantity || 0;
        let stockClass = '';
        let stockText = `${stock} قطعة`;
        if (stock <= 0) { stockClass = 'out'; stockText = 'غير متوفر'; }
        else if (stock <= 5) { stockClass = 'low'; }
        
        return `<div class="product-card" onclick="addToCart(${p.id}, '${p.name.replace(/'/g, "\\'")}', ${p.store_price || p.online_price || 0}, ${stock})">
            <div class="price">${(p.store_price || p.online_price || 0).toLocaleString()} DA</div>
            <div class="name">${p.name}</div>
            ${p.color ? `<div class="color-tag">${p.color}</div>` : ''}
            <div class="stock ${stockClass}">${stockText}</div>
        </div>`;
    }).join('');
}

async function searchProducts(q) {
    if (!q.trim()) {
        STATE.products = [...STATE.allProducts];
        renderProducts(STATE.products);
        return;
    }
    
    try {
        const data = await API.searchProducts(q);
        STATE.products = data.products || [];
        renderProducts(STATE.products);
    } catch {
        STATE.products = STATE.allProducts.filter(p => 
            p.name.includes(q) || p.sku?.includes(q) || p.barcode?.includes(q)
        );
        renderProducts(STATE.products);
    }
}

// ==============================================
//  PRODUCTS TABLE (View)
// ==============================================
function renderProductsTable() {
    const tbody = document.getElementById('products-table-body');
    if (!tbody) return;
    
    if (!STATE.allProducts || STATE.allProducts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="padding:40px;text-align:center;color:var(--text-muted);">لا توجد منتجات</td></tr>';
        return;
    }
    
    tbody.innerHTML = STATE.allProducts.map(p => {
        const stock = p.store_quantity || 0;
        let stockClass = '';
        let stockText = `${stock}`;
        if (stock <= 0) { stockClass = 'color:var(--accent-red);'; stockText = 'غير متوفر'; }
        else if (stock <= 5) { stockClass = 'color:var(--accent-orange);'; }
        
        return `<tr style="border-bottom:1px solid var(--border-light);">
            <td style="padding:10px 16px;font-weight:500;">${p.name}</td>
            <td style="padding:10px 16px;text-align:center;color:var(--text-muted);">${p.color || '—'}</td>
            <td style="padding:10px 16px;text-align:center;color:var(--accent-blue);font-weight:700;">${(p.store_price || p.online_price || 0).toLocaleString()} DA</td>
            <td style="padding:10px 16px;text-align:center;${stockClass}font-weight:500;">${stockText}</td>
        </tr>`;
    }).join('');
    
    // Wire search
    const searchInput = document.getElementById('products-search');
    if (searchInput) {
        searchInput.oninput = function() {
            const q = this.value.toLowerCase();
            const rows = tbody.querySelectorAll('tr');
            rows.forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        };
    }
}

// ==============================================
//  BARCODE SCANNER
// ==============================================
function handleBarcode(e) {
    const input = document.getElementById('barcode-input');
    
    if (e.key === 'Enter') {
        e.preventDefault();
        const code = input.value.trim();
        input.value = '';
        if (code) lookupBarcode(code);
        return;
    }
    
    const now = Date.now();
    if (now - STATE._lastBarcodeTime > 100) STATE._barcodeBuffer = '';
    STATE._barcodeBuffer += e.key;
    STATE._lastBarcodeTime = now;
    
    if (e.key === 'Enter' && STATE._barcodeBuffer.length > 3) {
        lookupBarcode(STATE._barcodeBuffer.replace('Enter', '').trim());
        STATE._barcodeBuffer = '';
        input.value = '';
    }
}

async function lookupBarcode(code) {
    try {
        const data = await API.getByBarcode(code);
        if (data.product) {
            const p = data.product;
            addToCart(p.id, p.name, p.store_price || p.online_price || 0, p.store_quantity || 0);
            showToast(`✅ ${p.name} — ${(p.store_price || p.online_price || 0).toLocaleString()} DA`);
        } else {
            showToast('⚠️ المنتج غير موجود', 'error');
        }
    } catch {
        const found = STATE.allProducts.find(p => p.barcode === code);
        if (found) {
            addToCart(found.id, found.name, found.store_price || found.online_price || 0, found.store_quantity || 0);
        } else {
            showToast('⚠️ باركود غير معروف', 'error');
        }
    }
}

// ==============================================
//  CART
// ==============================================
function addToCart(id, name, price, stock) {
    if (stock <= 0) {
        showToast('⚠️ هذا المنتج غير متوفر حالياً', 'error');
        return;
    }
    
    const existing = STATE.cart.find(item => item.id === id);
    if (existing) {
        if (existing.qty >= stock) {
            showToast(`⚠️ الكمية القصوى: ${stock}`, 'error');
            return;
        }
        existing.qty++;
    } else {
        STATE.cart.push({ id, name, price, qty: 1, stock });
    }
    
    renderCart();
    
    const el = document.getElementById('cart-count');
    if (el) {
        el.style.transform = 'scale(1.3)';
        setTimeout(() => el.style.transform = 'scale(1)', 200);
    }
}

function removeFromCart(id) {
    STATE.cart = STATE.cart.filter(item => item.id !== id);
    renderCart();
}

function updateQty(id, delta) {
    const item = STATE.cart.find(i => i.id === id);
    if (!item) return;
    
    item.qty += delta;
    if (item.qty <= 0) {
        removeFromCart(id);
        return;
    }
    if (item.qty > item.stock) {
        item.qty = item.stock;
        showToast(`⚠️ الكمية القصوى: ${item.stock}`, 'error');
    }
    
    renderCart();
}

function clearCart() {
    if (STATE.cart.length === 0) return;
    if (!confirm('تفريغ السلة؟')) return;
    STATE.cart = [];
    renderCart();
}

function renderCart() {
    const items = document.getElementById('cart-items');
    const summary = document.getElementById('cart-summary');
    const count = document.getElementById('cart-count');
    const mobileCount = document.getElementById('mobile-cart-count');
    const checkoutBtn = document.getElementById('btn-checkout');
    
    if (!items) return;
    
    if (STATE.cart.length === 0) {
        items.innerHTML = '<div class="cart-empty" id="cart-empty"><i class="fas fa-shopping-cart"></i><p>السلة فارغة</p><p style="font-size:12px;">امسح باركود أو اختر منتج</p></div>';
        if (summary) summary.style.display = 'none';
        if (count) count.textContent = '0';
        if (mobileCount) mobileCount.textContent = '0';
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
    }
    
    if (summary) summary.style.display = 'block';
    if (checkoutBtn) checkoutBtn.disabled = false;
    
    let total = 0;
    let totalItems = 0;
    
    items.innerHTML = STATE.cart.map(item => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;
        totalItems += item.qty;
        return `<div class="cart-item">
            <div class="item-name">${item.name}</div>
            <div class="item-qty">
                <button onclick="updateQty(${item.id}, -1)">−</button>
                <span>${item.qty}</span>
                <button onclick="updateQty(${item.id}, 1)">+</button>
            </div>
            <div class="item-total">${itemTotal.toLocaleString()}</div>
            <div class="item-remove" onclick="removeFromCart(${item.id})">✕</div>
        </div>`;
    }).join('');
    
    if (count) count.textContent = totalItems;
    if (mobileCount) mobileCount.textContent = totalItems;
    
    const itemsEl = document.getElementById('cart-total-items');
    const totalEl = document.getElementById('cart-total');
    if (itemsEl) itemsEl.textContent = totalItems;
    if (totalEl) totalEl.textContent = total.toLocaleString() + ' DA';
}

// ==============================================
//  CHECKOUT
// ==============================================
function openCheckout() {
    if (STATE.cart.length === 0) return;
    
    const modal = document.getElementById('payment-modal');
    document.getElementById('payment-form').style.display = 'block';
    document.getElementById('payment-success').style.display = 'none';
    
    let total = 0;
    let itemsHtml = '';
    STATE.cart.forEach(item => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;
        itemsHtml += `<div class="r-item">
            <span>${item.name} × ${item.qty}</span>
            <span>${itemTotal.toLocaleString()} DA</span>
        </div>`;
    });
    
    document.getElementById('payment-total').textContent = total.toLocaleString() + ' DA';
    document.getElementById('payment-items').innerHTML = itemsHtml;
    document.getElementById('payment-notes').value = '';
    
    selectPayment('cash');
    
    modal.classList.add('active');
}

function selectPayment(method) {
    STATE.selectedPayment = method;
    document.querySelectorAll('.payment-methods button').forEach(b => {
        b.classList.toggle('active', b.dataset.method === method);
    });
}

async function completeSale() {
    const btn = document.getElementById('btn-complete-sale');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> جاري...';
    
    try {
        const results = [];
        for (const item of STATE.cart) {
            const result = await API.recordSale({
                product_id: item.id,
                quantity: item.qty,
                unit_price: item.price,
                payment_method: STATE.selectedPayment,
                notes: document.getElementById('payment-notes').value.trim()
            });
            results.push(result);
        }
        
        const total = STATE.cart.reduce((sum, item) => sum + (item.price * item.qty), 0);
        const receipt = results[0]?.sale?.receipt_number || `POS-${Date.now()}`;
        
        STATE.lastSale = {
            receipt,
            total,
            items: [...STATE.cart],
            payment: STATE.selectedPayment
        };
        
        document.getElementById('payment-form').style.display = 'none';
        document.getElementById('payment-success').style.display = 'block';
        document.getElementById('success-total').textContent = total.toLocaleString() + ' DA';
        document.getElementById('success-receipt').textContent = `رقم الفاتورة: ${receipt}`;
        
        STATE.cart = [];
        renderCart();
        
    } catch (e) {
        showToast('❌ فشل إتمام البيع: ' + e.message, 'error');
    }
    
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-check-circle"></i> تأكيد البيع';
}

function resetSale() {
    document.getElementById('payment-form').style.display = 'block';
    document.getElementById('payment-success').style.display = 'none';
    switchView('sale');
    document.getElementById('barcode-input').focus();
    loadProducts();
}

// ==============================================
//  PRINT RECEIPT
// ==============================================
function printReceipt() {
    if (!STATE.lastSale) return;
    
    const s = STATE.lastSale;
    const itemsHtml = s.items.map(item => 
        `<tr><td>${item.name}</td><td style="text-align:center;">${item.qty}</td><td style="text-align:left;">${(item.price * item.qty).toLocaleString()}</td></tr>`
    ).join('');
    
    const methods = { cash: 'نقدي', card: 'بطاقة', bank_transfer: 'تحويل بنكي', check: 'شيك' };
    
    const printWindow = window.open('', '_blank', 'width=300,height=600');
    printWindow.document.write(`
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>فاتورة ${s.receipt}</title>
            <style>
                @page { margin: 0; size: 80mm auto; }
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    padding: 10px;
                    width: 80mm;
                    color: #000;
                }
                .header { text-align: center; margin-bottom: 10px; }
                .header h2 { font-size: 16px; font-weight: bold; }
                .header p { font-size: 11px; }
                hr { border-top: 1px dashed #000; margin: 8px 0; }
                table { width: 100%; border-collapse: collapse; }
                th { text-align: center; font-size: 11px; border-bottom: 1px solid #000; padding: 4px 0; }
                td { padding: 3px 0; }
                .total-row { font-weight: bold; font-size: 14px; }
                .footer { text-align: center; margin-top: 10px; font-size: 10px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🦁 Royal Chaussures</h2>
                <p>Imama, Tlemcen</p>
                <p>+213 659 83 24 26</p>
                <hr>
                <p>فاتورة: ${s.receipt}</p>
                <p>التاريخ: ${new Date().toLocaleDateString('ar-DZ')}</p>
                <p>وقت: ${new Date().toLocaleTimeString('ar-DZ')}</p>
            </div>
            <hr>
            <table>
                <thead>
                    <tr><th>المنتج</th><th>الكمية</th><th>المجموع</th></tr>
                </thead>
                <tbody>
                    ${itemsHtml}
                </tbody>
            </table>
            <hr>
            <div style="display:flex;justify-content:space-between;">
                <span>الإجمالي</span>
                <span class="total-row">${s.total.toLocaleString()} DA</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:5px;">
                <span>وسيلة الدفع</span>
                <span>${methods[s.payment] || s.payment}</span>
            </div>
            <hr>
            <div class="footer">
                <p>شكراً لتسوقكم مع Royal Chaussures 👑</p>
                <p>www.royalchaussures.com</p>
            </div>
            <script>
                window.onload = function() { window.print(); window.close(); };
            <\/script>
        </body></html>`);
    printWindow.document.close();
}

// ==============================================
//  MODAL
// ==============================================
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

document.getElementById('payment-modal')?.addEventListener('click', function(e) {
    if (e.target === this) closeModal('payment-modal');
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'F8') {
        e.preventDefault();
        document.getElementById('search-input')?.focus();
    }
    if (e.key === 'Escape') {
        closeModal('payment-modal');
    }
    if (e.key === 'F2') {
        e.preventDefault();
        document.getElementById('barcode-input')?.focus();
    }
});

// ==============================================
//  CONNECTION STATUS
// ==============================================
function updateConnectionStatus() {
    const dot = document.getElementById('conn-dot');
    const text = document.getElementById('conn-text');
    
    function check() {
        const online = navigator.onLine;
        if (dot) {
            dot.className = 'dot ' + (online ? 'online' : 'offline');
        }
        if (text) text.textContent = online ? 'متصل' : 'غير متصل';
        STATE.isOffline = !online;
    }
    
    check();
    window.addEventListener('online', check);
    window.addEventListener('offline', check);
}

// ==============================================
//  CART TOGGLE (Mobile)
// ==============================================
function toggleCart() {
    const panel = document.getElementById('cart-panel');
    if (!panel) return;
    panel.classList.toggle('active');
}

// Auto-close cart when selecting product on mobile
document.getElementById('products-grid')?.addEventListener('click', function() {
    if (window.innerWidth <= 900) {
        document.getElementById('cart-panel')?.classList.remove('active');
    }
});

// ==============================================
//  PENDING SALES SYNC
// ==============================================
(function() {
    const pending = JSON.parse(localStorage.getItem('pos_pending') || '[]');
    if (pending.length > 0) {
        STATE.pendingSales = pending;
        console.log(`[POS] ${pending.length} pending sales to sync`);
    }
})();

// ==============================================
//  TOAST NOTIFICATIONS
// ==============================================
function showToast(message, type) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = 'toast show ' + (type || 'success');
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.classList.remove('show');
        toast.style.display = 'none';
    }, 3000);
}

console.log('🦁 Royal POS Engine Ready — ShopLine Theme');
