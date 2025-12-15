from resources.nlp_dlm import get_access_token

# --- НАСТРОЙКИ ---
CONFIDENCE_THRESHOLD = 0.5
GIGACHAT_TOKEN = get_access_token()

# Настройки окна
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 100
MARGIN_X = 30
MARGIN_Y = 30

# Настройки голоса
VOICE_SPEAKER = 'baya'
ENABLE_ANIME_VOICE = False
ANIME_PITCH_STEPS = 4
SAMPLE_RATE = 48000

# Настройки логики
HISTORY_LENGTH = 10
ACTIVATION_THRESHOLD = 6
GLOBAL_COOLDOWN = 4.0

# --- СЛОВАРЬ ОПИСАНИЙ ДЛЯ ЛЛМ ---
EVENT_DESCRIPTIONS = {
    # Бомба
    'bomb planting': 'Враг устанавливает спайк (бомбу)',
    'bomb defusing': 'Враг обезвреживает спайк',
    'bomb planted':  'Спайк установлен, время пошло',
    'bomb dropped':  'Спайк валяется на земле',
    
    # Убийства
    'own kill':       'Я сделал крутое убийство',
    'enemy killed':   'Враг убит',
    'ally killed':    'Моего союзника убили',
    'round won':      'Мы выиграли раунд',
    'healing':        'Я лечусь',
    
    # Утилиты
    'gekko enemyflash': 'В меня летит флешка Гекко',
    'skye flash util':  'В меня летит птица (флешка) Скай',
    'yoru flash enemy': 'Флешка Йору',
    'cypher cam enemy': 'Заметил скрытую камеру Сайфера',
    'cypher ult enemy': 'Сайфер использовал ульту, меня видно',
    'sage wall':        'Стена Сейдж перекрыла проход',
}

# Кулдауны (в секундах)
EVENT_COOLDOWNS = {
    'bomb planting': 15.0,
    'bomb defusing': 15.0,
    'enemy':          8.0, 
    'own kill':       6.0,
}