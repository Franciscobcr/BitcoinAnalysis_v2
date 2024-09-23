import streamlit as st
import os
import pandas as pd
import pytz
from datetime import datetime, timedelta
import plotly.graph_objects as go
from database_setting import connect_to_db
#from exec_script import get_bitcoin_data
import re
from sqlalchemy import create_engine
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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
        btc_close as price
    FROM chatbot_data
    WHERE btc_close IS NOT NULL
    ORDER BY datetime
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    if not df.empty:
        df['daily_return'] = df['price'].pct_change()
        df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1
        return df
    return None

def get_bitcoin_returns():
    bitcoin_data = get_bitcoin_data()
    if bitcoin_data is not None:
        return bitcoin_data[['timestamp', 'cumulative_return']].rename(columns={'timestamp': 'date'})
    return pd.DataFrame()

def get_operation_data():
    connection = connect_to_db()
    query = """
    SELECT 
        prediction_date,
        AVG(
            CASE 
                WHEN risk_return LIKE '%:%' THEN 
                    CAST(SPLIT_PART(risk_return, ':', 2) AS FLOAT) / 
                    CAST(SPLIT_PART(risk_return, ':', 1) AS FLOAT)
                WHEN risk_return ~ '^[-]?[0-9]*\.?[0-9]+$' 
                THEN CAST(risk_return AS FLOAT)
                ELSE NULL
            END
        ) as avg_risk_return
    FROM 
        chatbot_data
    WHERE 
        actual_date IS NOT NULL
        AND risk_return IS NOT NULL
        AND risk_return != ''
    GROUP BY 
        prediction_date
    ORDER BY 
        prediction_date
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    if not df.empty:
        df['cumulative_return'] = (1 + df['avg_risk_return']).cumprod() - 1
    return df

def get_bitcoin_returns():
    connection = connect_to_db()
    query = """
    SELECT 
        DATE(datetime) as date,
        btc_close
    FROM 
        chatbot_data
    WHERE
        btc_close IS NOT NULL
    ORDER BY 
        datetime
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    df['return'] = df['btc_close'].pct_change()
    df = df.groupby('date')['return'].mean().reset_index()
    df['cumulative_return'] = (1 + df['return']).cumprod() - 1
    
    return df

def get_gpt_analysis():
    connection = connect_to_db()
    query = """
    SELECT 
        datetime,
        recommendation,
        trust_rate,
        stop_loss,
        take_profit,
        risk_return
    FROM 
        chatbot_data
    WHERE 
        recommendation IS NOT NULL
        AND trust_rate IS NOT NULL
        AND stop_loss IS NOT NULL
        AND take_profit IS NOT NULL
        AND risk_return IS NOT NULL
    ORDER BY 
        datetime DESC 
    LIMIT 1
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    if not df.empty:
        result = df.iloc[0].to_dict()
        # Converter valores para float, se possível
        for col in ['trust_rate', 'stop_loss', 'take_profit']:
            if pd.notna(result[col]):
                try:
                    result[col] = float(result[col])
                except ValueError:
                    result[col] = 0.0  # ou outro valor padrão
        return result
    else:
        return None

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

st.image("image_btc.jpg", use_column_width=True)
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

if not operation_data.empty and not btc_returns.empty and len(operation_data) > 1 and len(btc_returns) > 1:
    st.header("Comparação de Rentabilidade")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=operation_data['prediction_date'], y=operation_data['cumulative_return'], 
                             mode='lines', name='Rentabilidade das Operações'))
    fig.add_trace(go.Scatter(x=btc_returns['date'], y=btc_returns['cumulative_return'], 
                             mode='lines', name='Rentabilidade do Bitcoin'))
    fig.update_layout(title='Comparação de Rentabilidade: Operações vs Bitcoin',
                      xaxis_title='Data', yaxis_title='Retorno Cumulativo')
    st.plotly_chart(fig)
else:
    st.error("Dados de rentabilidade insuficientes para gerar o gráfico.")
    st.write(f"Número de registros de operações: {len(operation_data)}")
    st.write(f"Número de registros de retornos do Bitcoin: {len(btc_returns)}")

st.header("Última Análise GPT")
gpt_analysis = get_gpt_analysis()
if gpt_analysis is not None:
    st.text(f"Última análise realizada em: {gpt_analysis['datetime']}")
    
    col1, col2 = st.columns(2)
    col1.metric("Recomendação", gpt_analysis['recommendation'].strip())
    col2.metric("Taxa de Confiança", f"{gpt_analysis['trust_rate']:.2f}")
    
    col3, col4, col5 = st.columns(3)
    col3.metric("Stop Loss", f"{gpt_analysis['stop_loss']:.2f}")
    col4.metric("Take Profit", f"{gpt_analysis['take_profit']:.2f}")
    col5.metric("Retorno de Risco", gpt_analysis['risk_return'])  # Exibindo como string
    
    # Explicação adicional do Retorno de Risco
    risk_return_parts = gpt_analysis['risk_return'].split(':')
else:
    st.write("Nenhuma análise disponível com todos os dados necessários.")

if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0

st.session_state.update_counter += 1

if st.session_state.update_counter >= 60:
    st.session_state.update_counter = 0
    st.rerun()

st.empty().text(f"Próxima atualização em {60 - st.session_state.update_counter} segundos")