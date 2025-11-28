import cv2
from ultralytics import YOLO
import math

# --- НАСТРОЙКИ ---
VIDEO_PATH = "videos/2025-11-28_23-16-59.mp4"
MODEL_PATH = "runs/detect/valorant_events_yolov8s2/weights/best.pt"
OUTPUT_TXT_PATH = "valorant_events_comments.txt"
CONFIDENCE_THRESHOLD = 0.5
valorant_comments = {
    # --- Убийства и статус ---
    'own kill': 'Красивый фраг!',
    'ally killed': 'Потеряли союзника.',
    'enemy killed': 'Враг уничтожен.',
    'round won': 'Раунд наш!',
    
    # --- Бомба ---
    'bomb planted': 'Спайк установлен! Время пошло.',
    'bomb planting': 'Враг ставит спайк!',
    'bomb defusing': 'Идет разминирование спайка!',
    'bomb dropped': 'Спайк на земле.',

    # --- Враги ---
    'enemy': 'Контакт! Вижу врага.',
    'jett_enemy': 'Джетт у противника.',
    'reyna_enemy': 'Осторожно, вражеская Рейна.',
    'sage_enemy': 'Вижу Сейдж врага.',
    'iso_enemy': 'Исо замечен.',
    
    # --- Способности ---
    'sage wall': 'Стена перекрыла проход.',
    'gekko enemyflash': 'Гекко кидает флешку!',
    'skye flash util': 'Птица Скай! Отворачивайся!',
    'reyna flash ally': 'Флешка от Рейны.',
    'healing': 'Лечимся...',
}

# Загрузка обученной модели
model = YOLO(MODEL_PATH)

# Открытие видеофайла
cap = cv2.VideoCapture(VIDEO_PATH)

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Видео загружено: {VIDEO_PATH}")
print(f"FPS: {fps}")

# ОБРАБОТКА ВИДЕО
with open(OUTPUT_TXT_PATH, 'w', encoding='utf-8') as f:

    events = {}  
    frame_number = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, verbose=False)
        current_time_sec = frame_number / fps
        detected_events_in_frame = set()

        for result in results:
            for box in result.boxes:
                if box.conf[0] > CONFIDENCE_THRESHOLD:
                    class_id = int(box.cls[0])
                    event_name = model.names[class_id]
                    detected_events_in_frame.add(event_name)

                    if event_name not in events:
                        events[event_name] = {'start_time': current_time_sec}

        # Проверка на завершение событий
        for event_name in list(events.keys()):
            if event_name not in detected_events_in_frame:
                start_time = events[event_name]['start_time']
                end_time = current_time_sec
                
                start_sec = math.floor(start_time)
                end_sec = math.ceil(end_time)

                # Фильтр коротких событий (>= 1 сек)
                if end_sec - start_sec >= 1:
                    
                    # Проверяем, есть ли такой класс в нашем словаре
                    comment_text = valorant_comments.get(event_name)
                    
                    if comment_text:
                        # Если есть комментарий, пишем его красиво
                        output_string = f"[{start_sec}-{end_sec} сек] {comment_text} ({event_name})\n"
                    else:
                        # Если комментария нет, пишем как раньше (или можно вообще пропустить)
                        output_string = f"[{start_sec}-{end_sec} сек] Обнаружено событие: '{event_name}'\n"
                    
                    f.write(output_string)
                    f.flush()
                
                del events[event_name]

        frame_number += 1
        print(f"Обработка: {frame_number}/{frame_count}", end='\r')

    # Финальная очистка (если видео кончилось, а события висят)
    final_time_sec = frame_count / fps
    for event_name, data in events.items():
        start_sec = math.floor(data['start_time'])
        end_sec = math.ceil(final_time_sec)
        if end_sec - start_sec >= 1:
            
            # ### ТО ЖЕ САМОЕ ДЛЯ КОНЦА ВИДЕО ###
            comment_text = valorant_comments.get(event_name)
            if comment_text:
                output_string = f"[{start_sec}-{end_sec} сек] {comment_text} ({event_name})\n"
            else:
                output_string = f"[{start_sec}-{end_sec} сек] Обнаружено событие: '{event_name}'\n"
                
            f.write(output_string)

print(f"\nОбработка завершена. Результаты в файле: {OUTPUT_TXT_PATH}")