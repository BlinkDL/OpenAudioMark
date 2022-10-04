import os, sys, time
import numpy as np
import wave
from contextlib import closing

###############################################################################

def save_wav(out_dir, filename, fs, samples):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    SCALE = (2**31)-1
    raw = (SCALE * samples).astype(np.int32).tobytes() #  + np.random.random_sample(len(samples))
    with closing(wave.open(f'{out_dir}/{filename}', 'wb')) as wavwriter:
        wavwriter.setnchannels(1)
        wavwriter.setsampwidth(4)
        wavwriter.setframerate(fs)
        wavwriter.writeframes(raw)

###############################################################################

t_begin = time.time_ns()
seconds = 15

for fs in [384000, 705600, 768000]: # [44100, 352800, 

    t = np.linspace(0, seconds, int(fs*seconds))

    for dB in [0, -1, -2, -3, -10, -20, -34, -35, -60, -61]:
        for freq in [[50], [1000], [12000], [19000,20000], [60,60,60,60,7000]]:
            print(fs, dB, freq)

            samples = np.sin(2 * np.pi * freq[0] * t)
            for ii in range(1, len(freq)):
                samples += np.sin(2 * np.pi * freq[ii] * t)
            
            samples *= (10 ** (dB / 20)) / len(freq)
            fade = np.concatenate((np.linspace(0, 0, int(fs*1)), np.linspace(0, 1, int(fs*1))), axis=0)
            samples[:len(fade)] *= fade

            freq_name = str(freq[0]) if len(freq)==1 else '+'.join([str(f) for f in freq])
            save_wav(f'wav/{fs//1000}k', f'{freq_name} @ {round(dB,2)}.wav', fs, samples)

t_end = time.time_ns()
print(f'done. CPU time {(t_end - t_begin) / 1e9} seconds')
