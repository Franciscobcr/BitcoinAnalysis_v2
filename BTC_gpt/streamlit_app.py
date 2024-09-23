import streamlit as st
import os
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go
from database_setting import connect_to_db
import re
from sqlalchemy import create_engine
import pandas as pd

# Configurações da página
os.environ["TOKENIZERS_PARALLELISM"] = "false"
st.set_page_config(page_title="GPT_BTC", page_icon="🪙", layout="centered")
brazil_tz = pytz.timezone('America/Sao_Paulo')

def format_time(dt):
    return dt.strftime('%H:%M:%S')

def get_bitcoin_data():
    connection = connect_to_db()
    query = """
    SELECT 
        datetime as timestamp,
        BTC_close as price,
        (SELECT AVG(BTC_close) FROM chatbot_data WHERE datetime >= NOW() - INTERVAL '30 days') as price_30d_ago,
        (SELECT AVG(BTC_close) FROM chatbot_data WHERE datetime >= NOW() - INTERVAL '14 days') as price_14d_ago,
        (SELECT AVG(BTC_close) FROM chatbot_data WHERE datetime >= NOW() - INTERVAL '7 days') as price_7d_ago
    FROM chatbot_data
    ORDER BY datetime DESC
    LIMIT 1
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    if not df.empty:
        current_price = df['price'].iloc[0]
        df['var_30d'] = (current_price - df['price_30d_ago'].iloc[0]) / df['price_30d_ago'].iloc[0] * 100
        df['var_14d'] = (current_price - df['price_14d_ago'].iloc[0]) / df['price_14d_ago'].iloc[0] * 100
        df['var_7d'] = (current_price - df['price_7d_ago'].iloc[0]) / df['price_7d_ago'].iloc[0] * 100
        return df.iloc[0]
    return None

def get_operation_data():
    connection = connect_to_db()
    df = pd.read_sql_query("SELECT * FROM operation_data", connection)
    connection.close()
    return df

def get_bitcoin_returns():
    connection = connect_to_db()
    df = pd.read_sql_query("SELECT * FROM bitcoin_returns", connection)
    connection.close()
    return df

def get_gpt_analysis():
    connection = connect_to_db()
    query = "SELECT * FROM gpt_analysis ORDER BY timestamp DESC LIMIT 1"
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df.iloc[0] if not df.empty else None

def display_bitcoin_data(data):
    st.header("Dados do Bitcoin")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Preço atual", value=f"${data['price']:,.2f}", delta=None)
    col2.metric(label="Variação 30 dias", value=f"{data['var_30d']:.2f}%", delta=f"{data['var_30d']:.2f}%")
    col3.metric(label="Variação 14 dias", value=f"{data['var_14d']:.2f}%", delta=f"{data['var_14d']:.2f}%")
    col4.metric(label="Variação 7 dias", value=f"{data['var_7d']:.2f}%", delta=f"{data['var_7d']:.2f}%")
    st.text(f"Última atualização: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

def display_next_updates():
    st.header("Próximas Atualizações")
    col1, col2, col3, col4 = st.columns(4)
    now = datetime.now(brazil_tz)
    
    col1.metric("Próxima Análise GPT", 
                format_time(now.replace(hour=21, minute=0, second=0, microsecond=0) + timedelta(days=1 if now.hour >= 21 else 0)))
    col2.metric("Próxima Inserção de Dados BTC", 
                format_time(now.replace(hour=21, minute=5, second=0, microsecond=0) + timedelta(days=1 if now.hour >= 21 else 0)))
    col3.metric("Próxima Atualização de Operações", 
                format_time((now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)))
    col4.metric("Próxima Atualização de Dados BTC", 
                format_time((now + timedelta(minutes=1)).replace(second=0, microsecond=0)))

def display_chart(operation_data, btc_data):
    st.header("Comparação de Rentabilidade")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=operation_data['prediction_date'], y=operation_data['avg_risk_return'], 
                             mode='lines', name='Rentabilidade das Operações'))
    fig.add_trace(go.Scatter(x=btc_data['date'], y=btc_data['cumulative_return'], 
                             mode='lines', name='Rentabilidade do Bitcoin'))
    fig.update_layout(title='Comparação de Rentabilidade: Operações vs Bitcoin',
                      xaxis_title='Data', yaxis_title='Retorno Cumulativo')
    st.plotly_chart(fig)

st.image("D:\downloads\WhatsApp Image 2024-09-22 at 20.44.23.jpeg", use_column_width=True)
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

bitcoin_data = get_bitcoin_data()
if bitcoin_data is not None:
    display_bitcoin_data(bitcoin_data)
else:
    st.error("Dados do Bitcoin não disponíveis no momento.")

display_next_updates()

operation_data = get_operation_data()
btc_returns = get_bitcoin_returns()
if not operation_data.empty and not btc_returns.empty:
    display_chart(operation_data, btc_returns)
else:
    st.error("Dados de rentabilidade não disponíveis no momento.")

st.header("Última Análise GPT")
gpt_analysis = get_gpt_analysis()
if gpt_analysis is not None:
    st.write(gpt_analysis['analysis'])
    st.text(f"Última análise realizada em: {gpt_analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.write("Aguardando primeira análise...")

# Atualização automática a cada 60 segundos
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0

st.session_state.update_counter += 1

if st.session_state.update_counter >= 60:
    st.session_state.update_counter = 0
    st.rerun()

st.empty().text(f"Próxima atualização em {60 - st.session_state.update_counter} segundos")