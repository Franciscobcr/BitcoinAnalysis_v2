import os
import psycopg2
from openai import OpenAI
from exec_script import run_all_analyses  
from datetime import datetime, timedelta, timezone
import schedule
import time
from compare_predict import process_predictions
from database_setting import store_prediction
import base64
from prompts import prompts

class Conversation:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
    
    def encode_image(self, image_path):
        """Encodes an image in base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def send(self, analysis_date=None):
        """Sends a message or image to OpenAI's API and stores the response and analysis results in a database."""
        if analysis_date is None:
            # Obter a data de amanhã
            analysis_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = prompt.bitcoin_analyst_prompt()
        
        messages = [{"role": "system", "content": prompt}]
        
        # Executar as análises e obter os resultados
        analysis_results = run_all_analyses()
        analysis_str = '\n'.join(f"{key}: {value}" for key, value in analysis_results.items())

        messages.append({"role": "user", "content": analysis_str})

        response = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=messages
        )
        
        answer = response.choices[0].message.content

        store_prediction(prompt, answer, analysis_str)
        
        print(answer)
        return answer

def send_tomorrow_analysis():
    conv = Conversation()
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    formatted_tomorrow = tomorrow.strftime("%Y-%m-%d")

    conv.send(analysis_date=formatted_tomorrow)

def run_daily_task():
    # Agendar a tarefa para rodar diariamente às 00:00 UTC
    schedule.every().day.at("00:00").do(send_tomorrow_analysis)

    # Loop que verifica continuamente o horário para executar a tarefa
    while True:
        schedule.run_pending()
        time.sleep(60)  # Checa a cada minuto

if __name__ == "__main__":
    run_daily_task()
    process_predictions()  # Processa as previsões
