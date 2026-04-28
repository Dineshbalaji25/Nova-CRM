/**
 * Workflows Builder Logic
 */

let workflows = [];
let activeWorkflow = null;
let metadata = { triggers: [], actions: [] };
let activeNodeIndex = null; // null means editing trigger, number means editing specific node in nodes array

// UI Elements
const listContainer = document.getElementById('workflowItemsContainer');
const canvas = document.getElementById('canvas');
const emptyState = document.getElementById('emptyBuilderState');
const activeArea = document.getElementById('workflowCanvasArea');
const configPanel = document.getElementById('configPanel');
let createModal;

document.addEventListener('DOMContentLoaded', () => {
    createModal = new bootstrap.Modal(document.getElementById('createWorkflowModal'));
    fetchMetadata();
    fetchWorkflows();
});

async function fetchMetadata() {
    try {
        metadata = await api.get('/workflows/metadata/');
    } catch (err) {
        console.error('Failed to fetch metadata:', err);
    }
}

async function fetchWorkflows() {
    try {
        const data = await api.get('/workflows/definitions/');
        workflows = data.results || [];
        renderWorkflowList();
    } catch (err) {
        console.error('Failed to fetch workflows:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading workflows</div>';
    }
}

function renderWorkflowList() {
    if (workflows.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No workflows found. Create one to get started.</div>';
        return;
    }

    listContainer.innerHTML = workflows.map(w => `
        <div class="workflow-item ${activeWorkflow?.id === w.id ? 'active' : ''}" onclick="selectWorkflow('${w.id}')">
            <div class="d-flex justify-content-between align-items-center">
                <span class="font-bold text-sm text-truncate">${w.name}</span>
                ${w.is_active ? '<span class="badge bg-success" style="font-size: 10px;">Active</span>' : '<span class="badge bg-secondary" style="font-size: 10px;">Draft</span>'}
            </div>
            <div class="text-xs text-muted mt-1 text-truncate">${w.trigger_config?.model ? w.trigger_config.model.toUpperCase() : ''} • ${w.trigger_type}</div>
        </div>
    `).join('');
}

function openCreateModal() {
    createModal.show();
}

async function submitNewWorkflow() {
    const name = document.getElementById('newWorkflowName').value;
    const model = document.getElementById('newWorkflowModule').value;
    const trigger = document.getElementById('newWorkflowTrigger').value;

    if (!name) return alert('Name required');

    try {
        const w = await api.post('/workflows/definitions/', {
            name,
            trigger_type: trigger,
            trigger_config: { model },
            nodes: []
        });
        createModal.hide();
        await fetchWorkflows();
        selectWorkflow(w.id);
    } catch (err) {
        alert('Failed to create workflow: ' + (err.data?.detail || 'Unknown error'));
    }
}

async function selectWorkflow(id) {
    try {
        activeWorkflow = await api.get(`/workflows/definitions/${id}/`);
        // normalize nodes
        if (!activeWorkflow.nodes) activeWorkflow.nodes = [];
        
        emptyState.style.display = 'none';
        activeArea.style.display = 'flex';
        closeConfigPanel();

        document.getElementById('activeWorkflowName').innerText = activeWorkflow.name;
        document.getElementById('activeWorkflowTrigger').innerText = `${activeWorkflow.trigger_config?.model?.toUpperCase() || 'RECORD'} • ${activeWorkflow.trigger_type.replace('_', ' ').toUpperCase()}`;

        renderWorkflowList(); // Update active state
        renderCanvas();
    } catch (err) {
        console.error('Select failed:', err);
    }
}

function renderCanvas() {
    if (!activeWorkflow) return;

    let html = '';

    // 1. TRIGGER NODE
    html += `
        <div class="flow-node" onclick="openConfig('trigger')">
            <div class="flow-node-header">
                <div class="flow-icon trigger-icon"><i data-lucide="zap" size="16"></i></div>
                <div>
                    <div class="text-xs text-muted font-bold">TRIGGER</div>
                    <div class="text-sm font-bold">${activeWorkflow.trigger_config?.model?.toUpperCase() || 'Record'} ${activeWorkflow.trigger_type.replace('on_', '').toUpperCase() || 'Event'}</div>
                </div>
            </div>
            <div class="text-xs text-muted mt-2">When this event happens, the workflow starts.</div>
        </div>
    `;

    // 2. ACTION / CONDITION NODES
    activeWorkflow.nodes.forEach((node, index) => {
        // Line and Add Button above node
        html += `
            <div class="flow-line">
                <div class="flow-add-btn" onclick="openNodeSelector(${index})">
                    <i data-lucide="plus" size="14"></i>
                </div>
            </div>
        `;

        const isAction = node.node_type === 'action';
        const iconClass = isAction ? 'action-icon' : 'condition-icon';
        const iconName = isAction ? 'play' : 'git-branch';
        
        // Find metadata label if action
        let actionLabel = node.action_name;
        if(isAction) {
             const mAction = metadata.actions.find(a => a.key === node.action_name);
             if(mAction) actionLabel = mAction.label;
        }

        html += `
            <div class="flow-node" onclick="openConfig(${index})">
                <div class="flow-node-header">
                    <div class="flow-icon ${iconClass}"><i data-lucide="${iconName}" size="16"></i></div>
                    <div>
                        <div class="text-xs text-muted font-bold">${node.node_type.toUpperCase()}</div>
                        <div class="text-sm font-bold text-truncate" style="max-width: 200px;">${isAction ? actionLabel : 'Condition'}</div>
                    </div>
                </div>
                ${node.label ? `<div class="text-xs text-muted mt-2">${node.label}</div>` : ''}
            </div>
        `;
    });

    // End Line and Final Add Button
    html += `
        <div class="flow-line">
            <div class="flow-add-btn" onclick="openNodeSelector(${activeWorkflow.nodes.length})">
                <i data-lucide="plus" size="14"></i>
            </div>
        </div>
        <div style="width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--gray-300); margin: 0 auto; background: white;"></div>
    `;

    canvas.innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

// --- Configuration Panel ---

function closeConfigPanel() {
    configPanel.classList.remove('open');
    activeNodeIndex = null;
}

function openConfig(index) {
    activeNodeIndex = index;
    const body = document.getElementById('configPanelBody');
    const title = document.getElementById('configPanelTitle');
    const btnDelete = document.getElementById('btnDeleteNode');

    configPanel.classList.add('open');

    if (index === 'trigger') {
        title.innerText = 'Configure Trigger';
        btnDelete.style.display = 'none';
        body.innerHTML = `
            <div class="alert alert-info text-sm">
                Trigger configuration is set when creating the workflow. Advanced filtering coming soon.
            </div>
            <div class="mb-3">
                <label class="form-label text-xs fw-bold text-muted">Target Model</label>
                <input type="text" class="form-control bg-light" value="${activeWorkflow.trigger_config?.model || ''}" disabled>
            </div>
            <div class="mb-3">
                <label class="form-label text-xs fw-bold text-muted">Trigger Type</label>
                <input type="text" class="form-control bg-light" value="${activeWorkflow.trigger_type}" disabled>
            </div>
            <div class="form-check form-switch mt-4">
                <input class="form-check-input" type="checkbox" id="workflowActiveSwitch" ${activeWorkflow.is_active ? 'checked' : ''}>
                <label class="form-check-label text-sm fw-bold" for="workflowActiveSwitch">Workflow is Active</label>
            </div>
        `;
    } else {
        const node = activeWorkflow.nodes[index];
        title.innerText = `Configure ${node.node_type.toUpperCase()}`;
        btnDelete.style.display = 'block';

        if (node.node_type === 'action') {
            const mAction = metadata.actions.find(a => a.key === node.action_name);
            
            let fieldsHtml = '';
            if (node.action_name === 'crm.update_record') {
                fieldsHtml = `
                    <div class="mb-3">
                        <label class="form-label text-xs fw-bold text-muted">Field Updates (JSON Map)</label>
                        <textarea id="nodeActionConfig" class="form-control" rows="4" placeholder='{"status": "qualified"}'>${JSON.stringify(node.action_config || {}, null, 2)}</textarea>
                        <div class="form-text text-xs">Example: {"status": "won", "probability": 100}</div>
                    </div>
                `;
            } else if (node.action_name === 'crm.create_task') {
                 fieldsHtml = `
                    <div class="mb-3">
                        <label class="form-label text-xs fw-bold text-muted">Task Subject</label>
                        <input type="text" id="taskSubject" class="form-control" value="${node.action_config?.subject || ''}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-xs fw-bold text-muted">Task Notes</label>
                        <textarea id="taskNotes" class="form-control" rows="3">${node.action_config?.body || ''}</textarea>
                    </div>
                `;
            } else {
                fieldsHtml = `
                    <div class="mb-3">
                        <label class="form-label text-xs fw-bold text-muted">Configuration Payload</label>
                        <textarea id="nodeActionConfig" class="form-control" rows="4">${JSON.stringify(node.action_config || {}, null, 2)}</textarea>
                    </div>
                `;
            }

            body.innerHTML = `
                <div class="mb-3">
                    <label class="form-label text-xs fw-bold text-muted">Action Label</label>
                    <input type="text" id="nodeLabel" class="form-control" value="${node.label || ''}">
                </div>
                <div class="mb-3">
                    <label class="form-label text-xs fw-bold text-muted">Action Type</label>
                    <input type="text" class="form-control bg-light" value="${mAction ? mAction.label : node.action_name}" disabled>
                </div>
                ${fieldsHtml}
            `;
        } else {
            // Condition
            body.innerHTML = `
                <div class="mb-3">
                    <label class="form-label text-xs fw-bold text-muted">Condition Label</label>
                    <input type="text" id="nodeLabel" class="form-control" value="${node.label || ''}">
                </div>
                <div class="mb-3">
                    <label class="form-label text-xs fw-bold text-muted">Criteria (JSON list)</label>
                    <textarea id="nodeActionConfig" class="form-control" rows="6" placeholder='[{"field": "amount", "operator": "gt", "value": 1000}]'>${JSON.stringify(node.action_config || [], null, 2)}</textarea>
                    <div class="form-text text-xs">Example: [{"field": "status", "operator": "eq", "value": "new"}]</div>
                </div>
            `;
        }
    }
}

function openNodeSelector(insertIndex) {
    const body = document.getElementById('configPanelBody');
    const title = document.getElementById('configPanelTitle');
    document.getElementById('btnDeleteNode').style.display = 'none';

    configPanel.classList.add('open');
    title.innerText = 'Add New Node';
    activeNodeIndex = 'new_' + insertIndex;

    let actionsHtml = metadata.actions.map(a => `
        <button class="btn btn-outline-primary text-start w-100 mb-2" onclick="insertNode('action', '${a.key}', ${insertIndex})">
            <i data-lucide="play" size="14" class="me-2"></i> ${a.label}
        </button>
    `).join('');

    body.innerHTML = `
        <div class="mb-4">
            <h5 class="text-sm fw-bold mb-3">Add Logic</h5>
            <button class="btn btn-outline-warning text-start w-100 mb-2" onclick="insertNode('condition', '', ${insertIndex})">
                <i data-lucide="git-branch" size="14" class="me-2"></i> Condition / If-Else
            </button>
        </div>
        <div>
            <h5 class="text-sm fw-bold mb-3">Add Action</h5>
            ${actionsHtml}
        </div>
    `;
    if (window.lucide) lucide.createIcons();
}

function insertNode(type, actionName, index) {
    const newNode = {
        node_type: type,
        label: type === 'action' ? 'New Action' : 'Check Condition',
        action_name: actionName,
        action_config: type === 'action' ? {} : []
    };
    
    activeWorkflow.nodes.splice(index, 0, newNode);
    renderCanvas();
    openConfig(index);
}

function saveNodeConfig() {
    if (activeNodeIndex === 'trigger') {
        const switchEl = document.getElementById('workflowActiveSwitch');
        if (switchEl) activeWorkflow.is_active = switchEl.checked;
    } else if (typeof activeNodeIndex === 'number') {
        const node = activeWorkflow.nodes[activeNodeIndex];
        const labelInput = document.getElementById('nodeLabel');
        if (labelInput) node.label = labelInput.value;

        if (node.node_type === 'action' && node.action_name === 'crm.create_task') {
             node.action_config = {
                 subject: document.getElementById('taskSubject').value,
                 body: document.getElementById('taskNotes').value
             };
        } else {
            const configInput = document.getElementById('nodeActionConfig');
            if (configInput) {
                try {
                    node.action_config = JSON.parse(configInput.value);
                } catch(e) {
                    alert('Invalid JSON in configuration');
                    return;
                }
            }
        }
    }
    closeConfigPanel();
    renderCanvas();
}

function deleteActiveNode() {
    if (typeof activeNodeIndex === 'number') {
        if(confirm('Remove this node?')) {
            activeWorkflow.nodes.splice(activeNodeIndex, 1);
            closeConfigPanel();
            renderCanvas();
        }
    }
}

async function saveWorkflow() {
    if (!activeWorkflow) return;
    try {
        const btn = document.querySelector('.workflow-header .btn-primary');
        const origText = btn.innerText;
        btn.innerText = 'Saving...';
        btn.disabled = true;

        await api.put(`/workflows/definitions/${activeWorkflow.id}/`, {
            name: activeWorkflow.name,
            is_active: activeWorkflow.is_active,
            trigger_type: activeWorkflow.trigger_type,
            trigger_config: activeWorkflow.trigger_config,
            nodes: activeWorkflow.nodes
        });

        setTimeout(() => {
            btn.innerText = 'Saved!';
            setTimeout(() => {
                btn.innerText = origText;
                btn.disabled = false;
            }, 2000);
        }, 500);

        fetchWorkflows(); // update list silently
    } catch (err) {
        console.error('Save failed', err);
        alert('Failed to save workflow. ' + (err.data?.detail || ''));
        const btn = document.querySelector('.workflow-header .btn-primary');
        btn.innerText = 'Save Workflow';
        btn.disabled = false;
    }
}
