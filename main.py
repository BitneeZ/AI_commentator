from resources.smartmanager import *
from resources.valorantoverlay import *
from resources.workers import *


if __name__ == "__main__":
    print("\n>>> ЗАПУСК VALCOMMS...")

    app = None

    # 1. Инициализация объектов (Инструменты)
    overlay = ValorantOverlay()
    manager = SmartEventManager()

    # 2. Очереди для связи
    llm_queue = queue.Queue()
    speech_queue = queue.Queue()

    # 3. Загрузка тяжелых моделей
    print(">>> Загрузка YOLO...")
    yolo_model = YOLO(MODEL_PATH)
    
    print(">>> Загрузка TTS...")
    device = torch.device('cpu')
    local_file = 'tts_model.pt'
    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file)
    tts_model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    tts_model.to(device)
    
    overlay.set_text("") # Скрываем текст "Загрузка"
    print(">>> ВСЕ СЛУЖБЫ ГОТОВЫ.")

    # 4. Запуск фоновых потоков (передаем им очереди и ссылки на объекты)
    # Мы передаем 'overlay' в потоки, чтобы они могли менять текст
    t1 = threading.Thread(target=llm_worker, args=(llm_queue, speech_queue, overlay), daemon=True)
    t2 = threading.Thread(target=tts_worker, args=(speech_queue, tts_model, overlay), daemon=True)
    t1.start()
    t2.start()

    # 5. ГЛАВНЫЙ ЦИКЛ ПРИЛОЖЕНИЯ (INFINITE LOOP)
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
                # Можно сразу показать, что думаем
                # overlay.set_text("⚡ AI Думает...", "yellow")

        # Е. Обновление окна приложения (ВАЖНО! Без этого окно зависнет)
        overlay.update_gui()
        
        # Небольшая пауза, чтобы не грузить CPU на 100%
        # time.sleep(0.005) 