import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import re

# Função para obter o movimento do BTC entre 00:00 UTC e 23:59 UTC para a data prevista
def get_btc_movement(date):
    # Definir o período de 00:00 UTC a 23:59 UTC para o dia em questão
    start_date = date
    end_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Usar a biblioteca yfinance para obter os dados de preço do BTC a cada 1 hora
    btc_data = yf.download("BTC-USD", start=start_date, end=end_date, interval="1h")

    if btc_data.empty:
        return None

    open_price = btc_data['Open'][0]
    
    close_price = btc_data['Close'][-1]

    if close_price > open_price:
        return 'alta'
    elif close_price < open_price:
        return 'baixa'
    else:
        return 'lateral'

# Função para extrair a data da previsão a partir da resposta
def extract_date_from_response(response):
    # Extrai a data no formato 'dd/mm/yyyy' ou 'yyyy-mm-dd'
    date_match = re.search(r'(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})', response)
    if date_match:
        date_str = date_match.group(1)
        try:
            # Converte a data para o formato 'YYYY-MM-DD'
            if '/' in date_str:
                return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return None
    return None

# Função para extrair o movimento previsto a partir da resposta
def extract_predicted_movement_from_response(response):
    # Procurar pelo movimento (alta, baixa, lateral)
    movement = None
    #################################################################### alterar#####################
    if "alta" in response.lower():
        movement = 'alta'
    elif "baixa" in response.lower():
        movement = 'baixa'
    elif "lateral" in response.lower():
        movement = 'lateral'

    return movement
    #################################################################### alterar#####################
    
# Função para processar as previsões no arquivo Excel
def process_predictions():
    # Carregar o arquivo Excel, adicionando as colunas MOV_REAL e MOV_PREV se não existirem
    df = pd.read_excel('chatbot_data.xlsx', sheet_name='chatbot_analysis_data')
    
    if 'MOV_REAL' not in df.columns:
        df['MOV_REAL'] = None  
    
    if 'MOV_PREV' not in df.columns:
        df['MOV_PREV'] = None  
    for index, row in df.iterrows():
        # Verificar se MOV_REAL e MOV_PREV já estão preenchidos
        if pd.isna(row['MOV_REAL']) or pd.isna(row['MOV_PREV']):
            # Extrair a data da previsão a partir da resposta gerada pela API
            date = extract_date_from_response(row['response'])

            if date:
                # Obter o movimento real do BTC entre 00:00 e 23:59 UTC para a data da previsão
                real_movement = get_btc_movement(date)

                if real_movement:
                    # Extrair o movimento previsto
                    predicted_movement = extract_predicted_movement_from_response(row['response'])

                    # Atualizar o DataFrame com os novos dados
                    df.at[index, 'MOV_REAL'] = real_movement
                    df.at[index, 'MOV_PREV'] = predicted_movement

    # Salvar de volta no Excel
    with pd.ExcelWriter('chatbot_data.xlsx', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='chatbot_analysis_data', index=False)

