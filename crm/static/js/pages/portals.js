/**
 * Portals Admin Logic
 */

let portals = [];
let activePortalId = null;

const listContainer = document.getElementById('portalListContainer');
const emptyState = document.getElementById('emptyState');
const detailArea = document.getElementById('detailArea');

document.addEventListener('DOMContentLoaded', () => {
    fetchPortals();
    
    // Sync color picker with text
    document.getElementById('pColor').addEventListener('input', (e) => {
        document.getElementById('pColorText').innerText = e.target.value.toUpperCase();
    });
});

async function fetchPortals() {
    try {
        const data = await api.get('/portal/admin/');
        portals = data.results || [];
        renderList();
    } catch (err) {
        console.error('Failed to fetch portals:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading portals</div>';
    }
}

function renderList() {
    if (portals.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No portals configured.</div>';
        return;
    }

    listContainer.innerHTML = portals.map(p => {
        return `
            <div class="portal-item ${activePortalId === p.id ? 'active' : ''}" onclick="selectPortal('${p.id}')">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="font-bold text-sm text-truncate">${p.name}</span>
                    <div style="width:12px; height:12px; border-radius:50%; background:${p.theme_color};"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-xs text-muted">/${p.slug}</span>
                    ${p.is_active ? '<span class="badge bg-success" style="font-size: 9px;">Active</span>' : '<span class="badge bg-secondary" style="font-size: 9px;">Draft</span>'}
                </div>
            </div>
        `;
    }).join('');
}

function openCreatePortal() {
    activePortalId = 'new';
    
    emptyState.style.display = 'none';
    detailArea.style.display = 'flex';

    document.getElementById('pId').value = '';
    document.getElementById('pName').value = '';
    document.getElementById('pSlug').value = '';
    
    document.getElementById('pColor').value = '#2563EB';
    document.getElementById('pColorText').innerText = '#2563EB';
    
    document.getElementById('pActive').checked = true;
    document.getElementById('pAllowDeals').checked = true;
    document.getElementById('pAllowInvoices').checked = true;
    document.getElementById('pAllowProfile').checked = false;

    renderList();
}

async function selectPortal(id) {
    try {
        const p = await api.get(`/portal/admin/${id}/`);
        activePortalId = id;
        
        emptyState.style.display = 'none';
        detailArea.style.display = 'flex';

        document.getElementById('pId').value = p.id;
        document.getElementById('pName').value = p.name;
        document.getElementById('pSlug').value = p.slug;
        
        document.getElementById('pColor').value = p.theme_color || '#2563EB';
        document.getElementById('pColorText').innerText = p.theme_color || '#2563EB';
        
        document.getElementById('pActive').checked = p.is_active;
        document.getElementById('pAllowDeals').checked = p.allow_deals;
        document.getElementById('pAllowInvoices').checked = p.allow_invoices;
        document.getElementById('pAllowProfile').checked = p.allow_profile_edit;

        renderList();
    } catch (err) {
        console.error('Failed to select portal', err);
    }
}

async function savePortal() {
    const id = document.getElementById('pId').value;
    const name = document.getElementById('pName').value;
    const slug = document.getElementById('pSlug').value;
    
    if (!name || !slug) return alert('Name and Slug are required');

    const payload = {
        name,
        slug,
        theme_color: document.getElementById('pColor').value,
        is_active: document.getElementById('pActive').checked,
        allow_deals: document.getElementById('pAllowDeals').checked,
        allow_invoices: document.getElementById('pAllowInvoices').checked,
        allow_profile_edit: document.getElementById('pAllowProfile').checked
    };

    try {
        const btn = document.querySelector('#detailArea .btn-primary');
        btn.disabled = true;
        btn.innerText = 'Saving...';

        if (id) {
            await api.put(`/portal/admin/${id}/`, payload);
        } else {
            const res = await api.post('/portal/admin/', payload);
            activePortalId = res.id;
        }

        btn.disabled = false;
        btn.innerText = 'Save Configuration';
        fetchPortals();
    } catch (e) {
        alert('Failed to save portal. Ensure slug is unique.');
        const btn = document.querySelector('#detailArea .btn-primary');
        btn.disabled = false;
        btn.innerText = 'Save Configuration';
    }
}

async function deletePortal() {
    if (activePortalId === 'new' || !activePortalId) return;
    if (!confirm('Are you sure you want to delete this portal config?')) return;

    try {
        await api.delete(`/portal/admin/${activePortalId}/`);
        activePortalId = null;
        emptyState.style.display = 'flex';
        detailArea.style.display = 'none';
        fetchPortals();
    } catch (e) {
        alert('Failed to delete portal');
    }
}
