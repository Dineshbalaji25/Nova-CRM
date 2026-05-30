/**
 * Companies Page Logic
 */

let currentCompanies = [];
let currentFilterUrl = '/crm/companies/';
let editingCompanyId = null;

async function fetchCompanies(url = '/crm/companies/') {
    const tbody = document.getElementById('companiesTableBody');
    if (!tbody) return;

    try {
        currentFilterUrl = url;
        const data = await api.get(url);
        currentCompanies = data.results || [];

        if (currentCompanies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="text-gray-500">No companies found.</div></td></tr>';
            return;
        }

        tbody.innerHTML = currentCompanies.map(company => `
            <tr>
                <td><input type="checkbox" class="w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary/50"></td>
                <td>
                    <div class="company-name-group flex items-center gap-3">
                        <div class="company-logo-initials w-9 h-9 rounded-xl flex items-center justify-center font-extrabold text-sm border border-accent/20" style="background: var(--accent-glass); color: var(--accent-700); border: 1px solid var(--accent-500);">
                            ${company.name.substring(0, 2).toUpperCase()}
                        </div>
                        <div class="font-bold text-white">${company.name}</div>
                    </div>
                </td>
                <td class="text-sm text-gray-300">${company.industry || '-'}</td>
                <td class="text-sm font-semibold text-emerald-500">${company.annual_revenue ? '$' + parseFloat(company.annual_revenue).toLocaleString() : '-'}</td>
                <td>
                    <div class="flex items-center gap-2">
                        <div class="w-7 h-7 bg-primary/10 text-primary border border-primary/20 rounded-lg font-bold text-xs flex items-center justify-center">
                            ${(company.owner_name || 'U').substring(0, 1).toUpperCase()}
                        </div>
                        <span class="text-xs font-semibold text-gray-300">${company.owner_name || 'Unknown'}</span>
                    </div>
                </td>
                <td>
                    <span class="badge badge-success" style="background: var(--success-bg); color: var(--success); border: 1px solid currentColor; font-weight: 700;">
                        Active
                    </span>
                </td>
                <td>
                    <button class="btn-icon companies-more-btn" data-id="${company.id}">
                        <i data-lucide="more-horizontal" class="w-4 h-4 text-gray-400"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch companies failed:', err);
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--danger);">Failed to load companies. Check console.</td></tr>';
    }
}

// Action Menu delegate
const tbody = document.getElementById('companiesTableBody');
if (tbody) {
    tbody.addEventListener('click', (e) => {
        const btn = e.target.closest('.companies-more-btn');
        if (!btn) return;
        
        const companyId = btn.dataset.id;
        const company = currentCompanies.find(c => c.id === companyId);
        if (company) {
            showActionMenu(btn, [
                { label: 'Edit Company', icon: 'edit-3', onClick: () => openEditCompanyModal(company) },
                { label: 'Delete Company', icon: 'trash-2', onClick: () => deleteCompany(company.id) }
            ]);
        }
    });
}

function openAddCompanyModal() {
    editingCompanyId = null;
    const form = document.getElementById('addCompanyForm');
    if (form) form.reset();

    const titleEl = document.querySelector('#addCompanyModal h3');
    const submitBtn = document.querySelector('#addCompanyModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Add New Company';
    if (submitBtn) submitBtn.textContent = 'Save Company';

    const modal = document.getElementById('addCompanyModal');
    if (modal) modal.style.display = 'flex';
}

function openEditCompanyModal(company) {
    editingCompanyId = company.id;
    const form = document.getElementById('addCompanyForm');
    if (form) {
        form.reset();
        form.elements['name'].value = company.name || '';
        form.elements['industry'].value = company.industry || 'Technology';
        form.elements['annual_revenue'].value = company.annual_revenue || '';
    }

    const titleEl = document.querySelector('#addCompanyModal h3');
    const submitBtn = document.querySelector('#addCompanyModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Edit Company';
    if (submitBtn) submitBtn.textContent = 'Update Company';

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
        if (editingCompanyId) {
            await api.patch(`/crm/companies/${editingCompanyId}/`, payload);
        } else {
            await api.post('/crm/companies/', payload);
        }
        closeAddCompanyModal();
        e.target.reset();
        fetchCompanies(currentFilterUrl);
    } catch (err) {
        alert('Failed to save company: ' + (err.data?.detail || err.message));
    }
});

async function deleteCompany(id) {
    if (!confirm('Are you sure you want to delete this company?')) return;
    try {
        await api.delete(`/crm/companies/${id}/`);
        fetchCompanies(currentFilterUrl);
    } catch (err) {
        alert('Failed to delete company: ' + (err.data?.detail || err.message));
    }
}

// Side Drawer Filtering
const filterDrawer = document.getElementById('filterDrawer');
const filterOverlay = document.getElementById('filterDrawerOverlay');

const toggleFilterDrawer = (isOpen) => {
    if (filterDrawer) filterDrawer.classList.toggle('open', isOpen);
    if (filterOverlay) filterOverlay.classList.toggle('open', isOpen);
};

document.getElementById('filterBtn')?.addEventListener('click', (e) => {
    e.preventDefault();
    toggleFilterDrawer(true);
});

document.getElementById('closeFilterBtn')?.addEventListener('click', () => toggleFilterDrawer(false));
filterOverlay?.addEventListener('click', () => toggleFilterDrawer(false));

document.getElementById('clearFilterBtn')?.addEventListener('click', () => {
    const form = document.getElementById('filterForm');
    if (form) form.reset();
    toggleFilterDrawer(false);
    fetchCompanies('/crm/companies/');
});

document.getElementById('filterForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const industry = document.getElementById('filterIndustry').value;
    const owner = document.getElementById('filterOwner').value;

    const urlObj = new URL('/crm/companies/', window.location.origin);
    if (industry) urlObj.searchParams.set('industry', industry);
    if (owner === 'me') {
        const myUserId = localStorage.getItem('user_id');
        if (myUserId) urlObj.searchParams.set('owner', myUserId);
    }

    toggleFilterDrawer(false);
    fetchCompanies(urlObj.pathname + urlObj.search);
});

// Export Handling
document.getElementById('exportBtn')?.addEventListener('click', async (e) => {
    e.preventDefault();
    
    // Construct request url to get all matching results
    const urlObj = new URL(currentFilterUrl, window.location.origin);
    urlObj.searchParams.set('limit', '10000'); // large limit to pull all matching data

    try {
        const btn = document.getElementById('exportBtn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="w-4 h-4 animate-spin border-2 border-white/20 border-t-white rounded-full"></i> Exporting...';
        btn.disabled = true;

        const data = await api.get(urlObj.pathname + urlObj.search);
        const records = data.results || [];
        
        exportToCSV(
            'companies.csv',
            ['Company Name', 'Industry', 'Annual Revenue', 'Owner', 'Status'],
            records,
            c => [c.name, c.industry || '-', c.annual_revenue || '0.00', c.owner_name || 'Unknown', c.is_active ? 'Active' : 'Inactive']
        );

        btn.innerHTML = originalHTML;
        btn.disabled = false;
    } catch (err) {
        alert('Export failed: ' + err.message);
    }
});

// Search handling
let searchTimeout;
document.getElementById('companySearch')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value;
    searchTimeout = setTimeout(() => {
        fetchCompanies(`/crm/companies/?search=${query}`);
    }, 400); // 400ms debounce
});

// Run Init
fetchCompanies();
