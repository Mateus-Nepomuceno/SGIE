const API_BASE_URL = (function() {
    if (typeof window !== 'undefined') {
        if (window.SGIE_CONFIG && window.SGIE_CONFIG.API_BASE_URL) {
            return String(window.SGIE_CONFIG.API_BASE_URL).replace(/\/+$/, '');
        }
        if (window.SGIE_API_URL) {
            return String(window.SGIE_API_URL).replace(/\/+$/, '');
        }
        const customUrl = localStorage.getItem('sgie_api_base_url');
        if (customUrl) {
            return String(customUrl).replace(/\/+$/, '');
        }
    }
    return 'http://127.0.0.1:8000/api/sgie/v1';
})();

const ACCESS_TOKEN_KEY = 'sgie_access_token';
const REFRESH_TOKEN_KEY = 'sgie_refresh_token';
const USER_KEY = 'sgie_user';

function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function getUser() {
    try {
        const u = localStorage.getItem(USER_KEY);
        return u ? JSON.parse(u) : null;
    } catch {
        return null;
    }
}

function setAuth(data) {
    if (data.access) localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
    if (data.refresh) localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh);
    if (data.usuario) localStorage.setItem(USER_KEY, JSON.stringify(data.usuario));
}

function clearAuth() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function isAuthenticated() {
    return Boolean(getAccessToken());
}

async function refreshToken() {
    const refresh = getRefreshToken();
    if (!refresh) {
        clearAuth();
        return null;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh }),
        });

        if (response.ok) {
            const data = await response.json();
            if (data.access) {
                localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
                if (data.refresh) {
                    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh);
                }
                return data.access;
            }
        }
    } catch (err) {
        console.error('Falha ao renovar token JWT:', err);
    }

    clearAuth();
    return null;
}

async function apiFetch(path, options = {}) {
    const url = path.startsWith('http') ? path : `${API_BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
    const opts = { ...options };
    opts.headers = { ...options.headers };

    let token = getAccessToken();
    if (token) {
        opts.headers['Authorization'] = `Bearer ${token}`;
    }

    if (opts.body && !(opts.body instanceof FormData) && !opts.headers['Content-Type']) {
        opts.headers['Content-Type'] = 'application/json';
    }

    let response = await fetch(url, opts);

    if (response.status === 401 && getRefreshToken() && !options._retry) {
        const newToken = await refreshToken();
        if (newToken) {
            opts._retry = true;
            opts.headers['Authorization'] = `Bearer ${newToken}`;
            response = await fetch(url, opts);
        } else {
            clearAuth();
            if (window.location.pathname.indexOf('login.html') === -1) {
                window.location.href = 'login.html';
            }
        }
    }

    return response;
}

function showAlert(containerId, message, type = 'danger') {
    const container = document.getElementById(containerId);
    if (!container) return;

    let text = message;
    if (typeof message === 'object' && message !== null) {
        text = Object.entries(message)
            .map(([field, errs]) => {
                const arr = Array.isArray(errs) ? errs : [errs];
                return `<strong>${field}:</strong> ${arr.join(' ')}`;
            })
            .join('<br>');
    }

    container.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            ${text}
        </div>
    `;
    container.style.display = 'block';
}

function clearAlert(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

function mascaraCPF(valor) {
    let v = String(valor || '').replace(/\D/g, '').slice(0, 11);
    if (v.length > 9) {
        return `${v.slice(0, 3)}.${v.slice(3, 6)}.${v.slice(6, 9)}-${v.slice(9)}`;
    } else if (v.length > 6) {
        return `${v.slice(0, 3)}.${v.slice(3, 6)}.${v.slice(6)}`;
    } else if (v.length > 3) {
        return `${v.slice(0, 3)}.${v.slice(3)}`;
    }
    return v;
}

function mascaraTelefone(valor) {
    let v = String(valor || '').replace(/\D/g, '').slice(0, 11);
    if (v.length > 10) {
        return `(${v.slice(0, 2)}) ${v.slice(2, 7)}-${v.slice(7)}`;
    } else if (v.length > 6) {
        return `(${v.slice(0, 2)}) ${v.slice(2, 6)}-${v.slice(6)}`;
    } else if (v.length > 2) {
        return `(${v.slice(0, 2)}) ${v.slice(2)}`;
    }
    return v;
}
