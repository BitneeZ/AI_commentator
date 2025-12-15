import base64
import requests
import json

with open("keys.json", 'r', encoding='utf-8') as f:
        secrets = json.load(f)

GIGACHAT_CLIENT_ID = secrets.get("gigachat_client_id")
GIGACHAT_SECRET = secrets.get("gigachat_secret")
GIGACHAT_SCOPE = secrets.get("gigachat_scope")

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

    response = requests.post(url, headers=headers, data=payload, verify=False)

    if response.status_code != 200:
        raise Exception("Ошибка получения токена: " + response.text)

    return response.json()["access_token"]

token = get_access_token() # Получаем access token

def generate_text(event_name: str, access_token: str):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Полностью динамический промпт
    data = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "system", # для настройки внутри ответа
                "content": (
                    "Ты — профессиональный, эмоциональный киберспортивный комментатор Valorant на финале чемпионата мира. "
                    "Твоя задача — мгновенно и хайпово реагировать на игровые события. "
                    "ИСПОЛЬЗУЙ СЛЕНГ: ван-тап, клатч, эйс, диффуз, плент, ретейк, энтри-фраг, тайминг, эко-раунд, фулл-бай. "
                    "ТРЕБОВАНИЯ: "
                    "1. Отвечай ОДНОЙ короткой, емкой фразой (максимум 10 слов). "
                    "2. Будь энергичным, используй восклицания. "
                    "3. Не используй вводные слова типа 'Ого' или 'Смотрите'. Сразу к делу. "
                    "4. Никогда не повторяйся."
                )
            },
            {
                "role": "user", # настройка самого ответа
                "content": f"Сгенерируй короткую фразу для события: {event_name}"
            }
        ],
        "max_tokens": 100,
        "temperature": 1.0
    }

    response = requests.post(url, headers=headers, json=data, verify=False)

    # расскоментировать
    # if response.status_code != 200:
    #     raise Exception("Ошибка GigaChat: " + response.text)

    return response.json()["choices"][0]["message"]["content"]

# тест
if __name__ == "__main__":
    event = "Союзник убит"
    text = generate_text(event, token)
    print(text)