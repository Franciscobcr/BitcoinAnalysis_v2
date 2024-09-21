import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import numpy as np
import ta
import pytz
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import streamlit as st


load_dotenv()

class derivatives_data:
    
    def __init__(self):
        # Instancia a classe options_volume em vez de chamar diretamente a análise
        self.options_volume = self.options_volume()
        self.coinglass_key = "936395e1aa6943659c5ff7b729981532"

    def convert_to_brt(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        brt_tz = ZoneInfo("America/Sao_Paulo")
        dt_brt = dt.astimezone(brt_tz)
        return dt_brt.strftime('%Y-%m-%d %H:%M:%S')

    def get_unix_timestamp(self, days_ago=0):
        dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
        return int(dt.timestamp())

    class options_volume:
        def get_options_volume(self):
            url = 'https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option'
            response = requests.get(url)

            if response.status_code == 200:
                options_data = response.json().get('result', [])
                if not options_data:
                    print("Nenhum dado de opções foi retornado.")
                    return None

                df = pd.DataFrame(options_data)

                if 'volume' in df.columns:
                    df_volume = df[['instrument_name', 'volume']]
                    return df_volume
                else:
                    return "O campo de volume de negociação (volume) não está disponível nos dados."
            else:
                return "Erro ao obter dados de opções:", response.status_code, response.text
            
        def analysis(self):
            vol_negociacao = self.get_options_volume()

            if vol_negociacao is not None and not vol_negociacao.empty:
                vol_negociacao['volume'] = vol_negociacao['volume'].astype(float)

                total_volume = vol_negociacao['volume'].sum()
                avg_volume = vol_negociacao['volume'].mean()
                max_volume = vol_negociacao['volume'].max()

                top_instrument = vol_negociacao.loc[vol_negociacao['volume'].idxmax()]

                analysis = (f"O volume total de negociação de opções de Bitcoin foi de {total_volume:.2f}. "
                            f"O volume médio por instrumento foi de {avg_volume:.2f}. "
                            f"O maior volume registrado foi de {max_volume:.2f} para o instrumento {top_instrument['instrument_name']}.")
                return analysis
            else:
                return "Nenhum dado de volume de negociação foi retornado para análise."
            
    class cvd_data:
        def fetch_trades(self, pair='XXBTZUSD', interval=30, lookback_days=14):
            endpoint = 'https://api.kraken.com/0/public/OHLC'
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=lookback_days)
            start_time_ts = int(start_time.timestamp())

            params = {
                'pair': pair,
                'interval': interval,
                'since': start_time_ts
            }

            response = requests.get(endpoint, params=params)
            data = response.json()

            if 'result' not in data:
                raise ValueError("Não foi possível obter os dados da API.")

            ohlc_data = data['result'].get(pair, [])
            columns = ['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
            df = pd.DataFrame(ohlc_data, columns=columns)

            df['time'] = pd.to_datetime(df['time'], unit='s')
            df['time'] = df['time'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
            df['time'] = df['time'].dt.tz_localize(None)

            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

            return df

        def calculate_cvd_30min(self, df):
            df.set_index('time', inplace=True)
            df = df.resample('30min').agg({'volume': 'sum'})

            df['cvd'] = df['volume']
            df.reset_index(inplace=True)

            return df[['time', 'cvd']]

        def analysis(self):
            df = self.fetch_trades()

            cvd_30min = self.calculate_cvd_30min(df)

            if not cvd_30min.empty:
                avg_cvd = cvd_30min['cvd'].mean()
                max_cvd = cvd_30min['cvd'].max()
                min_cvd = cvd_30min['cvd'].min()

                last_cvd = cvd_30min['cvd'].iloc[-1]

                analysis = (f"A média do CVD nos últimos 14 dias foi de {avg_cvd:.2f}. "
                            f"O maior CVD registrado foi de {max_cvd:.2f}, enquanto o menor CVD foi de {min_cvd:.2f}. "
                            f"O CVD mais recente é de {last_cvd:.2f}.")

                return analysis

            else:
                return "Nenhum dado de CVD encontrado para análise."

    class volume_change:   
        def puxar_dados(self):
            url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'
            params = {
                'vs_currency': 'usd',
                'days': '14',
                'interval': 'daily'
            }
            response = requests.get(url, params=params)
            data = response.json()

            prices = data['prices']
            volumes = data['total_volumes']

            df_prices = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'], unit='ms')

            df_volumes = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
            df_volumes['timestamp'] = pd.to_datetime(df_volumes['timestamp'], unit='ms')

            df = pd.merge(df_prices, df_volumes, on='timestamp')

            return df
        
        def analysis(self):
            df = self.puxar_dados()

            df['change_in_volume'] = df['volume'].diff()

            mudanca_volume = df[['timestamp', 'change_in_volume']]

            if not mudanca_volume.empty:
                avg_change_volume = mudanca_volume['change_in_volume'].mean()
                max_change_volume = mudanca_volume['change_in_volume'].max()
                min_change_volume = mudanca_volume['change_in_volume'].min()

                last_change_volume = mudanca_volume['change_in_volume'].iloc[-1]

                analysis = (f"A média da mudança no volume nos últimos 14 dias foi de {avg_change_volume:.2e}. "
                            f"A maior mudança no volume foi de {max_change_volume:.2e}, enquanto a menor mudança foi de {min_change_volume:.2e}. "
                            f"A mudança de volume mais recente é de {last_change_volume:.2e}.")

                return analysis

            else:
                return "Nenhuma mudança de volume encontrada para análise."

    class skew:
        def calculate(self):
            url = 'https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option'
            response = requests.get(url)

            if response.status_code == 200:
                options_data = response.json().get('result', [])
                if not options_data:
                    print("Nenhum dado de opções foi retornado.")
                    return None

                df = pd.DataFrame(options_data)

                if 'ask_price' in df.columns and 'bid_price' in df.columns:
                    df['skew'] = (df['ask_price'] - df['bid_price']) / df['mid_price'] * 100
                    return df[['instrument_name', 'ask_price', 'bid_price', 'mid_price', 'skew']]
                else:
                    return "As colunas de preço (ask_price e bid_price) não estão disponíveis nos dados."

            else:
                return f"Erro ao obter dados de opções: {response.status_code} - {response.text}"

        def analysis(self):
            # Calcular o Skew
            skew_data = self.calculate()

            if skew_data is not None and not isinstance(skew_data, str) and not skew_data.empty:
                # Cálculo das estatísticas básicas
                avg_skew = skew_data['skew'].mean()
                max_skew = skew_data['skew'].max()
                min_skew = skew_data['skew'].min()

                # Último Skew registrado
                last_skew = skew_data['skew'].iloc[-1]

                # Gerando a análise sobre o Skew
                skew_anl = (f"A média do Skew das opções de Bitcoin foi de {avg_skew:.2f}%. "
                            f"O maior Skew registrado foi de {max_skew:.2f}%, enquanto o menor Skew foi de {min_skew:.2f}%. "
                            f"O Skew mais recente é de {last_skew:.2f}%.")

                return skew_anl

            elif isinstance(skew_data, str):
                return skew_data
            else:
                return "Nenhum dado de Skew foi retornado para análise."


    class iv:
        def get_options_iv(self):
            url = 'https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option'
            response = requests.get(url)

            if response.status_code == 200:
                options_data = response.json().get('result', [])
                if not options_data:
                    return "Nenhum dado de opções foi retornado."

                df = pd.DataFrame(options_data)

                if 'mark_iv' in df.columns:
                    df_iv = df[['instrument_name', 'mark_iv']]
                    return df_iv
                else:
                    print("O campo de volatilidade implícita (mark_iv) não está disponível nos dados.")
                    return None

            else:
                print("Erro ao obter dados de opções:", response.status_code, response.text)
                return None

        def analysis(self):
            iv = self.get_options_iv()

            if iv is not None and not iv.empty:
                iv['mark_iv'] = iv['mark_iv'].astype(float)

                avg_iv = iv['mark_iv'].mean()
                max_iv = iv['mark_iv'].max()
                min_iv = iv['mark_iv'].min()

                top_iv_instrument = iv.loc[iv['mark_iv'].idxmax()]
                low_iv_instrument = iv.loc[iv['mark_iv'].idxmin()]

                analysis = (f"A volatilidade implícita média para as opções de Bitcoin é de {avg_iv:.2f}%. "
                            f"A maior volatilidade implícita registrada foi de {max_iv:.2f}% para o instrumento {top_iv_instrument['instrument_name']}. "
                            f"A menor volatilidade implícita registrada foi de {min_iv:.2f}% para o instrumento {low_iv_instrument['instrument_name']}.")

                return analysis

            else:
                return "Nenhum dado de volatilidade implícita foi retornado para análise."


    class market_depth:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/orderbook/history"

        def get_order_book_depth(self, symbol, exchange="Binance", interval="30m", limit=1000, start_time=None, end_time=None):
            headers = {"accept": "application/json", "CG-API-KEY": os.getenv('COINGLASS_KEY')}
            
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": start_time,
                "endTime": end_time
            }
            
            response = requests.get(self.BASE_URL, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Erro na requisição: {response.text}")
                return None
            data = response.json()
            return data  # Corrigido para retornar apenas os dados

        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')


        # Função para processar os dados da profundidade do mercado e armazenar em um DataFrame
        def process_order_book_to_df(self, data):
            if data is None:
                return pd.DataFrame()  # Retornar DataFrame vazio em caso de erro na API
            records = []
            for item in data.get("data", []):
                bids_usd = item.get("bidsUsd", "N/A")
                bids_amount = item.get("bidsAmount", "N/A")
                asks_usd = item.get("asksUsd", "N/A")
                asks_amount = item.get("asksAmount", "N/A")
                timestamp = item.get("time", 0)
                # Converter timestamp para data e hora em São Paulo
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Bids (USD)": bids_usd,
                    "Bids Amount": bids_amount,
                    "Asks (USD)": asks_usd,
                    "Asks Amount": asks_amount
                })
            df = pd.DataFrame(records)
            return df

        # Função para capturar dados em blocos de 30 dias (30 minutos de intervalo por requisição)
        def fetch_order_book_in_blocks(self, symbol="BTCUSDT", interval="30m", days=30):
            now = datetime.utcnow()
            df_list = []

            while days > 0:
                end_time = int(now.timestamp())
                start_time = int((now - timedelta(minutes=30 * 1000)).timestamp())  # 1000 intervalos de 30 minutos
                order_book_data = self.get_order_book_depth(symbol, start_time=start_time, end_time=end_time, interval=interval)
                df = self.process_order_book_to_df(order_book_data)
                if df.empty:
                    print("Nenhum dado retornado para este intervalo.")
                    break
                df_list.append(df)

                now = now - timedelta(minutes=30 * 1000)
                days -= (30 * 1000) / (24 * 60)  # Subtrai o número de dias correspondentes

            final_df = pd.concat(df_list, ignore_index=True)
            return final_df

        def analysis(self):
            profundidade = self.fetch_order_book_in_blocks()

            if not profundidade.empty:
                # Converter as colunas para float
                profundidade["Bids (USD)"] = profundidade["Bids (USD)"].astype(float)
                profundidade["Bids Amount"] = profundidade["Bids Amount"].astype(float)
                profundidade["Asks (USD)"] = profundidade["Asks (USD)"].astype(float)
                profundidade["Asks Amount"] = profundidade["Asks Amount"].astype(float)

                # Cálculo das estatísticas básicas para bids e asks
                avg_bids_usd = profundidade["Bids (USD)"].mean()
                max_bids_usd = profundidade["Bids (USD)"].max()
                avg_asks_usd = profundidade["Asks (USD)"].mean()
                max_asks_usd = profundidade["Asks (USD)"].max()

                # Cálculo das quantidades (amount) de bids e asks
                avg_bids_amount = profundidade["Bids Amount"].mean()
                avg_asks_amount = profundidade["Asks Amount"].mean()

                # Gerando a análise para a profundidade do mercado
                profundidade_anl = (f"Durante os últimos 30 dias, o valor médio de Bids foi de {avg_bids_usd:.2f} USD, com um pico máximo de {max_bids_usd:.2f} USD. "
                            f"O valor médio de Asks foi de {avg_asks_usd:.2f} USD, com um pico máximo de {max_asks_usd:.2f} USD.\n"
                            f"A quantidade média de Bids foi de {avg_bids_amount:.2f}, enquanto a quantidade média de Asks foi de {avg_asks_amount:.2f}.")

                return profundidade_anl
            else:
                return "Nenhum dado foi retornado para análise."

    
    class liquidations:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/liquidation/v2/history"
        headers = {"accept": "application/json","CG-API-KEY": os.getenv('COINGLASS_KEY')}

        # Função para capturar o histórico de liquidações de Long/Short de 30 em 30 minutos
        def get_liquidation_history(self, symbol, exchange="Binance", interval="30m", limit=1000, start_time=None, end_time=None):
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": start_time,
                "endTime": end_time
            }
            response = requests.get(self.BASE_URL, headers=self.headers, params=params)
            return response.json()

        # Função para converter timestamp para data e hora de São Paulo
        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')


        # Função para processar os dados e armazenar em um DataFrame
        def process_liquidations_to_df(self, data):
            records = []
            for item in data.get("data", []):
                long_liq = item.get("longLiquidationUsd", "N/A")
                short_liq = item.get("shortLiquidationUsd", "N/A")
                timestamp = item.get("t", 0)
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Long Liquidation (USD)": long_liq,
                    "Short Liquidation (USD)": short_liq
                })
            df = pd.DataFrame(records)
            return df

        # Função para capturar dados em blocos de 30 dias (30 minutos de intervalo por requisição)
        def fetch_data_in_blocks(self, symbol = "BTCUSDT", interval="30m", days=30):
            now = datetime.utcnow()
            df_list = []

            # Dividimos os 30 dias em blocos de intervalos de 1000 registros (aprox. 20.8 dias de 30 minutos)
            while days > 0:
                end_time = int(now.timestamp())
                start_time = int((now - timedelta(minutes=30 * 1000)).timestamp())  # 1000 intervalos de 30 minutos
                liquidation_data = self.get_liquidation_history(symbol, start_time=start_time, end_time=end_time, interval=interval)
                df = self.process_liquidations_to_df(liquidation_data)
                df_list.append(df)

                # Atualiza a variável 'now' para continuar capturando períodos anteriores
                now = now - timedelta(minutes=30 * 1000)
                days -= (30 * 1000) / (24 * 60)  # Subtrai o número de dias correspondentes

            # Concatena todos os DataFrames
            final_df = pd.concat(df_list, ignore_index=True)
            return final_df

        def analysis(self):
            liquidacoes = self.fetch_data_in_blocks()

            if not liquidacoes.empty:
                # Converter as colunas "Long Liquidation (USD)" e "Short Liquidation (USD)" para float
                liquidacoes["Long Liquidation (USD)"] = liquidacoes["Long Liquidation (USD)"].astype(float)
                liquidacoes["Short Liquidation (USD)"] = liquidacoes["Short Liquidation (USD)"].astype(float)

                # Filtrar os valores não-zero para a análise
                long_liq_non_zero = liquidacoes[liquidacoes["Long Liquidation (USD)"] > 0]
                short_liq_non_zero = liquidacoes[liquidacoes["Short Liquidation (USD)"] > 0]

                # Cálculo das estatísticas básicas apenas para valores maiores que zero
                if not long_liq_non_zero.empty:
                    avg_long_liq = long_liq_non_zero["Long Liquidation (USD)"].mean()
                    max_long_liq = long_liq_non_zero["Long Liquidation (USD)"].max()
                    last_long_liq = long_liq_non_zero["Long Liquidation (USD)"].iloc[-1]
                else:
                    avg_long_liq = max_long_liq = last_long_liq = 0

                if not short_liq_non_zero.empty:
                    avg_short_liq = short_liq_non_zero["Short Liquidation (USD)"].mean()
                    max_short_liq = short_liq_non_zero["Short Liquidation (USD)"].max()
                    last_short_liq = short_liq_non_zero["Short Liquidation (USD)"].iloc[-1]
                else:
                    avg_short_liq = max_short_liq = last_short_liq = 0

                # Gerando a análise para liquidações Long e Short, sem considerar zeros
                liquidacoes_anl = (f"Durante os últimos 30 dias, o valor médio de liquidações Long (excluindo zeros) foi de {avg_long_liq:.2f} USD, "
                            f"com um pico máximo de {max_long_liq:.2f} USD. O valor de liquidação Long mais recente foi de {last_long_liq:.2f} USD.\n"
                            f"Para liquidações Short, o valor médio (excluindo zeros) foi de {avg_short_liq:.2f} USD, "
                            f"com um pico máximo de {max_short_liq:.2f} USD. O valor de liquidação Short mais recente foi de {last_short_liq:.2f} USD.")

                return liquidacoes_anl

            else:
                return "Nenhum dado foi retornado para análise."
            
    class ls_ratio:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/globalLongShortAccountRatio/history"
        headers = {"accept": "application/json", "CG-API-KEY": os.getenv('COINGLASS_KEY')}

        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')


        def get_long_short_ratio(self, symbol, exchange="Binance", interval="30m", limit=1000, start_time=None, end_time=None):
            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": start_time,
                "endTime": end_time
            }
            response = requests.get(self.BASE_URL, headers=self.headers, params=params)
            return response.json()

        def process_long_short_ratio_to_df(self, data):
            records = []
            for item in data.get("data", []):
                long_account = item.get("longAccount", "N/A")
                short_account = item.get("shortAccount", "N/A")
                long_short_ratio = item.get("longShortRatio", "N/A")
                timestamp = item.get("time", 0)
                # Converter timestamp para data e hora em São Paulo
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Long Account (%)": long_account,
                    "Short Account (%)": short_account,
                    "Long/Short Ratio": long_short_ratio
                })
            df = pd.DataFrame(records)
            return df

        def fetch_data_in_blocks(self, symbol="BTCUSDT", interval="30m", total_days=30):
            now = datetime.utcnow()
            df_list = []

            while total_days > 0:
                end_time = int(now.timestamp())
                start_time = int((now - timedelta(minutes=30 * 1000)).timestamp())  # 1000 intervalos de 30 minutos

                ratio_data = self.get_long_short_ratio(symbol, start_time=start_time, end_time=end_time, interval=interval)
                df = self.process_long_short_ratio_to_df(ratio_data)
                df_list.append(df)

                # Atualiza a variável 'now' para continuar capturando períodos anteriores
                now = now - timedelta(minutes=30 * 1000)
                total_days -= (30 * 1000) / (24 * 60)  # Subtrai o número de dias correspondentes

                    # Concatena todos os DataFrames
                final_df = pd.concat(df_list, ignore_index=True)
                return final_df
        
        def analysis(self):
            long_short_ratio = self.fetch_data_in_blocks()

            if not long_short_ratio.empty:
                # Converter as colunas "Long Account (%)", "Short Account (%)" e "Long/Short Ratio" para float
                long_short_ratio["Long Account (%)"] = long_short_ratio["Long Account (%)"].astype(float)
                long_short_ratio["Short Account (%)"] = long_short_ratio["Short Account (%)"].astype(float)
                long_short_ratio["Long/Short Ratio"] = long_short_ratio["Long/Short Ratio"].astype(float)

                # Cálculo das estatísticas básicas
                avg_ratio = long_short_ratio["Long/Short Ratio"].mean()
                max_ratio = long_short_ratio["Long/Short Ratio"].max()
                last_ratio = long_short_ratio["Long/Short Ratio"].iloc[-1]

                # Identificando a tendência do Long/Short Ratio
                if last_ratio > avg_ratio:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"

                    # Gerando a análise
                long_short_anl = (f"O Long/Short Ratio médio para o Bitcoin no período analisado é de {avg_ratio:.6f}. "
                            f"O maior Long/Short Ratio foi de {max_ratio:.6f}. "
                            f"O Long/Short Ratio mais recente está {trend}, indicando uma possível "
                            f"{('alta' if trend == 'acima da média' else 'queda')} na proporção de long/short.")

                return long_short_anl

            else:
                return "Nenhum dado foi retornado para análise."
            
    class funding_rate_ohlc:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/fundingRate/ohlc-history"
        headers = {"accept": "application/json", "CG-API-KEY": os.getenv('COINGLASS_KEY')}

        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')


        # Função para obter o timestamp Unix
        def get_unix_timestamp(self, days_ago=0):
            dt = datetime.now() - timedelta(days=days_ago)
            return int(dt.timestamp())

        # Função para capturar OHLC History (Funding Rate) dos últimos 30 dias com intervalos de 30 minutos
        def get_funding_rate_ohlc(self, symbol="BTCUSDT", exchange="Binance", interval="30m"):
            # Definir o período dos últimos 30 dias
            end_time = self.get_unix_timestamp(0)  # Agora
            start_time = self.get_unix_timestamp(30)  # Últimos 30 dias

            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time
            }

            response = requests.get(self.BASE_URL, headers=self.headers, params=params)

            if response.status_code != 200:
                return pd.DataFrame()

            data = response.json()

            if not data.get("data"):
                print("Nenhum dado retornado pela API.")
                return pd.DataFrame()

            # Processar os dados
            records = []
            for item in data.get("data", []):
                open_price = item.get("o", "N/A")
                high_price = item.get("h", "N/A")
                low_price = item.get("l", "N/A")
                close_price = item.get("c", "N/A")
                timestamp = item.get("t", 0)
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Open": open_price,
                    "High": high_price,
                    "Low": low_price,
                    "Close": close_price
                })
            df = pd.DataFrame(records)
            return df
        
        def analysis(self):
            # Capturar OHLC History para o par BTCUSDT com intervalos de 30 minutos nos últimos 30 dias
            funding_rate_ohlc = self.get_funding_rate_ohlc(interval="30m")

            if not funding_rate_ohlc.empty:
                funding_rate_ohlc['Close'] = funding_rate_ohlc['Close'].astype(float)

                avg_close = funding_rate_ohlc['Close'].mean()
                max_close = funding_rate_ohlc['Close'].max()
                last_close = funding_rate_ohlc['Close'].iloc[-1]

                # Identificando a tendência do preço de fechamento do funding rate
                if last_close > avg_close:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"

                # Gerando a análise
                funding_rate_ohlc_anl = (f"O funding rate médio para o Bitcoin no período analisado é de {avg_close:.6f}. "
                            f"O maior valor de fechamento foi {max_close:.6f}. "
                            f"O fechamento mais recente está {trend}, indicando uma possível "
                            f"{('alta' if trend == 'acima da média' else 'queda')} em relação à média.")

                # Exibindo a análise
                return funding_rate_ohlc_anl

            else:
                return "Nenhum dado foi retornado para análise."
            
    class oi_weight_ohlc:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/fundingRate/oi-weight-ohlc-history"
        headers = {"accept": "application/json", "CG-API-KEY": os.getenv('COINGLASS_KEY')}

        
        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')

        # Função para obter o timestamp Unix
        def get_unix_timestamp(self, days_ago=0):
            dt = datetime.now() - timedelta(days=days_ago)
            return int(dt.timestamp())

        # Função para capturar OI Weight OHLC History dos últimos 30 dias com intervalos de 30 minutos
        def get_oi_weight_ohlc_history(self, symbol="BTC", interval="30m"):
            end_time = self.get_unix_timestamp(0)  # Agora
            start_time = self.get_unix_timestamp(30)  # Últimos 30 dias #os

            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time
            }

            response = requests.get(self.BASE_URL, headers=self.headers, params=params)

            if response.status_code != 200:
                print("Erro na requisição:", response.text)
                return pd.DataFrame()

            data = response.json()

            if not data.get("data"):
                print("Nenhum dado retornado pela API.")
                return pd.DataFrame()

            # Processar os dados
            records = []
            for item in data.get("data", []):
                open_price = item.get("o", "N/A")
                high_price = item.get("h", "N/A")
                low_price = item.get("l", "N/A")
                close_price = item.get("c", "N/A")
                timestamp = item.get("t", 0)
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Open": open_price,
                    "High": high_price,
                    "Low": low_price,
                    "Close": close_price
                })

            df = pd.DataFrame(records)
            return df

        def analysis(self):
            oi_weight_ohlc = self.get_oi_weight_ohlc_history(interval="30m")
            if not oi_weight_ohlc.empty:
                oi_weight_ohlc['Close'] = oi_weight_ohlc['Close'].astype(float)

                avg_close = oi_weight_ohlc['Close'].mean()
                max_close = oi_weight_ohlc['Close'].max()
                last_close = oi_weight_ohlc['Close'].iloc[-1]

                if last_close > avg_close:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"

                # Gerando a análise
                analysis = (f"O funding rate ponderado pelo open interest para o Bitcoin no período analisado tem uma média de {avg_close:.6f}. "
                            f"O maior valor de fechamento foi {max_close:.6f}. "
                            f"O fechamento mais recente está {trend}, indicando uma possível "
                            f"{('alta' if trend == 'acima da média' else 'queda')} em relação à média.")

                return analysis

            else:
                return "Nenhum dado foi retornado para análise."
                

    class fundingratevol:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/fundingRate/vol-weight-ohlc-history"
        headers = {"accept": "application/json", "CG-API-KEY": os.getenv('COINGLASS_KEY')}

        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')


        def get_unix_timestamp(self, days_ago=0):
            dt = datetime.now() - timedelta(days=days_ago)
            return int(dt.timestamp())

    # Função para capturar Vol Weight OHLC History dos últimos 30 dias com intervalos de 30 minutos
        def get_vol_weight_ohlc_history(self, symbol="BTC", interval="30m"):
            end_time = self.get_unix_timestamp(0)  # Agora
            start_time = self.get_unix_timestamp(30)  # Últimos 30 dias

            params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time
            }

            response = requests.get(self.BASE_URL, headers=self.headers, params=params)

            if response.status_code != 200:
                print("Erro na requisição:", response.text)
                return pd.DataFrame()

            data = response.json()

            if not data.get("data"):
                print("Nenhum dado retornado pela API.")
                return pd.DataFrame()

            # Processar os dados
            records = []
            for item in data.get("data", []):
                open_price = item.get("o", "N/A")
                high_price = item.get("h", "N/A")
                low_price = item.get("l", "N/A")
                close_price = item.get("c", "N/A")
                timestamp = item.get("t", 0)
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Open": open_price,
                    "High": high_price,
                    "Low": low_price,
                    "Close": close_price
                })

            # Criar DataFrame
            df = pd.DataFrame(records)
            return df

    # Função para analisar os dados
        def analysis(self):
            vol_weight_ohlc = self.get_vol_weight_ohlc_history(interval="30m")

            if not vol_weight_ohlc.empty:
                vol_weight_ohlc['Close'] = vol_weight_ohlc['Close'].astype(float)

                # Cálculo das estatísticas básicas
                avg_close = vol_weight_ohlc['Close'].mean()
                max_close = vol_weight_ohlc['Close'].max()
                last_close = vol_weight_ohlc['Close'].iloc[-1]

            # Identificando a tendência do preço de fechamento ponderado pelo volume
                if last_close > avg_close:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"
                
                funding_rate_vol = (f"O funding rate ponderado pelo volume para o Bitcoin no período analisado tem uma média de {avg_close:.6f}. "
                        f"O maior valor de fechamento foi {max_close:.6f}. "
                        f"O fechamento mais recente está {trend}, indicando uma possível "
                        f"{('alta' if trend == 'acima da média' else 'queda')} em relação à média.")

                return funding_rate_vol

            else:
                return "Nenhum dado foi retornado para análise."

            
    class oi_ohlc:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/openInterest/ohlc-history"
        headers = {"accept": "application/json", "CG-API-KEY": os.getenv('COINGLASS_KEY')}

        
        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) 
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')

        # Função para obter o timestamp Unix
        def get_unix_timestamp(self,days_ago=0):
            dt = datetime.now() - timedelta(days=days_ago)
            return int(dt.timestamp())

        # Função para capturar Open Interest OHLC History dos últimos 30 dias com intervalos de 30 minutos
        def get_open_interest_ohlc_history(self,symbol="BTCUSDT", exchange="Binance", interval="30m"):
            # Definir o período dos últimos 30 dias
            end_time = self.get_unix_timestamp(0)
            start_time = self.get_unix_timestamp(30)  # Últimos 30 dias

            params = {
                "exchange": exchange,
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time
            }

            response = requests.get(self.BASE_URL, headers=self.headers, params=params)

            if response.status_code != 200:
                print("Erro na requisição:", response.text)
                return pd.DataFrame()

            data = response.json()

            if not data.get("data"):
                print("Nenhum dado retornado pela API.")
                return pd.DataFrame()

            # Processar os dados
            records = []
            for item in data.get("data", []):
                open_price = item.get("o", "N/A")
                high_price = item.get("h", "N/A")
                low_price = item.get("l", "N/A")
                close_price = item.get("c", "N/A")
                timestamp = item.get("t", 0)
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Open": open_price,
                    "High": high_price,
                    "Low": low_price,
                    "Close": close_price
                })

            df = pd.DataFrame(records)
            return df

        def analysis(self):
            open_interest_ohlc = self.get_open_interest_ohlc_history(interval="30m")

            if not open_interest_ohlc.empty:
                avg_close = open_interest_ohlc['Close'].astype(float).mean()
                max_close = open_interest_ohlc['Close'].astype(float).max()
                last_close = open_interest_ohlc['Close'].astype(float).iloc[-1]

                if last_close > avg_close:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"

                open_interest_anl = (f"O preço médio de fechamento do Bitcoin no período analisado é de {avg_close:.2f}. "
                            f"O preço de fechamento mais alto foi de {max_close:.2f}. "
                            f"O fechamento mais recente está {trend}, indicando uma possível "
                            f"{('alta' if trend == 'acima da média' else 'queda')} em relação à média.")

                return open_interest_anl

            else:
                return "Nenhum dado foi retornado para análise."
            
    class oi_ohlc_history:
        BASE_URL = "https://open-api-v3.coinglass.com/api/futures/openInterest/ohlc-aggregated-history"
        headers = {"accept": "application/json","CG-API-KEY": os.getenv('COINGLASS_KEY')}

        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Usando timezone.utc
            brt_tz = pytz.timezone('America/Sao_Paulo')
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')


        def get_unix_timestamp(self, days_ago=0):
            dt = datetime.now() - timedelta(days=days_ago)
            return int(dt.timestamp())

        # Função para capturar OHLC Aggregated History dos últimos 30 dias com intervalos de 30 minutos
        def get_ohlc_aggregated_history(self, symbol="BTC", interval="30m"):
            end_time = self.get_unix_timestamp(0)
            start_time = self.get_unix_timestamp(30)  # Últimos 30 dias

            params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time
            }

            response = requests.get(self. BASE_URL, headers=self.headers, params=params)

            if response.status_code != 200:
                return "Erro na requisição:", response.text

            data = response.json()

            if not data.get("data"):
                return "Nenhum dado retornado pela API."

            # Processar os dados
            records = []
            for item in data.get("data", []):
                open_price = item.get("o", "N/A")
                high_price = item.get("h", "N/A")
                low_price = item.get("l", "N/A")
                close_price = item.get("c", "N/A")
                timestamp = item.get("t", 0)
                brt_time = self.convert_to_brt(timestamp)
                records.append({
                    "Data/Hora (São Paulo)": brt_time,
                    "Open": open_price,
                    "High": high_price,
                    "Low": low_price,
                    "Close": close_price
                })

            df = pd.DataFrame(records)
            return df
        
        def analysis(self):
            ohlc_aggregated_history = self.get_ohlc_aggregated_history(interval="30m")

            if not ohlc_aggregated_history.empty:
                avg_close = ohlc_aggregated_history['Close'].astype(float).mean()
                max_close = ohlc_aggregated_history['Close'].astype(float).max()
                last_close = ohlc_aggregated_history['Close'].astype(float).iloc[-1]

                if last_close > avg_close:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"
                    
                analise_ohlc_aggr = (f"O preço médio de fechamento do Bitcoin no período analisado é de {avg_close:.2f}. "
                            f"O preço de fechamento mais alto foi de {max_close:.2f}. "
                            f"O fechamento mais recente está {trend}, indicando uma possível "
                            f"{('alta' if trend == 'acima da média' else 'queda')} em relação à média.")

                return analise_ohlc_aggr
            else:
                return "erro no oi_ohlc_history"
    
    
