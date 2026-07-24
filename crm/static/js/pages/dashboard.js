/**
 * Dashboard Page Logic
 */

// Global state for polling
let dashboardPollInterval = null;

async function initDashboard() {
    console.log("Initializing Enhanced Dashboard with Polling...");
    try {
        // 1. Fetch User Info (using the correct auth/check endpoint)
        const authData = await api.get('/auth/check/');
        if (authData && authData.user) {
            const welcomeEl = document.getElementById('welcome-name');
            if (welcomeEl) {
                // Use first name if available, else 'Explorer'
                const firstName = authData.user.full_name ? authData.user.full_name.split(' ')[0] : 'Explorer';
                welcomeEl.innerText = firstName;
            }
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
        
        // Fetch stats from backend view
        const statsResponse = await api.get('/stats/dashboard/');
        const kpis = statsResponse.kpis || {};
        const aiInsights = statsResponse.ai_insights || [];

        // Update KPI UI with smooth transition and trend badges
        const revenueVal = `$${parseFloat(kpis.total_revenue || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
        updateKPI('kpi-revenue', revenueVal, kpis.revenue_growth, kpis.revenue_growth >= 0 ? 'arrow-up' : 'arrow-down');
        
        updateKPI('kpi-deals', kpis.active_deals, kpis.deals_trend, kpis.deals_trend >= 0 ? 'arrow-up' : 'arrow-down');
        
        updateKPI('kpi-leads', kpis.leads_converted, kpis.leads_trend, kpis.leads_trend >= 0 ? 'arrow-up' : 'arrow-down');
        
        const winRateVal = `${parseFloat(kpis.win_rate || 0).toFixed(1)}%`;
        updateKPI('kpi-winrate', winRateVal, kpis.win_rate_trend, kpis.win_rate_trend >= 0 ? 'arrow-up' : 'arrow-down');

        // Update AI Insights count in welcome section
        const aiCountEl = document.getElementById('ai-insight-count');
        if (aiCountEl && aiCountEl.innerText != aiInsights.length) {
            aiCountEl.innerText = aiInsights.length;
        }

        // Render AI Insights
        renderAIInsights(aiInsights);

        // Fetch Recent Activity
        const activitiesResponse = await api.get('/crm/activities/');
        const activities = activitiesResponse.results || [];
        renderActivities(activities);

    } catch (err) {
        console.error('Dashboard Data Refresh Failed:', err);
    }
}

function updateKPI(id, value, trend, icon, suffix = '') {
    const el = document.getElementById(id);
    if (!el) return;

    // Smooth transition opacity effect
    if (el.innerText != value) {
        el.style.opacity = '0.5';
        setTimeout(() => {
            el.innerText = value;
            el.style.opacity = '1';
        }, 150);
    }

    // Update trend badge if exists in parent card
    const card = el.closest('.kpi-card-modern');
    if (card) {
        const badge = card.querySelector('.rounded-full');
        if (badge) {
            badge.classList.remove('animate-pulse');
            
            const trendSign = trend >= 0 ? '+' : '';
            badge.innerHTML = `<i data-lucide="${icon}" class="w-3 h-3"></i> ${trendSign}${trend}${suffix ? ' ' + suffix : '%'}`;
            
            // Toggle classes based on trend direction
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

function renderAIInsights(insights) {
    const container = document.getElementById('ai-insight-preview');
    if (!container) return;

    if (insights.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-6 text-center opacity-50">
                <p class="text-xs text-gray-400 font-medium">No active insights at the moment</p>
            </div>
        `;
        return;
    }

    const html = insights.map(insight => `
        <div class="p-4 rounded-xl bg-white/5 border border-white/5 flex gap-3 items-start hover:bg-white/10 transition-colors" style="border-radius: 14px;">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${insight.type === 'warning' ? 'bg-danger/10 text-danger' : 'bg-primary/10 text-primary'}">
                <i data-lucide="${insight.type === 'warning' ? 'alert-triangle' : 'sparkles'}" class="w-4 h-4"></i>
            </div>
            <div class="overflow-hidden">
                <h4 class="text-sm font-bold text-white mb-1 truncate">${insight.title}</h4>
                <p class="text-xs text-gray-400 font-medium leading-relaxed">${insight.description}</p>
            </div>
        </div>
    `).join('');

    // Only update if HTML changed
    if (container.innerHTML !== html) {
        container.innerHTML = html;
        if (window.lucide) lucide.createIcons();
    }
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
