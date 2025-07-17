/**
 * Módulo de Autenticação Melhorado
 * Sistema de Notificações Jotanunes - Versão 2.2.0
 * ✅ Implementa todas as correções do checklist de autenticação
 */

// Configurações de autenticação
const AUTH_CONFIG = {
    ACCESS_TOKEN_KEY: 'jotanunes_access_token',
    REFRESH_TOKEN_KEY: 'jotanunes_refresh_token',
    USER_KEY: 'jotanunes_user_data',
    REFRESH_THRESHOLD: 5 * 60 * 1000, // 5 minutos antes de expirar
    CHECK_INTERVAL: 60 * 1000 // Verifica a cada 1 minuto
};

// Gerenciador de Autenticação Melhorado
const AuthManager = {
    // ✅ Salvar tokens após login (implementação do checklist)
    saveTokens(accessToken, refreshToken, userData) {
        try {
            localStorage.setItem(AUTH_CONFIG.ACCESS_TOKEN_KEY, accessToken);
            localStorage.setItem(AUTH_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
            localStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(userData));
            console.log('Tokens e dados do usuário salvos no localStorage');
        } catch (error) {
            console.error('Erro ao salvar tokens:', error);
            // Fallback para sessionStorage
            sessionStorage.setItem(AUTH_CONFIG.ACCESS_TOKEN_KEY, accessToken);
            sessionStorage.setItem(AUTH_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
            sessionStorage.setItem(AUTH_CONFIG.USER_KEY, JSON.stringify(userData));
        }
    },

    // ✅ Obter token de acesso para requisições
    getAccessToken() {
        return localStorage.getItem(AUTH_CONFIG.ACCESS_TOKEN_KEY) || 
               sessionStorage.getItem(AUTH_CONFIG.ACCESS_TOKEN_KEY);
    },

    // ✅ Obter refresh token
    getRefreshToken() {
        return localStorage.getItem(AUTH_CONFIG.REFRESH_TOKEN_KEY) || 
               sessionStorage.getItem(AUTH_CONFIG.REFRESH_TOKEN_KEY);
    },

    // ✅ Obter dados do usuário
    getUserData() {
        try {
            const userData = localStorage.getItem(AUTH_CONFIG.USER_KEY) || 
                           sessionStorage.getItem(AUTH_CONFIG.USER_KEY);
            return userData ? JSON.parse(userData) : null;
        } catch (error) {
            console.error('Erro ao obter dados do usuário:', error);
            return null;
        }
    },

    // ✅ Verificar se usuário está autenticado
    isAuthenticated() {
        const accessToken = this.getAccessToken();
        const refreshToken = this.getRefreshToken();
        const userData = this.getUserData();
        return !!(accessToken && refreshToken && userData);
    },

    // ✅ Logout remove os tokens (implementação do checklist)
    clearAuth() {
        localStorage.removeItem(AUTH_CONFIG.ACCESS_TOKEN_KEY);
        localStorage.removeItem(AUTH_CONFIG.REFRESH_TOKEN_KEY);
        localStorage.removeItem(AUTH_CONFIG.USER_KEY);
        sessionStorage.removeItem(AUTH_CONFIG.ACCESS_TOKEN_KEY);
        sessionStorage.removeItem(AUTH_CONFIG.REFRESH_TOKEN_KEY);
        sessionStorage.removeItem(AUTH_CONFIG.USER_KEY);
        console.log('Dados de autenticação removidos');
    },

    // ✅ Verificar validade do token no servidor
    async verifyToken() {
        const accessToken = this.getAccessToken();
        if (!accessToken) return false;

        try {
            const response = await fetch('/api/auth/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.authenticated) {
                    // Atualiza dados do usuário se necessário
                    this.saveTokens(accessToken, this.getRefreshToken(), data.user);
                    return true;
                }
            }

            // Token inválido ou expirado, tenta renovar
            return await this.refreshToken();
        } catch (error) {
            console.error('Erro ao verificar token:', error);
            return await this.refreshToken();
        }
    },

    // ✅ Renovar token automaticamente
    async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) return false;

        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.access_token) {
                    const userData = this.getUserData();
                    this.saveTokens(data.access_token, refreshToken, userData);
                    console.log('Token renovado automaticamente');
                    return true;
                }
            }

            // Falha na renovação
            this.clearAuth();
            return false;
        } catch (error) {
            console.error('Erro ao renovar token:', error);
            this.clearAuth();
            return false;
        }
    },

    // ✅ Fazer requisições autenticadas (implementação do checklist)
    async authenticatedRequest(url, options = {}) {
        const accessToken = this.getAccessToken();
        
        if (!accessToken) {
            throw new Error('Token não encontrado. Faça login novamente.');
        }

        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        };

        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);

            // Se token expirou, tenta renovar
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Tenta novamente com o novo token
                    config.headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
                    return await fetch(url, config);
                } else {
                    // Redireciona para login
                    this.redirectToLogin();
                    throw new Error('Sessão expirada. Redirecionando para login...');
                }
            }

            return response;
        } catch (error) {
            console.error('Erro na requisição autenticada:', error);
            throw error;
        }
    },

    // ✅ Redirecionar para login quando necessário
    redirectToLogin() {
        this.clearAuth();
        if (typeof Auth !== 'undefined' && Auth.showLoginScreen) {
            Auth.showLoginScreen();
        } else {
            window.location.reload();
        }
    },

    // ✅ Inicializar verificação automática
    startTokenMonitoring() {
        // Verifica token periodicamente
        setInterval(async () => {
            if (this.isAuthenticated()) {
                const isValid = await this.verifyToken();
                if (!isValid) {
                    console.log('Token inválido detectado, redirecionando para login');
                    this.redirectToLogin();
                }
            }
        }, AUTH_CONFIG.CHECK_INTERVAL);

        console.log('Monitoramento de token iniciado');
    }
};

