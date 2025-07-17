/**
 * Sistema de Notificações Melhorado
 * Sistema de Notificações Jotanunes - Versão 2.2.0
 * ✅ Implementa correções para evitar notificações repetidas
 */

// Configurações de notificações
const NOTIFICATION_CONFIG = {
    CHECK_INTERVAL: 30000, // Verifica novas mensagens a cada 30 segundos
    COMPUTER_NAME: null, // Será definido automaticamente
    LAST_CHECK: null,
    PROCESSED_MESSAGES: new Set() // ✅ Controla mensagens já processadas
};

// Gerenciador de Notificações Melhorado
const NotificationManager = {
    // ✅ Inicialização do sistema
    init() {
        this.getComputerName();
        this.startNotificationPolling();
        console.log('Sistema de notificações melhorado inicializado');
    },

    // Obtém nome do computador
    getComputerName() {
        // Tenta obter do localStorage primeiro
        let computerName = localStorage.getItem('computer_name');
        
        if (!computerName) {
            // Gera nome baseado no hostname ou user agent
            computerName = this.generateComputerName();
            localStorage.setItem('computer_name', computerName);
        }
        
        NOTIFICATION_CONFIG.COMPUTER_NAME = computerName;
        console.log('Nome do computador:', computerName);
        return computerName;
    },

    // Gera nome do computador
    generateComputerName() {
        const userAgent = navigator.userAgent;
        const timestamp = Date.now();
        
        // Tenta extrair informações do user agent
        let os = 'Unknown';
        if (userAgent.includes('Windows')) os = 'Windows';
        else if (userAgent.includes('Mac')) os = 'Mac';
        else if (userAgent.includes('Linux')) os = 'Linux';
        
        return `WEB-${os}-${timestamp.toString().slice(-6)}`;
    },

    // ✅ Inicia polling de notificações
    startNotificationPolling() {
        // Primeira verificação imediata
        this.checkForNewMessages();
        
        // Verifica periodicamente
        setInterval(() => {
            this.checkForNewMessages();
        }, NOTIFICATION_CONFIG.CHECK_INTERVAL);
        
        console.log('Polling de notificações iniciado');
    },

    // ✅ Verifica novas mensagens (apenas não lidas)
    async checkForNewMessages() {
        if (!NOTIFICATION_CONFIG.COMPUTER_NAME) {
            console.warn('Nome do computador não definido');
            return;
        }

        try {
            const response = await AuthManager.authenticatedRequest(
                `/api/messages/for-computer/${NOTIFICATION_CONFIG.COMPUTER_NAME}`
            );

            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.messages && data.messages.length > 0) {
                    console.log(`Recebidas ${data.messages.length} mensagens não lidas`);
                    
                    // ✅ Processa apenas mensagens não processadas anteriormente
                    const newMessages = data.messages.filter(msg => 
                        !NOTIFICATION_CONFIG.PROCESSED_MESSAGES.has(msg.id)
                    );
                    
                    if (newMessages.length > 0) {
                        this.processNewMessages(newMessages);
                    }
                } else {
                    console.log('Nenhuma mensagem nova encontrada');
                }
            }
        } catch (error) {
            console.error('Erro ao verificar mensagens:', error);
        }
    },

    // ✅ Processa mensagens novas
    processNewMessages(messages) {
        messages.forEach(message => {
            // ✅ Marca como processada para evitar duplicatas
            NOTIFICATION_CONFIG.PROCESSED_MESSAGES.add(message.id);
            
            // Exibe notificação
            this.showNotification(message);
            
            // Reproduz som se habilitado
            if (message.sound_enabled) {
                this.playNotificationSound();
            }
        });
    },

    // ✅ Exibe notificação visual
    showNotification(message) {
        // Notificação do browser (se permitido)
        if (Notification.permission === 'granted') {
            const notification = new Notification(message.title || 'Nova Mensagem', {
                body: message.content,
                icon: '/static/images/jnunes_logo.png',
                tag: `message-${message.id}`, // ✅ Evita duplicatas
                requireInteraction: message.urgent || message.confirmation_required
            });

            notification.onclick = () => {
                window.focus();
                this.markAsRead(message.id);
                notification.close();
            };

            // Auto-close após 10 segundos (exceto urgentes)
            if (!message.urgent && !message.confirmation_required) {
                setTimeout(() => notification.close(), 10000);
            }
        }

        // Toast notification no sistema
        if (typeof Toast !== 'undefined') {
            const toastType = message.urgent ? 'warning' : 'info';
            const title = message.title || 'Nova Mensagem';
            
            const toast = Toast.show(
                message.content,
                toastType,
                title,
                message.urgent ? 0 : 8000 // Urgentes não fecham automaticamente
            );

            // Adiciona botão de marcar como lida
            if (toast) {
                const readButton = document.createElement('button');
                readButton.className = 'btn btn-sm btn-primary';
                readButton.innerHTML = '<i class="fas fa-check"></i> Marcar como Lida';
                readButton.onclick = () => {
                    this.markAsRead(message.id);
                    Toast.remove(toast);
                };
                
                toast.appendChild(readButton);
            }
        }

        console.log('Notificação exibida:', message.title || 'Nova Mensagem');
    },

    // ✅ Marca mensagem como lida
    async markAsRead(messageId) {
        try {
            const response = await AuthManager.authenticatedRequest(
                `/api/messages/${messageId}/read`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        computer_name: NOTIFICATION_CONFIG.COMPUTER_NAME
                    })
                }
            );

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log(`Mensagem ${messageId} marcada como lida`);
                    
                    // ✅ Remove da lista de processadas para permitir nova verificação
                    NOTIFICATION_CONFIG.PROCESSED_MESSAGES.delete(messageId);
                    
                    // Atualiza interface se necessário
                    this.updateNotificationBadge();
                } else {
                    console.error('Erro ao marcar como lida:', data.message);
                }
            }
        } catch (error) {
            console.error('Erro ao marcar mensagem como lida:', error);
        }
    },

    // Reproduz som de notificação
    playNotificationSound() {
        try {
            // Cria elemento de áudio temporário
            const audio = new Audio();
            audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
            audio.volume = 0.3;
            audio.play().catch(e => console.log('Não foi possível reproduzir som:', e));
        } catch (error) {
            console.log('Erro ao reproduzir som:', error);
        }
    },

    // Atualiza badge de notificações
    updateNotificationBadge() {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            const unreadCount = NOTIFICATION_CONFIG.PROCESSED_MESSAGES.size;
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    },

    // ✅ Solicita permissão para notificações
    async requestNotificationPermission() {
        if ('Notification' in window) {
            if (Notification.permission === 'default') {
                const permission = await Notification.requestPermission();
                console.log('Permissão de notificação:', permission);
                return permission === 'granted';
            }
            return Notification.permission === 'granted';
        }
        return false;
    },

    // ✅ Limpa cache de mensagens processadas
    clearProcessedMessages() {
        NOTIFICATION_CONFIG.PROCESSED_MESSAGES.clear();
        console.log('Cache de mensagens processadas limpo');
    },

    // Registra computador no servidor
    async registerComputer() {
        try {
            const computerData = {
                computer_name: NOTIFICATION_CONFIG.COMPUTER_NAME,
                ip_address: await this.getClientIP(),
                mac_address: 'WEB-CLIENT',
                department: this.detectDepartment(),
                user_name: AuthManager.getUserData()?.name || 'Usuário Web',
                client_version: '2.2.0'
            };

            const response = await AuthManager.authenticatedRequest('/api/computers/register', {
                method: 'POST',
                body: JSON.stringify(computerData)
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Computador registrado:', data);
            }
        } catch (error) {
            console.error('Erro ao registrar computador:', error);
        }
    },

    // Obtém IP do cliente
    async getClientIP() {
        try {
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch (error) {
            return 'Unknown';
        }
    },

    // Detecta departamento baseado no usuário
    detectDepartment() {
        const userData = AuthManager.getUserData();
        return userData?.department || 'TI';
    },

    // Envia heartbeat
    async sendHeartbeat() {
        try {
            const heartbeatData = {
                computer_name: NOTIFICATION_CONFIG.COMPUTER_NAME,
                ip_address: await this.getClientIP(),
                user_name: AuthManager.getUserData()?.name || 'Usuário Web'
            };

            await AuthManager.authenticatedRequest('/api/computers/heartbeat', {
                method: 'POST',
                body: JSON.stringify(heartbeatData)
            });
        } catch (error) {
            console.error('Erro no heartbeat:', error);
        }
    }
};

// ✅ Integração com o sistema principal
if (typeof Auth !== 'undefined') {
    // Sobrescreve loadInitialData para incluir notificações
    const originalLoadInitialData = Auth.loadInitialData;
    Auth.loadInitialData = async function() {
        try {
            // Carrega dados originais
            if (originalLoadInitialData) {
                await originalLoadInitialData.call(this);
            }
            
            // ✅ Inicializa sistema de notificações
            await NotificationManager.requestNotificationPermission();
            await NotificationManager.registerComputer();
            NotificationManager.init();
            
            // Inicia heartbeat
            setInterval(() => {
                NotificationManager.sendHeartbeat();
            }, 60000); // A cada 1 minuto
            
        } catch (error) {
            console.error('Erro ao carregar dados iniciais:', error);
        }
    };
}

// ✅ Limpeza ao sair da página
window.addEventListener('beforeunload', () => {
    NotificationManager.clearProcessedMessages();
});

// ✅ Inicialização automática quando autenticado
document.addEventListener('DOMContentLoaded', () => {
    // Aguarda autenticação antes de inicializar notificações
    const checkAuth = setInterval(() => {
        if (AuthManager.isAuthenticated()) {
            clearInterval(checkAuth);
            
            // Pequeno delay para garantir que tudo está carregado
            setTimeout(() => {
                NotificationManager.requestNotificationPermission();
                NotificationManager.registerComputer();
                NotificationManager.init();
            }, 2000);
        }
    }, 1000);
});

// Exporta para uso global
window.NotificationManager = NotificationManager;

