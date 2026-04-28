/**
 * Blueprints Logic
 */

let blueprints = [];
let activeBp = null;
let activeItemType = null; // 'state' or 'transition'
let activeItemIndex = null;

// UI Elements
const listContainer = document.getElementById('bpListContainer');
const canvas = document.getElementById('canvas');
const emptyState = document.getElementById('emptyState');
const activeArea = document.getElementById('activeArea');
const configDrawer = document.getElementById('configDrawer');
let createModal;

document.addEventListener('DOMContentLoaded', () => {
    createModal = new bootstrap.Modal(document.getElementById('createBlueprintModal'));
    fetchBlueprints();
});

async function fetchBlueprints() {
    try {
        const data = await api.get('/workflows/blueprints/');
        blueprints = data.results || [];
        renderList();
    } catch (err) {
        console.error('Failed to fetch blueprints:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading blueprints</div>';
    }
}

function renderList() {
    if (blueprints.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No blueprints found.</div>';
        return;
    }

    listContainer.innerHTML = blueprints.map(b => `
        <div class="bp-item ${activeBp?.id === b.id ? 'active' : ''}" onclick="selectBlueprint('${b.id}')">
            <div class="d-flex justify-content-between align-items-center">
                <span class="font-bold text-sm text-truncate">${b.name}</span>
                ${b.is_active ? '<span class="badge bg-success" style="font-size: 10px;">Active</span>' : '<span class="badge bg-secondary" style="font-size: 10px;">Draft</span>'}
            </div>
            <div class="text-xs text-muted mt-1 text-truncate">${b.target_model.toUpperCase()}</div>
        </div>
    `).join('');
}

function openCreateModal() {
    createModal.show();
}

async function submitNewBlueprint() {
    const name = document.getElementById('newBpName').value;
    const model = document.getElementById('newBpModule').value;

    if (!name) return alert('Name required');

    try {
        const b = await api.post('/workflows/blueprints/', {
            name,
            target_model: model,
            is_active: false,
            entry_criteria: {},
            states: [],
            transitions: []
        });
        createModal.hide();
        await fetchBlueprints();
        selectBlueprint(b.id);
    } catch (err) {
        alert('Failed to create blueprint: ' + (err.data?.detail || ''));
    }
}

async function selectBlueprint(id) {
    try {
        activeBp = await api.get(`/workflows/blueprints/${id}/`);
        
        if (!activeBp.states) activeBp.states = [];
        if (!activeBp.transitions) activeBp.transitions = [];

        emptyState.style.display = 'none';
        activeArea.style.display = 'flex';
        closeDrawer();

        document.getElementById('activeName').innerText = activeBp.name;
        document.getElementById('activeTarget').innerText = `Module: ${activeBp.target_model.toUpperCase()}`;

        renderList();
        renderCanvas();
    } catch (err) {
        console.error('Select failed:', err);
    }
}

function renderCanvas() {
    if (!activeBp) return;

    let html = '';

    if (activeBp.states.length === 0) {
        html = '<div class="alert alert-info">No states defined yet. Click "Add State" to begin.</div>';
    }

    activeBp.states.forEach((state, sIndex) => {
        // Find outgoing transitions from this state
        const outgoing = activeBp.transitions.filter(t => t.from_state === state.id || (state.id === undefined && t.from_state_index === sIndex));
        
        html += `
            <div class="state-card">
                <div class="state-header">
                    <div class="d-flex align-items-center gap-2">
                        <i data-lucide="circle-dot" size="18" style="color: var(--primary-500);"></i>
                        <span class="font-bold">${state.name}</span>
                        ${state.reference_value ? `<span class="badge bg-light text-dark border">${state.reference_value}</span>` : ''}
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-secondary" onclick="openStateConfig(${sIndex})">Edit</button>
                        <button class="btn btn-sm btn-outline-primary" onclick="openAddTransition(${sIndex})"><i data-lucide="plus" size="14"></i> Transition</button>
                    </div>
                </div>
                ${outgoing.length > 0 ? `
                    <ul class="transition-list">
                        ${outgoing.map((t, tIndexInFiltered) => {
                            // find real index
                            const tIndex = activeBp.transitions.findIndex(x => x === t);
                            let toStateName = 'Unknown';
                            if (t.to_state) {
                                const dest = activeBp.states.find(s => s.id === t.to_state);
                                if (dest) toStateName = dest.name;
                            } else if (t.to_state_index !== undefined) {
                                toStateName = activeBp.states[t.to_state_index].name;
                            }

                            return `
                                <li class="transition-item" onclick="openTransitionConfig(${tIndex})">
                                    <div>
                                        <span class="font-bold text-sm">${t.name}</span>
                                        <i data-lucide="arrow-right" size="14" class="mx-2 text-muted"></i>
                                        <span class="transition-badge">${toStateName}</span>
                                    </div>
                                    <i data-lucide="chevron-right" size="16" class="text-muted"></i>
                                </li>
                            `;
                        }).join('')}
                    </ul>
                ` : '<div class="p-3 text-sm text-muted text-center border-top">No outgoing transitions</div>'}
            </div>
        `;
    });

    canvas.innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

// --- Drawer Logic ---

function closeDrawer() {
    configDrawer.classList.remove('open');
    activeItemType = null;
    activeItemIndex = null;
}

function openAddState() {
    activeItemType = 'state';
    activeItemIndex = 'new';
    
    document.getElementById('drawerTitle').innerText = 'Add New State';
    document.getElementById('btnDelete').style.display = 'none';

    document.getElementById('drawerBody').innerHTML = `
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">State Name</label>
            <input type="text" id="stateName" class="form-control" placeholder="e.g., Negotiation">
        </div>
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">Reference Value (Database Field Value)</label>
            <input type="text" id="stateRef" class="form-control" placeholder="e.g., negotiation_stage">
            <div class="form-text text-xs">The actual value saved in the database when in this state.</div>
        </div>
    `;
    configDrawer.classList.add('open');
}

function openStateConfig(index) {
    activeItemType = 'state';
    activeItemIndex = index;
    const state = activeBp.states[index];

    document.getElementById('drawerTitle').innerText = 'Edit State';
    document.getElementById('btnDelete').style.display = 'block';

    document.getElementById('drawerBody').innerHTML = `
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">State Name</label>
            <input type="text" id="stateName" class="form-control" value="${state.name}">
        </div>
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">Reference Value</label>
            <input type="text" id="stateRef" class="form-control" value="${state.reference_value || ''}">
        </div>
    `;
    configDrawer.classList.add('open');
}

function openAddTransition(fromStateIndex) {
    activeItemType = 'transition';
    activeItemIndex = 'new';
    
    document.getElementById('drawerTitle').innerText = 'Add Transition';
    document.getElementById('btnDelete').style.display = 'none';

    let options = activeBp.states.map((s, i) => `<option value="${i}">${s.name}</option>`).join('');

    document.getElementById('drawerBody').innerHTML = `
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">Transition Name (Button Label)</label>
            <input type="text" id="transName" class="form-control" placeholder="e.g., Send Proposal">
        </div>
        <input type="hidden" id="transFrom" value="${fromStateIndex}">
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">To State</label>
            <select id="transTo" class="form-select">
                ${options}
            </select>
        </div>
        <hr>
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">DURING: Required Fields (JSON List)</label>
            <textarea id="transReqFields" class="form-control" rows="3" placeholder='["amount", "expected_close_date"]'></textarea>
            <div class="form-text text-xs">Fields the user MUST fill out before transition occurs.</div>
        </div>
    `;
    configDrawer.classList.add('open');
}

function openTransitionConfig(index) {
    activeItemType = 'transition';
    activeItemIndex = index;
    const t = activeBp.transitions[index];

    document.getElementById('drawerTitle').innerText = 'Edit Transition';
    document.getElementById('btnDelete').style.display = 'block';

    // Find state indexes to pre-select
    let fromIdx = activeBp.states.findIndex(s => s.id === t.from_state);
    if(fromIdx === -1 && t.from_state_index !== undefined) fromIdx = t.from_state_index;
    
    let toIdx = activeBp.states.findIndex(s => s.id === t.to_state);
    if(toIdx === -1 && t.to_state_index !== undefined) toIdx = t.to_state_index;

    let options = activeBp.states.map((s, i) => `<option value="${i}" ${i === toIdx ? 'selected' : ''}>${s.name}</option>`).join('');

    document.getElementById('drawerBody').innerHTML = `
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">Transition Name</label>
            <input type="text" id="transName" class="form-control" value="${t.name}">
        </div>
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">To State</label>
            <select id="transTo" class="form-select">
                ${options}
            </select>
        </div>
        <hr>
        <div class="mb-3">
            <label class="form-label text-xs fw-bold text-muted">DURING: Required Fields (JSON List)</label>
            <textarea id="transReqFields" class="form-control" rows="3">${JSON.stringify(t.required_fields || [])}</textarea>
        </div>
    `;
    configDrawer.classList.add('open');
}

function saveDrawerConfig() {
    if (activeItemType === 'state') {
        const name = document.getElementById('stateName').value;
        const ref = document.getElementById('stateRef').value;
        if(!name) return alert('Name required');

        if (activeItemIndex === 'new') {
            activeBp.states.push({ name, reference_value: ref });
        } else {
            activeBp.states[activeItemIndex].name = name;
            activeBp.states[activeItemIndex].reference_value = ref;
        }
    } else if (activeItemType === 'transition') {
        const name = document.getElementById('transName').value;
        const toStateIndex = parseInt(document.getElementById('transTo').value);
        let reqFields = [];
        try {
            const rfVal = document.getElementById('transReqFields').value;
            if(rfVal) reqFields = JSON.parse(rfVal);
        } catch(e) {
            return alert('Invalid JSON in required fields');
        }

        if(!name) return alert('Name required');

        if (activeItemIndex === 'new') {
            const fromStateIndex = parseInt(document.getElementById('transFrom').value);
            activeBp.transitions.push({
                name,
                from_state_index: fromStateIndex, // Temp index for unsaved
                from_state: activeBp.states[fromStateIndex].id,
                to_state_index: toStateIndex,
                to_state: activeBp.states[toStateIndex].id,
                required_fields: reqFields
            });
        } else {
            activeBp.transitions[activeItemIndex].name = name;
            activeBp.transitions[activeItemIndex].to_state_index = toStateIndex;
            activeBp.transitions[activeItemIndex].to_state = activeBp.states[toStateIndex].id;
            activeBp.transitions[activeItemIndex].required_fields = reqFields;
        }
    }

    closeDrawer();
    renderCanvas();
}

function deleteActiveItem() {
    if(!confirm('Are you sure?')) return;

    if (activeItemType === 'state') {
        // Also remove transitions involving this state
        const state = activeBp.states[activeItemIndex];
        activeBp.transitions = activeBp.transitions.filter(t => {
            let matchesFrom = (t.from_state && t.from_state === state.id) || t.from_state_index === activeItemIndex;
            let matchesTo = (t.to_state && t.to_state === state.id) || t.to_state_index === activeItemIndex;
            return !matchesFrom && !matchesTo;
        });
        activeBp.states.splice(activeItemIndex, 1);

    } else if (activeItemType === 'transition') {
        activeBp.transitions.splice(activeItemIndex, 1);
    }
    
    closeDrawer();
    renderCanvas();
}

async function saveBlueprint() {
    if (!activeBp) return;
    try {
        const btn = document.querySelector('.bp-header .btn-primary');
        const origText = btn.innerText;
        btn.innerText = 'Saving...';
        btn.disabled = true;

        // Currently, nested writes on BlueprintSerializer need to handle states/transitions mapping.
        // For standard DRF WritableNested serializers, the payload matches the GET format.
        // We will pass the full tree back.
        await api.put(`/workflows/blueprints/${activeBp.id}/`, {
            name: activeBp.name,
            target_model: activeBp.target_model,
            is_active: activeBp.is_active,
            entry_criteria: activeBp.entry_criteria,
            states: activeBp.states,
            transitions: activeBp.transitions
        });

        setTimeout(() => {
            btn.innerText = 'Saved!';
            setTimeout(() => {
                btn.innerText = origText;
                btn.disabled = false;
            }, 2000);
        }, 500);

        // Re-fetch to get accurate DB IDs for newly created states/transitions
        await selectBlueprint(activeBp.id);
        fetchBlueprints(); 
    } catch (err) {
        console.error('Save failed', err);
        alert('Failed to save blueprint. ' + (err.data?.detail || ''));
        const btn = document.querySelector('.bp-header .btn-primary');
        btn.innerText = 'Save Blueprint';
        btn.disabled = false;
    }
}
