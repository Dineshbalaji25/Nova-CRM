/**
 * Analytics Dashboards Logic
 */

let dashboards = [];
let activeDashId = null;
let allReports = [];

let dashModal, widgetModal;

const listContainer = document.getElementById('dashListContainer');
const emptyState = document.getElementById('emptyState');
const detailArea = document.getElementById('detailArea');
const grid = document.getElementById('widgetGrid');

document.addEventListener('DOMContentLoaded', () => {
    dashModal = new bootstrap.Modal(document.getElementById('dashModal'));
    widgetModal = new bootstrap.Modal(document.getElementById('widgetModal'));
    
    fetchDashboards();
    fetchReportsList();
});

async function fetchDashboards() {
    try {
        const data = await api.get('/analytics/dashboards/');
        dashboards = data.results || [];
        renderList();
    } catch (err) {
        console.error('Failed to fetch dashboards:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading dashboards</div>';
    }
}

async function fetchReportsList() {
    try {
        const data = await api.get('/analytics/reports/');
        allReports = data.results || [];
    } catch (err) {
        console.error(err);
    }
}

function renderList() {
    if (dashboards.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No dashboards found.</div>';
        return;
    }

    listContainer.innerHTML = dashboards.map(d => `
        <div class="dash-item ${activeDashId === d.id ? 'active' : ''}" onclick="selectDashboard('${d.id}')">
            <div class="dash-item-icon" style="width:36px; height:36px; border-radius:10px; background:var(--gray-50); display:flex; align-items:center; justify-content:center; color:var(--gray-400); transition: all 0.2s;">
                <i data-lucide="layout-dashboard" size="18"></i>
            </div>
            <div class="font-bold text-sm text-truncate">${d.name}</div>
            ${activeDashId === d.id ? '<i data-lucide="chevron-right" size="14" class="ms-auto"></i>' : ''}
        </div>
    `).join('');
    
    if (window.lucide) lucide.createIcons();
}

function openCreateDashboard() {
    document.getElementById('dashForm').reset();
    dashModal.show();
}

async function createDashboard() {
    const name = document.getElementById('newDashName').value;
    if (!name) return alert('Name required');

    try {
        const d = await api.post('/analytics/dashboards/', { name });
        dashModal.hide();
        await fetchDashboards();
        selectDashboard(d.id);
    } catch (err) {
        alert('Failed to create dashboard');
    }
}

async function deleteDashboard() {
    if (!activeDashId) return;
    if (!confirm('Delete dashboard?')) return;

    try {
        await api.delete(`/analytics/dashboards/${activeDashId}/`);
        activeDashId = null;
        emptyState.style.display = 'flex';
        detailArea.style.display = 'none';
        fetchDashboards();
    } catch (e) {
        alert('Failed to delete');
    }
}

async function selectDashboard(id) {
    activeDashId = id;
    const d = dashboards.find(x => x.id === id);
    
    emptyState.style.display = 'none';
    detailArea.style.display = 'flex';
    document.getElementById('detailName').innerText = d ? d.name : 'Dashboard';

    renderList();
    refreshDashboard();
}

async function refreshDashboard() {
    if (!activeDashId) return;

    grid.innerHTML = '<div class="col-span-12 text-center text-muted p-5">Loading widgets...</div>';

    try {
        const res = await api.get(`/analytics/dashboards/${activeDashId}/data/`);
        const components = res.components || [];
        renderWidgets(components);
    } catch (err) {
        console.error(err);
        grid.innerHTML = '<div class="col-span-12 text-center text-danger p-5">Failed to load widgets</div>';
    }
}

function renderWidgets(components) {
    if (components.length === 0) {
        grid.innerHTML = '<div class="col-span-12 text-center text-muted p-10 bg-white border rounded-xl">No widgets found. Add one to get started.</div>';
        return;
    }

    grid.innerHTML = '';

    components.forEach(c => {
        const widthClass = `col-span-${c.grid_width || 6}`; 

        let bodyHtml = '';

        if (c.error) {
            bodyHtml = `<div class="text-danger text-sm p-4 bg-red-50 rounded-lg border border-red-100">${c.error}</div>`;
        } else if (c.chart_type === 'metric') {
            let val = 0;
            if (c.data && c.data.length > 0) {
                const row = c.data[0];
                const keys = Object.keys(row);
                val = row[keys[keys.length - 1]];
            }
            bodyHtml = `<div class="widget-metric">${typeof val === 'number' ? val.toLocaleString() : val}</div>`;
        } else if (c.chart_type === 'table') {
            if (!c.data || c.data.length === 0) {
                bodyHtml = '<div class="text-muted">No data available</div>';
            } else {
                const keys = Object.keys(c.data[0]);
                const rows = c.data.slice(0, 8).map(row => `<tr>${keys.map(k => `<td class="text-xs p-2 border-bottom">${row[k]}</td>`).join('')}</tr>`).join('');
                bodyHtml = `<table class="w-100"><thead><tr>${keys.map(k => `<th class="text-xs p-2 border-bottom text-muted uppercase font-bold tracking-tighter">${k}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
            }
        } else {
            bodyHtml = `<div class="chart-container" style="position: relative; height:300px; width:100%"><canvas id="chart-${c.id}"></canvas></div>`;
        }

        const html = `
            <div class="widget-card ${widthClass} animate-slide-up">
                <div class="widget-header">
                    <h5 class="widget-title m-0">${c.name}</h5>
                    <div class="d-flex gap-2">
                        <button class="btn-icon btn-sm" onclick="refreshDashboard()"><i data-lucide="rotate-cw" size="14"></i></button>
                        <button class="btn-icon btn-sm text-danger" onclick="deleteWidget('${c.id}')"><i data-lucide="trash-2" size="14"></i></button>
                    </div>
                </div>
                <div class="widget-body">
                    ${bodyHtml}
                </div>
            </div>
        `;
        grid.insertAdjacentHTML('beforeend', html);
    });

    if (window.lucide) lucide.createIcons();

    // Render Charts
    components.forEach(c => {
        if (!c.error && ['bar', 'line', 'pie'].includes(c.chart_type)) {
            renderChartJS(c);
        }
    });
}

function renderChartJS(c) {
    const canvas = document.getElementById(`chart-${c.id}`);
    if (!canvas) return;

    const data = c.data || [];
    if (data.length === 0) return;

    // very naive parsing: first key is label, second key is data
    const keys = Object.keys(data[0]);
    const labelKey = keys[0];
    const dataKey = keys[1] || keys[0];

    const labels = data.map(r => r[labelKey]);
    const dataset = data.map(r => r[dataKey]);

    new Chart(canvas, {
        type: c.chart_type,
        data: {
            labels: labels,
            datasets: [{
                label: dataKey,
                data: dataset,
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Add Widget logic
function openAddWidget() {
    if (!activeDashId) return;
    
    document.getElementById('widgetForm').reset();
    
    const select = document.getElementById('wReport');
    select.innerHTML = allReports.map(r => `<option value="${r.id}">${r.name}</option>`).join('');
    
    if(allReports.length === 0) {
        select.innerHTML = '<option value="">Create a report first</option>';
    }

    widgetModal.show();
}

async function saveWidget() {
    const name = document.getElementById('wName').value;
    const report = document.getElementById('wReport').value;
    const chart_type = document.getElementById('wType').value;
    const grid_width = document.getElementById('wWidth').value || 6;

    if (!name || !report) return alert('Name and Report required');

    try {
        await api.post('/analytics/dashboard-components/', {
            dashboard: activeDashId,
            report: report,
            name: name,
            chart_type: chart_type,
            grid_width: parseInt(grid_width)
        });
        widgetModal.hide();
        refreshDashboard();
    } catch (e) {
        alert('Failed to add widget');
    }
}

async function deleteWidget(id) {
    if(!confirm('Delete widget?')) return;
    try {
        await api.delete(`/analytics/dashboard-components/${id}/`);
        refreshDashboard();
    } catch (e) {
        alert('Failed to delete widget');
    }
}
