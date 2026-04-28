/**
 * Dashboard Page Logic
 */

async function initDashboard() {
    console.log("Initializing Dashboard...");
    try {
        // Fetch Deals for KPIs
        const dealsResponse = await api.get('/crm/deals/');
        const deals = dealsResponse.results || [];

        // Calculate KPIs
        const totalRevenue = deals.reduce((sum, d) => sum + parseFloat(d.amount), 0);
        const activeDeals = deals.length;

        // Update UI
        document.querySelector('.kpi-grid .card:nth-child(1) .text-2xl').innerText = `$${totalRevenue.toLocaleString()}`;
        document.querySelector('.kpi-grid .card:nth-child(2) .text-2xl').innerText = activeDeals;

        // Fetch Recent Activity (Notes or Activities)
        const activitiesResponse = await api.get('/crm/activities/');
        const activities = activitiesResponse.results || [];
        renderActivities(activities);

    } catch (err) {
        console.error('Dashboard Init Failed:', err);
    }
}

function renderActivities(activities) {
    const container = document.querySelector('.card h3').parentElement.nextElementSibling;
    if (activities.length === 0) {
        container.innerHTML = '<div class="text-muted text-sm">No recent activity</div>';
        return;
    }

    container.innerHTML = activities.slice(0, 5).map(act => `
        <div style="display: flex; gap: 16px;">
            <div style="width: 32px; height: 32px; background: var(--primary-100); color: var(--primary-600); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <i data-lucide="${getActivityIcon(act.activity_type)}" size="16"></i>
            </div>
            <div>
                <div><strong>${act.subject}</strong></div>
                <div class="text-xs text-muted" style="margin-top: 4px;">${new Date(act.occurred_at).toLocaleString()}</div>
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
