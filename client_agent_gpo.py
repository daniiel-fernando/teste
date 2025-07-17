import requests
import platform
import time
import socket

SERVER_URL = "http://192.168.79.150:5000"


def get_computer_name():
    return platform.node()


def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return None


def register_computer():
    url = f"{SERVER_URL}/api/computers/register"
    data = {
        "computer_name": get_computer_name(),
        "ip_address": get_ip(),
        "department": "TI",  # Altere conforme necessário
        "user_name": get_computer_name(),
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        print("Registro:", resp.status_code, resp.text)
    except Exception as e:
        print("Erro ao registrar computador:", e)


def send_heartbeat():
    url = f"{SERVER_URL}/api/computers/heartbeat"
    data = {
        "computer_name": get_computer_name(),
        "ip_address": get_ip(),
        "user_name": get_computer_name(),
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        print("Heartbeat:", resp.status_code, resp.text)
    except Exception as e:
        print("Erro no heartbeat:", e)


def fetch_messages():
    computer_name = get_computer_name()
    url = f"{SERVER_URL}/api/messages/for-computer/{computer_name}"
    try:
        resp = requests.get(url, timeout=10)
        print("Mensagens:", resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            for msg in data.get("messages", []):
                print(
                    f"[{msg.get('timestamp')}] {msg.get('title')}: {msg.get('content')}"
                )
    except Exception as e:
        print("Erro ao buscar mensagens:", e)


if __name__ == "__main__":
    register_computer()
    while True:
        send_heartbeat()
        fetch_messages()
        time.sleep(30)  # Aguarda 30 segundos entre as buscas
