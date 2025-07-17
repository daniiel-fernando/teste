// Global variables
let currentUser = null;
let currentTheme = localStorage.getItem('theme') || 'light';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeApp();
});

// Theme management
function initializeTheme() {
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon();
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const themeIcon = document.querySelector('#theme-toggle i');
    if (themeIcon) {
        themeIcon.className = currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
}

// App initialization
async function initializeApp() {
    showLoading();
    
    try {
        // Check if user is already authenticated
        const authResponse = await fetch('/api/check-auth');
        const authData = await authResponse.json();
        
        if (authData.authenticated) {
            currentUser = authData.user;
            await initializeMainApp();
        } else {
            showLogin();
        }
    } catch (error) {
        console.error('Error checking authentication:', error);
        showLogin();
    }
    
    hideLoading();
}

function showLoading() {
    document.getElementById('loading-screen').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-screen').style.display = 'none';
}

function showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('main-app').style.display = 'none';
    
    // Setup login form
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', handleLogin);
}

function showMainApp() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'flex';
}

async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        // Tenta primeiro o login de demonstração
        const response = await fetch("/api/login-ad", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            await initializeMainApp();
            showMainApp();
        } else {
            showError(data.error || 'Erro na autenticação');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Erro de conexão');
    }
}

async function initializeMainApp() {
    // Update user info
    document.getElementById('user-name').textContent = currentUser.name;
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    await loadDepartments();
    await loadUsers();
    await loadScheduledMessages();
    await loadMessageHistory();
    
    // Show messages tab by default
    showTab('messages');
}

function setupEventListeners() {
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // User menu
    const userMenuBtn = document.getElementById('user-menu-btn');
    const userDropdown = document.getElementById('user-dropdown');
    
    userMenuBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        userDropdown.classList.toggle('show');
    });
    
    document.addEventListener('click', function() {
        userDropdown.classList.remove('show');
    });
    
    // Logout
    document.getElementById('logout-link').addEventListener('click', handleLogout);
    
    // Navigation tabs
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            showTab(tab);
        });
    });
    
    // Message form
    const messageForm = document.getElementById('message-form');
    messageForm.addEventListener('submit', handleSendMessage);
    
    // Clear message button
    document.getElementById('clear-message').addEventListener('click', clearMessageForm);
    
    // File upload
    const imageInput = document.getElementById('message-image');
    imageInput.addEventListener('change', handleImageUpload);
    
    // Schedule modal
    document.getElementById('new-schedule-btn').addEventListener('click', showScheduleModal);
    document.querySelector('.modal-close').addEventListener('click', hideScheduleModal);
    document.querySelector('.modal-cancel').addEventListener('click', hideScheduleModal);
    
    // Schedule form
    const scheduleForm = document.getElementById('schedule-form');
    scheduleForm.addEventListener('submit', handleScheduleMessage);
    
    // Modal backdrop click
    document.getElementById('schedule-modal').addEventListener('click', function(e) {
        if (e.target === this) {
            hideScheduleModal();
        }
    });
}

function showTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'schedule') {
        loadScheduledMessages();
    } else if (tabName === 'history') {
        loadMessageHistory();
    }
}

async function handleLogout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        currentUser = null;
        showLogin();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

