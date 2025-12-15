import cv2
from ultralytics import YOLO
import math

# --- НАСТРОЙКИ ---
VIDEO_PATH = "videos/2025-11-16_22-09-10.mp4"  # путь к обрабатываемому видео
MODEL_PATH = "runs/detect/valorant_events_yolov8s2/weights/best.pt"  # путь к файлу весов модели
OUTPUT_TXT_PATH = "valorant_events.txt"  # Логи
CONFIDENCE_THRESHOLD = 0.5  # Порог уверенности для детекции


# Загрузка обученной модели
model = YOLO(MODEL_PATH)


# Открытие видеофайла
cap = cv2.VideoCapture(VIDEO_PATH)

# Получение информации о видео
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Видео загружено: {VIDEO_PATH}")
print(f"Частота кадров (FPS): {fps}")
print(f"Общее количество кадров: {frame_count}")

# ОБРАБОТКА ВИДЕО И ЗАПИСЬ РЕЗУЛЬТАТОВ   
with open(OUTPUT_TXT_PATH, 'w', encoding='utf-8') as f:

    events = {}  # Словарь для отслеживания активных событий
    # флаг, чтобы отследить, было ли найдено хоть одно событие
    was_event_found = False

    frame_number = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Выполнение детекции на текущем кадре
        results = model(frame, verbose=False)

        current_time_sec = frame_number / fps
        detected_events_in_frame = set()

        # Анализ результатов детекции
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
                # Событие завершилось, получаем его данные
                start_time = events[event_name]['start_time']
                end_time = current_time_sec
                
                # ИЗМЕНЕНИЕ 3: Записываем событие в файл СРАЗУ ЖЕ
                start_sec = math.floor(start_time)
                end_sec = math.ceil(end_time)

                # Пропускаем очень короткие события (менее 1 секунды)
                if end_sec - start_sec >= 1:
                    output_string = (f"С {start_sec} до {end_sec} секунд: "
                                        f"'{event_name}'\n")
                    f.write(output_string)
                    f.flush() # Принудительно записываем буфер на диск
                    was_event_found = True
                
                # Удаляем событие из списка активных
                del events[event_name]

        frame_number += 1
        print(f"Обработка кадра {frame_number}/{frame_count} ({current_time_sec:.2f} сек)", end='\r')

    # Если видео закончилось, а какие-то события все еще активны!!!!
    # Записываем их как завершившиеся в конце видео!!!!
    final_time_sec = frame_count / fps
    for event_name, data in events.items():
        start_sec = math.floor(data['start_time'])
        end_sec = math.ceil(final_time_sec)
        if end_sec - start_sec >= 1:
            output_string = (f"С {start_sec} до {end_sec} секунд: "
                                f"'{event_name}'\n")
            f.write(output_string)
            was_event_found = True

print(f"\nОбработка видео завершена.")
print(f"Результаты успешно сохранены в файл: {OUTPUT_TXT_PATH}")