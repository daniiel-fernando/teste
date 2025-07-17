import requests
import platform
import time

SERVER_URL = "http://192.168.79.150:5000"  # Altere para o IP do seu servidor


def get_computer_name():
    return platform.node()


def register_computer():
    url = f"{SERVER_URL}/api/computers/register"
    data = {
        "computer_name": get_computer_name(),
        "department": "TI",  # Altere conforme necessário
        "user_name": "usuario_teste",
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        print("Registro:", resp.status_code, resp.text)
    except Exception as e:
        print("Erro ao registrar computador:", e)


def send_heartbeat():
    url = f"{SERVER_URL}/api/computers/heartbeat"
    data = {"computer_name": get_computer_name(), "user_name": "usuario_teste"}
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
        print("Mensagens:", resp.status_code, resp.text)
        if resp.status_code == 200:
            data = resp.json()
            for msg in data.get("messages", []):
                print("Nova mensagem:", msg.get("title"), "-", msg.get("content"))
    except Exception as e:
        print("Erro ao buscar mensagens:", e)


if __name__ == "__main__":
    register_computer()
    while True:
        send_heartbeat()
        fetch_messages()
        time.sleep(30)  # Aguarda 30 segundos entre as buscas
