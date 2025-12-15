from resources.valo_log import *
import time
from collections import deque, Counter

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