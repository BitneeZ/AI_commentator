import requests
import base64
from config import GIGACHAT_CLIENT_ID, GIGACHAT_SECRET, GIGACHAT_SCOPE


# -----------------------------------------
# Получение access_token (точно как у тебя)
# -----------------------------------------
def get_access_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    # Создаём Authorization key
    auth_string = f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_SECRET}"
    auth_key = base64.b64encode(auth_string.encode()).decode()

    payload = {
        "scope": GIGACHAT_SCOPE
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "096c79fd-9c28-40a9-9c5f-ee00ead9c348",
        "Authorization": f"Basic {auth_key}"
    }

    # ❗ Без сертификата — отключаем верификацию
    response = requests.post(url, headers=headers, data=payload, verify=False)

    if response.status_code != 200:
        raise Exception("Ошибка получения токена: " + response.text)

    return response.json()["access_token"]


# -------------------------------------------------
# Генерация текста через GigaChat на основе события
# -------------------------------------------------
def generate_text(event_name: str, access_token: str):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Полностью динамический промпт — никаких заранее заготовленных фраз
    data = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — генератор коротких игровых комментариев. "
                    "Отвечай одной фразой, без мата, эмоционально и живо. Фразами из сталкера. Не теряй изначальный смысл."
                )
            },
            {
                "role": "user",
                "content": f"Сгенерируй короткую фразу для события: {event_name}"
            }
        ],
        "max_tokens": 100,
        "temperature": 1.0
    }

    response = requests.post(url, headers=headers, json=data, verify=False)

    if response.status_code != 200:
        raise Exception("Ошибка GigaChat: " + response.text)

    return response.json()["choices"][0]["message"]["content"]


# -----------------------
# Пример использования
# -----------------------
if __name__ == "__main__":
    # 1) Получаем access token
    token = get_access_token()
    print("Access Token:", token)

    # 2) На лету генерируем текст
    event = "Союзник убит"
    text = generate_text(event, token)

    print("Событие:", event)
    print("Фраза:", text)
