#!/usr/bin/env python3
"""
Agente Cliente Melhorado do Sistema de Notificações Corporativas - Jotanunes
Versão 2.1.0 - Melhorada para instalação e estabilidade

Melhorias implementadas:
- Tratamento robusto de erros
- Instalação simplificada
- Interface melhorada
- Logs detalhados
- Configuração automática
- Fallback para dependências opcionais
"""

import os
import sys
import time
import json
import socket
import platform
import threading
import urllib.request
import urllib.parse
import urllib.error
import tkinter as tk
from tkinter import messagebox, ttk
import io
import base64
from datetime import datetime
import logging
import uuid
import getpass
import subprocess
import webbrowser

# Configurações
SERVER_URL = "http://192.168.79.150:5000"  # URL do servidor central
HEARTBEAT_INTERVAL = 300  # 5 minutos
CHECK_MESSAGES_INTERVAL = 30  # 30 segundos
CLIENT_VERSION = "2.1.0"

# Configuração de logging melhorada
def setup_logging():
    """Configura sistema de logging robusto"""
    log_dir = os.path.join(os.path.expanduser("~"), "JotanunesNotifications")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "notification_client.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ],
    )
    return log_file

# Função para verificar e instalar dependências opcionais
def check_optional_dependencies():
    """Verifica dependências opcionais e instala se necessário"""
    optional_deps = {
        'PIL': 'pillow',
        'pystray': 'pystray',
        'requests': 'requests'
    }
    
    missing_deps = []
    available_deps = {}
    
    for module, package in optional_deps.items():
        try:
            if module == 'PIL':
                from PIL import Image, ImageTk
                available_deps['PIL'] = True
            elif module == 'pystray':
                import pystray
                available_deps['pystray'] = True
            elif module == 'requests':
                import requests
                available_deps['requests'] = True
        except ImportError:
            missing_deps.append(package)
            available_deps[module] = False
    
    return available_deps, missing_deps

class NotificationClientImproved:
    def __init__(self):
        self.computer_name = platform.node()
        self.computer_id = None
        self.user_name = getpass.getuser()
        self.department = self.detect_department()
        self.running = True
        self.log_file = setup_logging()
        
        # Verifica dependências
        self.available_deps, self.missing_deps = check_optional_dependencies()
        
        # Interface gráfica
        self.root = None
        self.setup_gui()
        
        # Threads
        self.heartbeat_thread = None
        self.message_check_thread = None
        
        # Sistema de tray (se disponível)
        self.tray_icon = None
        
        logging.info(f"Cliente iniciado - Versão {CLIENT_VERSION}")
        logging.info(f"Dependências disponíveis: {self.available_deps}")
        if self.missing_deps:
            logging.warning(f"Dependências opcionais não encontradas: {self.missing_deps}")

    def detect_department(self):
        """Detecta o departamento baseado no nome do computador"""
        computer_name = self.computer_name.upper()
        
        department_mapping = {
            'TI': ['TI', 'TECH', 'INFO', 'SUPORTE'],
            'OPERACIONAL': ['OPER', 'PROD', 'OBRA', 'CAMPO'],
            'GESTORES': ['GEST', 'ADMIN', 'COORD', 'SUPER'],
            'DIRETORIA': ['DIR', 'BOARD', 'PRES', 'CEO']
        }
        
        for dept, keywords in department_mapping.items():
            if any(keyword in computer_name for keyword in keywords):
                return dept
        
        return "TI"  # Padrão

    def setup_gui(self):
        """Configura a interface gráfica melhorada"""
        self.root = tk.Tk()
        self.root.title("Sistema de Notificações - Jotanunes")
        self.root.geometry("450x350")
        self.root.resizable(False, False)
        
        # Ícone da janela (se disponível)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "Logo.JOTA.3.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Inicia oculto
        self.root.withdraw()
        
        # Configura menu de contexto
        self.setup_context_menu()
        
        # Configura sistema de tray se disponível
        if self.available_deps.get('pystray', False):
            self.setup_system_tray()
        else:
            # Fallback: cria atalho na área de trabalho
            self.create_desktop_shortcut()

    def setup_context_menu(self):
        """Configura menu de contexto da janela"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Mostrar Status", command=self.show_status)
        self.context_menu.add_command(label="Verificar Conexão", command=self.test_connection)
        self.context_menu.add_command(label="Abrir Logs", command=self.open_logs)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Sair", command=self.quit_application)

    def setup_system_tray(self):
        """Configura ícone na bandeja do sistema"""
        try:
            import pystray
            from PIL import Image
            
            # Cria ícone simples ou carrega logo
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "jnunes_logo.png")
                if os.path.exists(logo_path):
                    image = Image.open(logo_path)
                    image = image.resize((64, 64), Image.Resampling.LANCZOS)
                else:
                    raise FileNotFoundError
            except:
                # Cria ícone simples se logo não estiver disponível
                image = Image.new("RGB", (64, 64), color=(220, 20, 60))  # Vermelho Jotanunes
            
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar", self.show_window),
                pystray.MenuItem("Status", self.show_status),
                pystray.MenuItem("Testar Conexão", self.test_connection),
                pystray.MenuItem("Logs", self.open_logs),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", self.quit_application),
            )
            
            self.tray_icon = pystray.Icon("jotanunes_notifications", image, menu=menu)
            
            # Executa em thread separada
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            logging.info("Ícone na bandeja do sistema configurado")
            
        except Exception as e:
            logging.error(f"Erro ao configurar bandeja do sistema: {e}")

    def create_desktop_shortcut(self):
        """Cria atalho na área de trabalho como fallback"""
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "Área de Trabalho")
            
            if os.path.exists(desktop):
                shortcut_path = os.path.join(desktop, "Jotanunes Notifications.txt")
                with open(shortcut_path, 'w', encoding='utf-8') as f:
                    f.write(f"""Sistema de Notificações Jotanunes
