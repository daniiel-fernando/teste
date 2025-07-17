/**
 * Sistema de Notificações Jotanunes
 * JavaScript Melhorado - Versão 2.1.0
 * Interface Moderna e Responsiva
 */

// Configurações globais
const CONFIG = {
  API_BASE: "/api",
  TOAST_DURATION: 5000,
  HEARTBEAT_INTERVAL: 30000,
  MAX_FILE_SIZE: 16 * 1024 * 1024, // 16MB
  ALLOWED_EXTENSIONS: ["png", "jpg", "jpeg", "gif"],
  DEPARTMENTS: {
    TI: {
      name: "TI / Tecnologia",
      color: "#3b82f6",
      icon: "fas fa-laptop-code",
    },
    OPERACIONAL: {
      name: "Operacional",
      color: "#f59e0b",
      icon: "fas fa-hard-hat",
    },
    GESTORES: { name: "Gestores", color: "#8b5cf6", icon: "fas fa-user-tie" },
    DIRETORIA: { name: "Diretoria", color: "#dc143c", icon: "fas fa-crown" },
  },
};

// Estado da aplicação
const AppState = {
  user: null,
  computers: [],
  messages: [],
  schedules: [],
  currentTab: "messages",
  theme: localStorage.getItem("theme") || "light",
  selectedRecipients: [],
  selectedOU: "all",
  isLoading: false,
};

// Utilitários
const Utils = {
  // Formatação de data
  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  // Formatação de tamanho de arquivo
  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  },

  // Debounce para otimizar performance
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Validação de email
  isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },

  // Escape HTML
  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  },

  // Truncate text
  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + "...";
  },
};

// Gerenciador de API
const API = {
  async request(endpoint, options = {}) {
    const url = `${CONFIG.API_BASE}${endpoint}`;
    const isFormData = options.body instanceof FormData;

    const config = {
      ...options,
            headers: isFormData ? undefined : { 'Content-Type': 'application/json' }, credentials: "include",
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Erro na requisição");
      }

      return data;
    } catch (error) {
      console.error("API Error:", error);
      throw error;
    }
  },

  // Autenticação
  async login(username, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  async logout() {
    return this.request("/auth/logout", { method: "POST" });
  },

  // Computadores
  async getComputers() {
    return this.request("/computers");
  },

  async getComputersByDepartment(department) {
    return this.request(`/computers/department/${department}`);
  },

  // Mensagens
  async sendMessage(messageData) {
    const formData = new FormData();

    // Adiciona dados da mensagem
    Object.keys(messageData).forEach((key) => {
      if (
        key !== "image" &&
        messageData[key] !== null &&
        messageData[key] !== undefined
      ) {
        if (Array.isArray(messageData[key])) {
          messageData[key].forEach((item) => formData.append(key, item));
        } else {
          formData.append(key, messageData[key]);
        }
      }
    });

    // Adiciona imagem se houver
    if (messageData.image) {
      formData.append("image", messageData.image);
    }

    return this.request("/messages/send", {
      method: "POST",
      body: formData,
    });
  },

  async getMessageHistory(filters = {}) {
    const params = new URLSearchParams(filters);
    return this.request(`/messages/history?${params}`);
  },

  // Agendamentos
  async getSchedules() {
    return this.request("/schedules");
  },

  async createSchedule(scheduleData) {
    return this.request("/schedules", {
      method: "POST",
      body: JSON.stringify(scheduleData),
    });
  },

  async updateSchedule(id, scheduleData) {
    return this.request(`/schedules/${id}`, {
      method: "PUT",
      body: JSON.stringify(scheduleData),
    });
  },

  async deleteSchedule(id) {
    return this.request(`/schedules/${id}`, {
      method: "DELETE",
    });
  },
};

