import socket
import threading
import queue
import whisper
import numpy as np
import requests
import subprocess
import time
import os

# --- CONFIGURAÇÕES DE REDE ---
UDP_IP = "0.0.0.0"
UDP_PORT_IN = 5000      # Entrada (Microfone)
TCP_PORT_OUT = 5001     # Saída (Streaming de Resposta)
SAMPLE_RATE = 16000
SECRET_KEY = ""

PIPER_BINARY = "./piper_tts/piper/piper"
PIPER_MODEL = "./piper_tts/pt_BR-faber-medium.onnx"

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:1.5b"

print("Carregando Whisper na RAM...")
model_whisper = whisper.load_model("tiny")

audio_processing_queue = queue.Queue()
connected_listeners = [] 

SYSTEM_PROMPT = "Seu nome é Mander, um pequeno robô assistente. Você é fofo, curioso e prestativo. Responda com frases curtas. Não use emojis."

def ask_ollama(text):
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
            "stream": False,
            "options": {"temperature": 0.3}
        }
        r = requests.post(OLLAMA_URL, json=payload)
        return r.json()['message']['content']
    except:
        return "Erro no processamento."

def stream_audio_from_memory(text):
    """
    Gera áudio usando PIPER (Neural) + SOX (Efeito Wall-E)
    """
    global connected_listeners
    
    if not connected_listeners:
        print("Ninguém ouvindo. Texto gerado mas descartado.")
        return

    print(f"Gerando voz Neural (Piper): '{text[:30]}...'")

    # --- VOZ DE ROBÔ ---
    # echo 'texto' -> piper (gera wav limpo) -> sox (aplica efeitos)
    # Efeitos:
    #   pitch 500: Deixa a voz bem fina
    #   speed 1.1: Fala um pouco mais rápido
    #   echo ...: Adiciona um som metálico "caixa de lata"
    
    cmd = (
        f"echo '{text}' | "
        f"{PIPER_BINARY} --model {PIPER_MODEL} --output_file - | "
        f"sox -t wav - -t wav - pitch 500 speed 1.1 echo 0.8 0.88 6 0.4"
    )
    
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            
            for sock in connected_listeners:
                try:
                    sock.send(chunk)
                except:
                    pass
                    
        process.wait()
        
    except Exception as e:
        print(f"Erro no streaming: {e}")
        try:
             subprocess.run(["espeak", "-v", "pt-br", "--stdout", "Erro na voz."], stdout=subprocess.PIPE)
        except: pass

def output_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("0.0.0.0", TCP_PORT_OUT))
    server_sock.listen(5)
    print(f"Rádio ON na porta {TCP_PORT_OUT}")
    
    while True:
        client_sock, addr = server_sock.accept()
        print(f"Novo ouvinte: {addr}")
        connected_listeners.append(client_sock)

def input_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT_IN))
    print(f"Ouvindo porta {UDP_PORT_IN}")
    
    buffer = []
    silence_count = 0
    recording = False
    auth_cache = set()
    
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            client_ip = addr[0]

            if client_ip not in auth_cache:
                if data.decode(errors='ignore').strip() == f"AUTH:{SECRET_KEY}":
                    auth_cache.add(client_ip)
                    continue
                if client_ip not in auth_cache: continue

            audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            energy = np.abs(audio_chunk).mean()
            
            if energy > 0.01: 
                recording = True
                silence_count = 0
                buffer.extend(audio_chunk)
            elif recording:
                silence_count += 1
                buffer.extend(audio_chunk)
                
                if silence_count > 30: 
                    audio_processing_queue.put(np.array(buffer))
                    buffer = []
                    silence_count = 0
                    recording = False
                    
        except Exception as e:
            print(e)

def brain_processor():
    while True:
        audio_data = audio_processing_queue.get()
        if len(audio_data) < SAMPLE_RATE * 0.2: continue 
        
        try:
            result = model_whisper.transcribe(audio_data, language="pt", fp16=False)
            text = result["text"].strip()
            if not text: continue
            
            print(f"🗣️  Ouvi: {text}")
            resp = ask_ollama(text)
            print(f"🤖 Respondendo: {resp}")
            
            stream_audio_from_memory(resp)
            
        except Exception as e:
            print(f"Erro: {e}")

threading.Thread(target=output_server, daemon=True).start()
threading.Thread(target=input_receiver, daemon=True).start()
threading.Thread(target=brain_processor, daemon=True).start()

print("SISTEMA MANDER (PIPER NEURAL) ONLINE")
while True: time.sleep(1)