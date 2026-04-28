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
        if (!this.refreshToken) return false;
        try {
            const response = await fetch(`${CONFIG.API_BASE}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                this.accessToken = data.access;
                localStorage.setItem('access_token', data.access);
                return true;
            }
        } catch (e) {
            console.error('Token Refresh Failed', e);
        }
        return false;
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
        if (data.user) localStorage.setItem('user_full_name', data.user.full_name || data.user.email);
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

    delete(url) { return this.request(url, { method: 'DELETE' }); }
}

const api = new APIClient();
window.api = api;
window.apiClient = api; // For backward compatibility with login.html
