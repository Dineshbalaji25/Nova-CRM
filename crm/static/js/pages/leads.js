/**
 * Leads Page Logic
 */

let currentLeads = [];
let currentFilterUrl = '/crm/leads/';
let currentNext = null;
let currentPrev = null;
let editingLeadId = null;

async function fetchLeads(url = '/crm/leads/') {
    const tbody = document.getElementById('leadsTableBody');
    try {
        currentFilterUrl = url;
        const data = await api.get(url);
        currentLeads = data.results || [];

        document.getElementById('totalCount').innerText = data.count || 0;
        document.getElementById('nextBtn').disabled = !data.next;
        document.getElementById('prevBtn').disabled = !data.previous;

        currentNext = data.next;
        currentPrev = data.previous;

        if (currentLeads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="text-gray-500">No leads found.</div></td></tr>';
            return;
        }

        tbody.innerHTML = currentLeads.map(lead => `
            <tr>
                <td><input type="checkbox" class="w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary/50"></td>
                <td>
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 bg-gold/10 text-gold border border-gold/20 rounded-xl flex items-center justify-center font-extrabold text-sm">
                            ${(lead.first_name[0] + (lead.last_name ? lead.last_name[0] : '')).toUpperCase()}
                        </div>
                        <div>
                            <div class="font-bold text-white">${lead.first_name} ${lead.last_name || ''}</div>
                            <div class="text-[10px] text-gray-500 font-medium">${lead.title || 'Untitled Lead'}</div>
                        </div>
                    </div>
                </td>
                <td class="text-sm text-gray-300">${lead.company_name || '-'}</td>
                <td class="text-sm text-gray-300">${lead.email || '-'}</td>
                <td class="text-sm text-gray-300">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${getStatusBadgeClass(lead.status)}">
                        ${lead.status.toUpperCase()}
                    </span>
                </td>
                <td>
                    <div class="flex items-center gap-1.5">
                        <i data-lucide="zap" class="w-4 h-4 text-primary"></i>
                        <span class="font-bold text-xs text-primary">${lead.score || '0'}</span>
                    </div>
                </td>
                <td>
                    <button class="btn-icon leads-more-btn" data-id="${lead.id}">
                        <i data-lucide="more-horizontal" class="w-4 h-4 text-gray-400"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch failed:', err);
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--danger);">Failed to load leads. Check console.</td></tr>';
    }
}

function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'new': return 'bg-blue-500/10 border border-blue-500/20 text-blue-400';
        case 'contacted': return 'bg-amber-500/10 border border-amber-500/20 text-amber-400';
        case 'qualified': return 'bg-success/10 border border-success/20 text-success';
        case 'disqualified': return 'bg-danger/10 border border-danger/20 text-danger';
        default: return 'bg-white/5 border border-white/10 text-gray-400';
    }
}

// Action menu handlers
const tbody = document.getElementById('leadsTableBody');
if (tbody) {
    tbody.addEventListener('click', (e) => {
        const btn = e.target.closest('.leads-more-btn');
        if (!btn) return;
        
        const leadId = btn.dataset.id;
        const lead = currentLeads.find(l => l.id === leadId);
        if (lead) {
            showActionMenu(btn, [
                { label: 'Edit Lead', icon: 'edit-3', onClick: () => openEditLeadModal(lead) },
                { label: 'Delete Lead', icon: 'trash-2', onClick: () => deleteLead(lead.id) }
            ]);
        }
    });
}

function openAddLeadModal() {
    editingLeadId = null;
    const form = document.getElementById('addLeadForm');
    if (form) form.reset();
    
    const titleEl = document.querySelector('#addLeadModal h3');
    const submitBtn = document.querySelector('#addLeadModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Add New Lead';
    if (submitBtn) submitBtn.textContent = 'Save Lead';

    const modal = document.getElementById('addLeadModal');
    if (modal) modal.style.display = 'flex';
}

function openEditLeadModal(lead) {
    editingLeadId = lead.id;
    const form = document.getElementById('addLeadForm');
    if (form) {
        form.reset();
        form.elements['title'].value = lead.title || '';
        form.elements['first_name'].value = lead.first_name || '';
        form.elements['last_name'].value = lead.last_name || '';
        form.elements['email'].value = lead.email || '';
        form.elements['company_name'].value = lead.company_name || '';
        form.elements['status'].value = lead.status || 'new';
    }

    const titleEl = document.querySelector('#addLeadModal h3');
    const submitBtn = document.querySelector('#addLeadModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Edit Lead';
    if (submitBtn) submitBtn.textContent = 'Update Lead';

    const modal = document.getElementById('addLeadModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddLeadModal() {
    const modal = document.getElementById('addLeadModal');
    if (modal) modal.style.display = 'none';
}

document.getElementById('addLeadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        if (editingLeadId) {
            await api.patch(`/crm/leads/${editingLeadId}/`, payload);
        } else {
            await api.post('/crm/leads/', payload);
        }
        closeAddLeadModal();
        e.target.reset();
        fetchLeads(currentFilterUrl);
    } catch (err) {
        alert('Failed to save lead: ' + (err.data?.detail || err.message));
    }
});

async function deleteLead(id) {
    if (!confirm('Are you sure you want to delete this lead?')) return;
    try {
        await api.delete(`/crm/leads/${id}/`);
        fetchLeads(currentFilterUrl);
    } catch (err) {
        alert('Failed to delete lead: ' + (err.data?.detail || err.message));
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
    fetchLeads('/crm/leads/');
});

document.getElementById('filterForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const status = document.getElementById('filterStatus').value;
    const owner = document.getElementById('filterOwner').value;

    const urlObj = new URL('/crm/leads/', window.location.origin);
    if (status) urlObj.searchParams.set('status', status);
    if (owner === 'me') {
        const myUserId = localStorage.getItem('user_id');
        if (myUserId) urlObj.searchParams.set('owner', myUserId);
    }

    toggleFilterDrawer(false);
    fetchLeads(urlObj.pathname + urlObj.search);
});

// Export Handling
document.getElementById('exportBtn')?.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const urlObj = new URL(currentFilterUrl, window.location.origin);
    urlObj.searchParams.set('limit', '10000');

    try {
        const btn = document.getElementById('exportBtn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="w-4 h-4 animate-spin border-2 border-white/20 border-t-white rounded-full"></i> Exporting...';
        btn.disabled = true;

        const data = await api.get(urlObj.pathname + urlObj.search);
        const records = data.results || [];
        
        exportToCSV(
            'leads.csv',
            ['Title', 'First Name', 'Last Name', 'Email', 'Company Name', 'Status', 'Score'],
            records,
            l => [l.title, l.first_name, l.last_name || '', l.email || '', l.company_name || '', l.status, l.score || '0']
        );

        btn.innerHTML = originalHTML;
        btn.disabled = false;
    } catch (err) {
        alert('Export failed: ' + err.message);
    }
});

// Search handling
let searchTimeout;
document.getElementById('leadSearch')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value;
    searchTimeout = setTimeout(() => {
        fetchLeads(`/crm/leads/?search=${query}`);
    }, 400);
});

// Pagination handling
document.getElementById('nextBtn')?.addEventListener('click', () => {
    if (currentNext) fetchLeads(currentNext);
});
document.getElementById('prevBtn')?.addEventListener('click', () => {
    if (currentPrev) fetchLeads(currentPrev);
});

// Run Init
fetchLeads();
