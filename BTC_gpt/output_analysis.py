import pandas as pd
from openai import OpenAI
import streamlit as st
from datetime import datetime, timedelta
import os
import requests

client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

def get_bitcoin_price_and_variation(base_date):
    base_url = "https://api.coingecko.com/api/v3"

    # Converte a data base para o formato correto
    base_date = datetime.strptime(base_date, '%Y-%m-%d %H:%M:%S')

    # Endpoint para o preço atual do Bitcoin
    price_url = f"{base_url}/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(price_url)
    data = response.json()
    current_price = data['bitcoin']['usd']

    def get_variation(date):
        market_data_url = f"{base_url}/coins/bitcoin/history?date={date.strftime('%d-%m-%Y')}"
        response = requests.get(market_data_url)
        historical_data = response.json()
        historical_price = historical_data['market_data']['current_price']['usd']
        variation = ((current_price - historical_price) / historical_price) * 100
        return variation

    # Cálculo das variações a partir da data base
    variation_7d = get_variation(base_date + timedelta(days=7))

    return (
        f"Preço atual do Bitcoin: ${current_price:.2f}\n"
        f"Variação nos últimos 7 dias: {variation_7d:.2f}%"
    )
    
def analisar_previsao(previsao, data_selecionada):
    prompt = f"""
    Você é uma IA especialista em análise de previsões de Bitcoin. Sua tarefa é comparar a previsão feita há uma semana com o dado atual, avaliando se a previsão foi assertiva ou não.

    Esse é o preço atual do Bitcoin e o histórico de variação (foque nos últimos 7 dias):
    {get_bitcoin_price_and_variation(data_selecionada)}

    Siga o formato abaixo para sua resposta:

    1. **Previsão da LLM:** (alta, baixa ou lateralização)
    2. **Stop Loss e Take Profit:** (detalhe os níveis estabelecidos)
    3. **Nível de confiabilidade da previsão:** (indique o nível de confiança que a IA informou na previsão)

    ### Resultado:
    - Indique se a previsão foi **correta**, **incorreta** ou se a operação ainda está **em andamento**.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"{prompt}"},
            {"role": "user", "content": previsao}
        ]
    )

    return response.choices[0].message.content

def processar_previsoes_por_data(data_selecionada):
    df = pd.read_excel('chatbot_data.xlsx', sheet_name='chatbot_analysis_data')
    df['date_time'] = pd.to_datetime(df['date_time'])
    analises = []

    for index, row in df.iterrows():
        if row['date_time'] == data_selecionada:
            previsao = row['response']
            analise = analisar_previsao(previsao, data_selecionada)
            analises.append(analise) 

    df['analise_gpt'] = analises
    df.to_csv('analise_previsoes.csv', index=False)

    return analises

def obter_datas_disponiveis():
    df = pd.read_excel('chatbot_data.xlsx', sheet_name='chatbot_analysis_data')
    df['date_time'] = pd.to_datetime(df['date_time'])
    datas_disponiveis = df['date_time'].dt.strftime('%Y-%m-%d %H:%M:%S').unique()
    return datas_disponiveis