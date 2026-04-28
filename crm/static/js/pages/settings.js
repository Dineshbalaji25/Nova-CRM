/**
 * Settings Page Logic
 */

async function fetchAPIKeys() {
    const container = document.getElementById('apiKeyContainer');
    if (!container) return;

    try {
        const data = await api.get('/api-keys/');
        const keys = data.results || [];

        if (keys.length === 0) {
            container.innerHTML = '<div class="text-muted text-sm" style="padding: 12px; border: 1px dashed var(--gray-300); border-radius: 8px; text-align: center;">No API keys generated yet.</div>';
            return;
        }

        container.innerHTML = keys.map(k => `
            <div class="api-key-box" style="display: flex; justify-content: space-between; align-items: center; background: var(--gray-50); padding: 12px; border-radius: 8px; border: 1px solid var(--gray-200); margin-bottom: 12px;">
                <div style="display: flex; flex-direction: column;">
                    <span class="font-bold text-sm">${k.name}</span>
                    <span class="font-mono text-xs" style="margin-top: 4px; color: var(--primary-600);">${k.key}</span>
                    <span class="text-xs text-muted" style="margin-top: 4px;">Created: ${new Date(k.created_at).toLocaleDateString()}</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary text-xs" onclick="deleteKey('${k.id}')"><i data-lucide="trash-2" size="12"></i> Delete</button>
                    <button class="btn btn-secondary text-xs" onclick="copyKey('${k.key}')"><i data-lucide="copy" size="12"></i> Copy</button>
                </div>
            </div>
        `).join('');
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Failed to fetch keys:', err);
    }
}

async function createKey() {
    const name = prompt("Key Name (e.g. My Website):", "New API Key");
    if (!name) return;

    try {
        await api.post('/api-keys/', { name });
        fetchAPIKeys();
    } catch (err) {
        alert('Failed to create key');
    }
}

async function deleteKey(id) {
    if (!confirm('Are you sure you want to delete this key? This will break any application using it.')) return;
    try {
        await api.delete(`/api-keys/${id}/`);
        fetchAPIKeys();
    } catch (err) {
        alert('Failed to delete key');
    }
}

function copyKey(key) {
    navigator.clipboard.writeText(key).then(() => {
        alert('Key copied to clipboard');
    });
}

// Run Init
document.getElementById('settingOrgName').value = localStorage.getItem('organization_name') || '';
fetchAPIKeys();
