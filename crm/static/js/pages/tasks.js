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
    const tbody = document.getElementById('tasksTableBody');
    if (!tbody) return;

    if (allTasks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="text-muted">No tasks found.</div></td></tr>';
        return;
    }

    tbody.innerHTML = allTasks.map(task => `
        <tr>
            <td><input type="checkbox" class="form-check-input" ${task.is_completed ? 'checked' : ''} onclick="toggleTask('${task.id}', event)"></td>
            <td>
                <div class="font-bold text-gray-900 ${task.is_completed ? 'text-muted' : ''}" style="${task.is_completed ? 'text-decoration: line-through;' : ''}">${task.subject}</div>
                <div class="text-xs text-muted truncate" style="max-width: 300px;">${task.body || 'No description'}</div>
            </td>
            <td>
                <span class="badge ${task.is_completed ? 'badge-success' : 'badge-warning'}" style="background: ${task.is_completed ? 'var(--success-bg)' : 'var(--warning-bg)'}; color: ${task.is_completed ? 'var(--success)' : 'var(--warning)'};">
                    ${task.is_completed ? 'Completed' : 'Pending'}
                </span>
            </td>
            <td class="text-sm text-gray-600">${task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}</td>
            <td>
                <span class="text-xs font-bold px-2 py-1 rounded" style="background: ${getPriorityColor(task.priority)}; color: white;">
                    ${task.priority || 'Normal'}
                </span>
            </td>
            <td class="text-sm text-gray-600">${task.related_to_name || '-'}</td>
            <td><button class="btn-icon"><i data-lucide="more-horizontal" size="16"></i></button></td>
        </tr>
    `).join('');

    if (window.lucide) lucide.createIcons();
}

function getPriorityColor(p) {
    switch (p) {
        case 'High': return '#ef4444';
        case 'Normal': return '#3b82f6';
        case 'Low': return '#64748b';
        default: return '#3b82f6';
    }
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
