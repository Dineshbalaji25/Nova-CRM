/**
 * CRM Core API Client (Vanilla JS)
 * Handles Token Management, Retries, and Error Normalization
 */

const CONFIG = {
    API_BASE: window.CRM_API_BASE || 'http://localhost:8000/api/v1',
    LOGIN_URL: '/login',
};

class APIClient {
    constructor() {
        this.updateConfig();
        this._refreshPromise = null;
    }

    updateConfig() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.tenantId = localStorage.getItem('tenant_id');
    }

    getHeaders(body) {
        this.updateConfig(); // Ensure we have latest tokens
        const headers = {};

        // If body is NOT FormData, set to application/json
        if (!(body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        if (this.accessToken) headers['Authorization'] = `Bearer ${this.accessToken}`;
        if (this.tenantId) headers['X-Tenant-ID'] = this.tenantId;
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${CONFIG.API_BASE}${endpoint}`;

        // Proactive Refresh: If token is likely expired, refresh BEFORE making the request
        // This avoids the 'Unauthorized' log noise on the server
        if (this.accessToken && this.isTokenExpired(this.accessToken)) {
            console.log('Token proactively determined to be expired. Refreshing...');
            await this.refreshTokens();
        }

        const headers = { ...this.getHeaders(options.body), ...options.headers };

        const config = {
            ...options,
            headers: headers,
        };

        try {
            let response = await fetch(url, config);

            // Access Token Expired? Try Refresh
            if (response.status === 401 && !options._retry) {
                const refreshed = await this.refreshTokens();
                if (refreshed) {
                    // Retry original request with new token
                    config.headers = { ...this.getHeaders(options.body), ...options.headers };
                    config._retry = true;
                    response = await fetch(url, config);
                } else {
                    this.logout();
                    return;
                }
            }

            // Parse JSON
            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                data = await response.json();
            } else {
                data = await response.text();
                try { data = JSON.parse(data); } catch (e) { }
            }

            if (!response.ok) {
                const error = new Error('API Error');
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;

        } catch (error) {
            console.error('API Request Failed:', error);
            throw error;
        }
    }

    async refreshTokens() {
        if (this._refreshPromise) return this._refreshPromise;

        this._refreshPromise = (async () => {
            if (!this.refreshToken) {
                console.warn('No refresh token available');
                return false;
            }

            try {
                console.log('Attempting token refresh...');
                const response = await fetch(`${CONFIG.API_BASE}/auth/token/refresh/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh: this.refreshToken })
                });

                if (response.ok) {
                    const data = await response.json();
                    this.accessToken = data.access;
                    localStorage.setItem('access_token', data.access);
                    console.log('Token refreshed successfully');
                    return true;
                } else {
                    console.error('Refresh token invalid or expired');
                    return false;
                }
            } catch (e) {
                console.error('Token Refresh Network Error', e);
                return false;
            } finally {
                this._refreshPromise = null;
            }
        })();

        return this._refreshPromise;
    }

    async login(email, password) {
        const data = await this.request('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        // Save to local storage
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        if (data.tenant_id) localStorage.setItem('tenant_id', data.tenant_id);
        if (data.user) {
            localStorage.setItem('user_full_name', data.user.full_name || data.user.email);
            if (data.user.id) localStorage.setItem('user_id', data.user.id);
        }
        if (data.organization_name) localStorage.setItem('organization_name', data.organization_name);

        this.updateConfig();
        return data;
    }

    logout() {
        localStorage.clear();
        window.location.href = CONFIG.LOGIN_URL;
    }

    // --- Shortcuts ---
    get(url) { return this.request(url, { method: 'GET' }); }

    post(url, body) {
        const isFormData = body instanceof FormData;
        return this.request(url, {
            method: 'POST',
            body: isFormData ? body : JSON.stringify(body)
        });
    }

    patch(url, body) {
        const isFormData = body instanceof FormData;
        return this.request(url, {
            method: 'PATCH',
            body: isFormData ? body : JSON.stringify(body)
        });
    }

    put(url, body) {
        const isFormData = body instanceof FormData;
        return this.request(url, {
            method: 'PUT',
            body: isFormData ? body : JSON.stringify(body)
        });
    }

    delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    // --- Utilities ---
    isTokenExpired(token) {
        try {
            if (!token) return true;
            const base64Url = token.split('.')[1];
            if (!base64Url) return true;
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            
            const payload = JSON.parse(jsonPayload);
            const now = Math.floor(Date.now() / 1000);
            // Aggressive Buffer: Refresh if token has less than 60s left
            // This ensures we never hit the server with an expired token
            return payload.exp < (now + 60);
        } catch (e) {
            console.warn('Failed to parse JWT for expiration check', e);
            return true; // Assume expired if unparseable
        }
    }
}

const api = new APIClient();
window.api = api;
window.apiClient = api; // For backward compatibility with login.html

// --- Global UI Helpers ---

// Dynamic positioning of dropdown action menu to prevent scroll clipping
window.showActionMenu = function(button, items) {
    document.querySelectorAll('.action-dropdown-menu-container').forEach(el => el.remove());

    const rect = button.getBoundingClientRect();
    const menu = document.createElement('div');
    menu.className = 'action-dropdown-menu-container fixed bg-surface border border-white/10 rounded-xl shadow-2xl py-1.5 backdrop-blur-md min-w-[140px] z-[9999] animate-fade-in flex flex-col';
    
    // Position menu based on target element's bounding rect
    menu.style.top = `${rect.bottom + window.scrollY}px`;
    menu.style.left = `${Math.min(window.innerWidth - 150, rect.right + window.scrollX - 140)}px`;

    items.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'w-full text-left px-4 py-2.5 text-xs font-semibold text-gray-300 hover:bg-white/5 hover:text-white flex items-center gap-2 transition-all';
        btn.innerHTML = `${item.icon ? `<i data-lucide="${item.icon}" class="w-3.5 h-3.5"></i>` : ''} ${item.label}`;
        btn.onclick = (e) => {
            e.stopPropagation();
            menu.remove();
            item.onClick();
        };
        menu.appendChild(btn);
    });

    document.body.appendChild(menu);
    if (window.lucide) lucide.createIcons();

    // Close listener on click outside
    const closeHandler = (e) => {
        if (!menu.contains(e.target) && !button.contains(e.target)) {
            menu.remove();
            document.removeEventListener('click', closeHandler);
        }
    };
    setTimeout(() => document.addEventListener('click', closeHandler), 0);
};

// Client-side CSV Exporter
window.exportToCSV = function(filename, headers, rows, dataExtractor) {
    const csvRows = [];
    csvRows.push(headers.join(","));
    
    rows.forEach(row => {
        const values = dataExtractor(row).map(val => {
            const cleanVal = (val === null || val === undefined) ? '' : String(val).replace(/"/g, '""');
            return `"${cleanVal}"`;
        });
        csvRows.push(values.join(","));
    });
    
    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};
