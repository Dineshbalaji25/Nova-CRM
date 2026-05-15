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
            if (board) board.innerHTML = '<div class="p-10 text-gray-500 font-medium">No pipeline found. Please run setup script.</div>';
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
            <div class="flex items-center justify-between mb-2 px-1">
                <div class="flex items-center gap-2">
                    <span class="text-sm font-bold text-white">${stage.name}</span>
                    <span class="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-bold text-gray-500">${stageDeals.length}</span>
                </div>
                <span class="text-[10px] font-bold text-gray-600 tracking-wider">$${totalValue.toLocaleString()}</span>
            </div>
            <div class="h-1 w-full rounded-full mb-4" style="background: ${getStageColor(stage.position)}20">
                <div class="h-full rounded-full" style="width: 100%; background: ${getStageColor(stage.position)}"></div>
            </div>
            <div class="flex-1 flex flex-col gap-3 min-h-[200px]" id="stage-${stage.id}" data-stage-id="${stage.id}">
                ${stageDeals.map(deal => `
                    <div class="kanban-card group" id="deal-${deal.id}" draggable="true" ondragstart="handleDragStart(event)" data-deal-id="${deal.id}">
                        <div class="flex justify-between items-start mb-2">
                            <span class="text-[10px] font-bold text-gray-500 uppercase tracking-widest">${deal.company_name || 'Individual'}</span>
                            <button class="text-gray-700 hover:text-white transition-colors opacity-0 group-hover:opacity-100">
                                <i data-lucide="more-horizontal" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                        <p class="text-sm font-bold text-white mb-3 group-hover:text-primary transition-colors">${deal.title}</p>
                        <div class="flex justify-between items-center">
                            <span class="text-xs font-black text-white">$${parseFloat(deal.amount).toLocaleString()}</span>
                            <div class="w-6 h-6 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">
                                ${(deal.owner_name || 'U').substring(0, 1)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Add drag over and drop listeners to the column
        const cardsContainer = column.querySelector(`[data-stage-id="${stage.id}"]`);
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
    setTimeout(() => e.target.classList.add('opacity-40'), 0);
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    e.currentTarget.classList.add('bg-white/[0.02]', 'rounded-xl');
    return false;
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('bg-white/[0.02]', 'rounded-xl');
}

async function handleDrop(e) {
    e.stopPropagation();
    e.currentTarget.classList.remove('bg-white/[0.02]', 'rounded-xl');

    const stageId = e.currentTarget.getAttribute('data-stage-id');
    if (!draggedDealId || !stageId) return;

    const draggedEl = document.getElementById(`deal-${draggedDealId}`);
    if (draggedEl) {
        draggedEl.classList.remove('opacity-40');
        e.currentTarget.appendChild(draggedEl);
    }

    try {
        await api.patch(`/crm/deals/${draggedDealId}/`, { stage: stageId });
        initPipeline();
    } catch (err) {
        console.error('Failed to move deal', err);
        initPipeline();
    }

    draggedDealId = null;
    return false;
}

function getStageColor(pos) {
    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444'];
    return colors[pos % colors.length];
}

function openAddDealModal() {
    const modal = document.getElementById('addDealModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeAddDealModal() {
    const modal = document.getElementById('addDealModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
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