// Gerenciador de Toast
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById("toast-container");
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.id = "toast-container";
      this.container.className = "toast-container";
      document.body.appendChild(this.container);
    }
  },

  show(message, type = "info", title = "", duration = CONFIG.TOAST_DURATION) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = {
      success: "fas fa-check",
      error: "fas fa-times",
      warning: "fas fa-exclamation-triangle",
      info: "fas fa-info",
    };

    toast.innerHTML = `
            <div class="toast-icon">
                <i class="${icons[type]}"></i>
            </div>
            <div class="toast-content">
                ${
                  title
                    ? `<div class="toast-title">${Utils.escapeHtml(
                        title
                      )}</div>`
                    : ""
                }
                <div class="toast-message">${Utils.escapeHtml(message)}</div>
            </div>
            <button class="toast-close" onclick="Toast.remove(this.parentElement)">
                <i class="fas fa-times"></i>
            </button>
        `;

    this.container.appendChild(toast);

    // Anima entrada
    setTimeout(() => toast.classList.add("show"), 100);

    // Remove automaticamente
    if (duration > 0) {
      setTimeout(() => this.remove(toast), duration);
    }

    return toast;
  },

  remove(toast) {
    toast.classList.remove("show");
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
    }, 300);
  },

  success(message, title = "Sucesso") {
    return this.show(message, "success", title);
  },

  error(message, title = "Erro") {
    return this.show(message, "error", title);
  },

  warning(message, title = "Aviso") {
    return this.show(message, "warning", title);
  },

  info(message, title = "Informação") {
    return this.show(message, "info", title);
  },
};

// Gerenciador de Loading
const Loading = {
  show() {
    AppState.isLoading = true;
    document.body.classList.add("loading");
  },

  hide() {
    AppState.isLoading = false;
    document.body.classList.remove("loading");
  },

  showButton(button) {
    button.classList.add("loading");
    button.disabled = true;
  },

  hideButton(button) {
    button.classList.remove("loading");
    button.disabled = false;
  },
};

// Gerenciador de Tema
const Theme = {
  init() {
    this.apply(AppState.theme);
    this.setupToggle();
  },

  apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    AppState.theme = theme;
    localStorage.setItem("theme", theme);

    const themeIcon = document.querySelector("#theme-toggle i");
    if (themeIcon) {
      themeIcon.className = theme === "dark" ? "fas fa-sun" : "fas fa-moon";
    }
  },

  toggle() {
    const newTheme = AppState.theme === "light" ? "dark" : "light";
    this.apply(newTheme);
  },

  setupToggle() {
    const toggleBtn = document.getElementById("theme-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => this.toggle());
    }
  },
};

// Gerenciador de Autenticação
const Auth = {
  init() {
    this.setupLoginForm();
    this.setupLogout();
    this.checkAuthStatus();
  },

  setupLoginForm() {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", this.handleLogin.bind(this));
    }
  },

  setupLogout() {
    const logoutLink = document.getElementById("logout-link");
    if (logoutLink) {
      logoutLink.addEventListener("click", this.handleLogout.bind(this));
    }
  },

  async handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const errorDiv = document.getElementById("login-error");

    const username = form.username.value.trim();
    const password = form.password.value;

    if (!username || !password) {
      this.showLoginError("Por favor, preencha todos os campos");
      return;
    }

    Loading.showButton(submitBtn);
    this.hideLoginError();

    try {
      const response = await API.login(username, password);

      if (response.success) {
        AppState.user = response.user;
        this.showMainApp();
        Toast.success("Login realizado com sucesso!");

        // Carrega dados iniciais
        await this.loadInitialData();
      } else {
        this.showLoginError(response.message || "Erro ao fazer login");
      }
    } catch (error) {
      this.showLoginError("Erro de conexão. Tente novamente.");
      console.error("Login error:", error);
    } finally {
      Loading.hideButton(submitBtn);
    }
  },

  async handleLogout(event) {
    event.preventDefault();

    try {
      await API.logout();
      AppState.user = null;
      this.showLoginScreen();
      Toast.info("Logout realizado com sucesso");
    } catch (error) {
      console.error("Logout error:", error);
      // Força logout local mesmo se API falhar
      AppState.user = null;
      this.showLoginScreen();
    }
  },

  showLoginError(message) {
    const errorDiv = document.getElementById("login-error");
    if (errorDiv) {
      errorDiv.querySelector(".error-text").textContent = message;
      errorDiv.style.display = "flex";
    }
  },

  hideLoginError() {
    const errorDiv = document.getElementById("login-error");
    if (errorDiv) {
      errorDiv.style.display = "none";
    }
  },

  showMainApp() {
    document.getElementById("loading-screen").style.display = "none";
    document.getElementById("login-screen").style.display = "none";
    document.getElementById("main-app").style.display = "flex";

    // Atualiza nome do usuário
    const userNameSpan = document.getElementById("user-name");
    if (userNameSpan && AppState.user) {
      userNameSpan.textContent = AppState.user.name || AppState.user.username;
    }
  },

  showLoginScreen() {
    document.getElementById("loading-screen").style.display = "none";
    document.getElementById("main-app").style.display = "none";
    document.getElementById("login-screen").style.display = "flex";
  },

  async checkAuthStatus() {
    // Simula verificação de autenticação
    // Em produção, verificaria token/sessão
    setTimeout(() => {
      document.getElementById("loading-screen").style.display = "none";
      this.showLoginScreen();
    }, 2000);
  },

  async loadInitialData() {
    try {
      // Carrega computadores
      await Computers.loadComputers();

      // Carrega histórico
      await History.loadHistory();

      // Carrega agendamentos
      await Schedule.loadSchedules();
    } catch (error) {
      console.error("Error loading initial data:", error);
      Toast.error("Erro ao carregar dados iniciais");
    }
  },
};

