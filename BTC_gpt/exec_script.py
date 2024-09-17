from derivatives2 import derivatives_data
from onchain_data import OnChain
from economic_data import economic_dt
import requests
from datetime import datetime, timedelta

def get_bitcoin_price_and_variation():
    # URL base da API do CoinGecko
    base_url = "https://api.coingecko.com/api/v3"

    # Endpoint para o preço atual do Bitcoin
    price_url = f"{base_url}/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(price_url)
    data = response.json()
    
    # Preço atual do Bitcoin
    current_price = data['bitcoin']['usd']
    
    # Função auxiliar para calcular a variação de preço
    def get_variation(days):
        date = (datetime.now() - timedelta(days=days)).strftime('%d-%m-%Y')
        market_data_url = f"{base_url}/coins/bitcoin/history?date={date}"
        response = requests.get(market_data_url)
        historical_data = response.json()
        historical_price = historical_data['market_data']['current_price']['usd']
        variation = ((current_price - historical_price) / historical_price) * 100
        return variation
    
    # Cálculo das variações
    variation_30d = get_variation(30)
    variation_14d = get_variation(14)
    variation_7d = get_variation(7)

    # Formatação e retorno do texto
    return (
        f"Preço atual do Bitcoin: ${current_price:.2f}\n"
        f"Variação nos últimos 30 dias: {variation_30d:.2f}%\n"
        f"Variação nos últimos 14 dias: {variation_14d:.2f}%\n"
        f"Variação nos últimos 7 dias: {variation_7d:.2f}%"
    )
    
def run_all_analyses():
    # Obtém o preço e variação do Bitcoin
    bitcoin_analysis = get_bitcoin_price_and_variation()
    
    # Inicializa a lista de resultados
    results = {"Bitcoin Analysis": bitcoin_analysis}
    
    # Funções da classe de dados derivativos
    deriv_data = derivatives_data()
    
    # Profundidade do mercado
    results["Market Depth Analysis"] = deriv_data.market_depth().analysis()
    
    # Liquidações
    results["Liquidations Analysis"] = deriv_data.liquidations().analysis()
    
    # Long/Short Ratio
    results["Long/Short Ratio Analysis"] = deriv_data.ls_ratio().analysis()
    
    # Funding rate vol
    results["Funding Rate Volume Analysis"] = deriv_data.fundingratevol().analysis()
    
    # Funding rate ohlc
    results["Funding Rate OHLC Analysis"] = deriv_data.funding_rate_ohlc().analysis()
    
    # oi_weight_ohlc
    results["OI Weight OHLC Analysis"] = deriv_data.oi_weight_ohlc().analysis()
    
    # oi_ohlc
    results["OI OHLC Analysis"] = deriv_data.oi_ohlc().analysis()
    
    # oi_ohlc history
    results["OI OHLC History Analysis"] = deriv_data.oi_ohlc_history().analysis()
    
    # Volume de opções
    options_vol = derivatives_data.options_volume()
    results["Options Volume Analysis"] = options_vol.analysis()
    
    # CVD
    cvd = derivatives_data.cvd_data()
    results["CVD Analysis"] = cvd.analysis()
    
    # Volume change
    vol_change = derivatives_data.volume_change()
    results["Volume Change Analysis"] = vol_change.analysis()
    
    # Skew
    skew = derivatives_data.skew()
    results["Skew Analysis"] = skew.analysis()
    
    # IV
    iv = derivatives_data.iv()
    results["IV Analysis"] = iv.analysis()
    
    # Funções da classe de dados on chain
    on_chain_volume = OnChain.on_chain_volume()
    results["On-Chain Volume Analysis"] = on_chain_volume.analysis()
    
    blockchain_data = OnChain.BlockchainData()
    results["Blockchain Data Analysis"] = blockchain_data.analysis()
    
    exchange_flow = OnChain.ExchangeFlow()
    results["Exchange Flow Analysis"] = exchange_flow.analysis()
    
    # Dados econômicos
    news_analyzer = economic_dt.economic_news()
    econ_data = economic_dt()
    
    results["CPI Data"] = econ_data.cpi_data()
    results["PCE Data"] = econ_data.pce_data()
    results["PIB Data"] = econ_data.pib_data()
    results["S&P 500 and Nasdaq Indices Analysis"] = econ_data.analyze_indice()
    
    results["Top 8 Bitcoin News"] = news_analyzer.get_top_news_of_month_with_sentiment('Bitcoin')
    results["Top 8 Global Economy News"] = news_analyzer.get_top_news_of_month_with_sentiment('Global Economy')
    results["Top 8 Global Economy News"] = news_analyzer.get_top_news_of_month_with_sentiment('US Interest Rate')
    results["Top 8 Global Economy News"] = news_analyzer.get_top_news_of_month_with_sentiment('Crypto Market')
    results["Bitcoin-Gold Correlation"] = econ_data.gold_correlation()
    
    return results