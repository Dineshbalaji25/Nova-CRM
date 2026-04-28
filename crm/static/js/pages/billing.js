/**
 * Billing Page Logic
 */

async function fetchBillingData() {
    const plansGrid = document.getElementById('plansGrid');
    const invoicesTable = document.getElementById('invoicesTableBody');
    const usageContainer = document.getElementById('usageContainer');

    try {
        // 1. Fetch Plans
        const plansData = await api.get('/billing/plans/');
        const plans = plansData.results || [];

        // 2. Fetch My Subscription
        const subData = await api.get('/billing/my-subscription/');
        const currentSub = subData.results ? subData.results[0] : null;

        // 3. Render Plans
        if (plansGrid) {
            plansGrid.innerHTML = plans.map(p => {
                const isActive = currentSub && currentSub.plan === p.id;
                return `
                    <div class="plan-card ${isActive ? 'active' : ''}" style="position: relative;">
                        ${isActive ? `
                            <div style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--primary-500); color: white; padding: 2px 12px; border-radius: 99px; font-size: 11px; font-weight: 700;">
                                CURRENT PLAN
                            </div>
                        ` : ''}
                        <h4 class="font-bold ${isActive ? '' : 'text-muted'}" style="${isActive ? 'color: var(--primary-600);' : ''}">${p.name.toUpperCase()}</h4>
                        <div class="plan-price">$${(p.amount_cents / 100).toFixed(0)}<span style="font-size: 14px; font-weight: 400;">/${p.interval === 'month' ? 'mo' : 'yr'}</span></div>
                        <button class="btn ${isActive ? 'btn-primary' : 'btn-secondary'}" ${isActive ? 'disabled' : `onclick="upgradePlan('${p.id}')"`} style="width: 100%;">
                            ${isActive ? 'Active' : 'Upgrade'}
                        </button>
                    </div>
                `;
            }).join('');
        }

        // 4. Fetch usage (Mocked values if no records exist yet for better UX)
        // In real world, usage records would be created by background workers.
        let contactsCount = 0;
        try {
            const contactsData = await api.get('/crm/contacts/');
            contactsCount = contactsData.count || 0;
        } catch (e) { }

        const planName = currentSub ? currentSub.plan_name : 'Free';
        const limit = planName === 'Pro' ? 10000 : (planName === 'Enterprise' ? 100000 : 1000);
        const percent = Math.min(100, (contactsCount / limit) * 100);

        if (usageContainer) {
            usageContainer.innerHTML = `
                <div class="usage-meter-container" style="margin-bottom: 24px;">
                    <div class="meter-label" style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                        <span class="font-bold">Contacts</span>
                        <span class="text-muted">${contactsCount.toLocaleString()} / ${limit.toLocaleString()}</span>
                    </div>
                    <div class="meter-track" style="height: 8px; background: var(--gray-100); border-radius: 4px; overflow: hidden;">
                        <div class="meter-fill" style="width: ${percent}%; height: 100%; background: var(--primary-500); transition: width 0.5s;"></div>
                    </div>
                </div>
                <div class="usage-meter-container">
                    <div class="meter-label" style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px;">
                        <span class="font-bold">API Calls (Monthly)</span>
                        <span class="text-muted">0 / 50,000</span>
                    </div>
                    <div class="meter-track" style="height: 8px; background: var(--gray-100); border-radius: 4px; overflow: hidden;">
                        <div class="meter-fill" style="width: 0%; height: 100%; background: var(--success-fg);"></div>
                    </div>
                </div>
            `;
        }

        // 5. Fetch Invoices
        const invoicesData = await api.get('/billing/invoices/');
        const invoices = invoicesData.results || [];

        if (invoicesTable) {
            if (invoices.length === 0) {
                invoicesTable.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 40px;"><div class="text-muted">No invoices found.</div></td></tr>';
            } else {
                invoicesTable.innerHTML = invoices.map(inv => `
                    <tr>
                        <td class="text-sm">${new Date(inv.paid_at).toLocaleDateString()}</td>
                        <td class="font-bold">$${(inv.amount_paid_cents / 100).toFixed(2)}</td>
                        <td><span class="badge badge-success">${inv.status}</span></td>
                        <td><a href="${inv.invoice_pdf}" target="_blank" class="text-primary text-sm">Download PDF</a></td>
                    </tr>
                `).join('');
            }
        }

        if (window.lucide) lucide.createIcons();

    } catch (err) {
        console.error('Failed to fetch billing data:', err);
    }
}

async function upgradePlan(planId) {
    if (!confirm('Proceed to upgrade your plan?')) return;
    try {
        // This would typically redirect to Stripe Checkout or similar
        alert('Upgrading feature would normally redirect to Stripe Checkout. Plan ID: ' + planId);
    } catch (err) {
        alert('Upgrade failed');
    }
}

// Run Init
fetchBillingData();