// Gerenciador de Navegação
const Navigation = {
  init() {
    this.setupNavigation();
    this.setupUserMenu();
  },

  setupNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    navButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabName = btn.dataset.tab;
        this.switchTab(tabName);
      });
    });
  },

  setupUserMenu() {
    const userMenuBtn = document.getElementById("user-menu-btn");
    const userDropdown = document.getElementById("user-dropdown");

    if (userMenuBtn && userDropdown) {
      userMenuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle("show");
      });

      // Fecha dropdown ao clicar fora
      document.addEventListener("click", () => {
        userDropdown.classList.remove("show");
      });
    }
  },

  switchTab(tabName) {
    // Remove active de todos os botões e tabs
    document
      .querySelectorAll(".nav-btn")
      .forEach((btn) => btn.classList.remove("active"));
    document
      .querySelectorAll(".tab-content")
      .forEach((tab) => tab.classList.remove("active"));

    // Ativa botão e tab atual
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`${tabName}-tab`).classList.add("active");

    AppState.currentTab = tabName;

    // Carrega dados específicos da tab
    this.loadTabData(tabName);
  },

  async loadTabData(tabName) {
    switch (tabName) {
      case "computers":
        await Computers.loadComputers();
        break;
      case "history":
        await History.loadHistory();
        break;
      case "schedule":
        await Schedule.loadSchedules();
        break;
      case "analytics":
        Analytics.loadCharts();
        break;
    }
  },
};

