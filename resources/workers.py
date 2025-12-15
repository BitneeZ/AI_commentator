from resources.smartmanager import *
from resources.valorantoverlay import *
import librosa
import sounddevice as sd


def llm_worker(llm_queue, speech_queue, gui_ref):
    """Слушает очередь событий, генерирует текст, кидает в очередь речи"""
    while True:
        event_id = llm_queue.get()
        if event_id is None: break
        
        description = EVENT_DESCRIPTIONS.get(event_id, event_id)
        # Прямое обращение к методу класса GUI (безопасно для Tkinter только чтение/простые операции)
        # Лучше использовать gui_ref.set_text, но аккуратно с потоками
        print(f"[LLM] Генерация: {description}")
        
        generated_text = generate_text(description, GIGACHAT_TOKEN)
        print(f"[LLM] Ответ: {generated_text}")
        
        clean_text = generated_text.replace('"', '').replace("'", "").replace("\n", " ")
        speech_queue.put((clean_text, event_id))
            
        
        llm_queue.task_done()

def tts_worker(speech_queue, tts_model, gui_queue):
    """Слушает очередь речи, обновляет GUI, воспроизводит звук"""
    while True:
        data = speech_queue.get()
        if data is None: break
        
        text, event_id = data

        color = "red" if ("enemy" in event_id or "bomb" in event_id) else "#00FF00"
        
        # 1. ВМЕСТО ПРЯМОГО ВЫЗОВА, КИДАЕМ В ОЧЕРЕДЬ
        # Отправляем кортеж (текст, цвет)
        gui_queue.put((text, color))
        
        # 2. Синтез и воспроизведение (это можно делать в фоне)
        audio = tts_model.apply_tts(text=text, speaker='baya', sample_rate=48000)
        audio_np = audio.numpy()
        
        # (Если нужен питч шифт, добавь сюда librosa)
        
        sd.play(audio_np, 48000)
        sd.wait()
        
        # Пауза, чтобы текст повисел
        time.sleep(1.5)
        
        # 3. ОЧИСТКА ТЕКСТА (Тоже через очередь)
        gui_queue.put(("", "#00FF00"))

    speech_queue.task_done()