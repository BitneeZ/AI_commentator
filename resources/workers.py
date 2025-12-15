from resources.smartmanager import *
from resources.valorantoverlay import *


def llm_worker(llm_queue, speech_queue, gui_ref):
    """Слушает очередь событий, генерирует текст, кидает в очередь речи"""
    while True:
        event_id = llm_queue.get()
        if event_id is None: break
        
        try:
            description = EVENT_DESCRIPTIONS.get(event_id, event_id)
            # Прямое обращение к методу класса GUI (безопасно для Tkinter только чтение/простые операции)
            # Лучше использовать gui_ref.set_text, но аккуратно с потоками
            print(f"[LLM] Генерация: {description}")
            
            generated_text = generate_text(description, GIGACHAT_TOKEN)
            print(f"[LLM] Ответ: {generated_text}")
            
            clean_text = generated_text.replace('"', '').replace("'", "").replace("\n", " ")
            speech_queue.put((clean_text, event_id))
            
        except Exception as e:
            print(f"LLM Error: {e}")
        
        llm_queue.task_done()

def tts_worker(speech_queue, tts_model, gui_ref):
    """Слушает очередь речи, обновляет GUI, воспроизводит звук"""
    while True:
        data = speech_queue.get()
        if data is None: break
        
        text, event_id = data
        try:
            color = "red" if ("enemy" in event_id or "bomb" in event_id) else "#00FF00"
            
            # Обновляем текст на экране (из этого потока)
            # В Tkinter это не thread-safe, но часто работает. 
            # В идеале нужно использовать очередь для GUI, но для упрощения оставим так.
            gui_ref.set_text(text, color)
            
            audio = tts_model.apply_tts(text=text, speaker=VOICE_SPEAKER, sample_rate=SAMPLE_RATE)
            audio_np = audio.numpy()
            
            if ENABLE_ANIME_VOICE:
                audio_np = librosa.effects.pitch_shift(audio_np, sr=SAMPLE_RATE, n_steps=ANIME_PITCH_STEPS)
            
            sd.play(audio_np, SAMPLE_RATE)
            sd.wait()
            
            time.sleep(1.5)
            gui_ref.set_text("") # Очистка
            
        except Exception as e:
            print(f"TTS Error: {e}")
            
        speech_queue.task_done()