// Gerenciador de Mensagens
const Messages = {
  init() {
    this.setupMessageForm();
    this.setupFileUpload();
    this.setupRecipientSelection();
    this.setupCharCounter();
    this.loadComputerCounts();
  },

  setupMessageForm() {
    const messageForm = document.getElementById("message-form");
    if (messageForm) {
      messageForm.addEventListener("submit", this.handleSendMessage.bind(this));
    }

    // Botões de ação
    const clearBtn = document.getElementById("clear-message");
    const previewBtn = document.getElementById("preview-message");
    const saveDraftBtn = document.getElementById("save-draft");

    if (clearBtn) clearBtn.addEventListener("click", this.clearForm.bind(this));
    if (previewBtn)
      previewBtn.addEventListener("click", this.previewMessage.bind(this));
    if (saveDraftBtn)
      saveDraftBtn.addEventListener("click", this.saveDraft.bind(this));
  },

  setupFileUpload() {
    const fileInput = document.getElementById("message-image");
    const uploadArea = document.getElementById("file-upload-area");
    const removeBtn = document.getElementById("remove-image");

    if (fileInput && uploadArea) {
      // Click para selecionar arquivo
      uploadArea.addEventListener("click", () => fileInput.click());

      // Drag and drop
      uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("dragover");
      });

      uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("dragover");
      });

      uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("dragover");

        const files = e.dataTransfer.files;
        if (files.length > 0) {
          this.handleFileSelect(files[0]);
        }
      });

      // Seleção de arquivo
      fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.handleFileSelect(e.target.files[0]);
        }
      });
    }

    if (removeBtn) {
      removeBtn.addEventListener("click", this.removeImage.bind(this));
    }
  },

  setupRecipientSelection() {
    const recipientCheckboxes = document.querySelectorAll(
      'input[name="recipients"]'
    );
    const allCheckbox = document.getElementById("all-departments");

    recipientCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        if (checkbox.value === "all") {
          // Se "Todas as OUs" foi selecionado
          if (checkbox.checked) {
            recipientCheckboxes.forEach((cb) => {
              if (cb.value !== "all") cb.checked = false;
            });
            AppState.selectedOU = "all";
          }
        } else {
          // Se uma OU específica foi selecionada
          if (checkbox.checked) {
            if (allCheckbox) allCheckbox.checked = false;
            AppState.selectedOU = checkbox.value;

            // Desmarca outras OUs específicas
            recipientCheckboxes.forEach((cb) => {
              if (cb.value !== "all" && cb.value !== checkbox.value) {
                cb.checked = false;
              }
            });
          }
        }

        this.updateSelectedRecipients();
      });
    });
  },

  setupCharCounter() {
    const textarea = document.getElementById("message-content");
    const counter = document.getElementById("char-count");

    if (textarea && counter) {
      textarea.addEventListener("input", () => {
        const count = textarea.value.length;
        counter.textContent = count;

        if (count > 1000) {
          counter.style.color = "var(--error)";
        } else if (count > 800) {
          counter.style.color = "var(--warning)";
        } else {
          counter.style.color = "var(--text-muted)";
        }
      });
    }
  },

  async loadComputerCounts() {
    try {
      const computers = await API.getComputers();
      AppState.computers = computers.computers || [];

      // Atualiza contadores por departamento
      const counts = {
        all: AppState.computers.length,
        TI: AppState.computers.filter((c) => c.department === "TI").length,
        OPERACIONAL: AppState.computers.filter(
          (c) => c.department === "OPERACIONAL"
        ).length,
        GESTORES: AppState.computers.filter((c) => c.department === "GESTORES")
          .length,
        DIRETORIA: AppState.computers.filter(
          (c) => c.department === "DIRETORIA"
        ).length,
      };

      // Atualiza interface
      Object.keys(counts).forEach((dept) => {
        const countElement = document.getElementById(
          `${dept.toLowerCase()}-count`
        );
        if (countElement) {
          countElement.textContent = `${counts[dept]} computadores`;
        }
      });

      // Atualiza status online
      const onlineCount = AppState.computers.filter(
        (c) => c.status === "online"
      ).length;
      const onlineCountElement = document.getElementById("online-count");
      if (onlineCountElement) {
        onlineCountElement.textContent = onlineCount;
      }
    } catch (error) {
      console.error("Error loading computer counts:", error);
    }
  },

  updateSelectedRecipients() {
    const selected = [];
    const checkboxes = document.querySelectorAll(
      'input[name="recipients"]:checked'
    );

    checkboxes.forEach((cb) => selected.push(cb.value));
    AppState.selectedRecipients = selected;
  },

  handleFileSelect(file) {
    // Validações
    if (file.size > CONFIG.MAX_FILE_SIZE) {
      Toast.error("Arquivo muito grande. Máximo 16MB.");
      return;
    }

    const extension = file.name.split(".").pop().toLowerCase();
    if (!CONFIG.ALLOWED_EXTENSIONS.includes(extension)) {
      Toast.error("Tipo de arquivo não permitido. Use PNG, JPG ou GIF.");
      return;
    }

    // Mostra preview
    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById("image-preview");
      const img = document.getElementById("preview-img");
      const fileName = document.getElementById("file-name");
      const fileSize = document.getElementById("file-size");
      const uploadArea = document.getElementById("file-upload-area");

      if (preview && img && fileName && fileSize) {
        img.src = e.target.result;
        fileName.textContent = file.name;
        fileSize.textContent = Utils.formatFileSize(file.size);

        uploadArea.style.display = "none";
        preview.style.display = "flex";
      }
    };
    reader.readAsDataURL(file);
  },

  removeImage() {
    const fileInput = document.getElementById("message-image");
    const preview = document.getElementById("image-preview");
    const uploadArea = document.getElementById("file-upload-area");

    if (fileInput) fileInput.value = "";
    if (preview) preview.style.display = "none";
    if (uploadArea) uploadArea.style.display = "block";
  },

  async handleSendMessage(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    // Validações melhoradas
    const title = form.title.value.trim();
    const content = form.content.value.trim();
    
    if (!title) {
      Toast.error("Digite um título para a mensagem");
      form.title.focus();
      return;
    }
    
    if (!content) {
      Toast.error("Digite o conteúdo da mensagem");
      form.content.focus();
      return;
    }

    if (AppState.selectedRecipients.length === 0) {
      Toast.error("Selecione pelo menos um destinatário");
      return;
    }

    Loading.showButton(submitBtn);

    try {
      const messageData = {
        title: title,
        content: content,
        recipients: AppState.selectedRecipients,
        target_ou: AppState.selectedOU || "all",
        urgent: form.urgent?.checked || false,
        require_read_confirmation: form.confirmation?.checked || false,
        sound: form.sound?.checked !== false, // Default true
        image: form.image.files[0] || null,
      };

      const response = await API.sendMessage(messageData);

      if (response.success) {
        Toast.success("Mensagem enviada com sucesso!");
        this.clearForm();

        // Atualiza histórico se estiver na aba
        if (AppState.currentTab === "history") {
          await History.loadHistory();
        }
      } else {
        Toast.error(response.message || "Erro ao enviar mensagem");
      }
    } catch (error) {
      console.error("Send message error:", error);
      Toast.error("Erro ao enviar mensagem. Verifique sua conexão e tente novamente.");
    } finally {
      Loading.hideButton(submitBtn);
    }
  },

  clearForm() {
    const form = document.getElementById("message-form");
    if (form) {
      form.reset();
      this.removeImage();

      // Limpa seleção de destinatários
      document
        .querySelectorAll('input[name="recipients"]')
        .forEach((cb) => (cb.checked = false));
      AppState.selectedRecipients = [];

      // Reset contador
      const counter = document.getElementById("char-count");
      if (counter) {
        counter.textContent = "0";
        counter.style.color = "var(--text-muted)";
      }
    }
  },

  previewMessage() {
    // Implementar preview da mensagem
    Toast.info("Funcionalidade de preview em desenvolvimento");
  },

  saveDraft() {
    // Implementar salvamento de rascunho
    Toast.info("Rascunho salvo localmente");
  },
};

