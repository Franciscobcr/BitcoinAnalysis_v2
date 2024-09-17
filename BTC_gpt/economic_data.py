import os
from datetime import datetime, timedelta, timezone
import yfinance as yf
from fredapi import Fred 
import ta 
import requests
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from newsapi import NewsApiClient
from dotenv import load_dotenv



load_dotenv()

class economic_dt:
    
    def __init__(self):
        self.fred = Fred(api_key=os.getenv('API_fred'))
        self.economic_news = self.economic_news()
        
    def cpi_data(self):
        #(indicador: 'CPIA56rr566666dCSL')
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
    

    def indice_data(self, data, nome_indice):
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

    def fetch_data(self, ticker):
        # Baixar os dados de mercado do Yahoo Finance para o último mês com intervalos de 30 minutos
        data = yf.download(ticker, period="1mo", interval="30m")

        # Calcular os indicadores técnicos
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        bb = ta.volatility.BollingerBands(data['Close'], window=20, window_dev=2)
        data['BB_Upper'] = bb.bollinger_hband()
        data['BB_Lower'] = bb.bollinger_lband()

        return data.dropna()  # Remove linhas com dados faltantes

    def analyze_indice(self):
        # Capturar os dados reais do S&P 500 e Nasdaq
        analise_sp500 = self.fetch_data("^GSPC")  # S&P 500
        analise_nasdaq = self.fetch_data("^IXIC")  # Nasdaq

        # Análise para o S&P 500
        analise_sp500_texto = self.indice_data(analise_sp500, "S&P 500")

        # Análise para o Nasdaq
        analise_nasdaq_texto = self.indice_data(analise_nasdaq, "Nasdaq")

        # Exibir as análises
        print(f"Análise S&P 500: {analise_sp500_texto} \nAnálise Nasdaq: {analise_nasdaq_texto}")

