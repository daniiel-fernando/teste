#!/usr/bin/env python3
"""
Agente Cliente do Sistema de Notificacoes Corporativas
"""

import os
import sys
import time
import json
import socket
import platform
import threading
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import uuid
import getpass
from datetime import datetime
import logging

# Configuracoes
SERVER_URL = "http://192.168.79.150:5000"
HEARTBEAT_INTERVAL = 300
CHECK_MESSAGES_INTERVAL = 30
CLIENT_VERSION = "2.0.0"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("notification_client.log"), logging.StreamHandler()],
)


class NotificationClient:
    def __init__(self):
        self.computer_name = platform.node()
        self.computer_id = None
        self.user_name = getpass.getuser()
        self.department = self.detect_department()
        self.running = True

        self.root = None
        self.setup_gui()

        self.heartbeat_thread = None
        self.message_check_thread = None

    def detect_department(self):
        name = self.computer_name.upper()
        if "TI" in name or "TECH" in name:
            return "TI"
        elif "OPER" in name or "PROD" in name:
            return "OPERACIONAL"
        elif "GEST" in name or "ADMIN" in name:
            return "GESTORES"
        elif "DIR" in name or "BOARD" in name:
            return "DIRETORIA"
        else:
            return "TI"

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Notificacoes - Jotanunes")
        self.root.geometry("400x300")
        self.root.withdraw()
        try:
            import pystray

            self.setup_system_tray()
        except ImportError:
            logging.warning("pystray nao disponivel")

    def setup_system_tray(self):
        try:
            import pystray

            image = Image.new("RGB", (64, 64), color="red")
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar", self.show_window),
                pystray.MenuItem("Status", self.show_status),
                pystray.MenuItem("Sair", self.quit_application),
            )
            self.tray_icon = pystray.Icon("notifications", image, menu=menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            logging.error(f"Erro na bandeja: {e}")

    def show_window(self):
        self.root.deiconify()
        self.root.lift()

    def show_status(self):
        info = f"""
Versao: {CLIENT_VERSION}
Computador: {self.computer_name}
Usuario: {self.user_name}
Departamento: {self.department}
Status: {'Online' if self.computer_id else 'Offline'}
Servidor: {SERVER_URL}
        """
        messagebox.showinfo("Status do Cliente", info.strip())

    def quit_application(self):
        self.running = False
        if hasattr(self, "tray_icon"):
            self.tray_icon.stop()
        self.root.quit()

    def register_computer(self):
        try:
            data = {
                "computer_name": self.computer_name,
                "ip_address": self.get_local_ip(),
                "mac_address": self.get_mac_address(),
                "department": self.department,
                "user_name": self.user_name,
            }
            r = requests.post(
                f"{SERVER_URL}/api/computers/register", json=data, timeout=10
            )
            if r.status_code == 200 and r.json().get("success"):
                self.computer_id = r.json()["computer"]["id"]
                logging.info(f"Registrado com ID: {self.computer_id}")
                return True
            logging.error(f"Erro no registro: {r.text}")
        except Exception as e:
            logging.error(f"Erro ao registrar: {e}")
        return False

    def send_heartbeat(self):
        try:
            data = {
                "computer_name": self.computer_name,
                "ip_address": self.get_local_ip(),
                "mac_address": self.get_mac_address(),
                "department": self.department,
                "user_name": self.user_name,
            }
            r = requests.post(
                f"{SERVER_URL}/api/computers/heartbeat", json=data, timeout=5
            )
            if r.status_code == 200 and r.json().get("success"):
                self.computer_id = r.json().get("computer_id")
                return True
        except Exception as e:
            logging.error(f"Erro no heartbeat: {e}")
        return False

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def get_mac_address(self):
        try:
            mac = ":".join(
                [
                    "{:02x}".format((uuid.getnode() >> ele) & 0xFF)
                    for ele in range(0, 2 * 6, 2)
                ][::-1]
            )
            return mac
        except:
            return None

    def check_messages(self):
        if not self.computer_id:
            return
        try:
            r = requests.get(
                f"{SERVER_URL}/api/messages/for-computer/{self.computer_id}", timeout=5
            )
            if r.status_code == 200:
                result = r.json()
                if result.get("success") and result.get("messages"):
                    for msg in result["messages"]:
                        self.show_notification(msg)
        except Exception as e:
            logging.error(f"Erro ao buscar mensagens: {e}")

    def mark_message_delivered(self, message_id):
        try:
            payload = {"message_id": message_id, "computer_id": self.computer_id}
            r = requests.post(
                f"{SERVER_URL}/api/messages/mark-delivered", json=payload, timeout=5
            )
            if r.status_code == 200:
                logging.info(f"Mensagem {message_id} marcada como entregue")
            else:
                logging.warning(f"Erro ao marcar entrega: {r.text}")
        except Exception as e:
            logging.error(f"Erro ao notificar entrega: {e}")

    def show_notification(self, message):
        try:
            win = tk.Toplevel(self.root)
            win.title("Nova Notificacao - Jotanunes")
            win.geometry("500x400")
            win.resizable(False, False)
            win.attributes("-topmost", True)

            win.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - 250
            y = (win.winfo_screenheight() // 2) - 200
            win.geometry(f"500x400+{x}+{y}")

            main = ttk.Frame(win, padding="20")
            main.pack(fill=tk.BOTH, expand=True)

            header = ttk.Frame(main)
            header.pack(fill=tk.X, pady=(0, 20))

            title = ttk.Label(
                header, text="Sistema de Notificacoes", font=("Arial", 16, "bold")
            )
            title.pack(side=tk.RIGHT)

            ttk.Separator(main, orient="horizontal").pack(fill=tk.X, pady=(0, 20))

            content = ttk.Frame(main)
            content.pack(fill=tk.BOTH, expand=True)

            info = f"De: {message.get('sender_name', 'Sistema')}\n"
            info += f"Data: {self.format_datetime(message.get('timestamp'))}"
            ttk.Label(content, text=info, font=("Arial", 10), foreground="gray").pack(
                anchor=tk.W, pady=(0, 10)
            )

            if message.get("content"):
                text = tk.Text(
                    content,
                    wrap=tk.WORD,
                    height=8,
                    font=("Arial", 12),
                    state=tk.DISABLED,
                )
                text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                text.config(state=tk.NORMAL)
                text.insert(tk.END, message["content"])
                text.config(state=tk.DISABLED)

            if message.get("image_url"):
                try:
                    img_resp = requests.get(
                        f"{SERVER_URL}{message['image_url']}", timeout=10
                    )
                    if img_resp.status_code == 200:
                        img = Image.open(io.BytesIO(img_resp.content))
                        img = img.resize((400, 200), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        label = ttk.Label(content, image=photo)
                        label.image = photo
                        label.pack(pady=10)
                except Exception as e:
                    logging.error(f"Erro ao carregar imagem: {e}")

            btn_frame = ttk.Frame(main)
            btn_frame.pack(fill=tk.X, pady=(20, 0))
            ttk.Button(btn_frame, text="Fechar", command=win.destroy).pack(
                side=tk.RIGHT, padx=(10, 0)
            )

            win.after(30000, win.destroy)
            win.focus_force()

            logging.info(
                f"Notificacao exibida: {message.get('content', 'Imagem')[:50]}..."
            )

            self.mark_message_delivered(message.get("id"))

        except Exception as e:
            logging.error(f"Erro ao exibir notificacao: {e}")

    def format_datetime(self, dt_str):
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return dt_str

    def heartbeat_loop(self):
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                logging.error(f"Erro no heartbeat loop: {e}")
                time.sleep(60)

    def message_check_loop(self):
        while self.running:
            try:
                self.check_messages()
                time.sleep(CHECK_MESSAGES_INTERVAL)
            except Exception as e:
                logging.error(f"Erro no loop de mensagens: {e}")
                time.sleep(60)

    def start(self):
        logging.info(f"Iniciando cliente v{CLIENT_VERSION}")
        if not self.register_computer():
            logging.error("Falha ao registrar. Tentando novamente depois...")

        self.heartbeat_thread = threading.Thread(
            target=self.heartbeat_loop, daemon=True
        )
        self.heartbeat_thread.start()

        self.message_check_thread = threading.Thread(
            target=self.message_check_loop, daemon=True
        )
        self.message_check_thread.start()

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logging.info("Cliente interrompido")
        finally:
            self.running = False


def main():
    try:
        client = NotificationClient()
        client.start()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
