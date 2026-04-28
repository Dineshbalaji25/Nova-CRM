/**
 * Deals Page Logic (Kanban)
 */

let currentPipeline = null;
let stagesMap = {};

async function initPipeline() {
    try {
        // 1. Fetch Pipelines
        const pipelines = await api.get('/crm/pipelines/');
        if (pipelines.results && pipelines.results.length > 0) {
            currentPipeline = pipelines.results[0];
            const pInput = document.getElementById('pipelineId');
            if (pInput) pInput.value = currentPipeline.id;
        } else {
            const board = document.getElementById('kanbanBoard');
            if (board) board.innerHTML = '<div style="padding:40px;">No pipeline found. Please run setup script.</div>';
            return;
        }

        // 2. Fetch Deals
        const dealsResponse = await api.get('/crm/deals/');
        const deals = dealsResponse.results || [];

        // 3. Render Kanban
        renderBoard(currentPipeline.stages, deals);

        // 4. Fill Modal Selects
        const stageSelect = document.getElementById('stageSelect');
        if (stageSelect) {
            stageSelect.innerHTML = currentPipeline.stages.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        }

        const companies = await api.get('/crm/companies/');
        const companySelect = document.getElementById('companySelect');
        if (companySelect) {
            companySelect.innerHTML = '<option value="">None</option>' + (companies.results || []).map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }

    } catch (err) {
        console.error('Failed to init pipeline:', err);
    }
}

function renderBoard(stages, deals) {
    const board = document.getElementById('kanbanBoard');
    if (!board) return;
    board.innerHTML = '';

    stages.sort((a, b) => a.position - b.position).forEach(stage => {
        const stageDeals = deals.filter(d => d.stage === stage.id);
        const totalValue = stageDeals.reduce((sum, d) => sum + parseFloat(d.amount || 0), 0);

        const column = document.createElement('div');
        column.className = 'kanban-column';
        column.innerHTML = `
            <div class="kanban-header">
                <span>${stage.name} <span class="badge" style="background:white; margin-left:8px; color:#1e293b;">${stageDeals.length}</span></span>
                <span class="text-secondary">$${totalValue.toLocaleString()}</span>
            </div>
            <div class="stage-indicator" style="background: ${getStageColor(stage.position)}"></div>
            <div class="kanban-cards" id="stage-${stage.id}" data-stage-id="${stage.id}">
                ${stageDeals.map(deal => `
                    <div class="kanban-card glass-card hover-lift" id="deal-${deal.id}" draggable="true" ondragstart="handleDragStart(event)" data-deal-id="${deal.id}" style="padding: 16px; margin-bottom: 12px; border-left: 4px solid var(--accent-500);">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="text-xs font-bold text-muted uppercase tracking-wider">${deal.company_name || 'Individual'}</span>
                            <i data-lucide="external-link" size="12" class="text-muted cursor-pointer"></i>
                        </div>
                        <div class="font-bold text-gray-900 mb-3" style="font-size: 0.9375rem; line-height: 1.4;">${deal.title}</div>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <div class="text-accent font-bold" style="font-size: 0.875rem;">$${parseFloat(deal.amount).toLocaleString()}</div>
                            <div class="d-flex -space-x-2">
                                <div style="width: 24px; height: 24px; background: var(--primary-100); color: var(--primary-600); border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 800;">YO</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Add drag over and drop listeners to the column
        const cardsContainer = column.querySelector('.kanban-cards');
        cardsContainer.addEventListener('dragover', handleDragOver);
        cardsContainer.addEventListener('dragleave', handleDragLeave);
        cardsContainer.addEventListener('drop', handleDrop);

        board.appendChild(column);
    });
    if (window.lucide) lucide.createIcons();
}

// Drag and Drop Logic
let draggedDealId = null;

function handleDragStart(e) {
    draggedDealId = e.target.getAttribute('data-deal-id');
    e.dataTransfer.effectAllowed = 'move';
    // Slightly fade the element while dragging
    setTimeout(() => e.target.style.opacity = '0.5', 0);
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault(); // Necessary. Allows us to drop.
    }
    e.dataTransfer.dropEffect = 'move';
    const targetStage = e.currentTarget;
    targetStage.style.background = 'rgba(0,0,0,0.02)';
    targetStage.style.borderRadius = '8px';
    return false;
}

function handleDragLeave(e) {
    e.currentTarget.style.background = 'transparent';
}

async function handleDrop(e) {
    e.stopPropagation(); // Stops some browsers from redirecting.
    e.currentTarget.style.background = 'transparent';

    const stageId = e.currentTarget.getAttribute('data-stage-id');
    if (!draggedDealId || !stageId) return;

    // Instantly move the DOM node for snappy feedback
    const draggedEl = document.getElementById(`deal-${draggedDealId}`);
    if (draggedEl) {
        draggedEl.style.opacity = '1';
        e.currentTarget.appendChild(draggedEl);
    }

    try {
        await api.patch(`/crm/deals/${draggedDealId}/`, { stage: stageId });
        // Re-init the board entirely to update column totals
        initPipeline();
    } catch (err) {
        console.error('Failed to move deal', err);
        alert('Failed to update deal stage');
        initPipeline(); // Revert on failure
    }

    draggedDealId = null;
    return false;
}

function getStageColor(pos) {
    const colors = ['#64748b', '#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444'];
    return colors[pos % colors.length];
}

function openAddDealModal() {
    const modal = document.getElementById('addDealModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddDealModal() {
    const modal = document.getElementById('addDealModal');
    if (modal) modal.style.display = 'none';
}

document.getElementById('addDealForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        await api.post('/crm/deals/', payload);
        closeAddDealModal();
        initPipeline();
    } catch (err) {
        alert('Error creating deal: ' + (err.data?.detail || err.message));
    }
});

// Run Init
initPipeline();
