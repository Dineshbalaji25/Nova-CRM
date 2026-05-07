/**
 * Dashboard Page Logic
 */

async function initDashboard() {
    console.log("Initializing Enhanced Dashboard...");
    try {
        // Fetch Comprehensive Stats
        const stats = await api.get('/stats/dashboard/');
        const kpis = stats.kpis;

        // Update KPI UI
        updateKPI('kpi-revenue', `$${kpis.total_revenue.toLocaleString()}`, kpis.revenue_growth, 'trending-up');
        updateKPI('kpi-deals', kpis.active_deals, kpis.deals_today, 'plus', 'today');
        updateKPI('kpi-leads', kpis.leads_converted, kpis.leads_trend, kpis.leads_trend >= 0 ? 'trending-up' : 'trending-down');
        updateKPI('kpi-winrate', `${kpis.win_rate}%`, kpis.win_rate_trend, 'trending-up');

        // Update AI Insights
        const insightCountEl = document.getElementById('ai-insight-count');
        if (insightCountEl) insightCountEl.innerText = stats.ai_insights.length;

        const insightPreviewEl = document.getElementById('ai-insight-preview');
        if (insightPreviewEl && stats.ai_insights.length > 0) {
            insightPreviewEl.innerHTML = stats.ai_insights.slice(0, 2).map(ins => `
                <div class="p-3 bg-white/5 border border-white/10 rounded-xl">
                    <p class="text-xs font-bold text-white mb-1">${ins.title}</p>
                    <p class="text-[11px] text-gray-500 font-medium">${ins.description}</p>
                </div>
            `).join('');
        }

        // Fetch User Info for Welcome
        const profile = await api.get('/users/profile/');
        if (profile) {
            const welcomeEl = document.getElementById('welcome-name');
            if (welcomeEl) welcomeEl.innerText = profile.first_name || 'Explorer';
        }

        // Fetch Recent Activity
        const activitiesResponse = await api.get('/crm/activities/');
        const activities = activitiesResponse.results || [];
        renderActivities(activities);

    } catch (err) {
        console.error('Dashboard Init Failed:', err);
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

    container.innerHTML = activities.slice(0, 6).map(act => `
        <div class="flex items-center gap-4 p-4 bg-white/[0.02] border border-white/5 rounded-xl hover:bg-white/5 hover:border-white/10 transition-all group cursor-pointer">
            <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <i data-lucide="${getActivityIcon(act.activity_type)}" class="w-5 h-5"></i>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-white truncate">${act.subject}</p>
                <p class="text-[11px] text-gray-500 font-medium">${new Date(act.occurred_at).toLocaleDateString()} • ${act.activity_type.toUpperCase()}</p>
            </div>
            <i data-lucide="chevron-right" class="w-4 h-4 text-gray-700 group-hover:text-white transition-colors"></i>
        </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
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

// Run Init
initDashboard();
