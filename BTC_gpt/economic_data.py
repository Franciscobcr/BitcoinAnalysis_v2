import os
from datetime import datetime, timedelta
import yfinance as yf
import Fred
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class economic_data:
    
    def __init__(self):
        self.fred = Fred(api_key=os.getenv('API_fred'))
        self.economic_news = self.economic_news().analysis
        
    def cpi_data(self):
        #(indicador: 'CPIAUCSL')
        cpi_data = self.fred.get_series('CPIAUCSL')
        cpi_latest = cpi_data.iloc[-1]
        cpi_previous = cpi_data.iloc[-2]

        return(f"Valor mais recente do CPI (Fed): {cpi_latest}, Valor anterior do CPI (Fed): {cpi_previous}")

    def pce_data(self):
        # (indicador: 'PCE')
        pce_data = self.fred.get_series('PCE')

        pce_latest = pce_data.iloc[-1]  
        pce_previous = pce_data.iloc[-2] 

        return (f"Valor mais recente do PCE (Fed): {pce_latest}, Valor anterior do PCE (Fed): {pce_previous}")
    
    def pib_data(self):
        # Captura os dados do PIB dos EUA
        pib_series = self.fred.get_series('GDPC1')  # 'GDPC1' é a série para PIB real dos EUA

        # Pegue os últimos 2 valores de PIB (trimestrais)
        pib_ultimos_dois = pib_series.tail(2)

        return pib_ultimos_dois
    
    def indice_data(data, nome_indice):
        # Coletar os dados mais recentes
        ultimo_dado = data.tail(1)

        # Extração dos valores relevantes
        close = ultimo_dado['Close'].values[0]
        ma20 = ultimo_dado['MA20'].values[0]
        rsi = ultimo_dado['RSI'].values[0]
        bb_upper = ultimo_dado['BB_Upper'].values[0]
        bb_lower = ultimo_dado['BB_Lower'].values[0]

        # Análise do movimento de preço com base na MA20
        if close > ma20:
            tendencia = "alta"
        elif close < ma20:
            tendencia = "baixa"
        else:
            tendencia = "lateralizado"

        if rsi < 30:
            rsi_analise = "sobrevendido"
        elif rsi > 70:
            rsi_analise = "sobrecomprado"
        else:
            rsi_analise = "neutro"

        # Análise da posição do preço em relação às Bandas de Bollinger
        if close > bb_upper:
            bollinger_analise = "rompeu a banda superior"
        elif close < bb_lower:
            bollinger_analise = "rompeu a banda inferior"
        else:
            bollinger_analise = "dentro das bandas"

        # Montar a análise textual
        analise = f"""
        O índice {nome_indice} está atualmente em uma tendência de {tendencia}, com o preço de fechamento em {close:.2f} e a média móvel de 20 dias em {ma20:.2f}.
        O RSI indica que o mercado está {rsi_analise} com um valor de {rsi:.2f}.
        O preço está {bollinger_analise}, o que sugere que o mercado está {('em possível continuidade da tendência de alta' if bollinger_analise == 'rompeu a banda superior' else 'dentro de condições normais')}.
        """
        return analise

    def analyze_indice(self):
            # Análise para o S&P 500
        analise_sp500_texto = self.indice_data(analise_sp500, "S&P 500")

        # Análise para o Nasdaq
        analise_nasdaq_texto = self.indice_data(analise_nasdaq, "Nasdaq")

        # Exibir as análises
        print(f"Análise S&P 500: {analise_sp500_texto} \nAnálise Nasdaq: {analise_nasdaq_texto}")
        
    class economic_news:
        def __init__(self):
            self.api_news = os.getenv('API_news')
        
        def get_news(self,query):
            url = f"https://newsapi.org/v2/everything?q={query}&from=2024-08-14&sortBy=publishedAt&apiKey={self.api_news}"
            try:
                response = requests.get(url)
                response.raise_for_status() 
                data = response.json()

                if data["status"] == "ok" and data["totalResults"] > 0:
                    return data["articles"]
                else:
                    return []

            except requests.exceptions.RequestException as e:
                return f"Erro ao buscar notícias: {e}"

        def create_news_df(self, subject):
            news_list = self.get_news(subject)
            
            if len(news_list) > 0:
                df = pd.DataFrame(news_list)
                df = df[['source', 'title', 'description', 'publishedAt']] 
                df['source'] = df['source'].apply(lambda x: x['name']) 
                return df
            else:
                return pd.DataFrame() 
            
        def analyze_news(self):
            pass
        
    def gold_correlation(self, ticker='BTC-USD'):
        def get_data(ticker, start_date, end_date):
            data = yf.download(ticker, start=start_date, end=end_date)
            return data['Close']

        # Definir o período de análise (últimos 30 dias a partir da data atual)
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        ticker_data = get_data(ticker, start_date, end_date)
        gold_data = get_data('GC=F', start_date, end_date) 

        df = pd.DataFrame({ticker: ticker_data, 'Gold': gold_data})
        df = df.dropna()

        correlacao_xau_ticker = df.corr().loc[ticker, 'Gold']
        return f"Correlação entre {ticker} e Ouro nos últimos 30 dias: {correlacao_xau_ticker}"
        
    
        
    