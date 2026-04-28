/**
 * Tasks Page Logic
 */

let allTasks = [];

async function fetchTasks() {
    try {
        const response = await api.get('/crm/activities/?activity_type=task');
        allTasks = response.results || [];
        renderTasks();
    } catch (err) {
        console.error('Failed to fetch tasks:', err);
    }
}

function renderTasks() {
    const list = document.getElementById('tasksList');
    if (!list) return;

    if (allTasks.length === 0) {
        list.innerHTML = '<div style="padding: 20px;" class="text-muted">No tasks found.</div>';
        return;
    }

    list.innerHTML = allTasks.map(task => `
        <div class="task-item" onclick="selectTask('${task.id}')" id="task-${task.id}">
            <div class="task-checkbox ${task.is_completed ? 'checked' : ''}" onclick="toggleTask('${task.id}', event)"></div>
            <div class="task-content">
                <div class="font-bold text-sm ${task.is_completed ? 'text-muted' : ''}" style="${task.is_completed ? 'text-decoration: line-through;' : ''}">${task.subject}</div>
                <div class="task-meta">
                    <span>${task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function selectTask(id) {
    const task = allTasks.find(t => t.id === id);
    if (!task) return;

    // UI highlight
    document.querySelectorAll('.task-item').forEach(el => el.classList.remove('selected'));
    const item = document.getElementById('task-' + id);
    if (item) item.classList.add('selected');

    const pane = document.getElementById('taskDetailsPane');
    if (pane) {
        pane.innerHTML = `
            <div style="border-bottom: 1px solid var(--gray-100); padding-bottom: 16px; margin-bottom: 16px;">
                <div class="text-xs text-muted mb-4">TASK-${id.substring(0, 8).toUpperCase()}</div>
                <h3 class="text-lg font-bold mb-4">${task.subject}</h3>
                <div style="display: flex; gap: 24px; margin-bottom: 16px;">
                    <div class="flex-column">
                        <span class="text-xs text-muted">Status</span>
                        <span class="text-sm font-bold" style="margin-top: 4px;">${task.is_completed ? 'Completed' : 'Pending'}</span>
                    </div>
                    <div class="flex-column">
                        <span class="text-xs text-muted">Due Date</span>
                        <span class="text-sm font-bold" style="margin-top: 4px;">${task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}</span>
                    </div>
                </div>
            </div>
            <div class="text-sm text-muted" style="line-height: 1.6;">
                ${task.body || 'No description provided.'}
            </div>
        `;
    }
}

async function toggleTask(id, event) {
    if (event) event.stopPropagation();
    const task = allTasks.find(t => t.id === id);
    try {
        await api.patch('/crm/activities/' + id + '/', { is_completed: !task.is_completed });
        fetchTasks();
    } catch (err) {
        alert('Failed to update task');
    }
}

function openAddTaskModal() {
    const modal = document.getElementById('addTaskModal');
    if (modal) modal.style.display = 'flex';
}

function closeAddTaskModal() {
    const modal = document.getElementById('addTaskModal');
    if (modal) modal.style.display = 'none';
}

document.getElementById('addTaskForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());

    try {
        await api.post('/crm/activities/', payload);
        closeAddTaskModal();
        fetchTasks();
    } catch (err) {
        alert('Error creating task');
    }
});

// Run Init
fetchTasks();
