import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import ccxt
import numpy as np
import ta
import pytz
import yfinance as yf
import matplotlib.pyplot as plt
from fredapi import Fred
from bs4 import BeautifulSoup
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

class derivatives_data:
    
    def __init__(self):
        self.options_volume= self.options_volume().analysis
        self.coinglass_key=""

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

    class voume_change:   
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
                return "Erro ao obter dados de opções:", response.status_code, response.text

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

