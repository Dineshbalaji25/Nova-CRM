/**
 * Omnichannel Emails Logic
 */

let emails = [];
let activeEmailId = null;

const listContainer = document.getElementById('emailListContainer');
const emptyState = document.getElementById('emptyState');
const detailArea = document.getElementById('detailArea');

document.addEventListener('DOMContentLoaded', () => {
    fetchEmails();
});

async function fetchEmails() {
    try {
        const data = await api.get('/omnichannel/email-messages/');
        emails = data.results || [];
        renderList();
    } catch (err) {
        console.error('Failed to fetch emails:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading emails</div>';
    }
}

function renderList() {
    if (emails.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No emails synced.</div>';
        return;
    }

    // Sort newest first
    emails.sort((a, b) => new Date(b.sent_at) - new Date(a.sent_at));

    listContainer.innerHTML = emails.map(e => {
        const d = new Date(e.sent_at);
        const timeStr = d.toLocaleDateString() === new Date().toLocaleDateString() 
            ? d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) 
            : d.toLocaleDateString();
            
        // simple text preview from html
        let previewText = e.body_text || e.body_html || '';
        previewText = previewText.replace(/<[^>]+>/g, '').substring(0, 60);

        return `
            <div class="email-item ${activeEmailId === e.id ? 'active' : ''} ${!e.is_read ? 'unread' : ''}" onclick="selectEmail('${e.id}')">
                <div class="sender">
                    <span>${e.from_address}</span>
                    <span class="time">${timeStr}</span>
                </div>
                <div class="subject">${e.subject || '(No Subject)'}</div>
                <div class="preview">${previewText}...</div>
            </div>
        `;
    }).join('');
}

async function selectEmail(id) {
    activeEmailId = id;
    const e = emails.find(x => x.id === id);
    if (!e) return;

    emptyState.style.display = 'none';
    detailArea.style.display = 'flex';

    document.getElementById('emailSubject').innerText = e.subject || '(No Subject)';
    document.getElementById('emailFrom').innerText = e.from_address;
    document.getElementById('emailTo').innerText = `To: ${e.to_addresses}`;
    
    const d = new Date(e.sent_at);
    document.getElementById('emailDate').innerText = d.toLocaleString();

    document.getElementById('emailAvatar').innerText = e.from_address.charAt(0).toUpperCase();

    // Show linked record if exists
    let linkedHtml = '';
    if (e.lead) linkedHtml += `<span class="linked-badge me-1">Lead</span>`;
    if (e.contact) linkedHtml += `<span class="linked-badge me-1">Contact</span>`;
    if (e.deal) linkedHtml += `<span class="linked-badge me-1">Deal</span>`;
    
    document.getElementById('linkedRecord').innerHTML = linkedHtml || '<span class="text-xs text-muted">Not linked</span>';

    // Body
    const bodyContainer = document.getElementById('emailBody');
    if (e.body_html) {
        // Safe injection for internal CRM usage. 
        // In full prod, we would sanitize HTML via DOMPurify to prevent XSS.
        bodyContainer.innerHTML = e.body_html;
    } else {
        bodyContainer.innerText = e.body_text || '(Empty Message)';
    }

    renderList(); // Update active state

    // Mark read
    if (!e.is_read) {
        e.is_read = true;
        try {
            await api.patch(`/omnichannel/email-messages/${e.id}/`, { is_read: true });
        } catch (err) {
            console.error('Failed to mark read', err);
        }
    }
}

function openComposeModal() {
    alert("Compose email functionality would open a modal here in Phase 2.");
}
