import io
import sys
import tiktoken
from derivatives2 import derivatives_data
from onchain_data import OnChain
from economic_data import economic_dt


def num_tokens_from_string(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def capture_output():
    
    output_capture = io.StringIO()
    sys.stdout = output_capture

    try:
        
        test_derivatives_data()
        test_on_chain_volume()
        test_blockchain_data()
        test_exchange_flow()
        run_all()

        
        output_text = output_capture.getvalue()

    finally:
        
        sys.stdout = sys.__stdout__

    return output_text

def test_derivatives_data():
    print("Funções da classe de dados derivativos.")
    deriv_data = derivatives_data()

    # Profundidade do mercado
    print("\nAnálise da profundidade do mercado...")
    market_depth_analysis = deriv_data.market_depth().analysis()
    print(market_depth_analysis)

    # Liquidações
    print("\nAnálise de liquidações...")
    liquidation_analysis = deriv_data.liquidations().analysis()
    print(liquidation_analysis)

    # Long/Short Ratio
    print("\nAnálise de Long/Short Ratio...")
    ls_ratio_analysis = deriv_data.ls_ratio().analysis()
    print(ls_ratio_analysis)

    # Funding rate vol
    print("\nAnálise de volume de funding rate...")
    fundingratevol_anl = deriv_data.fundingratevol().analysis()
    print(fundingratevol_anl)

    # Funding rate ohlc
    print("\nAnálise de funding_rate_ohlc...")
    funding_rate_ohlc_anl = deriv_data.funding_rate_ohlc().analysis()
    print(funding_rate_ohlc_anl)

    # oi_weight_ohlc
    print("\nAnálise de oi_weight_ohlc")
    oi_weight_ohlc_anl = deriv_data.oi_weight_ohlc().analysis()
    print(oi_weight_ohlc_anl)

    # oi_ohlc
    print("\nAnálise de oi_ohlc")
    oi_ohlc_anl = deriv_data.oi_ohlc().analysis()
    print(oi_ohlc_anl)

    # oi_ohlc_history
    print("\nAnálise de oi_ohlc history")
    oi_ohlc_history_anl = deriv_data.oi_ohlc_history().analysis()
    print(oi_ohlc_history_anl)

    # Volume de opções
    print("\nAnálise de Volume de opçoes")
    options_vol = derivatives_data.options_volume()
    options_vol_anl = options_vol.analysis()
    print(options_vol_anl)

    # CVD
    print("\nAnálise de CVD")
    cvd = derivatives_data.cvd_data()
    cvd_anl = cvd.analysis()
    print(cvd_anl)

    # Volume change
    print("\nAnálise de Volume change")
    vol_change = derivatives_data.volume_change()
    vol_change_anl = vol_change.analysis()
    print(vol_change_anl)

    # Skew
    print("\nAnálise de Options volume")
    skew = derivatives_data.skew()
    skew_anl = skew.analysis()
    print(skew_anl)

    # iv
    print("\nAnálise de IV")
    iv = derivatives_data.iv()
    iv_anl = iv.analysis()
    print(iv_anl)

# Volume onchain   
def test_on_chain_volume():
    print('Funções da classe de dados on chain.')
    print("\nAnalise de on_chain_volume")
    on_chain_volume = OnChain.on_chain_volume()
    on_chain_volume_anl = on_chain_volume.analysis()
    print(on_chain_volume_anl)

# Blockchain data
def test_blockchain_data():
    print("\nAnalise de BlockchainData")
    blockchain_data = OnChain.BlockchainData()
    blockchain_data_anl = blockchain_data.analysis()
    print(blockchain_data_anl)

# Exchange flow
def test_exchange_flow():
    print("\nAnalise de ExchangeFlow")
    exchange_flow = OnChain.ExchangeFlow()
    exchange_flow_anl  = exchange_flow.analysis()
    print(exchange_flow_anl)

# Dados econômicos
def run_all():
    news_analyzer = economic_dt.economic_news()
    econ_data = economic_dt()

    # CPI Data
    print('Dados economicos')
    print("Análise CPI:")
    print(econ_data.cpi_data())

    # PCE Data
    print("\nAnálise PCE:")
    print(econ_data.pce_data())

    # PIB Data
    print("\nAnálise PIB:")
    print(econ_data.pib_data())

    # Análise dos índices S&P 500 e Nasdaq
    print("\nAnálise dos Índices:")
    econ_data.analyze_indice()

    # Top 5 notícias sobre Bitcoin com análise de sentimento
    print("\nTop 5 Notícias sobre Bitcoin:")
    bitcoin_news_df = news_analyzer.get_top_news_of_month_with_sentiment('Bitcoin')
    print(bitcoin_news_df)

    # Top 5 notícias sobre Economia Mundial com análise de sentimento
    print("\nTop 5 Notícias sobre Economia Mundial:")
    global_economy_news_df = news_analyzer.get_top_news_of_month_with_sentiment('Global Economy')
    print(global_economy_news_df)

    # Correlação entre Bitcoin e Ouro
    print("\nCorrelação entre Bitcoin e Ouro:")
    print(econ_data.gold_correlation())

if __name__ == "__main__":
    # Capturar o output gerado pelas funções
    output_text = capture_output()

    # Contar o número de tokens no texto gerado
    num_tokens = num_tokens_from_string(output_text, "gpt-3.5-turbo")
    
    # Exibir o número de tokens
    print(f"Número de tokens no output: {num_tokens}")
