import os, sys, time, struct
import numpy as np
import pyaudio
import wave
from contextlib import closing

DAC_API_HINT = 'ASIO' # KS ASIO
DAC_AVOID = ['Realtek', 'Cable', 'Cam', 'NVIDIA', 'Dirac', 'Virtual']
DAC_format = pyaudio.paInt32

ADC_API_HINT = 'KS' # KS WASAPI
ADC_HINT = 'Cosmos'
ADC_fs = 384000
ADC_format = pyaudio.paInt32
ADC_BUF = 65536

out_dir = "C:/Tools"
out_name = "output.wav"
sleep_time = 0.01
ignore_tail = 0.25

RECORD_TIME = -1
wav_name = 'wav/768k/1000 @ -1.wav'
#wav_name = 'wav/705k/60+60+60+60+7000 @ -1.wav'

###############################################################################

# ADC_API_HINT = 'MME' # debug
# ADC_HINT = 'Realtek'
# ADC_fs = 44100
# ADC_format = pyaudio.paInt16

print()
audio = pyaudio.PyAudio()

print(f"API:")
api_count = audio.get_host_api_count()
for i in range(api_count):
    api = audio.get_host_api_info_by_index(i)
    print(api['name'], end=' // ')
    if DAC_API_HINT in api['name']:
        DAC_API = api
    if ADC_API_HINT in api['name']:
        ADC_API = api

print(f"\n\n{DAC_API['name']} Out:")
for d in range(0, DAC_API['deviceCount']):
    info = audio.get_device_info_by_host_api_device_index(DAC_API['index'], d)
    if (info['maxOutputChannels']) > 0:
        print(info['name'], end=' // ')
        is_good = True
        for hh in DAC_AVOID:
            if hh in info['name']:
                is_good = False
        if is_good:
            DAC_INFO = info
            break

print(f"\n\n{ADC_API['name']} In:")
for d in range(0, ADC_API['deviceCount']):
    info = audio.get_device_info_by_host_api_device_index(ADC_API['index'], d)
    if (info['maxInputChannels']) > 0:
        print(info['name'], end=' // ')
        if ADC_HINT in info['name']:
            ADC_INFO = info
            break

###############################################################################

print(f"\n### {ADC_INFO['name']} Recording ({ADC_API['name']})")

raw = []
def ADC_step(in_data, frame_count, time_info, status):
    # print(frame_count, time_info)
    raw.append(in_data)
    return (None, pyaudio.paContinue)

ADC = audio.open(format=ADC_format,
                channels=2,
                rate=ADC_fs,
                input=True,
                frames_per_buffer=ADC_BUF,
                input_device_index=ADC_INFO['index'],
                # input_host_api_specific_stream_info=wasapi_flags,
                stream_callback=ADC_step
                )
while len(raw) == 0:
    time.sleep(sleep_time)

###############################################################################

if RECORD_TIME <= 0:
    src = wave.open(wav_name, 'rb')
    print(f"\n### [{DAC_INFO['name']}] Playing ({DAC_API['name']})", wav_name, src.getsampwidth(), src.getnchannels(), src.getframerate())

    def DAC_step(in_data, frame_count, time_info, status):
        data = src.readframes(frame_count)
        if src.getnchannels() == 1:
            d2 = bytearray()
            for i in range(len(data)):
                dd = data[i*4 : i*4+4]
                d2.extend(dd + dd)
            data = bytes(d2)
        return (data, pyaudio.paContinue)

    DAC = audio.open(format=DAC_format, channels=2,
        rate=src.getframerate(), output=True, output_device_index=DAC_INFO['index'], stream_callback=DAC_step)
    while not DAC.is_active():
        time.sleep(sleep_time)
    time.sleep(sleep_time)
    while DAC.is_active():
        time.sleep(sleep_time)
else:
    time.sleep(RECORD_TIME)

ADC.stop_stream()
ADC.close()
if RECORD_TIME <= 0:
    DAC.stop_stream()
    DAC.close()
    src.close()
audio.terminate()

###############################################################################

print(f'\nWriting {out_dir}/{out_name}...')

out = wave.open(f'{out_dir}/{out_name}', 'wb')
out.setnchannels(2)
out.setsampwidth(audio.get_sample_size(ADC_format))
out.setframerate(ADC_fs)

ignore_len = int(ignore_tail / (ADC_BUF / ADC_fs)) + 1
out.writeframes(b''.join(raw[:-ignore_len]))

out.close()
