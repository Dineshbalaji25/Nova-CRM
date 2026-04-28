/**
 * Territories & Assignment Rules Logic
 */

let territories = [];
let rules = [];
let activeTerId = null;

// Modals
let terModal;
let ruleModal;

// Elements
const listContainer = document.getElementById('terListContainer');
const emptyState = document.getElementById('emptyState');
const detailArea = document.getElementById('detailArea');
const rulesContainer = document.getElementById('rulesContainer');

document.addEventListener('DOMContentLoaded', () => {
    terModal = new bootstrap.Modal(document.getElementById('territoryModal'));
    ruleModal = new bootstrap.Modal(document.getElementById('ruleModal'));
    
    fetchTerritories();
});

async function fetchTerritories() {
    try {
        const [terData, rulesData] = await Promise.all([
            api.get('/crm/territories/'),
            api.get('/crm/assignment-rules/')
        ]);
        territories = terData.results || [];
        rules = rulesData.results || [];
        
        populateParentDropdown();
        renderList();
        
        if (activeTerId) {
            // Re-render detail if active
            selectTerritory(activeTerId);
        }
    } catch (err) {
        console.error('Failed to fetch data:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading territories</div>';
    }
}

function populateParentDropdown() {
    const select = document.getElementById('terParent');
    select.innerHTML = '<option value="">None (Top Level)</option>';
    territories.forEach(t => {
        // Prevent setting self as parent
        if (t.id !== document.getElementById('terId').value) {
            select.innerHTML += `<option value="${t.id}">${t.name}</option>`;
        }
    });
}

function renderList() {
    if (territories.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No territories found.</div>';
        return;
    }

    listContainer.innerHTML = territories.map(t => `
        <div class="ter-item ${activeTerId === t.id ? 'active' : ''}" onclick="selectTerritory('${t.id}')">
            <div style="width:32px; height:32px; border-radius:6px; background:var(--gray-100); display:flex; align-items:center; justify-content:center; color:var(--gray-500);">
                <i data-lucide="map-pin" size="16"></i>
            </div>
            <div>
                <div class="font-bold text-sm text-truncate">${t.name}</div>
                <div class="text-xs text-muted text-truncate">${t.parent ? 'Sub-territory' : 'Top Level'}</div>
            </div>
        </div>
    `).join('');
    
    if (window.lucide) lucide.createIcons();
}

// --- Territory CRUD ---

function openCreateTerritory() {
    document.getElementById('terModalTitle').innerText = 'New Territory';
    document.getElementById('territoryForm').reset();
    document.getElementById('terId').value = '';
    document.getElementById('btnDeleteTer').style.display = 'none';
    populateParentDropdown();
    terModal.show();
}

function editTerritory() {
    if (!activeTerId) return;
    const t = territories.find(x => x.id === activeTerId);
    if (!t) return;

    document.getElementById('terModalTitle').innerText = 'Edit Territory';
    document.getElementById('terId').value = t.id;
    document.getElementById('terName').value = t.name;
    document.getElementById('terDesc').value = t.description || '';
    
    populateParentDropdown();
    document.getElementById('terParent').value = t.parent || '';
    
    document.getElementById('btnDeleteTer').style.display = 'block';
    terModal.show();
}

async function saveTerritory() {
    const id = document.getElementById('terId').value;
    const name = document.getElementById('terName').value;
    const description = document.getElementById('terDesc').value;
    const parent = document.getElementById('terParent').value;

    if (!name) return alert('Name is required');

    const payload = { name, description, parent: parent || null };

    try {
        if (id) {
            await api.put(`/crm/territories/${id}/`, payload);
        } else {
            const res = await api.post('/crm/territories/', payload);
            activeTerId = res.id;
        }
        terModal.hide();
        fetchTerritories();
    } catch (e) {
        alert('Failed to save territory');
    }
}

async function deleteTerritory() {
    const id = document.getElementById('terId').value;
    if (!id) return;
    if (!confirm('Are you sure you want to delete this territory?')) return;

    try {
        await api.delete(`/crm/territories/${id}/`);
        activeTerId = null;
        emptyState.style.display = 'flex';
        detailArea.style.display = 'none';
        terModal.hide();
        fetchTerritories();
    } catch (e) {
        alert('Failed to delete territory');
    }
}

// --- Detail View ---

function selectTerritory(id) {
    const t = territories.find(x => x.id === id);
    if (!t) return;

    activeTerId = id;
    emptyState.style.display = 'none';
    detailArea.style.display = 'flex';

    document.getElementById('detailName').innerText = t.name;
    document.getElementById('detailManager').innerText = t.manager ? `Manager: ${t.manager}` : 'Manager: None';

    renderList(); // update active state
    renderRules();
}

// --- Rules ---

function renderRules() {
    const tRules = rules.filter(r => r.assign_to_territory === activeTerId);
    
    if (tRules.length === 0) {
        rulesContainer.innerHTML = '<div class="alert alert-light border text-center text-muted">No assignment rules defined for this territory.</div>';
        return;
    }

    // sort by position
    tRules.sort((a, b) => a.position - b.position);

    rulesContainer.innerHTML = tRules.map(r => `
        <div class="rule-card ${!r.is_active ? 'inactive' : ''}">
            <div>
                <div class="d-flex align-items-center gap-2 mb-1">
                    <span class="badge bg-secondary text-xs">${r.target_model.toUpperCase()}</span>
                    <h5 class="font-bold text-sm m-0">${r.name}</h5>
                    ${!r.is_active ? '<span class="badge bg-light text-dark border">Inactive</span>' : ''}
                </div>
                <div class="text-xs text-muted">
                    Priority: ${r.position} | Conditions: ${Object.keys(r.criteria || {}).length} rules
                </div>
            </div>
            <button class="btn btn-outline-secondary btn-sm" onclick="editRule('${r.id}')">Edit Rule</button>
        </div>
    `).join('');
}

// --- Rule CRUD ---

function openCreateRule() {
    document.getElementById('ruleModalTitle').innerText = 'New Assignment Rule';
    document.getElementById('ruleForm').reset();
    document.getElementById('ruleId').value = '';
    document.getElementById('btnDeleteRule').style.display = 'none';
    
    document.getElementById('ruleCriteriaContainer').innerHTML = '';
    addRuleCriteriaRow();
    
    ruleModal.show();
}

function editRule(id) {
    const r = rules.find(x => x.id === id);
    if (!r) return;

    document.getElementById('ruleModalTitle').innerText = 'Edit Assignment Rule';
    document.getElementById('ruleId').value = r.id;
    document.getElementById('ruleName').value = r.name;
    document.getElementById('ruleTarget').value = r.target_model;
    document.getElementById('rulePosition').value = r.position;
    document.getElementById('ruleActive').checked = r.is_active;

    document.getElementById('btnDeleteRule').style.display = 'block';

    const container = document.getElementById('ruleCriteriaContainer');
    container.innerHTML = '';
    
    // criteria is a dict like {"state": "CA", "industry": "Tech"}
    const keys = Object.keys(r.criteria || {});
    if (keys.length === 0) {
        addRuleCriteriaRow();
    } else {
        keys.forEach(k => addRuleCriteriaRow(k, r.criteria[k]));
    }

    ruleModal.show();
}

function addRuleCriteriaRow(field = '', value = '') {
    const rowId = 'rule_row_' + Math.random().toString(36).substr(2, 9);
    
    const html = `
        <div class="criteria-row" id="${rowId}">
            <input type="text" class="form-control rc-field" placeholder="Field name (e.g., state)" value="${field}">
            <div class="text-muted font-bold text-xs">EQUALS</div>
            <input type="text" class="form-control rc-value" placeholder="Value (e.g., CA)" value="${value}">
            <button type="button" class="btn-icon text-danger" onclick="document.getElementById('${rowId}').remove()">
                <i data-lucide="trash-2" size="18"></i>
            </button>
        </div>
    `;
    document.getElementById('ruleCriteriaContainer').insertAdjacentHTML('beforeend', html);
    if (window.lucide) lucide.createIcons();
}

async function saveRule() {
    const id = document.getElementById('ruleId').value;
    const name = document.getElementById('ruleName').value;
    const target_model = document.getElementById('ruleTarget').value;
    const position = parseInt(document.getElementById('rulePosition').value) || 10;
    const is_active = document.getElementById('ruleActive').checked;

    if (!name) return alert('Name required');

    // Gather criteria
    const criteria = {};
    const rows = document.querySelectorAll('#ruleCriteriaContainer .criteria-row');
    rows.forEach(row => {
        const k = row.querySelector('.rc-field').value.trim();
        const v = row.querySelector('.rc-value').value.trim();
        if (k && v) criteria[k] = v;
    });

    const payload = {
        name, target_model, position, is_active, criteria,
        assign_to_territory: activeTerId
    };

    try {
        if (id) {
            await api.put(`/crm/assignment-rules/${id}/`, payload);
        } else {
            await api.post('/crm/assignment-rules/', payload);
        }
        ruleModal.hide();
        fetchTerritories(); // refresh all to get updated rules
    } catch (e) {
        alert('Failed to save rule');
    }
}

async function deleteRule() {
    const id = document.getElementById('ruleId').value;
    if (!id) return;
    if (!confirm('Delete this assignment rule?')) return;

    try {
        await api.delete(`/crm/assignment-rules/${id}/`);
        ruleModal.hide();
        fetchTerritories();
    } catch (e) {
        alert('Failed to delete rule');
    }
}
