from resources.smartmanager import *
from resources.nlp_dlm import generate_text
import tkinter as tk
import mss
import cv2
import numpy as np


class ValorantOverlay:
    def __init__(self):
        # Инициализация окна
        self.root = tk.Tk()
        self.root.title("AI Overlay")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        try: self.root.wm_attributes("-disabled", True)
        except: pass

        screen_width = self.root.winfo_screenwidth()
        x_pos = screen_width - WINDOW_WIDTH - MARGIN_X
        y_pos = MARGIN_Y
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")
        self.root.configure(bg='black')

        self.label = tk.Label(self.root, text="Загрузка...", font=("Arial", 16, "bold"), 
                              fg="#00FF00", bg="black", anchor='e', justify='right', wraplength=WINDOW_WIDTH)
        self.label.pack(expand=True, fill='both', padx=10)
        
        # Инструмент захвата
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        
        # Обновляем окно первый раз
        self.root.update()

    def get_screen_image(self):
        """Делает скриншот и возвращает numpy array для OpenCV"""
        screenshot = self.sct.grab(self.monitor)
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def set_text(self, text, color="#00FF00"):
        """Меняет текст на экране"""
        self.label.config(text=text, fg=color)
    
    def update_gui(self):
        """
        ВАЖНО: Этот метод нужно вызывать в цикле while, 
        чтобы окно не зависло. Вместо root.mainloop()
        """
        self.root.update_idletasks()
        self.root.update()