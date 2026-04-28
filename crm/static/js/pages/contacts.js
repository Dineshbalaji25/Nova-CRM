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
                <td><input type="checkbox"></td>
                <td>
                    <div class="contact-info">
                        <div class="contact-avatar" style="background:var(--primary-100); color:var(--primary-600);">
                            ${(contact.first_name[0] + (contact.last_name ? contact.last_name[0] : '')).toUpperCase()}
                        </div>
                        <div class="font-bold">${contact.first_name} ${contact.last_name}</div>
                    </div>
                </td>
                <td class="text-muted text-sm">${contact.email || '-'}</td>
                <td class="text-muted text-sm">${contact.phone || '-'}</td>
                <td><span class="badge badge-success">Active</span></td>
                <td><button class="btn-icon"><i data-lucide="more-horizontal" size="16"></i></button></td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch failed:', err);
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--danger);">Failed to load contacts. Check console.</td></tr>';
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

// Pagination handling
document.getElementById('nextBtn')?.addEventListener('click', () => {
    if (currentNext) fetchContacts(currentNext);
});
document.getElementById('prevBtn')?.addEventListener('click', () => {
    if (currentPrev) fetchContacts(currentPrev);
});

// Run Init
fetchContacts();
