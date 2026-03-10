# W9A-demo.py: Normalize, Trim Silence, 2X Speed Up; LICENSE = BSD 3-Clause License

import numpy as np                          #BSD 3-Clause License
# from pedalboard.io import AudioFile         #GPLv3 License
from scipy.io import wavfile                #BSD 3-Clause License

# Trim starting and ending silence from the audio clip
def trim_silence(audio):
    chunk_size = 1024  # Process in 1024-sample chunks
    threshold = 0.1    # Linear fraction of silence compared to max amplitude

    # Find start index
    start = 0
    for i in range(0, len(audio), chunk_size):
        if np.max(np.abs(audio[i:i + chunk_size])) > threshold:
            start = i
            break

    # Find end index
    end = len(audio)
    for i in range(len(audio) - chunk_size, 0, -chunk_size):
        if np.max(np.abs(audio[i:i + chunk_size])) > threshold:
            end = i + chunk_size
            break

    return audio[start:end]

# Normalize audio to -1.0 to 1.0 range
def normalize_audio(audio):
    peak = np.max(np.abs(audio))
    if peak > 0:
        return audio / peak
    return audio

# Change audio speed
def change_speed(audio, rate):
    indices = (np.arange(0, len(audio) - 1, rate)).astype(int)
    return audio[indices]

# Read the input file
samplerate, audio = wavfile.read("output.wav")

# Convert audio to float range -1.0 to 1.0
if audio.dtype == np.int16:
    audio = audio.astype(np.float32) / 32768.0
elif audio.dtype == np.int32:
    audio = audio.astype(np.float32) / 2147483648.0
elif audio.dtype == np.uint8:
    audio = (audio.astype(np.float32) - 128) / 128.0
else:
    audio = audio.astype(np.float32)

# If stereo, take first channel
if audio.ndim > 1:
    audio = audio[:, 0]

# Normalize
normalized = normalize_audio(audio)

# Trim silence
trimmed = trim_silence(normalized)

# Speed up 2x
sped_up = change_speed(trimmed, 2.0)

# Convert back to int16 for saving
output_audio = np.clip(sped_up * 32767, -32768, 32767).astype(np.int16)

# Write output
wavfile.write("processed.wav", samplerate, output_audio)

print("Saved processed.wav")