async function loadDepartments() {
    try {
        const response = await fetch('/api/departments');
        const data = await response.json();
        
        if (data.success) {
            const selects = document.querySelectorAll('#message-recipients, #schedule-recipients');
            selects.forEach(select => {
                select.innerHTML = '';
                data.departments.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.id;
                    option.textContent = dept.name;
                    select.appendChild(option);
                });
            });
        }
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const data = await response.json();
        
        if (data.success) {
            // Store users for later use
            window.appUsers = data.users;
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function handleImageUpload(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('image-preview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        preview.style.display = 'none';
        preview.innerHTML = '';
    }
}

async function handleSendMessage(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const content = formData.get('content').trim();
    const imageFile = formData.get('image');
    const recipients = Array.from(document.getElementById('message-recipients').selectedOptions)
        .map(option => option.value);
    
    if (!content && !imageFile.name) {
        showToast('Por favor, adicione uma mensagem ou imagem', 'warning');
        return;
    }
    
    if (recipients.length === 0) {
        showToast('Por favor, selecione pelo menos um destinatário', 'warning');
        return;
    }
    
    try {
        let imageUrl = null;
        
        // Upload image if provided
        if (imageFile.name) {
            const uploadFormData = new FormData();
            uploadFormData.append('file', imageFile);
            
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                body: uploadFormData
            });
            
            const uploadData = await uploadResponse.json();
            
            if (uploadData.success) {
                imageUrl = uploadData.url;
            } else {
                showToast(uploadData.error || 'Erro no upload da imagem', 'error');
                return;
            }
        }
        
        // Send message
        const messageData = {
            content: content || null,
            image_url: imageUrl,
            recipients: recipients
        };
        
        const response = await fetch('/api/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(messageData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Mensagem enviada com sucesso!', 'success');
            clearMessageForm();
            loadMessageHistory(); // Refresh history
        } else {
            showToast(data.error || 'Erro ao enviar mensagem', 'error');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showToast('Erro de conexão', 'error');
    }
}

function clearMessageForm() {
    document.getElementById('message-form').reset();
    document.getElementById('image-preview').style.display = 'none';
    document.getElementById('image-preview').innerHTML = '';
}

function showScheduleModal() {
    document.getElementById('schedule-modal').classList.add('show');
}

function hideScheduleModal() {
    document.getElementById('schedule-modal').classList.remove('show');
    document.getElementById('schedule-form').reset();
}

