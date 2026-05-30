/**
 * Contacts Page Logic
 */

let currentContacts = [];
let currentFilterUrl = '/crm/contacts/';
let currentNext = null;
let currentPrev = null;
let editingContactId = null;

async function fetchContacts(url = '/crm/contacts/') {
    const tbody = document.getElementById('contactsTableBody');
    try {
        currentFilterUrl = url;
        const data = await api.get(url);
        currentContacts = data.results || [];

        document.getElementById('totalCount').innerText = data.count || 0;
        document.getElementById('nextBtn').disabled = !data.next;
        document.getElementById('prevBtn').disabled = !data.previous;

        currentNext = data.next;
        currentPrev = data.previous;

        if (currentContacts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="text-gray-500">No contacts found.</div></td></tr>';
            return;
        }

        tbody.innerHTML = currentContacts.map(contact => `
            <tr>
                <td><input type="checkbox" class="w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary/50"></td>
                <td>
                    <div class="flex items-center gap-3">
                        <div class="w-9 h-9 bg-primary/10 text-primary border border-primary/20 rounded-xl flex items-center justify-center font-extrabold text-sm">
                            ${(contact.first_name[0] + (contact.last_name ? contact.last_name[0] : '')).toUpperCase()}
                        </div>
                        <div>
                            <div class="font-bold text-white">${contact.first_name} ${contact.last_name}</div>
                            <div class="text-[10px] text-gray-500 font-medium">ID: ${contact.id.substring(0, 8)}</div>
                        </div>
                    </div>
                </td>
                <td class="text-sm text-gray-300">${contact.email || '-'}</td>
                <td class="text-sm text-gray-300">${contact.phone || '-'}</td>
                <td class="text-sm text-gray-300">
                    <span class="font-medium">${contact.company_name || 'Individual'}</span>
                </td>
                <td>
                    <div class="flex items-center gap-1.5">
                        <i data-lucide="award" class="w-4 h-4 text-amber-500"></i>
                        <span class="font-bold text-xs text-amber-500">${contact.score || '85'}</span>
                    </div>
                </td>
                <td>
                    <button class="btn-icon contacts-more-btn" data-id="${contact.id}">
                        <i data-lucide="more-horizontal" class="w-4 h-4 text-gray-400"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        // Populate Company Selects
        fetchCompanyList();

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch failed:', err);
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--danger);">Failed to load contacts. Check console.</td></tr>';
    }
}

async function fetchCompanyList() {
    const selects = [document.getElementById('companySelect'), document.getElementById('filterCompany')];
    try {
        const data = await api.get('/crm/companies/?limit=100');
        const companies = data.results || [];
        
        selects.forEach((select, idx) => {
            if (!select) return;
            const defaultText = idx === 0 ? 'Select Company' : 'All Companies';
            const currentValue = select.value;
            select.innerHTML = `<option value="">${defaultText}</option>` + 
                companies.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            if (currentValue) select.value = currentValue;
        });
    } catch (err) {
        console.error('Failed to fetch companies:', err);
    }
}

// Action menu handlers
const tbody = document.getElementById('contactsTableBody');
if (tbody) {
    tbody.addEventListener('click', (e) => {
        const btn = e.target.closest('.contacts-more-btn');
        if (!btn) return;
        
        const contactId = btn.dataset.id;
        const contact = currentContacts.find(c => c.id === contactId);
        if (contact) {
            showActionMenu(btn, [
                { label: 'Edit Contact', icon: 'edit-3', onClick: () => openEditContactModal(contact) },
                { label: 'Delete Contact', icon: 'trash-2', onClick: () => deleteContact(contact.id) }
            ]);
        }
    });
}

function openAddContactModal() {
    editingContactId = null;
    const form = document.getElementById('addContactForm');
    if (form) form.reset();
    
    const titleEl = document.querySelector('#addContactModal h3');
    const submitBtn = document.querySelector('#addContactModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Add New Contact';
    if (submitBtn) submitBtn.textContent = 'Save Contact';

    const modal = document.getElementById('addContactModal');
    if (modal) modal.style.display = 'flex';
}

function openEditContactModal(contact) {
    editingContactId = contact.id;
    const form = document.getElementById('addContactForm');
    if (form) {
        form.reset();
        form.elements['first_name'].value = contact.first_name || '';
        form.elements['last_name'].value = contact.last_name || '';
        form.elements['email'].value = contact.email || '';
        form.elements['company'].value = contact.company || '';
    }

    const titleEl = document.querySelector('#addContactModal h3');
    const submitBtn = document.querySelector('#addContactModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Edit Contact';
    if (submitBtn) submitBtn.textContent = 'Update Contact';

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
        if (editingContactId) {
            await api.patch(`/crm/contacts/${editingContactId}/`, payload);
        } else {
            await api.post('/crm/contacts/', payload);
        }
        closeAddContactModal();
        e.target.reset();
        fetchContacts(currentFilterUrl);
    } catch (err) {
        alert('Failed to save contact: ' + (err.data?.detail || err.message));
    }
});

async function deleteContact(id) {
    if (!confirm('Are you sure you want to delete this contact?')) return;
    try {
        await api.delete(`/crm/contacts/${id}/`);
        fetchContacts(currentFilterUrl);
    } catch (err) {
        alert('Failed to delete contact: ' + (err.data?.detail || err.message));
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
    fetchContacts('/crm/contacts/');
});

document.getElementById('filterForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const company = document.getElementById('filterCompany').value;
    const owner = document.getElementById('filterOwner').value;

    const urlObj = new URL('/crm/contacts/', window.location.origin);
    if (company) urlObj.searchParams.set('company', company);
    if (owner === 'me') {
        const myUserId = localStorage.getItem('user_id');
        if (myUserId) urlObj.searchParams.set('owner', myUserId);
    }

    toggleFilterDrawer(false);
    fetchContacts(urlObj.pathname + urlObj.search);
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
        fetchContacts(currentFilterUrl);
    } catch (err) {
        alert('Import failed: ' + (err.data?.error || err.message));
        e.target.value = '';
    }
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
            'contacts.csv',
            ['First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Score'],
            records,
            c => [c.first_name, c.last_name, c.email, c.phone, c.company_name || 'Individual', c.score || '85']
        );

        btn.innerHTML = originalHTML;
        btn.disabled = false;
    } catch (err) {
        alert('Export failed: ' + err.message);
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
