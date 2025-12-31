import socket
import threading
import queue
import whisper
import numpy as np

UDP_IP = "0.0.0.0"
UDP_PORT = 5000
SAMPLE_RATE = 16000

model = whisper.load_model("tiny")
audio_queue = queue.Queue()

def receive_audio():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Servidor rodando em {UDP_IP}:{UDP_PORT}")
    
    buffer = []
    silence_count = 0
    
    while True:
        data, addr = sock.recvfrom(4096)
        audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        buffer.extend(audio_chunk)
        
        if np.abs(audio_chunk).mean() < 0.01:
            silence_count += 1
        else:
            silence_count = 0
        
        if silence_count > 30 and len(buffer) > SAMPLE_RATE:
            audio_queue.put(np.array(buffer))
            buffer = []
            silence_count = 0

def transcribe_audio():
    while True:
        audio = audio_queue.get()
        if len(audio) < SAMPLE_RATE * 0.5:
            continue
        result = model.transcribe(audio, language="pt", fp16=False)
        text = result["text"].strip()
        if text:
            print(f">>> {text}")

threading.Thread(target=receive_audio, daemon=True).start()
threading.Thread(target=transcribe_audio, daemon=True).start()

input("Pressione Enter para parar\n")