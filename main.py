from resources.smartmanager import *
from resources.valorantoverlay import *
from resources.workers import *
import queue
import threading
import os
import torch
from ultralytics import YOLO
import random
from tkinter import filedialog


if __name__ == "__main__":
    print("\n>>> Подготовка к запуску VALCOMMS...")
    def get_file_path():
        root = tk.Tk()
        root.withdraw()

        # askopenfilename - для выбора одного файла
        file_path = filedialog.askopenfilename(
            title="Выберите файл зависимостей",
            filetypes=[("Text files", "*.pt"), ("All files", "*.*")] # Фильтр файлов
        )
        return file_path
    app = None

    # 1. Инициализация объектов (Инструменты)
    overlay = ValorantOverlay()
    manager = SmartEventManager()

    # 2. Очереди для связи
    llm_queue = queue.Queue()
    speech_queue = queue.Queue()
    gui_queue = queue.Queue() 

    # 3. Загрузка тяжелых моделей
    print("Укажите директорию файла 'my_yolo.pt'")
    time.sleep(3)
    yolo_model = YOLO(get_file_path())
    print(">>> Загрузка YOLO...")
    time.sleep(random.randint(2, 4))
    print(">>> Подключение LLM...")
    time.sleep(random.randint(2, 4))
    device = torch.device('cpu')
    print("Укажите в какой директории находиться файл 'tts_model.pt'")
    time.sleep(3)
    local_file = get_file_path()
    print(">>> Загрузка TTS...")
    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file)
    tts_model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    tts_model.to(device)
    
    overlay.set_text("") # Скрываем текст "Загрузка"
    print(">>> ВСЕ СЛУЖБЫ ГОТОВЫ.")
    time.sleep(1.5)
    print("\n>>> ЗАПУСК VALCOMMS...")

    # 4. Запуск фоновых потоков (передаем им очереди и ссылки на объекты)
    # 'overlay' в потоки, чтобы они могли менять текст
    t1 = threading.Thread(target=llm_worker, args=(llm_queue, speech_queue, overlay), daemon=True)
    t2 = threading.Thread(target=tts_worker, args=(speech_queue, tts_model, gui_queue), daemon=True)
    t1.start()
    t2.start()
    time.sleep(random.randint(2, 4))
    print("VALCOMMS ГОТОВА К РАБОТЕ!")

    # 5. ГЛАВНЫЙ ЦИКЛ ПРИЛОЖЕНИЯ
    while True:
        # А. Получаем картинку
        frame = overlay.get_screen_image()
        
        # Б. Нейросеть (YOLO)
        results = yolo_model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)
        
        # В. Сбор классов
        detected = set()
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if 0 <= cls_id < len(yolo_model.names):
                    detected.add(yolo_model.names[cls_id])
        
        # Г. Анализ (Smart Manager)
        event_id, color = manager.analyze(detected)
        
        # Д. Если событие есть -> В очередь к LLM
        if event_id:
            if llm_queue.qsize() == 0:
                llm_queue.put(event_id)
                # overlay.set_text("⚡ AI Думает...", "yellow")

        # Проверяем, прислал ли tts_worker просьбу обновить текст
        try:
            # get_nowait не блокирует цикл, если очередь пуста
            text_to_show, text_color = gui_queue.get_nowait()
            overlay.set_text(text_to_show, text_color)
        except queue.Empty:
            pass

        # Е. Обновление окна приложения (ВАЖНО! Без этого окно зависнет)
        overlay.update_gui()
        
        # Небольшая пауза, чтобы не грузить CPU на 100%
        # time.sleep(0.005)