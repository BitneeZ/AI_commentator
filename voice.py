import torch
import soundfile as sf
import librosa
from playsound import playsound
model_data = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v4_ru'
)
model = model_data[0] if isinstance(model_data, tuple) else model_data
speaker = input('Введите голос: aidar, baya, kseniya, xenia, eugene, random: ')
text = input("Введите текст для озвучки: ")
audio = model.apply_tts(text=text, speaker=speaker, sample_rate=48000)
sf.write('voice.wav', audio.numpy(), 48000)
print("<> Обычная озвучка сохранена в voice.wav")
y, sr = librosa.load('voice.wav')
y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=5)
sf.write('voice_anime.wav', y_shifted, sr)
print("Анимешный голос сохранен в voice_anime.wav")
print("\nВоспроизведение оригинала...")
playsound('voices/voice.wav')
print("Воспроизведение анимешной версии...")
playsound('voices/voice_anime.wav')