function resolverUrlApi() {
    if (typeof window !== 'undefined') {
        if (window.SGIE_API_URL) {
            return String(window.SGIE_API_URL).replace(/\/+$/, '');
        }
        const customUrl = localStorage.getItem('sgie_api_base_url');
        if (customUrl) {
            return String(customUrl).replace(/\/+$/, '');
        }

        const hostname = window.location.hostname;
        const protocol = window.location.protocol;

        // GitHub Codespaces / Dev Containers na web
        if (hostname && (hostname.endsWith('.app.github.dev') || hostname.endsWith('.github.dev'))) {
            const apiHost = hostname.replace(/-\d+(\.app\.github\.dev|\.github\.dev)$/, '-8000$1');
            return `${protocol}//${apiHost}/api/sgie/v1`;
        }

        // Ambiente local (localhost, 127.0.0.1 ou IP de rede local)
        if (hostname && hostname !== '') {
            const apiProtocol = protocol === 'https:' ? 'https:' : 'http:';
            return `${apiProtocol}//${hostname}:8000/api/sgie/v1`;
        }
    }
    return 'http://127.0.0.1:8000/api/sgie/v1';
}

const SGIE_CONFIG = {
    API_BASE_URL: resolverUrlApi(),
};

if (typeof window !== 'undefined') {
    window.SGIE_CONFIG = SGIE_CONFIG;

    // Remove popups e avisos gerados pelo Live Reload do Five Server em dev
    if (typeof document !== 'undefined' && window.MutationObserver) {
        const limparPopupsFiveServer = () => {
            const popups = document.querySelectorAll('#fiveserver-info-wrapper, [id^="fiveserver-info"]');
            popups.forEach((el) => el.remove());
        };
        const obs = new MutationObserver(limparPopupsFiveServer);
        if (document.documentElement) {
            obs.observe(document.documentElement, { childList: true, subtree: true });
        }
    }
}

