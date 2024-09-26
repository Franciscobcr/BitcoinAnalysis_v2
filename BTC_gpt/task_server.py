import schedule
import time
import pytz
from datetime import datetime, timedelta
from chatbot_v3 import Conversation
from database_setting import insert_actual_bitcoin_data, connect_to_db
from exec_script import get_bitcoin_price_and_variation
import pandas as pd
import threading
import json
import re

brazil_tz = pytz.timezone('America/Sao_Paulo')

def run_conversation():
    ai_response = Conversation()
    response = ai_response.send()
    save_gpt_analysis(response)
    print(f"Análise GPT executada em {datetime.now(brazil_tz)}")

def update_bitcoin_data():
    data = get_bitcoin_price_and_variation()
    
    # Verifique se o retorno é uma string e precisa ser processado
    if isinstance(data, str):
        # Usar regex para extrair os valores de 'price', 'var_30d', 'var_14d' e 'var_7d'
        price_match = re.search(r"Preço atual do Bitcoin: \$([0-9,.]+)", data)
        var_30d_match = re.search(r"Variação nos últimos 30 dias: ([0-9,.]+)%", data)
        var_14d_match = re.search(r"Variação nos últimos 14 dias: ([0-9,.]+)%", data)
        var_7d_match = re.search(r"Variação nos últimos 7 dias: ([0-9,.]+)%", data)
        
        # Certifique-se de que as correspondências foram encontradas antes de prosseguir
        if price_match and var_30d_match and var_14d_match and var_7d_match:
            data = {
                'price': float(price_match.group(1).replace(',', '')),
                'var_30d': float(var_30d_match.group(1).replace(',', '')),
                'var_14d': float(var_14d_match.group(1).replace(',', '')),
                'var_7d': float(var_7d_match.group(1).replace(',', ''))
            }
        else:
            print("Erro ao processar os dados da string.")
            return
    else:
        print("Erro: O objeto data não é uma string.")

    save_bitcoin_data(data)
    print(f"Dados do Bitcoin atualizados em {datetime.now(brazil_tz)}")

def update_operation_data():
    connection = connect_to_db()
    query = """
    SELECT 
        prediction_date,
        AVG("Risk_return") as avg_risk_return
    FROM 
        chatbot_data
    WHERE 
        actual_date IS NOT NULL
    GROUP BY 
        prediction_date
    ORDER BY 
        prediction_date
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    save_operation_data(df)
    print(f"Dados de operação atualizados em {datetime.now(brazil_tz)}")

def calculate_bitcoin_returns():
    connection = connect_to_db()
    query = """
    SELECT 
        DATE(datetime) as date,
        BTC_close
    FROM 
        chatbot_data
    ORDER BY 
        datetime
    """
    btc_df = pd.read_sql_query(query, connection)
    connection.close()
    
    btc_df['return'] = btc_df['BTC_close'].pct_change()
    btc_df = btc_df.groupby('date')['return'].mean().reset_index()
    btc_df['cumulative_return'] = (1 + btc_df['return']).cumprod() - 1
    
    save_bitcoin_returns(btc_df)
    print(f"Retornos do Bitcoin calculados em {datetime.now(brazil_tz)}")

def save_gpt_analysis(analysis):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO gpt_analysis (timestamp, analysis)
    VALUES (%s, %s)
    """, (datetime.now(brazil_tz), analysis))
    connection.commit()
    connection.close()

def save_bitcoin_data(data):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO bitcoin_data (timestamp, price, var_30d, var_14d, var_7d)
    VALUES (%s, %s, %s, %s, %s)
    """, (datetime.now(brazil_tz), data['price'], data['var_30d'], data['var_14d'], data['var_7d']))
    connection.commit()
    connection.close()

def save_operation_data(df):
    connection = connect_to_db()
    df.to_sql('operation_data', connection, if_exists='replace', index=False)
    connection.close()

def save_bitcoin_returns(df):
    connection = connect_to_db()
    df.to_sql('bitcoin_returns', connection, if_exists='replace', index=False)
    connection.close()

def schedule_next_run(task, scheduled_time):
    now = datetime.now(brazil_tz)
    next_run = now.replace(hour=scheduled_time.hour, minute=scheduled_time.minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    delay = (next_run - now).total_seconds()
    threading.Timer(delay, task).start()
    print(f"Próxima execução de {task.__name__} agendada para {next_run}")

if __name__ == "__main__":
    schedule_next_run(run_conversation, datetime.now(brazil_tz).replace(hour=21, minute=0))
    schedule_next_run(insert_actual_bitcoin_data, datetime.now(brazil_tz).replace(hour=21, minute=5))

    schedule.every().hour.do(update_operation_data)
    schedule.every().hour.do(calculate_bitcoin_returns)

    schedule.every().minute.do(update_bitcoin_data)

    print(f"Servidor de tarefas iniciado. (Horário de Brasília: {datetime.now(brazil_tz)})")
    while True:
        schedule.run_pending()
        time.sleep(1)
