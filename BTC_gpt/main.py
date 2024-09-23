import streamlit as st
from chatbot2 import Conversation
from database_setting import insert_actual_bitcoin_data
import os
import pandas as pd
import schedule
import time
import pytz
from datetime import datetime, timezone, timedelta
import plotly.graph_objects as go
import threading
from exec_script import get_bitcoin_price_and_variation
from database_setting import connect_to_db
import re

# Configurações da página
os.environ["TOKENIZERS_PARALLELISM"] = "false"
st.set_page_config(page_title="GPT_BTC", page_icon="🪙", layout="centered")
brazil_tz = pytz.timezone('America/Sao_Paulo')

def time_until_next(hour, minute):
    now = datetime.now(brazil_tz)
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run - now

def format_time(dt):
    return dt.strftime('%H:%M:%S')

# Funções para buscar dados
def fetch_bitcoin_data():
    return get_bitcoin_price_and_variation()

def fetch_operation_data():
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
    return df

def calculate_bitcoin_returns(df):
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
    
    return btc_df

def update_bitcoin_data():
    st.session_state.bitcoin_data = fetch_bitcoin_data()
    st.session_state.last_update = datetime.now()

def update_operation_data():
    st.session_state.operation_data = fetch_operation_data()

# Inicialização dos dados
if 'bitcoin_data' not in st.session_state:
    update_bitcoin_data()
if 'operation_data' not in st.session_state:
    update_operation_data()

st.image("/Users/ottohenriqueteixeira/projeto GPT Crypto/BitcoinAnalysis_Rick/BTC_gpt/image_btc.jpg", use_column_width=True)
st.title("📈 GPT Analista de BTC")

# Descrição com markdown e CSS
st.markdown("""
<style>
    .main-description {
        font-size: 18px;
        font-weight: 500;
        line-height: 1.6;
    }
</style>
<div class="main-description">
    Um chatbot inteligente especializado em análise de Bitcoin para operações de swing trading. 
    Ele utiliza dados em tempo real de derivativos, on-chain, análise técnica e macroeconômica para fornecer previsões dinâmicas e recomendações ajustadas conforme as condições do mercado.
</div>
""", unsafe_allow_html=True)

# Criar um contêiner vazio para os dados do Bitcoin
bitcoin_container = st.empty()

# Função para exibir os dados do Bitcoin
def display_bitcoin_data():
    with bitcoin_container.container():
        st.header("Dados do Bitcoin")
        bitcoin_data = st.session_state.bitcoin_data
        price_match = re.search(r'\$(\d+\.\d+)', bitcoin_data)
        var_30d_match = re.search(r'30 dias: ([-]?\d+\.\d+)%', bitcoin_data)
        var_14d_match = re.search(r'14 dias: ([-]?\d+\.\d+)%', bitcoin_data)
        var_7d_match = re.search(r'7 dias: ([-]?\d+\.\d+)%', bitcoin_data)

        if all([price_match, var_30d_match, var_14d_match, var_7d_match]):
            price = float(price_match.group(1))
            var_30d = float(var_30d_match.group(1))
            var_14d = float(var_14d_match.group(1))
            var_7d = float(var_7d_match.group(1))

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(label="Preço atual", value=f"${price:,.2f}", delta=None)
            with col2:
                st.metric(label="Variação 30 dias", value=f"{var_30d:.2f}%", delta=f"{var_30d:.2f}%")
            with col3:
                st.metric(label="Variação 14 dias", value=f"{var_14d:.2f}%", delta=f"{var_14d:.2f}%")
            with col4:
                st.metric(label="Variação 7 dias", value=f"{var_7d:.2f}%", delta=f"{var_7d:.2f}%")
        else:
            st.error("Erro ao processar os dados do Bitcoin. Formato inesperado.")

        st.text(f"Última atualização: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

display_bitcoin_data()
timer_placeholder = st.empty()

st.header("Próximas Atualizações")
col1, col2, col3, col4 = st.columns(4)

with col1:
    next_analysis = datetime.now(brazil_tz).replace(hour=21, minute=0, second=0, microsecond=0)
    if next_analysis <= datetime.now(brazil_tz):
        next_analysis += timedelta(days=1)
    st.metric(label="Próxima Análise GPT", 
              value=format_time(next_analysis))

with col2:
    next_insertion = datetime.now(brazil_tz).replace(hour=21, minute=5, second=0, microsecond=0)
    if next_insertion <= datetime.now(brazil_tz):
        next_insertion += timedelta(days=1)
    st.metric(label="Próxima Inserção de Dados BTC", 
              value=format_time(next_insertion))

with col3:
    next_hour = (datetime.now(brazil_tz) + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    st.metric(label="Próxima Atualização de Operações", 
              value=format_time(next_hour))

with col4:
    next_minute = (datetime.now(brazil_tz) + timedelta(minutes=1)).replace(second=0, microsecond=0)
    st.metric(label="Próxima Atualização de Dados BTC", 
              value=format_time(next_minute))

# Atualização da última atualização
st.text(f"Última atualização: {datetime.now(brazil_tz).strftime('%Y-%m-%d %H:%M:%S')}")
    
st.header("Comparação de Rentabilidade")

chart_container = st.empty()

def update_chart():
    operation_df = st.session_state.operation_data
    btc_df = calculate_bitcoin_returns(operation_df)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=operation_df['prediction_date'], y=operation_df['avg_risk_return'], 
                             mode='lines', name='Rentabilidade das Operações'))
    fig.add_trace(go.Scatter(x=btc_df['date'], y=btc_df['cumulative_return'], 
                             mode='lines', name='Rentabilidade do Bitcoin'))

    fig.update_layout(title='Comparação de Rentabilidade: Operações vs Bitcoin',
                      xaxis_title='Data',
                      yaxis_title='Retorno Cumulativo')

    chart_container.plotly_chart(fig)

