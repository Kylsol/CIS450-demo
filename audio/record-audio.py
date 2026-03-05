# record-clip.py
# Records a short voice clip from your default microphone and saves it as output.wav

import sounddevice as sd
from scipy.io.wavfile import write

fs = 44100        # Sample rate (Hz)
seconds = 5       # Duration of recording (seconds)

print("Recording...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="int16")
sd.wait()  # Wait until recording is finished

write("output.wav", fs, recording)
print("Saved as output.wav")