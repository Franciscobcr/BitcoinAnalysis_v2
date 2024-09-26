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
        value_btc as price
    FROM chatbot_data
    WHERE value_btc IS NOT NULL
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
    
def get_operation_data(connection):
    query = """
    SELECT 
        prediction_date,
        actual_date,
        btc_open,
        btc_high,
        btc_low,
        btc_close,
        stop_loss,
        take_profit,
        recommendation
    FROM 
        chatbot_data
    WHERE 
        actual_date IS NOT NULL
        AND stop_loss IS NOT NULL
        AND take_profit IS NOT NULL
        AND recommendation IS NOT NULL
    ORDER BY 
        prediction_date
    """
    df = pd.read_sql_query(query, connection)
    
    # Convert date columns to datetime
    df['prediction_date'] = pd.to_datetime(df['prediction_date'])
    df['actual_date'] = pd.to_datetime(df['actual_date'])
    
    # Calculate returns
    df['return'] = 0.0
    for i in df.index:
        if df.loc[i, 'recommendation'] == 'Compra':
            if df.loc[i, 'btc_high'] >= df.loc[i, 'take_profit']:
                df.loc[i, 'return'] = (df.loc[i, 'take_profit'] - df.loc[i, 'btc_open']) / df.loc[i, 'btc_open']
            elif df.loc[i, 'btc_low'] <= df.loc[i, 'stop_loss']:
                df.loc[i, 'return'] = (df.loc[i, 'stop_loss'] - df.loc[i, 'btc_open']) / df.loc[i, 'btc_open']
            else:
                df.loc[i, 'return'] = (df.loc[i, 'btc_close'] - df.loc[i, 'btc_open']) / df.loc[i, 'btc_open']
        elif df.loc[i, 'recommendation'] == 'Venda':
            if df.loc[i, 'btc_low'] <= df.loc[i, 'take_profit']:
                df.loc[i, 'return'] = (df.loc[i, 'btc_open'] - df.loc[i, 'take_profit']) / df.loc[i, 'btc_open']
            elif df.loc[i, 'btc_high'] >= df.loc[i, 'stop_loss']:
                df.loc[i, 'return'] = (df.loc[i, 'btc_open'] - df.loc[i, 'stop_loss']) / df.loc[i, 'btc_open']
            else:
                df.loc[i, 'return'] = (df.loc[i, 'btc_open'] - df.loc[i, 'btc_close']) / df.loc[i, 'btc_open']
    
    df['cumulative_return'] = (1 + df['return']).cumprod() - 1
    return df

def get_bitcoin_returns(connection):
    query = """
    SELECT 
        DATE(datetime) as date,
        btc_open,
        btc_close
    FROM 
        chatbot_data
    WHERE
        btc_open IS NOT NULL AND btc_close IS NOT NULL
    ORDER BY 
        datetime
    """
    df = pd.read_sql_query(query, connection)
    df['date'] = pd.to_datetime(df['date'])
    
    df['return'] = (df['btc_close'] - df['btc_open']) / df['btc_open']
    df['cumulative_return'] = (1 + df['return']).cumprod() - 1
    return df

def display_comparison_graph(operation_data, btc_returns):
    st.header("Comparação de Rentabilidade")
    
    fig = go.Figure()

    if not operation_data.empty:
        fig.add_trace(go.Scatter(
            x=operation_data['prediction_date'], 
            y=operation_data['cumulative_return'] * 100, 
            mode='markers+lines', 
            name='Rentabilidade das Operações'
        ))

    if not btc_returns.empty:
        fig.add_trace(go.Scatter(
            x=btc_returns['date'], 
            y=btc_returns['cumulative_return'] * 100, 
            mode='markers+lines', 
            name='Rentabilidade do Bitcoin'
        ))

    fig.update_layout(
        title='Comparação de Rentabilidade: Operações vs Bitcoin',
        xaxis_title='Data',
        yaxis_title='Retorno Cumulativo (%)',
        showlegend=True
    )

    y_min = min(operation_data['cumulative_return'].min() if not operation_data.empty else 0,
                btc_returns['cumulative_return'].min() if not btc_returns.empty else 0) * 100
    y_max = max(operation_data['cumulative_return'].max() if not operation_data.empty else 0,
                btc_returns['cumulative_return'].max() if not btc_returns.empty else 0) * 100
    y_range = y_max - y_min
    fig.update_yaxes(range=[y_min - 0.1 * y_range, y_max + 0.1 * y_range])

    st.plotly_chart(fig)

    st.write(f"Número de registros de operações: {len(operation_data)}")
    st.write(f"Número de registros de retornos do Bitcoin: {len(btc_returns)}")

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

