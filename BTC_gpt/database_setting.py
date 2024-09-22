import os
import psycopg2
from datetime import datetime, timedelta, timezone
import requests
from dotenv import load_dotenv

load_dotenv()

def connect_to_db():
    connection = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dbname=os.getenv('DB_NAME')
    )
    return connection

def create_db():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_data (
                id SERIAL PRIMARY KEY,
                datetime TIMESTAMP NOT NULL,
                prompt TEXT,
                response TEXT,
                analysis_results TEXT,
                Recommendation TEXT,
                Trust_rate NUMERIC,
                Stop_loss NUMERIC,
                Take_profit NUMERIC,
                Risk_return NUMERIC,
                BTC_high NUMERIC,
                BTC_low NUMERIC,
                BTC_close NUMERIC,
                BTC_open NUMERIC,
                prediction_date DATE,
                actual_date DATE
            )
        ''')
        connection.commit()
    connection.close()

def store_prediction(prompt, response, analysis_results):
    connection = connect_to_db()
    with connection.cursor() as cursor:
        prediction_date = datetime.now(timezone.utc).date()
        actual_date = prediction_date + timedelta(days=1)
        
        cursor.execute('''
            INSERT INTO chatbot_data (
                datetime, prompt, response, analysis_results, 
                prediction_date, actual_date
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            datetime.now(timezone.utc),
            prompt.strip().replace("\n", " "),
            response.strip().replace("\n", " "),
            analysis_results.strip().replace("\n", " "),
            prediction_date,
            actual_date
        ))
        connection.commit()
    connection.close()

def get_bitcoin_data(date):
    # URL da API do CoinGecko para dados OHLC do Bitcoin (últimas 24 horas)
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        
        if data and len(data) > 0:
            open_price = data[0][1]
            close_price = data[-1][4] 
            high_price = max(item[2] for item in data) 
            low_price = min(item[3] for item in data)
            
            print(f"Dados do Bitcoin para o dia inteiro:")
            print(f"Open: ${open_price}, High: ${high_price}, Low: ${low_price}, Close: ${close_price}")
            
            return high_price, low_price, close_price, open_price
        else:
            print("Erro: Dados OHLC do Bitcoin não disponíveis")
            return None
    
    except requests.RequestException as e:
        print(f"Erro ao buscar dados do Bitcoin: {e}")
        return None
        
def clean_up_test_data():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM chatbot_data WHERE prompt = 'Teste prompt'")
        connection.commit()
    connection.close()
    print("Dados de teste removidos.")
    
def insert_actual_bitcoin_data():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        
        btc_high, btc_low, btc_close, btc_open = get_bitcoin_data(yesterday)
        
        if all([btc_high, btc_low, btc_close, btc_open]):
            cursor.execute('''
                UPDATE chatbot_data
                SET BTC_high = %s, BTC_low = %s, BTC_close = %s, BTC_open = %s
                WHERE actual_date = %s AND BTC_high IS NULL
            ''', (btc_high, btc_low, btc_close, btc_open, yesterday))
            affected_rows = cursor.rowcount
            connection.commit()
            print(f"Dados reais do Bitcoin inseridos para {yesterday}. Linhas afetadas: {affected_rows}")
        else:
            print(f"Falha ao obter dados reais do Bitcoin para {yesterday}.")
    connection.close()