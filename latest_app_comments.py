import time
import traceback
import threading
import queue
from collections import deque, Counter
import os
import cv2
import numpy as np
import mss
import tkinter as tk
from ultralytics import YOLO
import torch
import sounddevice as sd
import librosa
from nlp_dlm import generate_text
from valo_log import *


class SmartEventManager:
    def __init__(self):
        self.history = deque(maxlen=HISTORY_LENGTH)
        self.last_spoken_times = {}
        self.last_global_speech = 0

    def process_frame(self, detected_classes_set):
        current_time = time.time()
        self.history.append(detected_classes_set)
        
        if len(self.history) < HISTORY_LENGTH:
            return None, None

        counts = Counter()
        for frame_set in self.history:
            for event in frame_set:
                counts[event] += 1
        
        stable_events = {evt for evt, count in counts.items() if count >= ACTIVATION_THRESHOLD}
        
        chosen_event = None
        priority_order = ['bomb planting', 'bomb defusing', 'bomb planted', 'own kill', 'enemy']
        
        for p_event in priority_order:
            if p_event in stable_events and p_event in event_descriptions:
                chosen_event = p_event
                break
        
        if not chosen_event:
            for evt in stable_events:
                if evt in event_descriptions:
                    chosen_event = evt
                    break
        
        if not chosen_event:
            return None, None

        # Проверка кулдаунов
        if current_time - self.last_global_speech < GLOBAL_COOLDOWN:
            return None, None

        last_time = self.last_spoken_times.get(chosen_event, 0)
        cooldown_needed = EVENT_COOLDOWNS.get(chosen_event, 5.0)
        
        if current_time - last_time < cooldown_needed:
            return None, None

        self.last_spoken_times[chosen_event] = current_time
        self.last_global_speech = current_time
        
        # ВОЗВРАЩАЕМ НЕ ТЕКСТ, А ID СОБЫТИЯ И ЦВЕТ
        color = "#00FF00"
        if "enemy" in chosen_event or "bomb" in chosen_event or "ult" in chosen_event:
            color = "red"
            
        return chosen_event, color

class ValorantOverlay:
    def __init__(self):
        print("1. Интерфейс...")
        self.root = tk.Tk()
        self.root.title("Valorant AI + LLM")
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

        self.label = tk.Label(self.root, text="Инициализация программы...", font=("Arial", 16, "bold"), 
                              fg="#00FF00", bg="black", anchor='e', justify='right', wraplength=WINDOW_WIDTH)
        self.label.pack(expand=True, fill='both', padx=10)
        self.root.update()

        self.event_manager = SmartEventManager()

        print(f"2. Загрузка YOLO...")
        self.model = YOLO(MODEL_PATH)

        print("3. Загрузка голоса...")
        self.device = torch.device('cpu')
        local_file = 'model.pt'
        if not os.path.isfile(local_file):
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file)
        self.tts_model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        self.tts_model.to(self.device)

        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        
        # --- ОЧЕРЕДИ ---
        self.llm_queue = queue.Queue()   # Событие -> Генерация текста
        self.speech_queue = queue.Queue() # Текст -> Озвучка

        # --- ЗАПУСК ПОТОКОВ ---
        # 1. Поток, который генерирует текст
        self.llm_thread = threading.Thread(target=self.llm_worker, daemon=True)
        self.llm_thread.start()

        # 2. Поток, который озвучивает текст
        self.tts_thread = threading.Thread(target=self.tts_worker, daemon=True)
        self.tts_thread.start()

        self.process_screen()
        self.root.mainloop()

    def llm_worker(self):
        """Берет событие, отправляет в llm, кладет результат в очередь озвучки"""
        while True:
            event_id = self.llm_queue.get()
            if event_id is None: break
            
            # Берем описание для промпта
            description = event_descriptions.get(event_id, event_id)
            
            # Показываем на экране, что думаем...
            # self.label.config(text=f"⚡ GigaChat думает: {description}...", fg="yellow")
            
            # --- ВЫЗОВ ТВОЕЙ ФУНКЦИИ ---
            print(f"[LLM] Генерирую для: {description}")
            generated_text = generate_text(description, GIGACHAT_TOKEN)
            print(f"[LLM] Ответ: {generated_text}")
            
            # Убираем кавычки если есть
            generated_text = generated_text.replace('"', '').replace("'", "")
            
            # Отправляем на озвучку
            self.speech_queue.put((generated_text, event_id))
            
            self.llm_queue.task_done()

    def tts_worker(self):
        """Берет текст, озвучивает и обновляет текст на экране"""
        while True:
            data = self.speech_queue.get()
            if data is None: break
            
            text_to_speak, event_id = data

            # Обновляем текст на экране на сгенерированный
            color = "red" if "enemy" in event_id or "bomb" in event_id else "#00FF00"
            self.label.config(text=text_to_speak, fg=color)
            
            # Синтез
            audio = self.tts_model.apply_tts(text=text_to_speak, speaker=VOICE_SPEAKER, sample_rate=SAMPLE_RATE)
            audio_np = audio.numpy()
            
            if ENABLE_ANIME_VOICE:
                audio_np = librosa.effects.pitch_shift(audio_np, sr=SAMPLE_RATE, n_steps=ANIME_PITCH_STEPS)
            
            sd.play(audio_np, SAMPLE_RATE)
            sd.wait()
            
            # Даем тексту повисеть немного после озвучки
            time.sleep(2.0)
            self.label.config(text="")
                
            
            self.speech_queue.task_done()

    def process_screen(self):
        try:
            screenshot = self.sct.grab(self.monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            results = self.model(img, verbose=False, conf=CONFIDENCE_THRESHOLD)
            
            current_frame_classes = set()
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    if 0 <= cls_id < len(self.model.names):
                        current_frame_classes.add(self.model.names[cls_id])

            # Менеджер возвращает ID события (например 'bomb planting')
            event_id, color = self.event_manager.process_frame(current_frame_classes)

            if event_id:
                # Если нашли событие - отправляем его в очередь к GigaChat
                # (Только если очередь не забита, чтобы не копить лаги)
                if self.llm_queue.qsize() == 0:
                    self.llm_queue.put(event_id)

            self.root.after(10, self.process_screen)

        except Exception as e:
            print(f"Ошибка Loop: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    app = ValorantOverlay()