// Atualização do módulo Auth original
if (typeof Auth !== 'undefined') {
    // ✅ Sobrescreve método de login para usar tokens
    const originalHandleLogin = Auth.handleLogin;
    Auth.handleLogin = async function(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const errorDiv = document.getElementById('login-error');
        
        const username = form.username.value.trim();
        const password = form.password.value;

        if (!username || !password) {
            Auth.showLoginError('Por favor, preencha todos os campos');
            return;
        }

        Loading.showButton(submitBtn);
        Auth.hideLoginError();

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            
            if (data.success && data.access_token && data.refresh_token) {
                // ✅ Salva ambos os tokens
                AuthManager.saveTokens(data.access_token, data.refresh_token, data.user);
                
                AppState.user = data.user;
                Auth.showMainApp();
                Toast.success('Login realizado com sucesso!');
                
                // Carrega dados iniciais
                await Auth.loadInitialData();
            } else {
                Auth.showLoginError(data.message || 'Erro ao fazer login');
            }
        } catch (error) {
            Auth.showLoginError('Erro de conexão. Tente novamente.');
            console.error('Login error:', error);
        } finally {
            Loading.hideButton(submitBtn);
        }
    };

    // ✅ Sobrescreve método de logout para limpar tokens
    const originalHandleLogout = Auth.handleLogout;
    Auth.handleLogout = async function(event) {
        event.preventDefault();
        
        try {
            // Chama API de logout com refresh token
            const refreshToken = AuthManager.getRefreshToken();
            await AuthManager.authenticatedRequest('/api/auth/logout', {
                method: 'POST',
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // ✅ Limpa dados locais sempre
            AuthManager.clearAuth();
            AppState.user = null;
            Auth.showLoginScreen();
            Toast.info('Logout realizado com sucesso');
        }
    };

    // ✅ Sobrescreve verificação de autenticação
    Auth.checkAuthStatus = async function() {
        try {
            // Verifica se há token salvo
            if (AuthManager.isAuthenticated()) {
                const isValid = await AuthManager.verifyToken();
                
                if (isValid) {
                    // Token válido, carrega dados do usuário
                    AppState.user = AuthManager.getUserData();
                    Auth.showMainApp();
                    await Auth.loadInitialData();
                    return;
                }
            }
            
            // Não autenticado ou token inválido
            document.getElementById('loading-screen').style.display = 'none';
            Auth.showLoginScreen();
        } catch (error) {
            console.error('Erro na verificação de autenticação:', error);
            document.getElementById('loading-screen').style.display = 'none';
            Auth.showLoginScreen();
        }
    };
}

// ✅ Atualiza o módulo API para usar autenticação
if (typeof API !== 'undefined') {
    // Sobrescreve método request para usar autenticação
    const originalRequest = API.request;
    API.request = async function(endpoint, options = {}) {
        // Para endpoints de autenticação, usa método original
        if (endpoint.includes('/auth/')) {
            return originalRequest.call(this, endpoint, options);
        }

        // Para outros endpoints, usa requisição autenticada
        try {
            const url = `${CONFIG.API_BASE}${endpoint}`;
            const response = await AuthManager.authenticatedRequest(url, options);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Erro na requisição');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    };
}

// ✅ Inicialização automática
document.addEventListener('DOMContentLoaded', () => {
    // Inicia monitoramento de token
    AuthManager.startTokenMonitoring();
    
    console.log('Sistema de autenticação melhorado inicializado');
});

// Exporta para uso global
window.AuthManager = AuthManager;

