import sys
import time
import traceback
import os
import cv2
import numpy as np
import mss
import tkinter as tk
from ultralytics import YOLO

# --- НАСТРОЙКИ ---
MODEL_PATH = "runs/detect/valorant_events_yolov8s2/weights/best.pt" 
CONFIDENCE_THRESHOLD = 0.5
COOLDOWN_SECONDS = 2.0 

valorant_comments = {
    # --- БОМБА (SPIKE) - САМОЕ ВАЖНОЕ ---
    'bomb planting': 'ВРАГ ПЛАНТИТ!',
    'bomb defusing': 'ДИФУЗЯТ СПАЙК!',
    'bomb planted':  'СПАЙК УСТАНОВЛЕН',
    'bomb dropped':  'Спайк на земле',
    'bomb carrier':  'Несут спайк',

    # --- УБИЙСТВА И БОЙ ---
    'own kill':       'ОТЛИЧНЫЙ ВЫСТРЕЛ!',
    'enemy killed':   'Минус один',
    'ally killed':    'Союзник погиб',
    'round won':      'РАУНД НАШ!',
    'healing':        'Лечение...',
    'enemy_revealed': 'ВРАГ ОБНАРУЖЕН!',

    # --- ВРАЖЕСКИЕ СПОСОБНОСТИ (ОПАСНОСТЬ) ---
    'gekko enemyflash': 'ФЛЕШКА ГЕККО!',
    'gekko moly enemy': 'МОЛИК ГЕККО!',
    'skye flash util':  'ПТИЦА СКАЙ!',
    'yoru flash enemy': 'ФЛЕШКА ЙОРУ!',
    'cypher cam enemy': 'КАМЕРА!',
    'cypher ult enemy': 'УЛЬТА САЙФЕРА!',
    'omen_smoke_enemy': 'Смок врага',
    'sage_wall_enemy':  'Стена врага',
    'astra utils':      'Звезды Астры',
    'clove_smoke':      'Смок Клоув',
    
    # --- СОЮЗНЫЕ И НЕЙТРАЛЬНЫЕ ВЕЩИ (ИНФОРМАЦИЯ) ---
    'killjoy_touret_ally': 'Турелька',
    'sage wall':           'Стена Сейдж',
    'sage slow':           'Сфера замедления',
    'reyna flash ally':    'Глаз Рейны',
    'fade_wolf_timer':     'Волк Фейд',
    'neon stun util':      'Стан Неон',
    'neon wall util':      'Стенка Неон',
    'raze_grenade_ally':   'Грешка Рейз',
    'raze_satchel':        'Ранец',
}


# Настройки окна
WINDOW_WIDTH = 450   # Ширина плашки с текстом
WINDOW_HEIGHT = 80   # Высота плашки
MARGIN_X = 30        # Отступ от правого края
MARGIN_Y = 30        # Отступ от верхнего края


class ValorantOverlay:
    def __init__(self):
        print("1. Инициализация интерфейса...")
        self.root = tk.Tk()
        self.root.title("Valorant AI Assistant")
        
        # Настройки прозрачности
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        
        try:
            self.root.wm_attributes("-disabled", True)
        except Exception:
            pass

        # --- РАСЧЕТ КООРДИНАТ ДЛЯ ПРАВОГО ВЕРХНЕГО УГЛА ---
        # Получаем ширину экрана
        screen_width = self.root.winfo_screenwidth()
        
        # Считаем X: (ШиринаЭкрана - ШиринаОкна - Отступ)
        x_pos = screen_width - WINDOW_WIDTH - MARGIN_X
        y_pos = MARGIN_Y
        
        # Применяем координаты
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")
        self.root.configure(bg='black')

        # anchor='e' прижимает текст вправо внутри бокса
        self.label = tk.Label(
            self.root, 
            text="", 
            font=("Arial", 20, "bold"), 
            fg="#00FF00", 
            bg="black",
            anchor='e',  # Текст выравнивается по правому краю
            justify='right'
        )
        self.label.pack(expand=True, fill='both', padx=10) # padx чтобы не прилипало к самому краю
        
        self.root.update()

        print(f"2. Загрузка модели из: {os.path.abspath(MODEL_PATH)}")
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Файл модели НЕ НАЙДЕН по пути: {MODEL_PATH}")
            
        self.model = YOLO(MODEL_PATH)
        print("Модель успешно загружена!")
        
        print("3. Настройка захвата экрана...")
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1] # 1 - это основной монитор

        self.last_comment_time = 0
        self.current_comment = ""
        
        print("4. Запуск цикла обработки...")
        self.process_screen()
        self.root.mainloop()

    def process_screen(self):
        try:
            # --- ЗАХВАТ ---
            screenshot = self.sct.grab(self.monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # --- ДЕТЕКЦИЯ ---
            results = self.model(img, verbose=False, conf=CONFIDENCE_THRESHOLD)
            
            detected_classes = set()
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    # Проверка на выход за границы списка классов
                    if 0 <= cls_id < len(self.model.names):
                        cls_name = self.model.names[cls_id]
                        detected_classes.add(cls_name)

            # --- ЛОГИКА ---
            found_comment = None
            priority_events = ['bomb planting', 'bomb defusing', 'own kill', 'enemy']
            
            for event in priority_events:
                if event in detected_classes and event in valorant_comments:
                    found_comment = valorant_comments[event]
                    break
            
            if not found_comment:
                for cls_name in detected_classes:
                    if cls_name in valorant_comments:
                        found_comment = valorant_comments[cls_name]
                        break

            # --- ОБНОВЛЕНИЕ GUI ---
            if found_comment:
                if (found_comment != self.current_comment) or (time.time() - self.last_comment_time > COOLDOWN_SECONDS):
                    self.label.config(text=found_comment)
                    self.current_comment = found_comment
                    self.last_comment_time = time.time()
                    
                    if "враг" in found_comment.lower() or "bomb" in str(detected_classes):
                        self.label.config(fg="red")
                    else:
                        self.label.config(fg="#00FF00")
            else:
                if time.time() - self.last_comment_time > 3.0:
                    self.label.config(text="")

            # Планируем следующий кадр через 10 мс
            self.root.after(10, self.process_screen)

        except Exception as e:
            print(f"\nОШИБКА В ЦИКЛЕ ОБРАБОТКИ: {e}")
            traceback.print_exc()
            # Не закрываем программу сразу, даем прочитать
            # Но останавливаем цикл root.after

# --- ТОЧКА ВХОДА С ОТЛОВОМ ОШИБОК ---
if __name__ == "__main__":
    print("Запуск приложения...")
    try:
        app = ValorantOverlay()
    except Exception as e:
        print("\n" + "="*50)
        print("КРИТИЧЕСКАЯ ОШИБКА! ПРИЛОЖЕНИЕ ОСТАНОВЛЕНО.")
        print("="*50)
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Описание: {e}")
        print("-" * 20)
        print("Подробности:")
        traceback.print_exc()
        print("="*50)

        input("\nНажмите Enter, чтобы закрыть это окно...")
