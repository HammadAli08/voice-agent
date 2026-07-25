import sounddevice as sd
import numpy as np
import time

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    
    # Calculate volume (RMS)
    audio_data = np.frombuffer(indata, dtype=np.int16).astype(np.float32) / 32768.0
    rms = np.sqrt(np.mean(np.square(audio_data)))
    
    # Visual bar
    bar_length = 50
    filled_length = int(bar_length * (rms * 10)) # Amplify for visibility
    bar = '#' * min(filled_length, bar_length) + '-' * (bar_length - min(filled_length, bar_length))
    
    print(f"\rMic Level: [{bar}] {rms:.4f}", end='', flush=True)

print("Audio Diagnostic Tool")
print("---------------------")
print("Please speak into your microphone.")
print("If the bar does not move, check your system audio settings (pavucontrol).")
print("Press Ctrl+C to exit.\n")

try:
    with sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=audio_callback):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")
except Exception as e:
    print(f"\nError: {e}")