Versão: {CLIENT_VERSION}
Status: Executando em segundo plano
Computador: {self.computer_name}
Usuário: {self.user_name}
Departamento: {self.department}

Para ver o status completo, execute o programa novamente.
""")
                logging.info("Arquivo de status criado na área de trabalho")
        except Exception as e:
            logging.error(f"Erro ao criar atalho: {e}")

    def show_window(self):
        """Mostra a janela principal com informações detalhadas"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        # Limpa conteúdo anterior
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo (se disponível)
        try:
            if self.available_deps.get('PIL', False):
                from PIL import Image, ImageTk
                logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "jnunes_logo.png")
                if os.path.exists(logo_path):
                    logo_image = Image.open(logo_path)
                    logo_image = logo_image.resize((80, 40), Image.Resampling.LANCZOS)
                    logo_photo = ImageTk.PhotoImage(logo_image)
                    logo_label = ttk.Label(header_frame, image=logo_photo)
                    logo_label.image = logo_photo
                    logo_label.pack(side=tk.LEFT)
        except Exception as e:
            logging.error(f"Erro ao carregar logo: {e}")
        
        # Título
        title_label = ttk.Label(
            header_frame, 
            text="Sistema de Notificações", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.RIGHT)
        
        # Separador
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=(0, 15))
        
        # Informações do sistema
        info_frame = ttk.LabelFrame(main_frame, text="Informações do Sistema", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        info_data = [
            ("Versão:", CLIENT_VERSION),
            ("Computador:", self.computer_name),
            ("Usuário:", self.user_name),
            ("Departamento:", self.department),
            ("Status:", "Online" if self.computer_id else "Offline"),
            ("Servidor:", SERVER_URL),
            ("ID do Computador:", str(self.computer_id) if self.computer_id else "Não registrado")
        ]
        
        for i, (label, value) in enumerate(info_data):
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(row_frame, text=label, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=value, font=("Arial", 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # Botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="Testar Conexão", command=self.test_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Abrir Logs", command=self.open_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Ocultar", command=self.root.withdraw).pack(side=tk.RIGHT)

    def show_status(self):
        """Mostra status do cliente em messagebox"""
        status_lines = [
            f"Sistema de Notificações - Jotanunes",
            f"Versão: {CLIENT_VERSION}",
            f"",
            f"Computador: {self.computer_name}",
            f"Usuário: {self.user_name}",
            f"Departamento: {self.department}",
            f"Status: {'Online' if self.computer_id else 'Offline'}",
            f"Servidor: {SERVER_URL}",
            f"",
            f"Dependências:",
        ]
        
        for dep, available in self.available_deps.items():
            status = "✓" if available else "✗"
            status_lines.append(f"  {status} {dep}")
        
        messagebox.showinfo("Status do Cliente", "\n".join(status_lines))

    def test_connection(self):
        """Testa conexão com o servidor"""
        try:
            if self.available_deps.get('requests', False):
                import requests
                response = requests.get(f"{SERVER_URL}/api/health", timeout=5)
                if response.status_code == 200:
                    messagebox.showinfo("Teste de Conexão", "✓ Conexão com servidor OK!")
                else:
                    messagebox.showerror("Teste de Conexão", f"✗ Erro: {response.status_code}")
            else:
                # Fallback usando urllib
                req = urllib.request.Request(f"{SERVER_URL}/api/health")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.getcode() == 200:
                        messagebox.showinfo("Teste de Conexão", "✓ Conexão com servidor OK!")
                    else:
                        messagebox.showerror("Teste de Conexão", f"✗ Erro: {response.getcode()}")
        except Exception as e:
            messagebox.showerror("Teste de Conexão", f"✗ Erro de conexão:\n{str(e)}")

    def open_logs(self):
        """Abre arquivo de logs"""
        try:
            if os.path.exists(self.log_file):
                if sys.platform.startswith('win'):
                    os.startfile(self.log_file)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open', self.log_file])
                else:
                    subprocess.call(['xdg-open', self.log_file])
            else:
                messagebox.showwarning("Logs", "Arquivo de log não encontrado")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir logs: {e}")

    def quit_application(self):
        """Encerra a aplicação"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        logging.info("Cliente encerrado pelo usuário")

    def register_computer(self):
        """Registra o computador no servidor central"""
        try:
            data = {
                "computer_name": self.computer_name,
                "ip_address": self.get_local_ip(),
                "mac_address": self.get_mac_address(),
                "department": self.department,
                "user_name": self.user_name,
                "client_version": CLIENT_VERSION
            }
            
            success = self.make_request("POST", "/api/computers/register", data)
            if success and success.get("success"):
                self.computer_id = success["computer"]["id"]
                logging.info(f"Computador registrado com ID: {self.computer_id}")
                return True
            
            logging.error(f"Erro ao registrar computador: {success}")
            return False
            
        except Exception as e:
            logging.error(f"Erro na conexão com servidor: {e}")
            return False

    def send_heartbeat(self):
        """Envia heartbeat para o servidor"""
        try:
            data = {
                "computer_name": self.computer_name,
                "ip_address": self.get_local_ip(),
                "mac_address": self.get_mac_address(),
                "department": self.department,
                "user_name": self.user_name,
                "client_version": CLIENT_VERSION
            }
            
            result = self.make_request("POST", "/api/computers/heartbeat", data)
            if result and result.get("success"):
                self.computer_id = result.get("computer_id")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Erro no heartbeat: {e}")
            return False

    def make_request(self, method, endpoint, data=None):
        """Faz requisição HTTP com fallback para urllib se requests não estiver disponível"""
        url = f"{SERVER_URL}{endpoint}"
        
        try:
            if self.available_deps.get('requests', False):
                import requests
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"HTTP {response.status_code}: {response.text}")
                    return None
            else:
                # Fallback usando urllib
                if method == "POST" and data:
                    data_encoded = json.dumps(data).encode('utf-8')
                    req = urllib.request.Request(
                        url, 
                        data=data_encoded,
                        headers={'Content-Type': 'application/json'}
                    )
                else:
                    req = urllib.request.Request(url)
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.getcode() == 200:
                        return json.loads(response.read().decode('utf-8'))
                    else:
                        logging.error(f"HTTP {response.getcode()}")
                        return None
                        
        except Exception as e:
            logging.error(f"Erro na requisição {method} {endpoint}: {e}")
            return None

    def get_local_ip(self):
        """Obtém o IP local da máquina de forma robusta"""
        try:
            # Método 1: Conectar a um endereço externo para descobrir a interface local
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Conecta ao DNS do Google (não envia dados)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                
                # Verifica se o IP está na faixa da rede corporativa
                if local_ip.startswith("192.168.80.") or local_ip.startswith("192.168.79."):
                    return local_ip
                    
            # Método 2: Buscar por interfaces de rede específicas
            import subprocess
            result = subprocess.run(['ipconfig' if platform.system() == 'Windows' else 'ip', 'addr'], 
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if '192.168.80.' in line or '192.168.79.' in line:
                    # Extrai o IP da linha
                    parts = line.strip().split()
                    for part in parts:
                        if '192.168.80.' in part or '192.168.79.' in part:
                            ip = part.split('/')[0]  # Remove máscara se presente
                            return ip
                            
            # Método 3: Fallback para hostname
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            return local_ip
            
        except Exception as e:
            logging.warning(f"Erro ao obter IP local: {e}")
            return "127.0.0.1"

    def get_mac_address(self):
        """Obtém endereço MAC do computador"""
        try:
            mac = ":".join([
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 2 * 6, 2)
            ][::-1])
            return mac
        except:
            return None

    def check_messages(self):
        """Verifica se há mensagens para este computador"""
        try:
            if not self.computer_id:
                return
            
            result = self.make_request("GET", f"/api/messages/for-computer/{self.computer_id}")
            if result and result.get("success") and result.get("messages"):
                for message in result["messages"]:
                    self.show_notification(message)
                    
        except Exception as e:
            logging.error(f"Erro ao verificar mensagens: {e}")

    def show_notification(self, message):
        """Exibe notificação na tela com interface melhorada"""
        try:
            # Cria janela de notificação
            notification_window = tk.Toplevel(self.root)
            notification_window.title("Nova Notificação - Jotanunes")
            notification_window.geometry("550x450")
            notification_window.resizable(False, False)
            
            # Sempre no topo
            notification_window.attributes("-topmost", True)
            
            # Centraliza na tela
            notification_window.update_idletasks()
            x = (notification_window.winfo_screenwidth() // 2) - (550 // 2)
            y = (notification_window.winfo_screenheight() // 2) - (450 // 2)
            notification_window.geometry(f"550x450+{x}+{y}")
            
            # Estilo da janela
            notification_window.configure(bg='#f0f0f0')
            
            # Frame principal
            main_frame = ttk.Frame(notification_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Cabeçalho com logo
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Logo (se disponível)
            try:
                if self.available_deps.get('PIL', False):
                    from PIL import Image, ImageTk
                    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "jnunes_logo.png")
                    if os.path.exists(logo_path):
                        logo_image = Image.open(logo_path)
                        logo_image = logo_image.resize((100, 50), Image.Resampling.LANCZOS)
                        logo_photo = ImageTk.PhotoImage(logo_image)
                        logo_label = ttk.Label(header_frame, image=logo_photo)
                        logo_label.image = logo_photo
                        logo_label.pack(side=tk.LEFT)
            except Exception as e:
                logging.error(f"Erro ao carregar logo na notificação: {e}")
            
            # Título
            title_label = ttk.Label(
                header_frame, 
                text="Sistema de Notificações", 
                font=("Arial", 16, "bold")
            )
            title_label.pack(side=tk.RIGHT)
            
            # Separador
            ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=(0, 20))
            
            # Conteúdo da mensagem
            content_frame = ttk.Frame(main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Informações do remetente
            info_text = f"De: {message.get('sender_name', 'Sistema')}\n"
            info_text += f"Data: {self.format_datetime(message.get('timestamp'))}\n"
            info_text += f"Para: {self.department}"
            
            info_label = ttk.Label(
                content_frame, 
                text=info_text, 
                font=("Arial", 10), 
                foreground="gray"
            )
            info_label.pack(anchor=tk.W, pady=(0, 15))
            
            # Texto da mensagem
            if message.get("content"):
                text_frame = ttk.LabelFrame(content_frame, text="Mensagem", padding="10")
                text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                
                text_widget = tk.Text(
                    text_frame,
                    wrap=tk.WORD,
                    height=8,
                    font=("Arial", 11),
                    state=tk.DISABLED,
                    bg='white',
                    relief=tk.FLAT
                )
                text_widget.pack(fill=tk.BOTH, expand=True)
                
                text_widget.config(state=tk.NORMAL)
                text_widget.insert(tk.END, message["content"])
                text_widget.config(state=tk.DISABLED)
            
            # Imagem (se houver e PIL disponível)
            if message.get("image_url") and self.available_deps.get('PIL', False):
                try:
                    from PIL import Image, ImageTk
                    
                    image_result = self.make_request("GET", message['image_url'])
                    if image_result:
                        # Aqui você precisaria implementar o download da imagem
                        # Por simplicidade, vou apenas mostrar que há uma imagem
                        image_label = ttk.Label(
                            content_frame, 
                            text="📷 Imagem anexada (clique para visualizar)",
                            font=("Arial", 10),
                            foreground="blue",
                            cursor="hand2"
                        )
                        image_label.pack(pady=10)
                        image_label.bind("<Button-1>", lambda e: webbrowser.open(f"{SERVER_URL}{message['image_url']}"))
                        
                except Exception as e:
                    logging.error(f"Erro ao carregar imagem: {e}")
            
            # Botões
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))
            
            ttk.Button(
                button_frame, 
                text="Fechar", 
                command=notification_window.destroy
            ).pack(side=tk.RIGHT, padx=(10, 0))
            
            ttk.Button(
                button_frame, 
                text="Marcar como Lida", 
                command=lambda: self.mark_message_read(message.get('id'), notification_window)
            ).pack(side=tk.RIGHT)
            
            # Auto-close após 60 segundos
            notification_window.after(60000, notification_window.destroy)
            
            # Foca na janela
            notification_window.focus_force()
            
            # Som de notificação (se disponível)
            try:
                notification_window.bell()
            except:
                pass
            
            # Log da notificação
            logging.info(f"Notificação exibida: {message.get('content', 'Imagem')[:50]}...")
            
        except Exception as e:
            logging.error(f"Erro ao exibir notificação: {e}")

    def mark_message_read(self, message_id, window):
        """Marca mensagem como lida"""
        try:
            if message_id:
                result = self.make_request("POST", f"/api/messages/{message_id}/read")
                if result and result.get("success"):
                    logging.info(f"Mensagem {message_id} marcada como lida")
            window.destroy()
        except Exception as e:
            logging.error(f"Erro ao marcar mensagem como lida: {e}")
            window.destroy()

    def format_datetime(self, datetime_str):
        """Formata data/hora para exibição com fuso horário local"""
        try:
            if datetime_str:
                # Tenta diferentes formatos de data
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S.%f"
                ]
                
                dt = None
                for fmt in formats:
                    try:
                        dt = datetime.strptime(datetime_str.replace("Z", ""), fmt)
                        break
                    except ValueError:
                        continue
                
                if dt:
                    # Assume que o timestamp do servidor está em UTC e converte para horário local
                    import time
                    utc_timestamp = dt.timestamp()
                    local_timestamp = utc_timestamp - time.timezone
                    local_dt = datetime.fromtimestamp(local_timestamp)
                    return local_dt.strftime("%d/%m/%Y, %H:%M")
                    
        except Exception as e:
            logging.warning(f"Erro ao formatar data/hora: {e}")
            
        return datetime_str or "Data não disponível"

    def heartbeat_loop(self):
        """Loop de heartbeat em thread separada"""
        while self.running:
            try:
                success = self.send_heartbeat()
                if not success:
                    logging.warning("Falha no heartbeat, tentando reconectar...")
                    # Tenta registrar novamente se heartbeat falhar
                    self.register_computer()
                
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                logging.error(f"Erro no loop de heartbeat: {e}")
                time.sleep(60)

    def message_check_loop(self):
        """Loop de verificação de mensagens em thread separada"""
        while self.running:
            try:
                self.check_messages()
                time.sleep(CHECK_MESSAGES_INTERVAL)
            except Exception as e:
                logging.error(f"Erro no loop de mensagens: {e}")
                time.sleep(60)

    def start(self):
        """Inicia o cliente"""
        logging.info(f"Iniciando cliente de notificações v{CLIENT_VERSION}")
        logging.info(f"Computador: {self.computer_name}")
        logging.info(f"Usuário: {self.user_name}")
        logging.info(f"Departamento: {self.department}")
        
        # Verifica se já está executando
        if self.is_already_running():
            logging.warning("Cliente já está executando")
            messagebox.showwarning(
                "Aviso", 
                "O cliente de notificações já está executando.\n\nVerifique o ícone na bandeja do sistema."
            )
            return
        
        # Registra o computador
        if not self.register_computer():
            logging.error("Falha ao registrar computador. Tentando novamente em 60 segundos...")
        
        # Inicia threads
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        self.message_check_thread = threading.Thread(target=self.message_check_loop, daemon=True)
        self.message_check_thread.start()
        
        # Mostra janela inicial se não há sistema de tray
        if not self.available_deps.get('pystray', False):
            self.show_window()
        
        # Inicia interface gráfica
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logging.info("Cliente interrompido pelo usuário")
        finally:
            self.running = False

    def is_already_running(self):
        """Verifica se o cliente já está executando"""
        try:
            lock_file = os.path.join(os.path.expanduser("~"), "JotanunesNotifications", "client.lock")
            if os.path.exists(lock_file):
                # Verifica se o processo ainda está ativo
                try:
                    with open(lock_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    if sys.platform.startswith('win'):
                        import subprocess
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                              capture_output=True, text=True)
                        return str(pid) in result.stdout
                    else:
                        os.kill(pid, 0)  # Não mata, apenas verifica se existe
                        return True
                except (ProcessLookupError, ValueError):
                    # Processo não existe, remove lock file
                    os.remove(lock_file)
                    return False
            
            # Cria lock file
            os.makedirs(os.path.dirname(lock_file), exist_ok=True)
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            return False
            
        except Exception as e:
            logging.error(f"Erro ao verificar instância: {e}")
            return False


def install_dependencies():
    """Instala dependências opcionais se necessário"""
    try:
        available_deps, missing_deps = check_optional_dependencies()
        
        if missing_deps:
            response = messagebox.askyesno(
                "Dependências Opcionais",
                f"Algumas funcionalidades opcionais não estão disponíveis:\n\n"
                f"Dependências não encontradas: {', '.join(missing_deps)}\n\n"
                f"Deseja tentar instalar automaticamente?\n"
                f"(Requer conexão com internet)"
            )
            
            if response:
                for package in missing_deps:
                    try:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                        logging.info(f"Dependência {package} instalada com sucesso")
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Erro ao instalar {package}: {e}")
                
                messagebox.showinfo(
                    "Instalação Concluída",
                    "Instalação de dependências concluída.\n\n"
                    "Reinicie o programa para usar todas as funcionalidades."
                )
    except Exception as e:
        logging.error(f"Erro na instalação de dependências: {e}")


def main():
    """Função principal"""
    try:
        # Verifica argumentos de linha de comando
        if len(sys.argv) > 1:
            if sys.argv[1] == '--install-deps':
                install_dependencies()
                return
            elif sys.argv[1] == '--version':
                print(f"Cliente de Notificações Jotanunes v{CLIENT_VERSION}")
                return
            elif sys.argv[1] == '--help':
                print(f"""Cliente de Notificações Jotanunes v{CLIENT_VERSION}

Uso: {sys.argv[0]} [opções]

Opções:
  --install-deps    Instala dependências opcionais
  --version         Mostra versão
  --help            Mostra esta ajuda
  
Sem argumentos: Executa o cliente normalmente
""")
                return
        
        client = NotificationClientImproved()
        client.start()
        
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        messagebox.showerror("Erro Fatal", f"Erro fatal no cliente:\n\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

