/**
 * Dashboard Page Logic
 */

// Global state for polling
let dashboardPollInterval = null;

async function initDashboard() {
    console.log("Initializing Enhanced Dashboard with Polling...");
    try {
        // 1. Fetch Static User Info (only once)
        const profile = await api.get('/users/profile/');
        if (profile) {
            const welcomeEl = document.getElementById('welcome-name');
            if (welcomeEl) welcomeEl.innerText = profile.first_name || 'Explorer';
        }

        // 2. Fetch Initial Dynamic Data
        await refreshDashboardData();

        // 3. Start Polling for Dynamic Data (every 10 seconds)
        dashboardPollInterval = setInterval(refreshDashboardData, 10000);

    } catch (err) {
        console.error('Dashboard Init Failed:', err);
    }
}

async function refreshDashboardData() {
    try {
        // console.log("Refreshing Dashboard Data...");
        
        // Fetch Deals for KPIs
        const dealsResponse = await api.get('/crm/deals/');
        const deals = dealsResponse.results || [];

        // Calculate KPIs
        const totalRevenue = deals.reduce((sum, d) => sum + parseFloat(d.amount || 0), 0);
        const activeDeals = deals.filter(d => d.status !== 'closed').length;

        // Update KPI UI with smooth transition
        updateKpi('kpi-revenue', `$${totalRevenue.toLocaleString()}`);
        updateKpi('kpi-deals', activeDeals);

        // Fetch Recent Activity
        const activitiesResponse = await api.get('/crm/activities/');
        const activities = activitiesResponse.results || [];
        renderActivities(activities);

    } catch (err) {
        console.error('Dashboard Data Refresh Failed:', err);
    }
}

function updateKpi(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    
    // Only update if value changed to avoid unnecessary re-renders
    if (el.innerText != value) {
        el.style.opacity = '0.5';
        setTimeout(() => {
            el.innerText = value;
            el.style.opacity = '1';
        }, 150);
    }
}

function updateKPI(id, value, trend, icon, suffix = '') {
    const el = document.getElementById(id);
    if (!el) return;

    el.innerText = value;

    // Update trend badge if exists in parent
    const card = el.closest('.kpi-card-modern');
    if (card) {
        const badge = card.querySelector('.rounded-full');
        if (badge) {
            badge.classList.remove('animate-pulse');
            badge.innerHTML = `<i data-lucide="${icon}" class="w-3 h-3"></i> ${Math.abs(trend)}${suffix ? ' ' + suffix : '%'}`;
            // Toggle classes based on trend
            if (trend >= 0) {
                badge.classList.remove('bg-danger/10', 'border-danger/20', 'text-danger');
                badge.classList.add('bg-success/10', 'border-success/20', 'text-success');
            } else {
                badge.classList.remove('bg-success/10', 'border-success/20', 'text-success');
                badge.classList.add('bg-danger/10', 'border-danger/20', 'text-danger');
            }
        }
    }
    if (window.lucide) lucide.createIcons();
}

function renderActivities(activities) {
    const container = document.getElementById('activity-list');
    if (!container) return;

    if (activities.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-10 text-center opacity-50">
                <div class="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center mb-3">
                    <i data-lucide="inbox" class="w-6 h-6"></i>
                </div>
                <p class="text-[10px] font-bold uppercase tracking-widest text-gray-500">No recent activity</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    const html = activities.slice(0, 6).map(act => `
        <div class="activity-item d-flex gap-3 p-3 rounded-md hover-bg" style="transition: background 0.2s; border-radius: 12px;">
            <div class="activity-icon" style="width: 40px; height: 40px; background: var(--gray-100); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <i data-lucide="${getActivityIcon(act.activity_type)}" size="18" style="color: var(--primary-600);"></i>
            </div>
            <div class="overflow-hidden">
                <div class="font-bold text-sm truncate">${act.subject}</div>
                <div class="text-xs text-muted mt-1">${new Date(act.occurred_at || act.created_at).toLocaleTimeString()} • ${act.activity_type.toUpperCase()}</div>
            </div>
            <i data-lucide="chevron-right" class="w-4 h-4 text-gray-700 group-hover:text-white transition-colors"></i>
        </div>
    `).join('');

    // Only update if HTML changed
    if (container.innerHTML !== html) {
        container.innerHTML = html;
        if (window.lucide) lucide.createIcons();
    }
}

function getActivityIcon(type) {
    switch (type.toLowerCase()) {
        case 'call': return 'phone';
        case 'email': return 'mail';
        case 'meeting': return 'calendar';
        case 'task': return 'check-square';
        default: return 'activity';
    }
}

// Global click handling
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn');
    if (!btn) return;

    const text = btn.innerText.trim();

    if (text === 'View All' || text === 'View History') {
        window.location.href = '/audit';
    } else if (text.includes('View AI Insights')) {
        alert('Analyzing your data with AI... Check back in a moment for deep insights.');
    } else if (text === 'Download Report') {
        alert('Preparing your PDF report for download...');
    }
});

// Run Init
initDashboard();

// Cleanup polling on page navigation (if SPA)
window.addEventListener('beforeunload', () => {
    if (dashboardPollInterval) clearInterval(dashboardPollInterval);
});
