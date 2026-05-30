/**
 * Tasks Page Logic
 */

let allTasks = [];
let showCompleted = false;
let editingTaskId = null;

async function fetchTasks() {
    try {
        const response = await api.get(`/crm/activities/?activity_type=task&is_completed=${showCompleted}`);
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
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px;"><div class="text-gray-500">No ${showCompleted ? 'completed' : 'pending'} tasks found.</div></td></tr>`;
        return;
    }

    tbody.innerHTML = allTasks.map(task => `
        <tr>
            <td><input type="checkbox" class="w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary/50" ${task.is_completed ? 'checked' : ''} onclick="toggleTask('${task.id}', event)"></td>
            <td>
                <div class="font-bold text-white ${task.is_completed ? 'text-gray-500 line-through' : ''}">${task.subject}</div>
                <div class="text-xs text-gray-500 truncate" style="max-width: 300px;">${task.body || 'No description'}</div>
            </td>
            <td>
                <span class="badge ${task.is_completed ? 'badge-success' : 'badge-warning'}" style="background: ${task.is_completed ? 'var(--success-bg)' : 'var(--warning-bg)'}; color: ${task.is_completed ? 'var(--success)' : 'var(--warning)'}; border: 1px solid currentColor;">
                    ${task.is_completed ? 'Completed' : 'Pending'}
                </span>
            </td>
            <td class="text-sm text-gray-300">${task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}</td>
            <td>
                <span class="text-xs font-bold px-2 py-1 rounded" style="background: ${getPriorityColor(task.priority || 'Normal')}; color: white;">
                    ${task.priority || 'Normal'}
                </span>
            </td>
            <td class="text-sm text-gray-300">${task.related_to_name || '-'}</td>
            <td>
                <button class="btn-icon tasks-more-btn" data-id="${task.id}">
                    <i data-lucide="more-horizontal" class="w-4 h-4 text-gray-400"></i>
                </button>
            </td>
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

// Action Menu delegate
const tbody = document.getElementById('tasksTableBody');
if (tbody) {
    tbody.addEventListener('click', (e) => {
        const btn = e.target.closest('.tasks-more-btn');
        if (!btn) return;
        
        const taskId = btn.dataset.id;
        const task = allTasks.find(t => t.id === taskId);
        if (task) {
            showActionMenu(btn, [
                { label: 'Edit Task', icon: 'edit-3', onClick: () => openEditTaskModal(task) },
                { label: 'Delete Task', icon: 'trash-2', onClick: () => deleteTask(task.id) }
            ]);
        }
    });
}

function openAddTaskModal() {
    editingTaskId = null;
    const form = document.getElementById('addTaskForm');
    if (form) form.reset();

    const titleEl = document.querySelector('#addTaskModal h3');
    const submitBtn = document.querySelector('#addTaskModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'New Task';
    if (submitBtn) submitBtn.textContent = 'Create Task';

    const modal = document.getElementById('addTaskModal');
    if (modal) modal.style.display = 'flex';
}

function openEditTaskModal(task) {
    editingTaskId = task.id;
    const form = document.getElementById('addTaskForm');
    if (form) {
        form.reset();
        form.elements['subject'].value = task.subject || '';
        form.elements['priority'].value = task.priority || 'Normal';
        if (task.due_date) {
            form.elements['due_date'].value = task.due_date.substring(0, 10);
        }
    }

    const titleEl = document.querySelector('#addTaskModal h3');
    const submitBtn = document.querySelector('#addTaskModal button[type="submit"]');
    if (titleEl) titleEl.textContent = 'Edit Task';
    if (submitBtn) submitBtn.textContent = 'Update Task';

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
    payload.activity_type = 'task'; // Must be task

    try {
        if (editingTaskId) {
            await api.patch(`/crm/activities/${editingTaskId}/`, payload);
        } else {
            await api.post('/crm/activities/', payload);
        }
        closeAddTaskModal();
        fetchTasks();
    } catch (err) {
        alert('Error saving task');
    }
});

async function toggleTask(id, event) {
    if (event) event.stopPropagation();
    const task = allTasks.find(t => t.id === id);
    if (!task) return;
    try {
        await api.patch('/crm/activities/' + id + '/', { is_completed: !task.is_completed });
        fetchTasks();
    } catch (err) {
        alert('Failed to update task');
    }
}

async function deleteTask(id) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
        await api.delete(`/crm/activities/${id}/`);
        fetchTasks();
    } catch (err) {
        alert('Failed to delete task');
    }
}

// Completed Toggling
document.getElementById('viewCompletedBtn')?.addEventListener('click', (e) => {
    e.preventDefault();
    showCompleted = !showCompleted;
    
    const btn = document.getElementById('viewCompletedBtn');
    if (showCompleted) {
        btn.innerHTML = '<i data-lucide="list-todo" class="w-4 h-4"></i> View Pending';
    } else {
        btn.innerHTML = '<i data-lucide="check-square" class="w-4 h-4"></i> View Completed';
    }
    if (window.lucide) lucide.createIcons();
    
    fetchTasks();
});

// Run Init
fetchTasks();