async function handleScheduleMessage(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const title = formData.get('title').trim();
    const content = formData.get('content').trim();
    const imageFile = formData.get('image');
    const time = formData.get('time');
    const days = formData.get('days');
    const recipients = Array.from(document.getElementById('schedule-recipients').selectedOptions)
        .map(option => option.value);
    
    if (!title) {
        showToast('Por favor, adicione um título', 'warning');
        return;
    }
    
    if (!content && !imageFile.name) {
        showToast('Por favor, adicione uma mensagem ou imagem', 'warning');
        return;
    }
    
    if (!time) {
        showToast('Por favor, selecione um horário', 'warning');
        return;
    }
    
    if (recipients.length === 0) {
        showToast('Por favor, selecione pelo menos um destinatário', 'warning');
        return;
    }
    
    try {
        let imageUrl = null;
        
        // Upload image if provided
        if (imageFile.name) {
            const uploadFormData = new FormData();
            uploadFormData.append('file', imageFile);
            
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                body: uploadFormData
            });
            
            const uploadData = await uploadResponse.json();
            
            if (uploadData.success) {
                imageUrl = uploadData.url;
            } else {
                showToast(uploadData.error || 'Erro no upload da imagem', 'error');
                return;
            }
        }
        
        // Schedule message
        const scheduleData = {
            title: title,
            content: content || null,
            image_url: imageUrl,
            schedule_time: time,
            schedule_days: days,
            recipients: recipients
        };
        
        const response = await fetch('/api/schedule-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scheduleData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Mensagem agendada com sucesso!', 'success');
            hideScheduleModal();
            loadScheduledMessages(); // Refresh schedules
        } else {
            showToast(data.error || 'Erro ao agendar mensagem', 'error');
        }
    } catch (error) {
        console.error('Error scheduling message:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function loadScheduledMessages() {
    try {
        const response = await fetch('/api/scheduled-messages');
        const data = await response.json();
        
        if (data.success) {
            renderScheduledMessages(data.messages);
        }
    } catch (error) {
        console.error('Error loading scheduled messages:', error);
    }
}

function renderScheduledMessages(messages) {
    const container = document.getElementById('schedules-list');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-calendar-alt"></i>
                <h3>Nenhum agendamento encontrado</h3>
                <p>Clique em "Novo Agendamento" para criar seu primeiro agendamento.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = messages.map(message => `
        <div class="schedule-card">
            <div class="schedule-header">
                <div>
                    <div class="schedule-title">${escapeHtml(message.title)}</div>
                    <div class="schedule-time">
                        ${message.schedule_time} - ${getScheduleDaysText(message.schedule_days)}
                    </div>
                </div>
                <div class="schedule-actions-btn">
                    <span class="schedule-status ${message.is_active ? 'active' : 'inactive'}">
                        <i class="fas fa-${message.is_active ? 'play' : 'pause'}"></i>
                        ${message.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                    <button class="btn btn-icon" onclick="toggleSchedule(${message.id}, ${!message.is_active})" title="${message.is_active ? 'Desativar' : 'Ativar'}">
                        <i class="fas fa-${message.is_active ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="btn btn-icon" onclick="deleteSchedule(${message.id})" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${message.content ? `<div class="schedule-content">${escapeHtml(message.content)}</div>` : ''}
            ${message.image_url ? `<img src="${message.image_url}" alt="Imagem agendada" class="message-image">` : ''}
            <div class="schedule-meta">
                <span><i class="fas fa-clock"></i> Criado em ${formatDate(message.created_at)}</span>
                ${message.last_sent ? `<span><i class="fas fa-paper-plane"></i> Último envio: ${formatDate(message.last_sent)}</span>` : ''}
                ${message.next_send ? `<span><i class="fas fa-calendar"></i> Próximo envio: ${formatDate(message.next_send)}</span>` : ''}
            </div>
        </div>
    `).join('');
}

async function toggleSchedule(id, isActive) {
    try {
        const response = await fetch(`/api/scheduled-messages/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: isActive })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Agendamento ${isActive ? 'ativado' : 'desativado'} com sucesso!`, 'success');
            loadScheduledMessages();
        } else {
            showToast(data.error || 'Erro ao atualizar agendamento', 'error');
        }
    } catch (error) {
        console.error('Error toggling schedule:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function deleteSchedule(id) {
    if (!confirm('Tem certeza que deseja excluir este agendamento?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/scheduled-messages/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Agendamento excluído com sucesso!', 'success');
            loadScheduledMessages();
        } else {
            showToast(data.error || 'Erro ao excluir agendamento', 'error');
        }
    } catch (error) {
        console.error('Error deleting schedule:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function loadMessageHistory() {
    try {
        const response = await fetch('/api/messages');
        const data = await response.json();
        
        if (data.success) {
            renderMessageHistory(data.messages);
        }
    } catch (error) {
        console.error('Error loading message history:', error);
    }
}

function renderMessageHistory(messages) {
    const container = document.getElementById('messages-history');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <h3>Nenhuma mensagem encontrada</h3>
                <p>As mensagens enviadas aparecerão aqui.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = messages.map(message => `
        <div class="message-card">
            <div class="message-header">
                <div class="message-sender">${escapeHtml(message.sender_name)}</div>
                <div class="message-time">${formatDate(message.timestamp)}</div>
            </div>
            ${message.content ? `<div class="message-content">${escapeHtml(message.content)}</div>` : ''}
            ${message.image_url ? `<img src="${message.image_url}" alt="Imagem da mensagem" class="message-image">` : ''}
            <div class="message-meta">
                <span><i class="fas fa-tag"></i> Tipo: ${getMessageTypeText(message.message_type)}</span>
                <span><i class="fas fa-check"></i> Status: ${getStatusText(message.status)}</span>
            </div>
        </div>
    `).join('');
}

// Utility functions
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div>${escapeHtml(message)}</div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function showError(message) {
    const errorDiv = document.getElementById('login-error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getScheduleDaysText(days) {
    const daysMap = {
        'daily': 'Todos os dias',
        'weekdays': 'Dias úteis',
        'weekends': 'Fins de semana'
    };
    return daysMap[days] || days;
}

function getMessageTypeText(type) {
    const typeMap = {
        'text': 'Texto',
        'image': 'Imagem',
        'mixed': 'Texto + Imagem'
    };
    return typeMap[type] || type;
}

function getStatusText(status) {
    const statusMap = {
        'sent': 'Enviado',
        'delivered': 'Entregue',
        'read': 'Lido'
    };
    return statusMap[status] || status;
}