def display_bitcoin_data():
    # Fetch Bitcoin data from CoinGecko API
    url = "https://api.coingecko.com/api/v3/coins/bitcoin"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract relevant information
        current_price = data['market_data']['current_price']['usd']
        market_cap = data['market_data']['market_cap']['usd']
        total_volume = data['market_data']['total_volume']['usd']
        price_change_24h = data['market_data']['price_change_percentage_24h']
        price_change_7d = data['market_data']['price_change_percentage_7d']
        price_change_30d = data['market_data']['price_change_percentage_30d']
        
        # Helper function to create color-coded delta strings with arrows
        def format_delta(value):
            color = "green" if value > 0 else "red"
            arrow = "↑" if value > 0 else "↓"
            return f"<span style='color: {color};'>{value:.2f}% {arrow}</span>"
        
        # Display data
        col1, col2 = st.columns(2)
        
        col1.metric(label="Preço Atual", value=f"${current_price:,.2f}", 
                    delta=price_change_24h,
                    delta_color="normal")
        col2.metric(label="Capitalização de Mercado", value=f"${market_cap:,.0f}")
        
        col1, col2, col3 = st.columns(3)
        
        col1.markdown(f"**Variação 24h**\n{format_delta(price_change_24h)}", unsafe_allow_html=True)
        col2.markdown(f"**Variação 7d**\n{format_delta(price_change_7d)}", unsafe_allow_html=True)
        col3.markdown(f"**Variação 30d**\n{format_delta(price_change_30d)}", unsafe_allow_html=True)
        
        # Fetch historical data to calculate median volume
        historical_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30&interval=daily"
        historical_response = requests.get(historical_url)
        if historical_response.status_code == 200:
            historical_data = historical_response.json()
            volumes = [v[1] for v in historical_data['total_volumes']]
            median_volume = sorted(volumes)[len(volumes)//2]
        
            volume_color = "red" if total_volume < median_volume else "green"
            volume_arrow = "↓" if total_volume < median_volume else "↑"
        
            st.markdown("**Volume de Negociação 24h**")
            st.markdown(f"${total_volume:,.0f}")
            st.markdown(
                f"<span style='color: {volume_color};'>Mediana 30d: ${median_volume:,.0f} {volume_arrow}</span>",
                unsafe_allow_html=True
            )
        else:
            st.metric(label="Volume de Negociação 24h", value=f"${total_volume:,.0f}")
            st.warning("Não foi possível calcular o volume médio.")
        
        # Additional data
        st.subheader("Informações Adicionais")
        col1, col2 = st.columns(2)
        col1.write(f"Máxima Histórica: ${data['market_data']['ath']['usd']:,.2f}")
        
        # Last updated timestamp
        last_updated = datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
        st.write(f"Última Atualização: {last_updated.strftime('%d/%m/%Y %H:%M:%S')} UTC")
    else:
        st.error("Falha ao obter dados do Bitcoin da API CoinGecko.")

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

st.write("## Dados do Bitcoin")
if bitcoin_data is not None:
    display_bitcoin_data()
else:
    st.error("Dados do Bitcoin não disponíveis no momento.")

display_next_updates()

connection = connect_to_db()
operation_data = get_operation_data(connection)
btc_returns = get_bitcoin_returns(connection)
connection.close()
display_comparison_graph(operation_data, btc_returns)

st.header("Última Análise GPT")
gpt_analysis = get_gpt_analysis()
if gpt_analysis is not None:
    st.text(f"Última análise realizada em: {gpt_analysis['datetime']}")
    
    col1, col2 = st.columns(2)
    col1.metric("Recomendação", gpt_analysis['recommendation'].strip())
    col2.metric("Taxa de Confiança", f"{gpt_analysis['trust_rate']:.2f}%")
    
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