// Gerenciador de Computadores
const Computers = {
  init() {
    this.setupFilters();
    this.setupRefresh();
  },

  setupFilters() {
    const departmentFilter = document.getElementById("department-filter");
    const statusFilter = document.getElementById("status-filter");
    const searchInput = document.getElementById("search-computers");

    if (departmentFilter) {
      departmentFilter.addEventListener("change", this.applyFilters.bind(this));
    }

    if (statusFilter) {
      statusFilter.addEventListener("change", this.applyFilters.bind(this));
    }

    if (searchInput) {
      searchInput.addEventListener(
        "input",
        Utils.debounce(this.applyFilters.bind(this), 300)
      );
    }
  },

  setupRefresh() {
    const refreshBtn = document.getElementById("refresh-computers");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", this.loadComputers.bind(this));
    }
  },

  async loadComputers() {
    try {
      const response = await API.getComputers();
      AppState.computers = response.computers || [];
      this.renderComputers(AppState.computers);
    } catch (error) {
      console.error("Error loading computers:", error);
      Toast.error("Erro ao carregar computadores");
    }
  },

  applyFilters() {
    const departmentFilter =
      document.getElementById("department-filter")?.value || "";
    const statusFilter = document.getElementById("status-filter")?.value || "";
    const searchTerm =
      document.getElementById("search-computers")?.value.toLowerCase() || "";

    let filtered = AppState.computers;

    if (departmentFilter) {
      filtered = filtered.filter((c) => c.department === departmentFilter);
    }

    if (statusFilter) {
      filtered = filtered.filter((c) => c.status === statusFilter);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.computer_name.toLowerCase().includes(searchTerm) ||
          c.user_name.toLowerCase().includes(searchTerm)
      );
    }

    this.renderComputers(filtered);
  },

  renderComputers(computers) {
    const grid = document.getElementById("computers-grid");
    if (!grid) return;

    if (computers.length === 0) {
      grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-desktop"></i>
                    <h3>Nenhum computador encontrado</h3>
                    <p>Não há computadores que correspondam aos filtros aplicados.</p>
                </div>
            `;
      return;
    }

    grid.innerHTML = computers
      .map(
        (computer) => `
            <div class="computer-card">
                <div class="computer-header">
                    <h3 class="computer-name">${Utils.escapeHtml(
                      computer.computer_name
                    )}</h3>
                    <span class="computer-status ${computer.status}">
                        ${computer.status === "online" ? "Online" : "Offline"}
                    </span>
                </div>
                <div class="computer-info">
                    <div class="computer-info-item">
                        <span class="computer-info-label">Usuário:</span>
                        <span class="computer-info-value">${Utils.escapeHtml(
                          computer.user_name
                        )}</span>
                    </div>
                    <div class="computer-info-item">
                        <span class="computer-info-label">Departamento:</span>
                        <span class="computer-info-value">${Utils.escapeHtml(
                          computer.department
                        )}</span>
                    </div>
                    <div class="computer-info-item">
                        <span class="computer-info-label">IP:</span>
                        <span class="computer-info-value">${Utils.escapeHtml(
                          computer.ip_address
                        )}</span>
                    </div>
                    <div class="computer-info-item">
                        <span class="computer-info-label">Última atividade:</span>
                        <span class="computer-info-value">${Utils.formatDate(
                          computer.last_seen
                        )}</span>
                    </div>
                </div>
            </div>
        `
      )
      .join("");
  },
};

// Gerenciador de Histórico
const History = {
  init() {
    this.setupFilters();
    this.setupExport();
  },

  setupFilters() {
    const periodFilter = document.getElementById("period-filter");
    const departmentFilter = document.getElementById(
      "history-department-filter"
    );
    const searchInput = document.getElementById("search-history");

    if (periodFilter) {
      periodFilter.addEventListener("change", this.applyFilters.bind(this));
    }

    if (departmentFilter) {
      departmentFilter.addEventListener("change", this.applyFilters.bind(this));
    }

    if (searchInput) {
      searchInput.addEventListener(
        "input",
        Utils.debounce(this.applyFilters.bind(this), 300)
      );
    }
  },

  setupExport() {
    const exportBtn = document.getElementById("export-history");
    if (exportBtn) {
      exportBtn.addEventListener("click", this.exportHistory.bind(this));
    }
  },

  async loadHistory() {
    try {
      const response = await API.getMessageHistory();
      AppState.messages = response.messages || [];
      this.renderHistory(AppState.messages);
    } catch (error) {
      console.error("Error loading history:", error);
      Toast.error("Erro ao carregar histórico");
    }
  },

  applyFilters() {
    // Implementar filtros do histórico
    this.renderHistory(AppState.messages);
  },

  renderHistory(messages) {
    const list = document.getElementById("history-list");
    if (!list) return;

    if (messages.length === 0) {
      list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h3>Nenhuma mensagem encontrada</h3>
                    <p>Não há mensagens no histórico.</p>
                </div>
            `;
      return;
    }

    list.innerHTML = messages
      .map(
        (message) => `
            <div class="history-item">
                <div class="history-header">
                    <h3 class="history-title">${Utils.escapeHtml(
                      message.title || "Sem título"
                    )}</h3>
                    <span class="history-date">${Utils.formatDate(
                      message.timestamp
                    )}</span>
                </div>
                <div class="history-content">
                    ${Utils.truncateText(
                      Utils.escapeHtml(message.content),
                      150
                    )}
                </div>
                <div class="history-footer">
                    <span class="history-recipients">
                        Para: ${
                          message.recipients
                            ? message.recipients.join(", ")
                            : "N/A"
                        }
                    </span>
                    <span class="history-status ${message.status || "sent"}">
                        ${message.status === "sent" ? "Enviada" : "Falhou"}
                    </span>
                </div>
            </div>
        `
      )
      .join("");
  },

  exportHistory() {
    Toast.info("Funcionalidade de exportação em desenvolvimento");
  },
};

