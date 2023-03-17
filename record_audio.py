import pyaudio
import wave
import threading
import queue

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()


def list_devices():
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        print(f"Device {i}: {device_info['name']}")


# Choose the input device index
input_device_index = 1


def record_audio():
    input_queue = queue.Queue()  # Queue for input events

    # Start a separate thread for input
    input_thread = threading.Thread(target=get_input, args=(input_queue,))
    input_thread.start()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=input_device_index)

    frames = []
    while True:
        data = stream.read(CHUNK)
        frames.append(data)

        # Check the input queue for input events
        try:
            if input_queue.get_nowait():
                break
        except queue.Empty:
            pass

    stream.stop_stream()
    stream.close()

    waveFile = wave.open('output.wav', 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()


def get_input(input_queue):
    # This function runs in a separate thread
    input('')  # Wait for user input
    input_queue.put(True)  # Signal to stop recording