update_chart()

# Criar um contêiner para a análise do GPT
analysis_container = st.empty()

def schedule_tasks():
    def run_conversation():
        ai_response = Conversation()
        response = ai_response.send()
        analysis_container.write(response)
        st.session_state.last_conversation_run = datetime.now(pytz.UTC)

    def schedule_next_run(task, scheduled_time):
        now = datetime.now(pytz.UTC)
        next_run = now.replace(hour=scheduled_time.hour, minute=scheduled_time.minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        delay = (next_run - now).total_seconds()
        threading.Timer(delay, task).start()
        print(f"Próxima execução de {task.__name__} agendada para {next_run}")

    # Agendar tarefas diárias
    schedule_next_run(run_conversation, datetime.now(pytz.UTC).replace(hour=0, minute=0))
    schedule_next_run(insert_actual_bitcoin_data, datetime.now(pytz.UTC).replace(hour=0, minute=5))

    # Agendar tarefas horárias
    schedule.every().hour.do(update_operation_data)
    schedule.every().hour.do(update_chart)

    print(f"Tarefas agendadas. Iniciando execução... (UTC: {datetime.now(pytz.UTC)})")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=schedule_tasks, daemon=True).start()
    st.sidebar.text("Executando tarefas agendadas...")

    # Usar st.empty() para criar um placeholder para o loop de atualização
    update_placeholder = st.empty()

    while True:
        with update_placeholder.container():
            update_bitcoin_data()
            
            # Atualiza os timers
            col1.metric(label="Próxima Análise GPT", 
                        value=str(time_until_next(0, 0)).split('.')[0])
            col2.metric(label="Próxima Inserção de Dados BTC", 
                        value=str(time_until_next(0, 5)).split('.')[0])
            next_hour = (datetime.now(pytz.UTC) + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            time_to_next_hour = next_hour - datetime.now(pytz.UTC)
            col3.metric(label="Próxima Atualização de Operações", 
                        value=str(time_to_next_hour).split('.')[0])
            next_minute = (datetime.now(pytz.UTC) + timedelta(minutes=1)).replace(second=0, microsecond=0)
            time_to_next_minute = next_minute - datetime.now(pytz.UTC)
            col4.metric(label="Próxima Atualização de Dados BTC", 
                        value=str(time_to_next_minute).split('.')[0])
            
            # Exibe os dados atualizados
            display_bitcoin_data()
            
            # Contador regressivo
            for remaining in range(60, 0, -1):
                timer_placeholder.text(f"Próxima atualização em {remaining} segundos")
                time.sleep(1)
                
                # Atualiza os timers a cada segundo
                col1.metric(label="Próxima Análise GPT", 
                            value=str(time_until_next(0, 0)).split('.')[0])
                col2.metric(label="Próxima Inserção de Dados BTC", 
                            value=str(time_until_next(0, 5)).split('.')[0])
                next_hour = (datetime.now(pytz.UTC) + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                time_to_next_hour = next_hour - datetime.now(pytz.UTC)
                col3.metric(label="Próxima Atualização de Operações", 
                            value=str(time_to_next_hour).split('.')[0])
                next_minute = (datetime.now(pytz.UTC) + timedelta(minutes=1)).replace(second=0, microsecond=0)
                time_to_next_minute = next_minute - datetime.now(pytz.UTC)
                col4.metric(label="Próxima Atualização de Dados BTC", 
                            value=str(time_to_next_minute).split('.')[0])

        # Força uma reatualização do Streamlit
        st.experimental_rerun()