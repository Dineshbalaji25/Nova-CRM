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
                <td><input type="checkbox"></td>
                <td>
                    <div class="company-name-group">
                        <div class="company-logo-initials">${company.name.substring(0, 2).toUpperCase()}</div>
                        <div class="font-bold">${company.name}</div>
                    </div>
                </td>
                <td class="text-muted">${company.industry || '-'}</td>
                <td class="revenue-text">${company.annual_revenue ? '$' + parseFloat(company.annual_revenue).toLocaleString() : '-'}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="width: 24px; height: 24px; background: #e0e7ff; color: #4f46e5; border-radius: 50%; font-size: 10px; display: flex; align-items: center; justify-content: center;">
                            ${(company.owner_name || 'U').substring(0, 2).toUpperCase()}
                        </div>
                        <span class="text-sm">${company.owner_name || 'Unknown'}</span>
                    </div>
                </td>
                <td><span class="badge ${company.is_active ? 'badge-success' : 'badge-warning'}">${company.status || 'Active'}</span></td>
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
