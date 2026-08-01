/* =============================================
   Royal Chaussures — Premium Dashboard JS
   script_premium.js
   تصميم: Claude Sonnet 5 + Louve ❤️
   ============================================= */

(function() {
    'use strict';

    // ===== 1. PARTICLE BACKGROUND =====
    function initParticles() {
        const canvas = document.getElementById('particleCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let particles = [];
        let animFrame;

        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', resize);
        resize();

        const count = Math.min(60, Math.floor(window.innerWidth / 20));
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                r: Math.random() * 1.5 + 0.5,
                alpha: Math.random() * 0.3 + 0.1
            });
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(212, 175, 55, ${p.alpha})`;
                ctx.fill();
            });

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 150) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(212, 175, 55, ${0.06 * (1 - dist / 150)})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
            animFrame = requestAnimationFrame(draw);
        }
        draw();
    }

    // ===== 2. ANIMATED COUNT-UP =====
    function animateValue(el, start, end, duration = 800) {
        if (!el) return;
        const range = end - start;
        const startTime = performance.now();
        const isCurrency = typeof end === 'string' && /[A-Z]{3}/.test(end);
        const numericEnd = parseFloat(String(end).replace(/[^0-9.]/g, '')) || 0;
        const numericStart = parseFloat(String(start).replace(/[^0-9.]/g, '')) || 0;
        const numRange = numericEnd - numericStart;

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const currentVal = numericStart + numRange * eased;

            if (isCurrency) {
                el.textContent = Math.round(currentVal).toLocaleString() + ' DZD';
            } else {
                el.textContent = Math.round(currentVal).toLocaleString();
            }

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        requestAnimationFrame(update);
    }

    // ===== 3. SPARKLINE (Revenue Trend) =====
    function drawSparkline(dataPoints, pathId, fillId) {
        const sparkPath = document.getElementById(pathId);
        const sparkFill = document.getElementById(fillId);
        if (!sparkPath || !dataPoints || dataPoints.length < 2) return;

        const width = 300, height = 80;
        const padding = 10;
        const maxVal = Math.max(...dataPoints);
        const minVal = Math.min(...dataPoints);
        const range = maxVal - minVal || 1;
        const stepX = (width - padding * 2) / (dataPoints.length - 1);

        const points = dataPoints.map((val, i) => ({
            x: padding + i * stepX,
            y: height - padding - ((val - minVal) / range) * (height - padding * 2)
        }));

        let pathD = `M ${points[0].x} ${points[0].y}`;
        for (let i = 1; i < points.length; i++) {
            const cx = (points[i-1].x + points[i].x) / 2;
            pathD += ` Q ${points[i-1].x} ${points[i-1].y}, ${cx} ${(points[i-1].y + points[i].y) / 2}`;
            pathD += ` Q ${points[i].x} ${points[i].y}, ${points[i].x} ${points[i].y}`;
        }

        sparkPath.setAttribute('d', pathD);

        // Fill area under curve
        const fillD = pathD + ` L ${points[points.length-1].x} ${height} L ${points[0].x} ${height} Z`;
        if (sparkFill) sparkFill.setAttribute('d', fillD);
    }

    // ===== 4. DONUT CHART =====
    function drawDonut(percentages, colors, elementId) {
        const svg = document.getElementById(elementId);
        if (!svg) return;

        const cx = 60, cy = 60, r = 48, strokeW = 12;
        const circum = 2 * Math.PI * r;
        let offset = 0;
        let totalPct = 0;

        // Clear existing
        svg.querySelectorAll('.donut-segment').forEach(el => el.remove());

        // Background ring
        const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        bgCircle.setAttribute('cx', cx);
        bgCircle.setAttribute('cy', cy);
        bgCircle.setAttribute('r', r);
        bgCircle.setAttribute('fill', 'none');
        bgCircle.setAttribute('stroke', 'rgba(255,255,255,0.06)');
        bgCircle.setAttribute('stroke-width', strokeW);
        svg.appendChild(bgCircle);

        const total = percentages.reduce((a, b) => a + b, 0);
        if (total === 0) return;

        percentages.forEach((pct, i) => {
            const p = (pct / total) * 100;
            const len = (p / 100) * circum;
            const color = colors[i] || '#D4AF37';

            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('class', 'donut-segment');
            circle.setAttribute('cx', cx);
            circle.setAttribute('cy', cy);
            circle.setAttribute('r', r);
            circle.setAttribute('fill', 'none');
            circle.setAttribute('stroke', color);
            circle.setAttribute('stroke-width', strokeW);
            circle.setAttribute('stroke-dasharray', `${len} ${circum - len}`);
            circle.setAttribute('stroke-dashoffset', -offset);
            circle.setAttribute('stroke-linecap', 'round');
            circle.setAttribute('transform', `rotate(-90 ${cx} ${cy})`);
            circle.style.transition = 'stroke-dasharray 0.5s ease';
            svg.appendChild(circle);
            offset += len;

            totalPct += p;
        });

        // Center text
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', cx);
        text.setAttribute('y', cy + 4);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#D4AF37');
        text.setAttribute('font-size', '14');
        text.setAttribute('font-weight', '700');
        text.textContent = Math.round(totalPct) + '%';
        svg.appendChild(text);
    }

    // ===== 5. SIDEBAR TOGGLE =====
    window.toggleSidebar = function() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (!sidebar) return;
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('show');
    };

    // ===== 6. TIME UPDATE =====
    function updateTime() {
        const el = document.getElementById('currentTime');
        if (!el) return;
        const now = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' };
        el.textContent = now.toLocaleDateString('ar-DZ', options);
    }

    // ===== 7. SYNC BUTTON =====
    window.syncNow = async function() {
        const btn = document.getElementById('syncBtn');
        if (!btn) return;
        btn.textContent = '🔄 جاري المزامنة...';
        btn.disabled = true;
        try {
            const res = await fetch('/api/sync-orders', { method: 'POST' });
            if (res.ok) {
                btn.textContent = '✅ تمت المزامنة';
                setTimeout(() => { btn.textContent = '🔄 مزامنة'; btn.disabled = false; }, 2000);
                loadDashboard();
            } else {
                btn.textContent = '❌ فشلت المزامنة';
                setTimeout(() => { btn.textContent = '🔄 مزامنة'; btn.disabled = false; }, 2000);
            }
        } catch(e) {
            btn.textContent = '❌ خطأ';
            setTimeout(() => { btn.textContent = '🔄 مزامنة'; btn.disabled = false; }, 2000);
        }
    };

    // ===== 8. FILTER ORDERS =====
    let allOrders = [];

    window.filterOrders = function(filter) {
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');

        const tbody = document.getElementById('ordersTable');
        if (!tbody) return;

        let filtered = allOrders;
        if (filter !== 'all') {
            filtered = allOrders.filter(o => {
                const status = (o.financial_status || 'pending').toLowerCase();
                const fulfillment = (o.fulfillment || 'unfulfilled').toLowerCase();
                if (filter === 'paid') return status === 'paid';
                if (filter === 'pending') return status === 'pending' || status === 'unfulfilled';
                if (filter === 'shipped') return fulfillment === 'fulfilled' || fulfillment === 'partial';
                if (filter === 'cancelled') return status === 'cancelled' || status === 'refunded';
                return true;
            });
        }

        renderOrders(filtered);
        const countBadge = document.querySelector('.count-badge');
        if (countBadge) countBadge.textContent = filtered.length;
    };

    function renderOrders(orders) {
        const tbody = document.getElementById('ordersTable');
        if (!tbody) return;

        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:40px;font-size:14px;">📭 لا توجد طلبات بهذه الحالة</td></tr>';
            return;
        }

        tbody.innerHTML = orders.map(function(o) {
            var finClass = o.financial_status === 'paid' ? 'badge-paid' : 'badge-pending';
            var fl = o.fulfillment || 'unfulfilled';
            var fulClass = fl === 'fulfilled' ? 'badge-delivered' : (fl === 'partial' ? 'badge-shipped' : 'badge-pending');
            var oid = o.id || '';
            var amount = o.total || '0';
            var formattedAmount = typeof amount === 'number' ? amount.toLocaleString() + ' DZD' : amount + ' DZD';
            return '<tr onclick="window.location.href=\'/dashboard/orders/' + oid + '\'" style="cursor:pointer;">' +
                '<td>' + (o.name || o.id || '-') + '</td>' +
                '<td>' + (o.customer || 'زائر') + '</td>' +
                '<td>' + formattedAmount + '</td>' +
                '<td><span class="badge ' + finClass + '">' + (o.financial_status || 'pending') + '</span></td>' +
                '<td><span class="badge ' + fulClass + '">' + fl + '</span></td>' +
            '</tr>';
        }).join('');
    }

    // ===== 9. MAIN DASHBOARD LOAD =====
    async function loadDashboard() {
        try {
            const res = await fetch('/api/dashboard-data');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();

            // KPI Cards with animation
            animateValue(document.getElementById('totalRevenue'), 0, data.total_revenue || '0 DZD');
            animateValue(document.getElementById('totalOrders'), 0, data.total_orders || '0');
            animateValue(document.getElementById('unfulfilled'), 0, data.unfulfilled_orders || '0');
            animateValue(document.getElementById('totalProducts'), 0, data.products_count || '0');

            // Status
            const setStatus = (id, text, isOk) => {
                const el = document.getElementById(id);
                if (!el) return;
                el.textContent = text;
                const parent = el.closest('.item');
                if (parent) {
                    const dot = parent.querySelector('.dot');
                    if (dot) {
                        dot.className = 'dot ' + (isOk ? 'green' : text.includes('خطأ') ? 'red' : 'yellow');
                    }
                }
            };
            setStatus('shopifyStatus', data.shopify_status || 'متصل', true);
            setStatus('dbStatus', data.db_status || 'متصل', true);
            setStatus('webhookStatus', data.webhook_status || 'في انتظار الاتصال', data.webhook_status !== 'خطأ');

            // Orders
            allOrders = data.recent_orders || [];
            renderOrders(allOrders);
            const countBadge = document.querySelector('.count-badge');
            if (countBadge) countBadge.textContent = allOrders.length;

            // Revenue Sparkline
            if (data.revenue_trend && data.revenue_trend.length > 0) {
                drawSparkline(data.revenue_trend, 'sparkPath', 'sparkFill');
                const sparkVal = document.getElementById('revenueSparklineValue');
                if (sparkVal) {
                    const total = data.revenue_trend.reduce((a, b) => a + b, 0);
                    sparkVal.textContent = Math.round(total / data.revenue_trend.length).toLocaleString() + ' DZD';
                }
            } else {
                // Sample sparkline data
                const sampleData = [12000, 15000, 13000, 18000, 22000, 19000, 25000];
                drawSparkline(sampleData, 'sparkPath', 'sparkFill');
            }

            // Donut chart
            if (data.order_status_breakdown) {
                const breakdown = data.order_status_breakdown;
                drawDonut(
                    [breakdown.paid || 0, breakdown.pending || 0, breakdown.cancelled || 0, breakdown.fulfilled || 0],
                    ['#22c55e', '#eab308', '#ef4444', '#3b82f6'],
                    'donutChart'
                );
            } else {
                drawDonut([40, 35, 10, 15], ['#22c55e', '#eab308', '#ef4444', '#3b82f6'], 'donutChart');
            }

        } catch(e) {
            console.error('Dashboard fetch error:', e);
            document.getElementById('totalOrders').textContent = '🔴';
            document.getElementById('ordersTable').innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:40px;">⚠️ فشل الاتصال بالسيرفر</td></tr>';
        }
    }

    // ===== 10. AGENT FUNCTIONS =====
    window.switchAgent = async function(agentId) {
        try {
            const res = await fetch('/api/agent/switch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({agent: agentId})
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            if (data.success) {
                updateAgentUI(data.stats || data);
            }
        } catch(e) {
            console.error('Switch agent error:', e);
        }
    };

    function updateAgentUI(data) {
        document.querySelectorAll('.agent-card').forEach(function(card) {
            const agentId = card.dataset.agent;
            const isActive = agentId === data.active_agent;
            card.classList.toggle('active', isActive);
            const badge = document.getElementById('badge-' + agentId);
            if (badge) badge.style.display = isActive ? 'inline-block' : 'none';
        });
    }

    async function loadAgentStatus() {
        try {
            const res = await fetch('/api/agent/status');
            if (!res.ok) return;
            const data = await res.json();
            updateAgentUI(data);
        } catch(e) { console.error('Agent status error:', e); }
    }

    window.testAgentRoute = async function() {
        const msg = document.getElementById('testMessage');
        if (!msg) return;
        const message = msg.value.trim();
        if (!message) {
            alert('الرجاء كتابة رسالة للاختبار');
            return;
        }

        const resultDiv = document.getElementById('agentTestResult');
        const detectedSpan = document.getElementById('detectedAgent');
        const replySpan = document.getElementById('agentReplyText');
        if (!resultDiv || !detectedSpan || !replySpan) return;

        resultDiv.classList.remove('show');
        detectedSpan.textContent = 'جار التحليل...';
        replySpan.textContent = '';

        try {
            const res = await fetch('/api/agent/route-test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            if (data.success) {
                const agentNames = {
                    'customer_support': '🤝 خدمة العملاء',
                    'shipping_tracking': '📦 متابعة الشحنات'
                };
                detectedSpan.textContent = '‏' + (agentNames[data.detected_agent] || data.detected_agent);
                replySpan.textContent = data.reply || 'تم التوجيه بنجاح ✅';
                resultDiv.classList.add('show');
            }
        } catch(e) {
            detectedSpan.textContent = '❌ خطأ: ' + e.message;
            replySpan.textContent = '';
            resultDiv.classList.add('show');
        }
    };

    // Enter key for test message
    document.addEventListener('DOMContentLoaded', function() {
        const testInput = document.getElementById('testMessage');
        if (testInput) {
            testInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') testAgentRoute();
            });
        }

        // Close sidebar on link click (mobile)
        document.querySelectorAll('.sidebar a').forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    toggleSidebar();
                }
            });
        });
    });

    // ===== 11. INITIALIZE =====
    document.addEventListener('DOMContentLoaded', function() {
        initParticles();
        updateTime();
        setInterval(updateTime, 60000);

        const serverUrl = document.getElementById('serverUrl');
        if (serverUrl) serverUrl.textContent = window.location.origin;

        loadDashboard();
        setInterval(loadDashboard, 30000);
        loadAgentStatus();
        setInterval(loadAgentStatus, 60000);
    });

})();
