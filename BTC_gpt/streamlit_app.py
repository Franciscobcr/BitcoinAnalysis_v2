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
import numpy as np
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Configurações da página
os.environ["TOKENIZERS_PARALLELISM"] = "false"
st.set_page_config(page_title="GPT_BTC", page_icon="🪙", layout="centered")
brazil_tz = pytz.timezone('America/Sao_Paulo')

def format_time(dt):
    return dt.strftime('%H:%M:%S')

def get_bitcoin_data(limit):
    connection = connect_to_db()
    query = f"""
    SELECT 
        datetime as timestamp,
        btc_close as price
    FROM chatbot_data
    WHERE btc_close IS NOT NULL
    ORDER BY datetime DESC
    LIMIT {limit}
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    if not df.empty:
        return df
    return None

def get_bitcoin_returns(analysis_date):
    # Converter a data de análise para o formato necessário
    analysis_date_str = analysis_date.strftime("%d-%m-%Y")
    
    # Calcular a data do dia anterior
    previous_date = analysis_date - timedelta(days=1)
    previous_date_str = previous_date.strftime("%d-%m-%Y")
    
    # Fazer a chamada à API do CoinGecko
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={analysis_date_str}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        current_price = data['market_data']['current_price']['usd']
        
        # Obter o preço do dia anterior
        url_previous = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={previous_date_str}"
        response_previous = requests.get(url_previous)
        
        if response_previous.status_code == 200:
            data_previous = response_previous.json()
            previous_price = data_previous['market_data']['current_price']['usd']
            
            # Calcular o retorno
            daily_return = (current_price - previous_price) / previous_price
            
            return pd.DataFrame({
                'date': [analysis_date],
                'price': [current_price],
                'daily_return': [daily_return],
                'cumulative_return': [daily_return]  # Para um dia, é o mesmo que o retorno diário
            })
    
    # Se algo der errado, retornar um DataFrame vazio
    return pd.DataFrame(columns=['date', 'price', 'daily_return', 'cumulative_return'])

def get_operation_data():
    connection = connect_to_db()
    query = """
    SELECT 
        prediction_date,
        risk_return
    FROM 
        chatbot_data
    WHERE 
        actual_date IS NOT NULL
        AND risk_return IS NOT NULL
        AND TRIM(risk_return) != ''
    ORDER BY 
        prediction_date
    """
    df = pd.read_sql_query(query, connection)
    connection.close()
    
    def process_risk_return(value):
        value = str(value).strip()
        if ':' in value:
            parts = value.split(':')
            if len(parts) == 2:
                try:
                    return float(parts[1].replace(',', '.')) / float(parts[0].replace(',', '.'))
                except ValueError:
                    return np.nan
        else:
            try:
                return float(value.replace(',', '.'))
            except ValueError:
                return np.nan
    
    df['avg_risk_return'] = df['risk_return'].apply(process_risk_return)
    df = df.groupby('prediction_date')['avg_risk_return'].mean().reset_index()
    
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
    if data is not None and not data.empty:
        col1, col2 = st.columns(2)
        
        latest_price = data['price'].iloc[-1]
        latest_timestamp = data['timestamp'].iloc[-1]
        
        col1.metric(label="Preço atual", value=f"${latest_price:,.2f}", delta=None)
        col2.metric(label="Data da última atualização", value=latest_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        
        if len(data) >= 1:
            col1, col2, col3 = st.columns(3)
            
            var_1d = ((latest_price / data['price'].iloc[-2]) - 1) * 100 if len(data) >= 2 else None
            var_7d = ((latest_price / data['price'].iloc[0]) - 1) * 100 if len(data) >= 7 else None
            var_total = ((latest_price / data['price'].iloc[0]) - 1) * 100
            
            col1.metric(label="Variação 24h", value=f"{var_1d:.2f}%" if var_1d is not None else "N/A")
            col2.metric(label="Variação 7 dias", value=f"{var_7d:.2f}%" if var_7d is not None else "N/A")
            col3.metric(label=f"Variação total ({len(data)} registros)", value=f"{var_total:.2f}%")
        else:
            st.info("Não há dados históricos suficientes para calcular variações de preço.")
    else:
        st.error("Não foi possível obter dados do Bitcoin.")

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

bitcoin_data = get_bitcoin_data(30)
if bitcoin_data is not None:
    display_bitcoin_data(bitcoin_data)
else:
    st.error("Dados do Bitcoin não disponíveis no momento.")

display_next_updates()


def display_comparison_graph(operation_data, btc_returns):
    st.header("Comparação de Rentabilidade")
    
    #st.write("Debug Info:")
    #st.write(f"Operation Data: {operation_data.to_dict('records')}")
    #st.write(f"BTC Returns: {btc_returns.to_dict('records')}")
    
    fig = go.Figure()

    # Add trace for operation data
    if not operation_data.empty:
        fig.add_trace(go.Scatter(
            x=operation_data['prediction_date'], 
            y=operation_data['avg_risk_return'], 
            mode='markers+lines', 
            name='Rentabilidade das Operações'
        ))

    # Add trace for Bitcoin returns
    if not btc_returns.empty:
        # Remove NaN values
        btc_returns_clean = btc_returns.dropna()
        fig.add_trace(go.Scatter(
            x=btc_returns_clean['date'], 
            y=btc_returns_clean['cumulative_return'], 
            mode='markers+lines', 
            name='Rentabilidade do Bitcoin'
        ))

    fig.update_layout(
        title='Comparação de Rentabilidade: Operações vs Bitcoin',
        xaxis_title='Data',
        yaxis_title='Retorno Cumulativo',
        showlegend=True
    )

    # Adjust y-axis to show both datasets clearly
    y_min = min(operation_data['avg_risk_return'].min() if not operation_data.empty else 0,
                btc_returns_clean['cumulative_return'].min() if not btc_returns_clean.empty else 0)
    y_max = max(operation_data['avg_risk_return'].max() if not operation_data.empty else 0,
                btc_returns_clean['cumulative_return'].max() if not btc_returns_clean.empty else 0)
    y_range = y_max - y_min
    fig.update_yaxes(range=[y_min - 0.1 * y_range, y_max + 0.1 * y_range])

    st.plotly_chart(fig)

    st.write(f"Número de registros de operações: {len(operation_data)}")
    st.write(f"Número de registros de retornos do Bitcoin: {len(btc_returns)}")

# Usage
operation_data = get_operation_data()
btc_returns = get_bitcoin_returns()
display_comparison_graph(operation_data, btc_returns)

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