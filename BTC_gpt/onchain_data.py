import os
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
from zoneinfo import ZoneInfo  # Substituindo o uso de timedelta para fuso horário
from dotenv import load_dotenv
import streamlit as st

load_dotenv()  # Carregar as variáveis do arquivo .env

class OnChain:

    class on_chain_volume:
        def get_onchain_data(self):
            url = 'https://api.santiment.net/graphql'

            to_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            from_date = "2023-09-14T00:00:00Z"

            query = f"""
            {{
            getMetric(metric: "transaction_volume") {{
                timeseriesData(
                slug: "bitcoin"
                from: "{from_date}"
                to: "{to_date}"
                interval: "30m"
                ) {{
                datetime
                value
                }}
            }}
            }}
            """

            headers = {'Authorization': f"Apikey {os.getenv('santiment_KEY')}"}

            response = requests.post(url, json={'query': query}, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if 'data' in data and 'getMetric' in data['data'] and 'timeseriesData' in data['data']['getMetric']:
                    data = data['data']['getMetric']['timeseriesData']

                    if data:
                        df = pd.DataFrame(data)
                        if 'datetime' in df.columns:
                            df['datetime'] = pd.to_datetime(df['datetime'])
                        else:
                            return "A chave 'datetime' não foi encontrada. Verifique o JSON retornado."

                        df['datetime'] = df['datetime'].dt.tz_convert('America/Sao_Paulo')
                        return df
                    else:
                        return "Nenhum dado foi retornado para o período solicitado."
                else:
                    return "A estrutura de dados retornada pela API não está correta. Verifique a resposta JSON."
            else:
                return f'Erro na requisição: {response.status_code}, {response.text}'

        def analysis(self):
            on_chain = self.get_onchain_data()

            if isinstance(on_chain, pd.DataFrame):
                avg_volume = on_chain['value'].mean()
                max_volume = on_chain['value'].max()
                last_volume = on_chain['value'].iloc[-1]

                if last_volume > avg_volume:
                    trend = "acima da média"
                else:
                    trend = "abaixo da média"

                analise_onchain = (f"O volume médio de transações on-chain para o Bitcoin no período analisado é de {avg_volume:.2f}. "
                                   f"O volume máximo registrado foi de {max_volume:.2f}. "
                                   f"O volume mais recente está {trend}, indicando uma possível {('alta' if trend == 'acima da média' else 'queda')} "
                                   f"no número de transações em comparação com a média do período.")
                return analise_onchain
            else:
                return f"Erro ao analisar os dados: {on_chain}"

    class BlockchainData:
        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            brt_tz = ZoneInfo("America/Sao_Paulo")
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')

        def get_blockchain_data(self):
            url = "https://min-api.cryptocompare.com/data/blockchain/histo/day"
            params = {
                'fsym': 'BTC',
                'limit': '30',
                'api_key': os.getenv('CRYPTOCOMPARE_API_KEY')
            }
            response = requests.get(url, params=params)
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                data = response.json()

                # Verificar se a chave 'Data' está presente
                if 'Data' in data and 'Data' in data['Data']:
                    return data['Data']['Data']
                else:
                    print("Estrutura inesperada na resposta da API. Resposta completa:")
                    print(data)  # Exibir a resposta completa para ajudar no diagnóstico
                    return "Estrutura de dados inesperada"
            else:
                return f"Failed to retrieve data. Status code: {response.status_code}, Response: {response.text}"

        def parse_blockchain_data(self, data):
            parsed_data = []
            for day_data in data:
                parsed_data.append({
                    'data': self.convert_to_brt(day_data['time']),
                    'enderecos_ativos': day_data['active_addresses'],
                    'volume_transacoes': day_data['transaction_count'],
                    'hash_rate': day_data['hashrate'],
                    'dificuldade': day_data['difficulty'],
                    'movimentacao_whales': day_data['large_transaction_count'],
                    'valor_transferido': day_data['average_transaction_value']
                })
            return parsed_data

        def analysis(self):
            blockchain_data = self.get_blockchain_data()
            if blockchain_data == "Failed to retrieve data":
                return "Falha ao recuperar os dados da blockchain"

            parsed_blockchain_data = self.parse_blockchain_data(blockchain_data)

            total_enderecos_ativos = sum(d['enderecos_ativos'] for d in parsed_blockchain_data)
            media_enderecos_ativos = total_enderecos_ativos / len(parsed_blockchain_data)

            total_volume_transacoes = sum(d['volume_transacoes'] for d in parsed_blockchain_data)
            media_volume_transacoes = total_volume_transacoes / len(parsed_blockchain_data)

            total_hash_rate = sum(d['hash_rate'] for d in parsed_blockchain_data)
            media_hash_rate = total_hash_rate / len(parsed_blockchain_data)

            total_movimentacao_whales = sum(d['movimentacao_whales'] for d in parsed_blockchain_data)
            media_movimentacao_whales = total_movimentacao_whales / len(parsed_blockchain_data)

            blockchain_analysis = (f"Média de Endereços Ativos: {media_enderecos_ativos:.2f}\n"
                                   f"Média de Volume de Transações: {media_volume_transacoes:.2f}\n"
                                   f"Média de Hash Rate: {media_hash_rate:.2f}\n"
                                   f"Média de Movimentação de Whales: {media_movimentacao_whales:.2f}")

            return blockchain_analysis

    class ExchangeFlow:
        def convert_to_brt(self, timestamp):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            brt_tz = ZoneInfo("America/Sao_Paulo")
            dt_brt = dt.astimezone(brt_tz)
            return dt_brt.strftime('%Y-%m-%d %H:%M:%S')

        def get_exchange_flow(self):
            url = 'https://api.glassnode.com/v1/metrics/exchanges/flow_total_sum'
            params = {
                'a': 'BTC',
                'api_key': os.getenv('GLASSNODE_API_KEY'),
                's': int((datetime.now() - timedelta(days=30)).timestamp()), 
                'u': int(datetime.now().timestamp()) 
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return "Failed to retrieve data"

        def parse_exchange_flow(self, data):
            parsed_data = []
            for day_data in data:
                parsed_data.append({
                    'data': self.convert_to_brt(day_data['t']),
                    'fluxo_entrada': day_data['v_in'],
                    'fluxo_saida': day_data['v_out'],
                })
            return parsed_data

        def analysis(self):
            exchange_flow_data = self.get_exchange_flow()
            if exchange_flow_data == "Failed to retrieve data":
                return "Falha ao recuperar os dados de fluxo de exchanges"

            parsed_exchange_flow = self.parse_exchange_flow(exchange_flow_data)

            total_fluxo_entrada = sum(d['fluxo_entrada'] for d in parsed_exchange_flow)
            media_fluxo_entrada = total_fluxo_entrada / len(parsed_exchange_flow)

            total_fluxo_saida = sum(d['fluxo_saida'] for d in parsed_exchange_flow)
            media_fluxo_saida = total_fluxo_saida / len(parsed_exchange_flow)

            fluxo_anl = (f"Média de Fluxo de Entrada nas Exchanges: {media_fluxo_entrada:.2f} BTC\n"
                         f"Média de Fluxo de Saída das Exchanges: {media_fluxo_saida:.2f} BTC")

            return fluxo_anl

# Testando as classes aninhadas dentro de OnChain
def test_onchain_volume():
    on_chain_volume_analyzer = OnChain.on_chain_volume()
    volume_analysis = on_chain_volume_analyzer.analysis()
    print("Teste - Análise de Volume On-chain:")
    print(volume_analysis)

def test_blockchain_data():
    blockchain_data_analyzer = OnChain.BlockchainData()
    blockchain_analysis = blockchain_data_analyzer.analysis()
    print("Teste - Análise de Dados de Blockchain (CryptoCompare):")
    print(blockchain_analysis)

def test_exchange_flow():
    exchange_flow_analyzer = OnChain.ExchangeFlow()
    exchange_flow_analysis = exchange_flow_analyzer.analysis()
    print("Teste - Análise de Fluxo de Exchanges (Glassnode):")
    print(exchange_flow_analysis)


if __name__ == "__main__":
    test_onchain_volume()
    test_blockchain_data()
    test_exchange_flow()