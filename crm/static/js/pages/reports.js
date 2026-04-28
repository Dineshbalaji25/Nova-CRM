/**
 * Analytics Reports Logic
 */

let reports = [];
let activeReport = null;
let reportModal;

const listContainer = document.getElementById('repListContainer');
const emptyState = document.getElementById('emptyState');
const detailArea = document.getElementById('detailArea');

document.addEventListener('DOMContentLoaded', () => {
    reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
    fetchReports();
});

async function fetchReports() {
    try {
        const data = await api.get('/analytics/reports/');
        reports = data.results || [];
        renderList();
    } catch (err) {
        console.error('Failed to fetch reports:', err);
        listContainer.innerHTML = '<div class="p-4 text-center text-danger">Error loading reports</div>';
    }
}

function renderList() {
    if (reports.length === 0) {
        listContainer.innerHTML = '<div class="p-4 text-center text-muted">No reports found.</div>';
        return;
    }

    listContainer.innerHTML = reports.map(r => `
        <div class="rep-item ${activeReport?.id === r.id ? 'active' : ''}" onclick="selectReport('${r.id}')">
            <div style="width:32px; height:32px; border-radius:6px; background:var(--gray-100); display:flex; align-items:center; justify-content:center; color:var(--gray-500);">
                <i data-lucide="bar-chart-2" size="16"></i>
            </div>
            <div>
                <div class="font-bold text-sm text-truncate">${r.name}</div>
                <div class="text-xs text-muted text-truncate">${r.target_model.toUpperCase()}</div>
            </div>
        </div>
    `).join('');
    
    if (window.lucide) lucide.createIcons();
}

function openCreateReport() {
    document.getElementById('reportForm').reset();
    reportModal.show();
}

async function createReport() {
    const name = document.getElementById('newRepName').value;
    const description = document.getElementById('newRepDesc').value;

    if (!name) return alert('Name required');

    try {
        const r = await api.post('/analytics/reports/', {
            name,
            description,
            target_model: 'deal', // default
            selected_columns: [],
            filters: {},
            group_by: '',
            aggregate_functions: {}
        });
        reportModal.hide();
        await fetchReports();
        selectReport(r.id);
    } catch (err) {
        alert('Failed to create report');
    }
}

async function selectReport(id) {
    try {
        activeReport = await api.get(`/analytics/reports/${id}/`);
        
        emptyState.style.display = 'none';
        detailArea.style.display = 'flex';

        document.getElementById('detailName').innerText = activeReport.name;
        document.getElementById('detailTarget').innerText = `Module: ${activeReport.target_model.toUpperCase()}`;

        // Populate Builder
        document.getElementById('repTarget').value = activeReport.target_model;
        document.getElementById('repColumns').value = JSON.stringify(activeReport.selected_columns || []);
        document.getElementById('repGroupBy').value = activeReport.group_by || '';
        document.getElementById('repAggs').value = JSON.stringify(activeReport.aggregate_functions || {});

        // Clear Table
        document.getElementById('dataTableHeader').innerHTML = '<th>No data loaded. Click Run Report.</th>';
        document.getElementById('dataTableBody').innerHTML = '';
        document.getElementById('dataCount').innerText = '0 records';

        renderList();
    } catch (err) {
        console.error('Select failed:', err);
    }
}

async function saveReportConfig() {
    if (!activeReport) return;
    
    const target = document.getElementById('repTarget').value;
    const groupBy = document.getElementById('repGroupBy').value;
    let cols = [];
    let aggs = {};

    try {
        cols = JSON.parse(document.getElementById('repColumns').value || '[]');
        const aggsStr = document.getElementById('repAggs').value;
        if (aggsStr) aggs = JSON.parse(aggsStr);
    } catch (e) {
        return alert('Invalid JSON in Columns or Aggregates field.');
    }

    try {
        await api.put(`/analytics/reports/${activeReport.id}/`, {
            name: activeReport.name,
            description: activeReport.description,
            target_model: target,
            selected_columns: cols,
            group_by: groupBy,
            aggregate_functions: aggs,
            filters: activeReport.filters
        });
        alert('Configuration saved');
        fetchReports();
    } catch (e) {
        alert('Failed to save config');
    }
}

async function deleteReport() {
    if (!activeReport) return;
    if (!confirm('Delete this report?')) return;

    try {
        await api.delete(`/analytics/reports/${activeReport.id}/`);
        activeReport = null;
        emptyState.style.display = 'flex';
        detailArea.style.display = 'none';
        fetchReports();
    } catch (e) {
        alert('Failed to delete');
    }
}

async function runReport() {
    if (!activeReport) return;
    
    const btn = document.querySelector('.rep-header .btn-primary');
    const origText = btn.innerHTML;
    btn.innerHTML = 'Running...';
    btn.disabled = true;

    try {
        const res = await api.post(`/analytics/reports/${activeReport.id}/run/`, {});
        renderTable(res.data || []);
    } catch (e) {
        console.error(e);
        alert('Failed to run report. Check if fields are valid.');
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
}

function renderTable(data) {
    const thead = document.getElementById('dataTableHeader');
    const tbody = document.getElementById('dataTableBody');
    document.getElementById('dataCount').innerText = `${data.length} records`;

    if (data.length === 0) {
        thead.innerHTML = '<th>No results</th>';
        tbody.innerHTML = '';
        return;
    }

    const keys = Object.keys(data[0]);
    
    thead.innerHTML = keys.map(k => `<th>${k}</th>`).join('');
    
    tbody.innerHTML = data.map(row => {
        return `<tr>${keys.map(k => {
            let val = row[k];
            if (val === null || val === undefined) val = '-';
            else if (typeof val === 'object') val = JSON.stringify(val);
            return `<td>${val}</td>`;
        }).join('')}</tr>`;
    }).join('');
}
