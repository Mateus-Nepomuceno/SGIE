const SGIE_CONFIG = {
    API_BASE_URL: 'http://127.0.0.1:8000/api/sgie/v1',
};

if (typeof window !== 'undefined') {
    window.SGIE_CONFIG = SGIE_CONFIG;
}
