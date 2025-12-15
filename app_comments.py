import sys
import time
import traceback
import os
import threading
import queue

import cv2
import numpy as np
import mss
import tkinter as tk
from ultralytics import YOLO

# Импорты для звука
import torch
import sounddevice as sd
import librosa


# --- НАСТРОЙКИ ---
MODEL_PATH = "runs/detect/valorant_events_yolov8s2/weights/best.pt" 
CONFIDENCE_THRESHOLD = 0.5
TEXT_DISAPPEAR_DELAY = 0.5 

# Настройки окна
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 80
MARGIN_X = 30
MARGIN_Y = 30

# --- НАСТРОЙКИ ГОЛОСА ---
VOICE_SPEAKER = 'baya'     
ENABLE_ANIME_VOICE = False # Если True — делает голос писклявым 
ANIME_PITCH_STEPS = 2      # На сколько полутонов повышать голос
SAMPLE_RATE = 24000


valorant_comments = {
    # --- Спайк ---
    'bomb planting': 'Враг ставит спайк!',
    'bomb defusing': 'Дифузят спайк!',
    'bomb planted':  'Спайк установлен',
    'bomb dropped':  'Спайк упал',
    
    # --- БОЙ ---
    'own kill':       'Хорош! Минус один',
    'enemy killed':   'Враг убит',
    'ally killed':    'Нашего сняли',
    'round won':      'Раунд наш!',
    'healing':        'Лечусь',
    'enemy_revealed': 'Спалили врага',
    
    # --- УТИЛИТЫ ---
    'gekko enemyflash': 'Флешка Гекко!',
    'skye flash util':  'Птица! Овернись!',
    'yoru flash enemy': 'Флешка Йору!',
    'cypher cam enemy': 'Сломай камеру!',
    'cypher ult enemy': 'Нас видят!',
    'sage wall':        'Стенка',
}

class ValorantOverlay:
    def __init__(self):
        print("1. Инициализация интерфейса...")
        self.root = tk.Tk()
        self.root.title("Valorant AI Commentator")
        
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        try:
            self.root.wm_attributes("-disabled", True)
        except Exception:
            pass

        screen_width = self.root.winfo_screenwidth()
        x_pos = screen_width - WINDOW_WIDTH - MARGIN_X
        y_pos = MARGIN_Y
        
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")
        self.root.configure(bg='black')

        self.label = tk.Label(
            self.root, text="Загрузка AI...", font=("Arial", 20, "bold"), 
            fg="#00FF00", bg="black", anchor='e', justify='right'
        )
        self.label.pack(expand=True, fill='both', padx=10)
        self.root.update()

        # --- ЗАГРУЗКА ВИДЕО МОДЕЛИ ---
        print(f"2. Загрузка YOLO...")
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Нет файла модели: {MODEL_PATH}")
        self.model = YOLO(MODEL_PATH)

        # --- ЗАГРУЗКА ГОЛОСОВОЙ МОДЕЛИ ---
        print("3. Загрузка Silero TTS (Голос)...")
        # Используем GPU если есть, иначе CPU (Torch сам решит, но для TTS CPU обычно ок)
        self.device = torch.device('cpu') 
        
        local_file = 'model.pt' # Кэширование модели
        if not os.path.isfile(local_file):
            print("Скачивание голосовой модели...")
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                           local_file)  
        
        self.tts_model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        self.tts_model.to(self.device)
        print("Голос загружен!")
        self.label.config(text="") # Очистка текста

        # --- НАСТРОЙКА ПОТОКОВ ---
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]

        # Очередь для фраз, чтобы не говорить одновременно
        self.speech_queue = queue.Queue()
        
        # Запускаем поток озвучки
        self.tts_thread = threading.Thread(target=self.tts_worker, daemon=True)
        self.tts_thread.start()

        self.last_detection_time = 0
        self.current_comment = ""
        self.last_spoken_text = ""
        self.last_spoken_time = 0

        self.process_screen()
        self.root.mainloop()

    def tts_worker(self):
        """Этот код работает в фоне и озвучивает текст из очереди"""
        while True:
            text_to_speak = self.speech_queue.get() # Ждет, пока появится текст
            if text_to_speak is None:
                break
            
            try:
                # Генерация аудио
                audio = self.tts_model.apply_tts(text=text_to_speak,
                                                 speaker=VOICE_SPEAKER,
                                                 sample_rate=SAMPLE_RATE)
                
                audio_np = audio.numpy()

                # Анимешный эффект (если включен)
                if ENABLE_ANIME_VOICE:
                    audio_np = librosa.effects.pitch_shift(audio_np, sr=SAMPLE_RATE, n_steps=ANIME_PITCH_STEPS)

                # Воспроизведение (sd.play не блокирует поток, но sd.wait - блокирует этот поток до конца звука)
                sd.play(audio_np, SAMPLE_RATE)
                sd.wait()
                
            except Exception as e:
                print(f"Ошибка озвучки: {e}")
            
            # Небольшая пауза после фразы
            time.sleep(0.2) 
            self.speech_queue.task_done()

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
                    if 0 <= cls_id < len(self.model.names):
                        detected_classes.add(self.model.names[cls_id])

            # --- ПОИСК КОММЕНТАРИЯ ---
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

            # --- ОБНОВЛЕНИЕ GUI И ЗВУКА ---
            if found_comment:
                self.label.config(text=found_comment)
                self.last_detection_time = time.time()
                
                if "враг" in found_comment.lower() or "bomb" in str(detected_classes):
                    self.label.config(fg="red")
                else:
                    self.label.config(fg="#00FF00")

                # --- ЛОГИКА ДОБАВЛЕНИЯ В ОЗВУЧКУ ---
                # Озвучиваем, только если:
                # 1. Это новая фраза (не та же самая, что 1 сек назад)
                # 2. ИЛИ прошло много времени с прошлой озвучки (например, 3 секунды)
                current_time = time.time()
                
                is_new_phrase = (found_comment != self.last_spoken_text)
                is_time_passed = (current_time - self.last_spoken_time > 3.0)
                
                if is_new_phrase or is_time_passed:
                    # Добавляем в очередь на озвучку
                    # Проверяем, не переполнена ли очередь (чтобы не было лага речи на 10 сек вперед)
                    if self.speech_queue.qsize() < 2: 
                        print(f"Озвучиваю: {found_comment}")
                        self.speech_queue.put(found_comment)
                        self.last_spoken_text = found_comment
                        self.last_spoken_time = current_time

            else:
                if time.time() - self.last_detection_time > TEXT_DISAPPEAR_DELAY:
                    self.label.config(text="")

            self.root.after(10, self.process_screen)

        except Exception as e:
            print(f"ОШИБКА: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        app = ValorantOverlay()
    except Exception as e:
        print("КРИТИЧЕСКАЯ ОШИБКА:")
        print(e)

        input("Нажмите Enter...")
