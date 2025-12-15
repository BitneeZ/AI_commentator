from ultralytics import YOLO

model = YOLO('yolov8s.pt')

if __name__ == '__main__':
    results = model.train(
        data='dataset/data.yaml',
        epochs=100,
        imgsz=1024,  # можно [высота, ширина], кратные 32 (32 из за того что 1080p не делиться на 2, короче проблемы будут в матрицах)
        batch=16,
        cache=True,  # Кэшируем датасет в ОЗУ для устранения I/O
        name='valorant_events_yolov8s',
        patience=20, # остановка после n не улучшений
        workers=8,   # задействованные ядра CPU
        device=0     # ГПУ
    )