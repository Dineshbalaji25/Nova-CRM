/**
 * Audit Logs Logic
 */

async function fetchAuditLogs() {
    const tbody = document.getElementById('auditLogsBody');
    if (!tbody) return;

    try {
        const data = await api.get('/audit/logs/');
        const results = data.results || [];

        if (results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;"><div class="text-muted">No audit logs found.</div></td></tr>';
            return;
        }

        tbody.innerHTML = results.map(log => {
            // Determine action color
            let color = 'var(--primary-600)';
            if (log.action === 'create' || log.action === 'login') color = 'var(--success-fg)';
            if (log.action === 'delete') color = 'var(--danger-fg)';

            return `
                <tr>
                    <td class="monospace-cell" style="font-family: monospace; font-size: 12px;">${new Date(log.created_at).toLocaleString()}</td>
                    <td class="text-sm font-bold">${log.actor_email || 'System'}</td>
                    <td><span class="action-badge" style="color: ${color}; font-weight: 600; text-transform: uppercase; font-size: 10px; border: 1px solid currentColor; padding: 2px 6px; border-radius: 4px;">${log.action}</span></td>
                    <td class="monospace-cell" style="font-family: monospace; font-size: 11px; color: var(--text-muted);">${log.ip_address || '-'}</td>
                    <td class="text-sm">${log.description || (log.content_type ? `Ref: ${log.object_id}` : '-')}</td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error('Fetch audit logs failed:', err);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: var(--danger-fg);">Failed to load logs.</td></tr>';
    }
}

fetchAuditLogs();
