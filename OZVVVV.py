import pyttsx3
import queue
import threading
import time

# === Инициализация движка ===
engine = pyttsx3.init()
engine.setProperty('rate', 190)
engine.setProperty('volume', 1.0)

events_queue = queue.Queue()
emotion_state = {"speed": 1.0, "emotion": 0.3}

# === Создаём отдельный движок для каждого вызова ===
def speak_text(text, speed):
    local_engine = pyttsx3.init()
    rate = int(190 * speed)
    local_engine.setProperty('rate', rate)
    local_engine.setProperty('volume', 1.0)
    local_engine.say(text)
    local_engine.runAndWait()
    local_engine.stop()

# === Основной поток озвучки ===
def announcer_loop():
    recent_events = []
    while True:
        try:
            event = events_queue.get(timeout=1)
            recent_events.append(time.time())
            recent_events = [t for t in recent_events if time.time() - t < 10]

            intensity = min(len(recent_events) / 5, 1.0)
            emotion_state["speed"] = 1.0 + intensity * 0.5
            emotion_state["emotion"] = 0.3 + intensity * 0.7

            if intensity > 0.7:
                event = event.upper() + "!!!"
            elif intensity > 0.4:
                event = "⚡ " + event.capitalize()

            print(f"[🎙speed={emotion_state['speed']:.2f}, intensity={intensity:.2f}] → {event}")
            speak_text(event, emotion_state["speed"])

        except queue.Empty:
            pass

# === Ввод текста в консоль ===
def user_input_loop():
    print("\nВводи текст для озвучки (пиши 'exit' для выхода):")
    while True:
        text = input("➡ ")
        if text.lower().strip() in ["exit", "quit", "выход"]:
            print("Завершение...")
            break
        if text.strip():
            events_queue.put(text)

# === Запуск ===
if __name__ == "__main__":
    announcer_thread = threading.Thread(target=announcer_loop, daemon=True)
    announcer_thread.start()
    user_input_loop()
