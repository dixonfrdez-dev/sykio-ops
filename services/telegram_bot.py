import time
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def enviar_alerta(mensaje):
    """Envía notificaciones a Telegram con reintentos."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    for _ in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
        except Exception:
            time.sleep(1)
    return False
