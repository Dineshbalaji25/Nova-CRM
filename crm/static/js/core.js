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
