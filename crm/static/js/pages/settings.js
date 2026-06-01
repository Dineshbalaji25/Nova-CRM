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
const settingOrgNameEl = document.getElementById('settingOrgName');
if (settingOrgNameEl) {
    settingOrgNameEl.value = localStorage.getItem('organization_name') || '';
}
fetchAPIKeys();
let availableOAuthScopes = [];
fetchOAuthScopes();
fetchOAuthApps();

async function fetchOAuthApps() {
    const container = document.getElementById('oauthAppContainer');
    if (!container) return;

    try {
        const data = await api.get('/oauth-apps/');
        const apps = data.results || [];

        if (apps.length === 0) {
            container.innerHTML = '<div class="text-muted text-sm" style="padding: 12px; border: 1px dashed var(--white-10); border-radius: 8px; text-align: center;">No OAuth applications registered.</div>';
            return;
        }

        container.innerHTML = apps.map(a => `
            <div class="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
                <div class="flex justify-between items-start">
                    <div>
                        <h6 class="text-white font-bold text-sm">${a.name}</h6>
                        <p class="text-gray-500 text-[10px]">ID: ${a.client_id}</p>
                    </div>
                    <button class="text-danger hover:bg-danger/10 p-1.5 rounded" onclick="deleteOAuthApp('${a.id}')"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
                </div>
                <div class="bg-black/20 p-2 rounded border border-white/5">
                    <label class="text-[9px] uppercase text-gray-500 font-bold block mb-1">Redirect URI</label>
                    <p class="font-mono text-[11px] text-gray-300 break-all">${a.redirect_uri || 'Not set'}</p>
                </div>
                <div class="grid grid-cols-1 gap-2">
                    <div class="bg-black/20 p-2 rounded border border-white/5">
                        <label class="text-[9px] uppercase text-gray-500 font-bold block mb-1">Client Secret</label>
                        <div class="flex items-center justify-between gap-2">
                            <span class="font-mono text-[11px] text-primary truncate">${a.client_secret}</span>
                            <button class="text-gray-400 hover:text-white" onclick="copyKey('${a.client_secret}')"><i data-lucide="copy" class="w-3 h-3"></i></button>
                        </div>
                    </div>
                    <div class="bg-black/20 p-2 rounded border border-white/5">
                        <label class="text-[9px] uppercase text-gray-500 font-bold block mb-1">Allowed Scopes</label>
                        <p class="text-[11px] text-primary break-words">${(a.allowed_scopes || []).join(', ') || 'NovaCRM.modules.ALL'}</p>
                    </div>
                </div>
            </div>
        `).join('');
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error('Failed to fetch OAuth apps:', err);
    }
}

async function fetchOAuthScopes() {
    const scopeContainer = document.getElementById('oauthScopeOptions');
    if (!scopeContainer) return;

    try {
        const data = await api.get('/oauth/scopes/');
        availableOAuthScopes = data.scopes || [];
    } catch (err) {
        console.error('Failed to fetch OAuth scopes:', err);
        availableOAuthScopes = ['NovaCRM.modules.ALL'];
    }

    if (availableOAuthScopes.length === 0) {
        availableOAuthScopes = ['NovaCRM.modules.ALL'];
    }

    scopeContainer.innerHTML = availableOAuthScopes.map(scope => `
        <label class="flex items-center gap-2 text-xs text-gray-300">
            <input type="checkbox" value="${scope}" class="oauth-scope-checkbox accent-primary" ${scope === 'NovaCRM.modules.ALL' ? 'checked' : ''}/>
            <span class="font-mono">${scope}</span>
        </label>
    `).join('');
}

async function createOAuthApp() {
    const nameInput = document.getElementById('oauthAppName');
    const redirectInput = document.getElementById('oauthRedirectUri');
    const selectedScopes = Array.from(document.querySelectorAll('.oauth-scope-checkbox:checked')).map(cb => cb.value);
    const name = (nameInput?.value || '').trim();
    const redirect_uri = (redirectInput?.value || '').trim();

    if (!name) {
        alert('Application name is required');
        return;
    }
    if (selectedScopes.length === 0) {
        alert('Select at least one scope');
        return;
    }

    try {
        await api.post('/oauth-apps/', { name, redirect_uri, allowed_scopes: selectedScopes });
        nameInput.value = '';
        redirectInput.value = '';
        document.querySelectorAll('.oauth-scope-checkbox').forEach(cb => {
            cb.checked = cb.value === 'NovaCRM.modules.ALL';
        });
        fetchOAuthApps();
    } catch (err) {
        const message = err?.data?.allowed_scopes?.[0] || err?.data?.detail || 'Failed to register application';
        alert(message);
    }
}

async function deleteOAuthApp(id) {
    if (!confirm('Are you sure? This will immediately invalidate all Client Secrets and Tokens for this app.')) return;
    try {
        await api.delete(`/oauth-apps/${id}/`);
        fetchOAuthApps();
    } catch (err) {
        alert('Failed to delete app');
    }
}

function openOAuthModal() {
    const modal = new bootstrap.Modal(document.getElementById('oauthAppModal'));
    modal.show();
}
