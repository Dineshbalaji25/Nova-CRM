/**
 * Support Page Logic
 */

async function fetchTickets() {
    const tbody = document.getElementById('ticketsTableBody');
    if (!tbody) return;

    try {
        const data = await api.get('/support/tickets/');
        const results = data.results || [];

        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="py-20 text-center text-gray-500 font-medium bg-white/[0.02] border border-white/5 rounded-xl">No support tickets found.</td></tr>';
            return;
        }

        tbody.innerHTML = results.map(ticket => `
            <tr class="group">
                <td class="w-12 text-center">
                    <input type="checkbox" class="w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary/50">
                </td>
                <td>
                    <div class="flex flex-col">
                        <span class="text-sm font-bold text-white group-hover:text-primary transition-colors cursor-pointer">${ticket.subject}</span>
                        <span class="text-[10px] text-gray-500 font-medium">#${ticket.id.substring(0, 8)}</span>
                    </div>
                </td>
                <td>
                    <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-widest bg-white/5 border border-white/10 text-gray-400">
                        ${ticket.status.replace('_', ' ')}
                    </span>
                </td>
                <td>
                    <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-widest ${getPriorityClass(ticket.priority)}">
                        ${ticket.priority}
                    </span>
                </td>
                <td>
                    <div class="flex items-center gap-2">
                        <div class="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-[10px] font-bold">
                            ${(ticket.assigned_to_name || 'U').substring(0, 1)}
                        </div>
                        <span class="text-xs font-medium text-gray-300">${ticket.assigned_to_name || 'Unassigned'}</span>
                    </div>
                </td>
                <td class="text-xs text-gray-500 font-medium">
                    ${new Date(ticket.created_at).toLocaleDateString()}
                </td>
                <td>
                    <button class="p-2 hover:bg-white/5 rounded-lg text-gray-500 hover:text-white transition-all opacity-0 group-hover:opacity-100">
                        <i data-lucide="external-link" class="w-4 h-4"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Fetch tickets failed:', err);
    }
}

function getPriorityClass(p) {
    switch (p.toLowerCase()) {
        case 'urgent': return 'bg-danger/10 border border-danger/20 text-danger';
        case 'high': return 'bg-orange-500/10 border border-orange-500/20 text-orange-500';
        case 'medium': return 'bg-gold/10 border border-gold/20 text-gold';
        default: return 'bg-success/10 border border-success/20 text-success';
    }
}

function openAddTicketModal() {
    const modal = document.getElementById('addTicketModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        loadTicketPrerequisites();
    }
}

function closeAddTicketModal() {
    const modal = document.getElementById('addTicketModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

async function loadTicketPrerequisites() {
    try {
        const companies = await api.get('/crm/companies/');
        const select = document.getElementById('ticketCompanySelect');
        if (select) {
            select.innerHTML = '<option value="">None</option>' +
                (companies.results || []).map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }
    } catch (err) {
        console.error('Failed to load companies for tickets', err);
    }
}

document.getElementById('addTicketForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        await api.post('/support/tickets/', payload);
        closeAddTicketModal();
        e.target.reset();
        fetchTickets();
    } catch (err) {
        alert('Failed to create ticket: ' + (err.data?.detail || err.message));
    }
});

// Run Init
fetchTickets();
