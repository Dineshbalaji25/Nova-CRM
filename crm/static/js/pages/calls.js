/**
 * Omnichannel Calls Logic
 */

let calls = [];
let callModal;

const tbody = document.getElementById('callTableBody');

document.addEventListener('DOMContentLoaded', () => {
    callModal = new bootstrap.Modal(document.getElementById('logCallModal'));
    fetchCalls();
});

async function fetchCalls() {
    try {
        const data = await api.get('/omnichannel/call-logs/');
        calls = data.results || [];
        renderTable();
    } catch (err) {
        console.error('Failed to fetch calls:', err);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4 text-danger">Error loading calls</td></tr>';
    }
}

function renderTable() {
    if (calls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center p-5 text-muted">No calls logged yet.</td></tr>';
        return;
    }

    // sort newest first
    calls.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    tbody.innerHTML = calls.map(c => {
        const dirIcon = c.direction === 'inbound' ? 'arrow-down-left' : 'arrow-up-right';
        const phone = c.direction === 'inbound' ? c.from_number : c.to_number;
        const linked = c.lead ? 'Lead' : (c.contact ? 'Contact' : '-');
        
        let dur = '-';
        if (c.duration_seconds > 0) {
            const m = Math.floor(c.duration_seconds / 60);
            const s = c.duration_seconds % 60;
            dur = m > 0 ? `${m}m ${s}s` : `${s}s`;
        }

        return `
            <tr>
                <td>
                    <div class="dir-badge">
                        <i data-lucide="${dirIcon}" size="14"></i> ${c.direction.toUpperCase()}
                    </div>
                </td>
                <td class="font-bold">${phone}</td>
                <td>${dur}</td>
                <td><span class="status-badge status-${c.status}">${c.status.toUpperCase()}</span></td>
                <td style="max-width:300px;" class="text-truncate" title="${c.notes}">${c.notes || '-'}</td>
                <td><span class="badge bg-light text-dark border">${linked}</span></td>
            </tr>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

function openLogCallModal() {
    document.getElementById('callForm').reset();
    callModal.show();
}

async function saveCall() {
    const direction = document.getElementById('callDirection').value;
    const status = document.getElementById('callStatus').value;
    const phone = document.getElementById('callPhone').value;
    const duration = parseInt(document.getElementById('callDuration').value) || 0;
    const notes = document.getElementById('callNotes').value;

    if (!phone) return alert('Phone number required');

    let from_number = 'System';
    let to_number = phone;

    if (direction === 'inbound') {
        from_number = phone;
        to_number = 'System';
    }

    const payload = {
        direction,
        status,
        from_number,
        to_number,
        duration_seconds: duration,
        notes
    };

    try {
        const btn = document.querySelector('#logCallModal .btn-primary');
        btn.disabled = true;
        btn.innerText = 'Saving...';

        await api.post('/omnichannel/call-logs/', payload);
        callModal.hide();
        fetchCalls();

        btn.disabled = false;
        btn.innerText = 'Log Call';
    } catch (e) {
        alert('Failed to log call');
        const btn = document.querySelector('#logCallModal .btn-primary');
        btn.disabled = false;
        btn.innerText = 'Log Call';
    }
}
