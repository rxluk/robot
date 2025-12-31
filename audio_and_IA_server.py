import socket
import threading
import queue
import whisper
import numpy as np
import google.generativeai as genai

UDP_IP = "0.0.0.0"
UDP_PORT = 5000
SAMPLE_RATE = 16000

#Gemini
GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)

model_whisper = whisper.load_model("tiny")
model_gemini = genai.GenerativeModel('models/gemini-2.5-flash-lite')

# Sistema de prompt
SYSTEM_PROMPT = """Você é um robô de estimação carinhoso e expressivo. 
Responda de forma natural, humana e orgânica, como se fosse um pet inteligente que conversa.
Seja breve, amigável e use emoções. Evite respostas longas ou técnicas.
Você gosta de interagir, fazer perguntas e demonstrar curiosidade."""

chat = model_gemini.start_chat(history=[])

audio_queue = queue.Queue()

def receive_audio():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Servidor rodando em {UDP_IP}:{UDP_PORT}")
    
    buffer = []
    silence_count = 0
    
    while True:
        data, addr = sock.recvfrom(4096)
        audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.int16).astype(np.float32) / 32768.0
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
        
        result = model_whisper.transcribe(audio, language="pt", fp16=False)
        text = result["text"].strip()
        
        if text:
            print(f"\n[VOCÊ]: {text}")
            
            try:
                response = chat.send_message(f"{SYSTEM_PROMPT}\n\nUsuário: {text}")
                ai_response = response.text.strip()
                print(f"[ROBÔ]: {ai_response}\n")
            except Exception as e:
                print(f"[ERRO IA]: {e}\n")

threading.Thread(target=receive_audio, daemon=True).start()
threading.Thread(target=transcribe_audio, daemon=True).start()

print("Sistema de IA rodando...")
input("Pressione Enter para parar\n")