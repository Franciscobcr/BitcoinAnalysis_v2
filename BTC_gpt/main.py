import subprocess
import sys
import os
import time
import signal
import psutil
from datetime import datetime, timedelta, timezone

# Arquivo de controle para sinalizar a interrupção
STOP_FILE = '/tmp/stop_gpt_btc_analyzer'

def create_stop_file():
    with open(STOP_FILE, 'w') as f:
        f.write('stop')

def remove_stop_file():
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)

def should_stop():
    return os.path.exists(STOP_FILE)

def run_task_server():
    print("Iniciando o servidor de tarefas...")
    return subprocess.Popen([sys.executable, "task_server.py"])

def run_streamlit_app():
    print("Iniciando o aplicativo Streamlit...")
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

def terminate_process(process):
    if process.poll() is None:
        print(f"Terminando processo {process.pid}")
        parent = psutil.Process(process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        process.wait(timeout=10)

def signal_handler(signum, frame):
    print("Sinal de interrupção recebido. Iniciando o desligamento gracioso...")
    create_stop_file()

if __name__ == "__main__":
    # Configurar o manipulador de sinais
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Remover arquivo de parada, caso exista de uma execução anterior
    remove_stop_file()

    # Iniciar processos
    task_server_process = run_task_server()
    time.sleep(5)
    streamlit_process = run_streamlit_app()

    print("Ambos os processos foram iniciados. Para interromper, use SIGTERM ou crie o arquivo /tmp/stop_gpt_btc_analyzer")

    try:
        while not should_stop():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupção de teclado recebida.")
    finally:
        print("Iniciando processo de desligamento...")
        terminate_process(streamlit_process)
        terminate_process(task_server_process)
        remove_stop_file()

