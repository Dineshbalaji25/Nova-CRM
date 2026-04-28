/**
 * Scoring Rules Builder Logic
 */

let rules = [];
let activeRuleId = null;

// UI Elements
const listContainer = document.getElementById('ruleListContainer');
const emptyState = document.getElementById('emptyState');
const editorArea = document.getElementById('editorArea');
const criteriaContainer = document.getElementById('criteriaContainer');

document.addEventListener('DOMContentLoaded', () => {
    fetchRules();
});

async function fetchRules() {
    try {
        const data = await api.get('/scoring-rules/');
        rules = data.results || [];
        renderList();
    } catch (err) {
        console.error('Failed to fetch rules:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading rules</div>';
    }
}

function renderList() {
    if (rules.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No rules found. Create one to get started.</div>';
        return;
    }

    listContainer.innerHTML = rules.map(r => {
        const isPositive = r.points > 0;
        const sign = isPositive ? '+' : '';
        const badgeClass = isPositive ? 'points-positive' : 'points-negative';
        
        return `
            <div class="score-item ${activeRuleId === r.id ? 'active' : ''}" onclick="selectRule('${r.id}')">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="font-bold text-sm text-truncate pe-2">${r.name}</span>
                    <span class="points-badge ${badgeClass}">${sign}${r.points}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-xs text-muted text-uppercase fw-bold">${r.target_model}</span>
                    ${r.is_active ? '<span class="badge bg-success" style="font-size: 9px;">Active</span>' : '<span class="badge bg-secondary" style="font-size: 9px;">Draft</span>'}
                </div>
            </div>
        `;
    }).join('');
}

function openCreateMode() {
    activeRuleId = 'new';
    
    emptyState.style.display = 'none';
    editorArea.style.display = 'flex';
    document.getElementById('editorTitle').innerText = 'Create New Rule';
    document.getElementById('btnDelete').style.display = 'none';

    document.getElementById('ruleName').value = '';
    document.getElementById('ruleModule').value = 'lead';
    document.getElementById('rulePoints').value = '';
    document.getElementById('ruleActive').checked = true;
    
    criteriaContainer.innerHTML = '';
    addCriteriaRow(); // Start with one empty row

    renderList(); // Update active highlight
}

async function selectRule(id) {
    try {
        const rule = await api.get(`/scoring-rules/${id}/`);
        activeRuleId = rule.id;

        emptyState.style.display = 'none';
        editorArea.style.display = 'flex';
        document.getElementById('editorTitle').innerText = 'Edit Rule';
        document.getElementById('btnDelete').style.display = 'inline-block';

        document.getElementById('ruleName').value = rule.name;
        document.getElementById('ruleModule').value = rule.target_model;
        document.getElementById('rulePoints').value = rule.points;
        document.getElementById('ruleActive').checked = rule.is_active;

        criteriaContainer.innerHTML = '';
        const conditions = rule.criteria || [];
        if (conditions.length === 0) {
            addCriteriaRow();
        } else {
            conditions.forEach(c => addCriteriaRow(c.field, c.operator, c.value));
        }

        renderList();
    } catch (err) {
        console.error('Select failed:', err);
    }
}

function addCriteriaRow(field = '', operator = 'eq', value = '') {
    const rowId = 'row_' + Math.random().toString(36).substr(2, 9);
    
    // For demo purposes, we provide a generic list of fields. 
    // In a full implementation, this could be fetched dynamically based on the target_model's custom fields.
    const fields = [
        'title', 'email', 'phone', 'company', 'industry', 'city', 'country', 'status', 'source'
    ];

    const fieldOptions = fields.map(f => `<option value="${f}" ${f === field ? 'selected' : ''}>${f.charAt(0).toUpperCase() + f.slice(1)}</option>`).join('');

    const html = `
        <div class="criteria-row" id="${rowId}">
            <select class="form-select criteria-field">
                <option value="" disabled ${!field ? 'selected' : ''}>Select Field...</option>
                ${fieldOptions}
                <option value="_custom" ${!fields.includes(field) && field ? 'selected' : ''}>Custom...</option>
            </select>
            
            ${!fields.includes(field) && field ? `<input type="text" class="form-control criteria-custom-field" value="${field}" placeholder="Field name">` : ''}

            <select class="form-select criteria-operator">
                <option value="eq" ${operator === 'eq' ? 'selected' : ''}>Equals</option>
                <option value="neq" ${operator === 'neq' ? 'selected' : ''}>Not Equals</option>
                <option value="contains" ${operator === 'contains' ? 'selected' : ''}>Contains</option>
                <option value="gt" ${operator === 'gt' ? 'selected' : ''}>Greater Than</option>
                <option value="lt" ${operator === 'lt' ? 'selected' : ''}>Less Than</option>
            </select>
            
            <input type="text" class="form-control criteria-value" placeholder="Value" value="${value}">
            
            <button class="btn-icon text-danger" onclick="document.getElementById('${rowId}').remove()">
                <i data-lucide="trash-2" size="18"></i>
            </button>
        </div>
    `;

    criteriaContainer.insertAdjacentHTML('beforeend', html);
    
    // Handle custom field select
    const newRow = document.getElementById(rowId);
    const selectEl = newRow.querySelector('.criteria-field');
    selectEl.addEventListener('change', (e) => {
        if (e.target.value === '_custom') {
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control criteria-custom-field mt-2';
            input.placeholder = 'Custom field key';
            e.target.parentNode.insertBefore(input, e.target.nextSibling);
        } else {
            const customInput = newRow.querySelector('.criteria-custom-field');
            if(customInput) customInput.remove();
        }
    });

    if (window.lucide) lucide.createIcons();
}

async function saveRule() {
    const name = document.getElementById('ruleName').value;
    const target_model = document.getElementById('ruleModule').value;
    const pointsStr = document.getElementById('rulePoints').value;
    const is_active = document.getElementById('ruleActive').checked;

    if (!name || !pointsStr) return alert('Name and Points are required.');
    
    const points = parseInt(pointsStr, 10);
    if (isNaN(points)) return alert('Points must be a number.');

    // Gather criteria
    const criteria = [];
    const rows = criteriaContainer.querySelectorAll('.criteria-row');
    
    for (let row of rows) {
        let field = row.querySelector('.criteria-field').value;
        if (field === '_custom') {
            field = row.querySelector('.criteria-custom-field')?.value;
        }
        
        const operator = row.querySelector('.criteria-operator').value;
        const value = row.querySelector('.criteria-value').value;

        if (field && value) {
            criteria.push({ field, operator, value });
        }
    }

    if (criteria.length === 0) return alert('Please add at least one valid condition.');

    const payload = {
        name,
        target_model,
        points,
        is_active,
        criteria
    };

    try {
        const btn = document.querySelector('#editorArea .btn-primary');
        const origText = btn.innerText;
        btn.innerText = 'Saving...';
        btn.disabled = true;

        if (activeRuleId === 'new') {
            const r = await api.post('/scoring-rules/', payload);
            activeRuleId = r.id;
        } else {
            await api.put(`/scoring-rules/${activeRuleId}/`, payload);
        }

        setTimeout(() => {
            btn.innerText = 'Saved!';
            setTimeout(() => {
                btn.innerText = origText;
                btn.disabled = false;
            }, 2000);
        }, 500);

        fetchRules(); // Update list silently
    } catch (err) {
        console.error('Save failed', err);
        alert('Failed to save rule. ' + (err.data?.detail || ''));
        const btn = document.querySelector('#editorArea .btn-primary');
        btn.innerText = 'Save Rule';
        btn.disabled = false;
    }
}

async function deleteRule() {
    if (activeRuleId === 'new' || !activeRuleId) return;
    if (!confirm('Are you sure you want to delete this scoring rule?')) return;

    try {
        await api.delete(`/scoring-rules/${activeRuleId}/`);
        activeRuleId = null;
        emptyState.style.display = 'flex';
        editorArea.style.display = 'none';
        fetchRules();
    } catch (err) {
        alert('Failed to delete rule.');
    }
}