// Gerenciador de Agendamentos
const Schedule = {
  init() {
    this.setupNewSchedule();
  },

  setupNewSchedule() {
    const newBtn = document.getElementById("new-schedule-btn");
    if (newBtn) {
      newBtn.addEventListener("click", this.showNewScheduleModal.bind(this));
    }
  },

  async loadSchedules() {
    try {
      const response = await API.getSchedules();
      AppState.schedules = response.schedules || [];
      this.renderSchedules(AppState.schedules);
      this.updateStats();
    } catch (error) {
      console.error("Error loading schedules:", error);
      Toast.error("Erro ao carregar agendamentos");
    }
  },

  renderSchedules(schedules) {
    const list = document.getElementById("schedule-list");
    if (!list) return;

    if (schedules.length === 0) {
      list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-alt"></i>
                    <h3>Nenhum agendamento encontrado</h3>
                    <p>Crie seu primeiro agendamento clicando no botão acima.</p>
                </div>
            `;
      return;
    }

    // Implementar renderização de agendamentos
    list.innerHTML = "<p>Lista de agendamentos em desenvolvimento...</p>";
  },

  updateStats() {
    // Atualizar estatísticas dos agendamentos
    const activeCount = AppState.schedules.filter((s) => s.active).length;
    const activeElement = document.getElementById("active-schedules");
    if (activeElement) {
      activeElement.textContent = activeCount;
    }
  },

  showNewScheduleModal() {
    Toast.info("Modal de novo agendamento em desenvolvimento");
  },
};

// Gerenciador de Analytics
const Analytics = {
  init() {
    this.setupReportGeneration();
  },

  setupReportGeneration() {
    const generateBtn = document.getElementById("generate-report");
    if (generateBtn) {
      generateBtn.addEventListener("click", this.generateReport.bind(this));
    }
  },

  loadCharts() {
    // Implementar carregamento de gráficos
    Toast.info("Gráficos em desenvolvimento");
  },

  generateReport() {
    Toast.info("Geração de relatórios em desenvolvimento");
  },
};

// Utilitário para toggle de senha
function togglePassword() {
  const passwordInput = document.getElementById("password");
  const toggleBtn = document.querySelector(".password-toggle i");

  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    toggleBtn.className = "fas fa-eye-slash";
  } else {
    passwordInput.type = "password";
    toggleBtn.className = "fas fa-eye";
  }
}

// Utilitário para fechar modais
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("show");
  }
}

// Inicialização da aplicação
document.addEventListener("DOMContentLoaded", () => {
  // Inicializa componentes
  Toast.init();
  Theme.init();
  Auth.init();
  Navigation.init();
  Messages.init();
  Computers.init();
  History.init();
  Schedule.init();
  Analytics.init();

  // Heartbeat para manter conexão
  setInterval(async () => {
    if (AppState.user && AppState.currentTab === "computers") {
      await Computers.loadComputers();
    }
  }, CONFIG.HEARTBEAT_INTERVAL);

  console.log("Sistema de Notificações Jotanunes v2.1.0 inicializado");
});
