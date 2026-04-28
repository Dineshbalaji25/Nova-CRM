/**
 * Dashboard Page Logic
 */

async function initDashboard() {
    console.log("Initializing Enhanced Dashboard...");
    try {
        // Fetch Deals for KPIs
        const dealsResponse = await api.get('/crm/deals/');
        const deals = dealsResponse.results || [];

        // Calculate KPIs
        const totalRevenue = deals.reduce((sum, d) => sum + parseFloat(d.amount), 0);
        const activeDeals = deals.filter(d => d.status !== 'closed').length;

        // Update UI
        const revEl = document.getElementById('kpi-revenue');
        if (revEl) revEl.innerText = `$${totalRevenue.toLocaleString()}`;
        
        const dealsEl = document.getElementById('kpi-deals');
        if (dealsEl) dealsEl.innerText = activeDeals;

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

function renderActivities(activities) {
    const container = document.getElementById('activity-list');
    if (!container) return;

    if (activities.length === 0) {
        container.innerHTML = '<div class="text-muted text-sm p-4 text-center">No recent activity to display.</div>';
        return;
    }

    container.innerHTML = activities.slice(0, 6).map(act => `
        <div class="activity-item d-flex gap-3 p-3 rounded-md hover-bg" style="transition: background 0.2s; border-radius: 12px;">
            <div class="activity-icon" style="width: 40px; height: 40px; background: var(--gray-100); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <i data-lucide="${getActivityIcon(act.activity_type)}" size="18" style="color: var(--primary-600);"></i>
            </div>
            <div class="overflow-hidden">
                <div class="font-bold text-sm truncate">${act.subject}</div>
                <div class="text-xs text-muted mt-1">${new Date(act.occurred_at).toLocaleDateString()} • ${act.activity_type}</div>
            </div>
        </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
}

function getActivityIcon(type) {
    switch (type) {
        case 'call': return 'phone';
        case 'email': return 'mail';
        case 'meeting': return 'calendar';
        case 'task': return 'check-square';
        default: return 'activity';
    }
}

// "View All" button handling
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn') && e.target.innerText.trim() === 'View All') {
        // Redirect to audit logs as "Activity" view
        window.location.href = 'audit';
    }
});

// Run Init
initDashboard();
