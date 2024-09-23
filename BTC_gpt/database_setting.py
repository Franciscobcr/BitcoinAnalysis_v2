import os
import psycopg2
from datetime import datetime, timedelta, timezone
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def connect_to_db():
    """Conecta ao banco de dados PostgreSQL usando variáveis de ambiente."""
    connection = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dbname=os.getenv('DB_NAME')
    )
    return connection

def create_db():
    """Cria a tabela chatbot_data se ela ainda não existir no banco de dados."""
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

def store_prediction(prompt, response, recommendation, trust_rate, stop_loss, take_profit, risk_return, btc_high, btc_low, btc_close, btc_open, actual_date):
    """Armazena a previsão no banco de dados, incluindo o prompt e a resposta da API."""
    connection = connect_to_db()
    with connection.cursor() as cursor:
        prediction_date = datetime.now(timezone.utc).date()

        cursor.execute('''
            INSERT INTO chatbot_data (
                datetime, prompt, response, Recommendation, Trust_rate, Stop_loss, 
                Take_profit, Risk_return, BTC_high, BTC_low, BTC_close, BTC_open, 
                prediction_date, actual_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            datetime.now(timezone.utc),
            prompt,
            response,
            recommendation,
            trust_rate,
            stop_loss,
            take_profit,
            risk_return,
            btc_high,
            btc_low,
            btc_close,
            btc_open,
            prediction_date,
            actual_date
        ))
        connection.commit()
    connection.close()

def get_bitcoin_data(date):
    """Obtém dados OHLC do Bitcoin da API CoinGecko."""
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
    """Remove os dados de teste da tabela chatbot_data."""
    connection = connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM chatbot_data WHERE Recommendation = 'Teste'")
        connection.commit()
    connection.close()
    print("Dados de teste removidos.")

def insert_actual_bitcoin_data():
    """Insere dados reais do Bitcoin na tabela chatbot_data."""
    connection = connect_to_db()
    with connection.cursor() as cursor:
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        
        btc_high, btc_low, btc_close, btc_open = get_bitcoin_data(yesterday)
        
        if all([btc_high, btc_low, btc_close, btc_open]):
            cursor.execute('''
                UPDATE chatbot_data
                SET BTC_high = %s, BTC_low = %s, BTC_close = %s, BTC_open = %s
                WHERE prediction_date = %s AND BTC_high IS NULL
            ''', (btc_high, btc_low, btc_close, btc_open, yesterday))
            affected_rows = cursor.rowcount
            connection.commit()
            print(f"Dados reais do Bitcoin inseridos para {yesterday}. Linhas afetadas: {affected_rows}")
        else:
            print(f"Falha ao obter dados reais do Bitcoin para {yesterday}.")
    connection.close()
