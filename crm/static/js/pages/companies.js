/**
 * Companies Page Logic
 */

async function fetchCompanies() {
    const tbody = document.getElementById('companiesTableBody');
    if (!tbody) return;

    try {
        const data = await api.get('/crm/companies/');
        const results = data.results || [];

        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="text-muted">No companies found.</div></td></tr>';
            return;
        }

        tbody.innerHTML = results.map(company => `
            <tr>
                <td><input type="checkbox" class="form-check-input"></td>
                <td>
                    <div class="company-name-group">
                        <div class="company-logo-initials" style="background: var(--accent-glass); color: var(--accent-700); font-weight: 800; border: 1px solid var(--accent-500);">${company.name.substring(0, 2).toUpperCase()}</div>
                        <div class="font-bold">${company.name}</div>
                    </div>
                </td>
                <td class="text-muted">${company.industry || '-'}</td>
                <td class="revenue-text">${company.annual_revenue ? '$' + parseFloat(company.annual_revenue).toLocaleString() : '-'}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 28px; height: 28px; background: var(--primary-100); color: var(--primary-600); border-radius: 8px; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center;">
                            ${(company.owner_name || 'U').substring(0, 1).toUpperCase()}
                        </div>
                        <span class="text-sm font-medium">${company.owner_name || 'Unknown'}</span>
                    </div>
                </td>
                <td><span class="badge ${company.is_active ? 'badge-success' : 'badge-warning'}" style="background: ${company.is_active ? 'var(--success-bg)' : 'var(--warning-bg)'}; color: ${company.is_active ? 'var(--success)' : 'var(--warning)'}; border: 1px solid currentColor; font-weight: 700;">${company.status || 'Active'}</span></td>
                <td><button class="btn-icon"><i data-lucide="more-horizontal" size="16"></i></button></td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch companies failed:', err);
    }
}

function openAddCompanyModal() {
    const modal = document.getElementById('addCompanyModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddCompanyModal() {
    const modal = document.getElementById('addCompanyModal');
    if (modal) modal.style.display = 'none';
}

document.getElementById('addCompanyForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        await api.post('/crm/companies/', payload);
        closeAddCompanyModal();
        e.target.reset();
        fetchCompanies();
    } catch (err) {
        alert('Failed to save company: ' + (err.data?.detail || err.message));
    }
});

// Run Init
fetchCompanies();