import os
from datetime import datetime, timedelta
import yfinance as yf
from fredapi import Fred
import ta
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from newsapi import NewsApiClient
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class economic_dt:
    
    def __init__(self):
        self.fred = Fred(api_key=os.getenv('API_fred'))
        self.economic_news = self.economic_news()

    def cpi_data(self):
        cpi_data = self.fred.get_series('CPIAUCSL')
        cpi_latest = cpi_data.iloc[-1]
        cpi_previous = cpi_data.iloc[-2]

        return f"Valor mais recente do CPI (Fed): {cpi_latest}, Valor anterior do CPI (Fed): {cpi_previous}"

    def pce_data(self):
        pce_data = self.fred.get_series('PCE')
        pce_latest = pce_data.iloc[-1]
        pce_previous = pce_data.iloc[-2]

        return f"Valor mais recente do PCE (Fed): {pce_latest}, Valor anterior do PCE (Fed): {pce_previous}"
    
    def pib_data(self):
        pib_series = self.fred.get_series('GDPC1')
        pib_ultimos_dois = pib_series.tail(2)
        return pib_ultimos_dois
    
    def indice_data(self, data, nome_indice):
        ultimo_dado = data.tail(1)
        close = ultimo_dado['Close'].values[0]
        ma20 = ultimo_dado['MA20'].values[0]
        rsi = ultimo_dado['RSI'].values[0]
        bb_upper = ultimo_dado['BB_Upper'].values[0]
        bb_lower = ultimo_dado['BB_Lower'].values[0]

        tendencia = "alta" if close > ma20 else "baixa" if close < ma20 else "lateralizado"
        rsi_analise = "sobrevendido" if rsi < 30 else "sobrecomprado" if rsi > 70 else "neutro"
        bollinger_analise = "rompeu a banda superior" if close > bb_upper else "rompeu a banda inferior" if close < bb_lower else "dentro das bandas"

        analise = f"""
        O índice {nome_indice} está atualmente em uma tendência de {tendencia}, com o preço de fechamento em {close:.2f} e a média móvel de 20 dias em {ma20:.2f}.
        O RSI indica que o mercado está {rsi_analise} com um valor de {rsi:.2f}.
        O preço está {bollinger_analise}, o que sugere que o mercado está {'em possível continuidade da tendência de alta' if bollinger_analise == 'rompeu a banda superior' else 'dentro de condições normais'}.
        """
        return analise

    def fetch_data(self, ticker):
        data = yf.download(ticker, period="1mo", interval="30m")
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        bb = ta.volatility.BollingerBands(data['Close'], window=20, window_dev=2)
        data['BB_Upper'] = bb.bollinger_hband()
        data['BB_Lower'] = bb.bollinger_lband()

        return data.dropna()

    def analyze_indice(self):
        analise_sp500 = self.fetch_data("^GSPC")
        analise_nasdaq = self.fetch_data("^IXIC")

        analise_sp500_texto = self.indice_data(analise_sp500, "S&P 500")
        analise_nasdaq_texto = self.indice_data(analise_nasdaq, "Nasdaq")

        print(f"Análise S&P 500: {analise_sp500_texto} \nAnálise Nasdaq: {analise_nasdaq_texto}")

    def gold_correlation(self, ticker='BTC-USD'):
        def get_data(ticker, start_date, end_date):
            data = yf.download(ticker, start=start_date, end=end_date)
            return data['Close']

        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        ticker_data = get_data(ticker, start_date, end_date)
        gold_data = get_data('GC=F', start_date, end_date) 

        df = pd.DataFrame({ticker: ticker_data, 'Gold': gold_data})
        df = df.dropna()

        correlacao_xau_ticker = df.corr().loc[ticker, 'Gold']
        return f"Correlação entre {ticker} e Ouro nos últimos 30 dias: {correlacao_xau_ticker}"
    
    class economic_news:
        def __init__(self):
            self.api_news = os.getenv('API_news')
            self.newsapi = NewsApiClient(api_key=self.api_news)
            self.tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
            self.model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
            self.sentiment_pipeline = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)

        def get_most_relevant_news(self, query, from_date, to_date, page_size=5):
            all_articles = self.newsapi.get_everything(
                q=query,
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='relevancy',
                page_size=page_size
            )
            return all_articles['articles']

        def create_news_df(self, news_list):
            if len(news_list) > 0:
                df = pd.DataFrame(news_list)
                df = df[['source', 'title', 'description', 'publishedAt', 'url']]
                df['source'] = df['source'].apply(lambda x: x['name'])
                df['publishedAt'] = pd.to_datetime(df['publishedAt'])
                return df
            else:
                return pd.DataFrame()

        def analyze_sentiment(self, text):
            return self.sentiment_pipeline(text)[0]

        def get_top_news_of_month_with_sentiment(self, subject):
            today = datetime.today()
            one_month_ago = today - timedelta(weeks=4)

            from_date = one_month_ago.strftime('%Y-%m-%d')
            to_date = today.strftime('%Y-%m-%d')

            news_list = self.get_most_relevant_news(subject, from_date, to_date, page_size=5)
            news_df = self.create_news_df(news_list)

            if not news_df.empty:
                news_df['sentiment'] = news_df.apply(
                    lambda row: self.analyze_sentiment((row['title'] or '') + ' ' + (row['description'] or '')), axis=1
                )
                return news_df
            else:
                return pd.DataFrame()

        # Script para buscar as top 5 notícias de Bitcoin e Economia Mundial com análise de sentimentos
        def fetch_bitcoin_and_global_economy_news():
            news_analyzer = economic_dt.economic_news()

            # Top 5 notícias sobre Bitcoin
            print("\nTop 5 Notícias sobre Bitcoin:")
            bitcoin_news_df = news_analyzer.get_top_news_of_month_with_sentiment('Bitcoin')
            print(bitcoin_news_df)

            # Top 5 notícias sobre Economia Mundial
            print("\nTop 5 Notícias sobre Economia Mundial:")
            global_economy_news_df = news_analyzer.get_top_news_of_month_with_sentiment('Global Economy')
            print(global_economy_news_df)

if __name__ == "__main__":
    econ_data = economic_dt()

    # Análise dos dados econômicos
    print(econ_data.cpi_data())
    print(econ_data.pce_data())
    print(econ_data.pib_data())

    # Análise dos índices S&P 500 e Nasdaq
    econ_data.analyze_indice()

    # Correlação entre Bitcoin e Ouro
    print(econ_data.gold_correlation())

    # Análise de notícias para Bitcoin e Economia Mundial
    fetch_bitcoin_and_global_economy_news()
    

        
        
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
        
    
        
    