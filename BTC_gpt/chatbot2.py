import os
import psycopg2
from openai import OpenAI
from exec_script import run_all_analyses  
from datetime import datetime, timedelta, timezone
import schedule
import time
from compare_predict import process_predictions
import base64


# Função para conectar ao banco de dados PostgreSQL no Google Cloud SQL
def connect_to_db():
    connection = psycopg2.connect(
        host=os.getenv('DB_HOST'),  # Endereço do servidor do Google Cloud SQL
        user=os.getenv('DB_USER'),  # Usuário do banco de dados
        password=os.getenv('DB_PASSWORD'),  # Senha do banco de dados
        dbname=os.getenv('DB_NAME')  # Nome do banco de dados
    )
    return connection

# Função para inicializar o banco de dados (se necessário)
def init_db():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        # Criar a tabela no banco de dados (caso não exista)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_data (
                id SERIAL PRIMARY KEY,
                date_time TIMESTAMP NOT NULL,
                prompt TEXT,
                response TEXT,
                analysis_results TEXT
            )
        ''')
        connection.commit()
    connection.close()

# Função para armazenar os dados no banco de dados PostgreSQL
def store_data(prompt, response, analysis_results):
    connection = connect_to_db()
    with connection.cursor() as cursor:
        # Obter a data/hora atual
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Formatar prompt e response
        formatted_prompt = prompt.strip().replace("\n", " ")
        formatted_response = response.strip().replace("\n", " ")
        formatted_analysis_results = analysis_results.strip().replace("\n", " ")

        # Inserir os dados no banco de dados
        cursor.execute('''
            INSERT INTO chatbot_data (date_time, prompt, response, analysis_results)
            VALUES (%s, %s, %s, %s)
        ''', (date_time, formatted_prompt, formatted_response, formatted_analysis_results))
        connection.commit()
    connection.close()

def get_current_date_time():
    now = datetime.now()
    formatted_date_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return f"Data e horário atuais: {formatted_date_time}"

class Conversation:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
        init_db()  # Inicializa o banco de dados ao criar a instância da classe
    
    def encode_image(self, image_path):
        """Encodes an image in base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def send(self, analysis_date=None):
        """Sends a message or image to OpenAI's API and stores the response and analysis results in a database."""
        if analysis_date is None:
            # Obter a data de amanhã
            analysis_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

        data = get_current_date_time()
        prompt = f"""
        ### Contexto:
        Você é um analista de investimento especializado em Bitcoin, com uma capacidade excepcional de raciocínio analítico...
        """  # Continuação do prompt (mesmo que o anterior)
        
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

        # Armazenar os dados no banco de dados com formatação aplicada
        store_data(prompt, answer, analysis_str)
        
        print(answer)
        return answer

# Função para enviar a análise do dia seguinte
def send_tomorrow_analysis():
    conv = Conversation()

    # Obter a data de amanhã
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    formatted_tomorrow = tomorrow.strftime("%Y-%m-%d")

    # Enviar a análise para a data de amanhã
    conv.send(analysis_date=formatted_tomorrow)

# Função para agendar a tarefa diária
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
