/**
 * Contacts Page Logic
 */

let currentPage = 1;
let currentNext = null;
let currentPrev = null;

async function fetchContacts(url = '/crm/contacts/') {
    const tbody = document.getElementById('contactsTableBody');
    try {
        const data = await api.get(url);
        const results = data.results || [];

        document.getElementById('totalCount').innerText = data.count || 0;
        document.getElementById('nextBtn').disabled = !data.next;
        document.getElementById('prevBtn').disabled = !data.previous;

        currentNext = data.next;
        currentPrev = data.previous;

        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;"><div class="text-muted">No contacts found.</div></td></tr>';
            return;
        }

        tbody.innerHTML = results.map(contact => `
            <tr>
                <td><input type="checkbox" class="form-check-input"></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 36px; height: 36px; background: var(--accent-glass); color: var(--accent-700); border: 1px solid var(--accent-500); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px;">
                            ${(contact.first_name[0] + (contact.last_name ? contact.last_name[0] : '')).toUpperCase()}
                        </div>
                        <div>
                            <div class="font-bold text-gray-900">${contact.first_name} ${contact.last_name}</div>
                            <div class="text-xs text-muted">ID: ${contact.id.substring(0, 8)}</div>
                        </div>
                    </div>
                </td>
                <td class="text-sm text-gray-600">${contact.email || '-'}</td>
                <td class="text-sm text-gray-600">${contact.phone || '-'}</td>
                <td class="text-sm">
                    <span class="font-medium text-gray-700">${contact.company_name || 'Individual'}</span>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        <i data-lucide="award" size="14" class="text-accent"></i>
                        <span class="font-bold text-xs">85</span>
                    </div>
                </td>
                <td><button class="btn-icon"><i data-lucide="more-horizontal" size="16"></i></button></td>
            </tr>
        `).join('');

        // Populate Company Select
        fetchCompanyList();

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch failed:', err);
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--danger);">Failed to load contacts. Check console.</td></tr>';
    }
}

async function fetchCompanyList() {
    const select = document.getElementById('companySelect');
    if (!select) return;
    try {
        const data = await api.get('/crm/companies/');
        const companies = data.results || [];
        select.innerHTML = '<option value="">Select Company</option>' + 
            companies.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    } catch (err) {
        console.error('Failed to fetch companies:', err);
    }
}

function openAddContactModal() {
    const modal = document.getElementById('addContactModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddContactModal() {
    const modal = document.getElementById('addContactModal');
    if (modal) modal.style.display = 'none';
}

document.getElementById('addContactForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        await api.post('/crm/contacts/', payload);
        closeAddContactModal();
        e.target.reset();
        fetchContacts();
    } catch (err) {
        alert('Failed to save contact: ' + (err.data?.detail || err.message));
    }
});

// CSV Import Handler
document.getElementById('csvImportInput')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const btn = document.querySelector('button[onclick*="csvImportInput"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Importing...';
        btn.disabled = true;

        const response = await api.post('/crm/contacts/import-csv/', formData);
        alert(response.message);

        btn.innerHTML = originalText;
        btn.disabled = false;
        e.target.value = ''; // Reset input
        fetchContacts();
    } catch (err) {
        alert('Import failed: ' + (err.data?.error || err.message));
        e.target.value = '';
    }
});

// Search handling
let searchTimeout;
document.getElementById('contactSearch')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value;
    searchTimeout = setTimeout(() => {
        fetchContacts(`/crm/contacts/?search=${query}`);
    }, 400); // 400ms debounce
});

// Pagination handling
document.getElementById('nextBtn')?.addEventListener('click', () => {
    if (currentNext) fetchContacts(currentNext);
});
document.getElementById('prevBtn')?.addEventListener('click', () => {
    if (currentPrev) fetchContacts(currentPrev);
});

// Run Init
fetchContacts();
