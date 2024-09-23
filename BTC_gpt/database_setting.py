
import os
import psycopg2
from datetime import datetime, timedelta, timezone
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def connect_to_db():
    """Conecta ao banco de dados PostgreSQL usando variáveis de ambiente."""
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            dbname=os.getenv('DB_NAME')
        )
        print("Conectado ao banco de dados")  # Adiciona um print para verificar a conexão
        return connection
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def create_db():
    """Cria a tabela chatbot_data se ela ainda não existir no banco de dados."""
    connection = connect_to_db()
    if connection is None:
        print("Conexão ao banco de dados falhou. Abortando criação da tabela.")
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chatbot_data (
                    id SERIAL PRIMARY KEY,
                    datetime TIMESTAMP NOT NULL,
                    prompt TEXT,
                    response TEXT,
                    analysis_results TEXT,
                    recommendation TEXT,
                    value_btc NUMERIC,
                    trust_rate NUMERIC,
                    stop_loss NUMERIC,
                    take_profit NUMERIC,
                    risk_return NUMERIC,
                    btc_high NUMERIC,
                    btc_low NUMERIC,
                    btc_close NUMERIC,
                    btc_open NUMERIC,
                    prediction_date DATE,
                    actual_date DATE
                )
            ''')
            connection.commit()
            print("Tabela chatbot_data criada ou já existente")  # Adiciona um print para verificar a criação da tabela
    except Exception as e:
        print(f"Erro ao criar a tabela: {e}")
    finally:
        connection.close()

def store_prediction(prompt, response, recommendation, trust_rate, value_btc, stop_loss, take_profit, risk_return, btc_high, btc_low, btc_close, btc_open, actual_date):
    """Armazena a previsão no banco de dados, incluindo o prompt e a resposta da API."""
    connection = connect_to_db()
    if connection is None:
        print("Conexão ao banco de dados falhou. Abortando inserção.")
        return

    try:
        prediction_date = datetime.now(timezone.utc).date()

        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO chatbot_data (
                    datetime, prompt, response, recommendation, trust_rate, value_btc, stop_loss, 
                    take_profit, risk_return, btc_high, btc_low, btc_close, btc_open, 
                    prediction_date, actual_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                datetime.now(timezone.utc),
                prompt,
                response,
                recommendation,
                trust_rate,
                value_btc,
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
            print(f"Previsão armazenada com sucesso para {actual_date}.")
    except Exception as e:
        print(f"Erro ao inserir dados no banco de dados: {e}")
    finally:
        connection.close()

def get_bitcoin_data(date):
    """Obtém dados OHLC do Bitcoin da API CoinGecko."""
    print(f"Buscando dados do Bitcoin para a data {date}...")  # Verifica se a função está sendo chamada corretamente
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
        data = response.json()

        if data and len(data) > 0:
            open_price = data[0][1]
            close_price = data[-1][4] 
            high_price = max(item[2] for item in data)
            low_price = min(item[3] for item in data)
            
            print(f"Dados do Bitcoin para o dia: Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}")
            return high_price, low_price, close_price, open_price
        else:
            print("Erro: Dados OHLC do Bitcoin não disponíveis")
            return None, None, None, None
    
    except requests.RequestException as e:
        print(f"Erro ao buscar dados do Bitcoin: {e}")
        return None, None, None, None

def insert_actual_bitcoin_data():
    """Insere dados reais do Bitcoin na tabela chatbot_data."""
    connection = connect_to_db()
    if connection is None:
        print("Conexão ao banco de dados falhou. Abortando inserção de dados do Bitcoin.")
        return

    try:
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        
        btc_high, btc_low, btc_close, btc_open = get_bitcoin_data(yesterday)
        
        if all([btc_high, btc_low, btc_close, btc_open]):
            with connection.cursor() as cursor:
                cursor.execute('''
                    UPDATE chatbot_data
                    SET btc_high = %s, btc_low = %s, btc_close = %s, btc_open = %s
                    WHERE prediction_date = %s AND btc_high IS NULL
                ''', (btc_high, btc_low, btc_close, btc_open, yesterday))
                affected_rows = cursor.rowcount
                connection.commit()
                print(f"Dados reais do Bitcoin inseridos para {yesterday}. Linhas afetadas: {affected_rows}")
        else:
            print(f"Falha ao obter dados reais do Bitcoin para {yesterday}.")
    except Exception as e:
        print(f"Erro ao inserir dados do Bitcoin: {e}")
    finally:
        connection.close()
