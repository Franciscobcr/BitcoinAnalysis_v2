import datetime
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()  # Carregar as variáveis do arquivo .env

class on_chain_volume:

    def get_onchain_data(self):
        url = 'https://api.santiment.net/graphql'

        # Ajustar as datas para dentro do intervalo permitido (14 de setembro de 2023 em diante)
        to_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        from_date = "2023-09-14T00:00:00Z"  # Começo permitido

        # Query ajustada com as datas permitidas
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

        # Depurando: imprimindo a query e o cabeçalho
        print(f"Query GraphQL:\n{query}")
        print(f"Headers:\n{headers}")

        # Enviar a requisição
        response = requests.post(url, json={'query': query}, headers=headers)
        
        if response.status_code == 200:
            # Exibindo o JSON retornado para verificar a estrutura
            data = response.json()

            # Acessando os dados corretos
            if 'data' in data and 'getMetric' in data['data'] and 'timeseriesData' in data['data']['getMetric']:
                data = data['data']['getMetric']['timeseriesData']

                # Convertendo os dados para DataFrame do pandas
                if data:
                    df = pd.DataFrame(data)

                    # Verifique se o nome da coluna de tempo é 'datetime' ou outro
                    if 'datetime' in df.columns:
                        df['datetime'] = pd.to_datetime(df['datetime'])
                    else:
                        return "A chave 'datetime' não foi encontrada. Verifique o JSON retornado."

                    # Ajustando o fuso horário para Brasília (BRT)
                    df['datetime'] = df['datetime'].dt.tz_convert('America/Sao_Paulo')

                    return df
                else:
                    return "Nenhum dado foi retornado para o período solicitado."
            else:
                return "A estrutura de dados retornada pela API não está correta. Verifique a resposta JSON."
        else:
            return f'Erro na requisição: {response.status_code}, {response.text}'

    def analyze(self):
        on_chain = self.get_onchain_data()

        if isinstance(on_chain, pd.DataFrame):
            avg_volume = on_chain['value'].mean()
            max_volume = on_chain['value'].max()
            last_volume = on_chain['value'].iloc[-1]
        
            if last_volume > avg_volume:
                trend = "acima da média"
            else:
                trend = "abaixo da média"

            # Gerando a análise
            analise_onchain = (f"O volume médio de transações on-chain para o Bitcoin no período analisado é de {avg_volume:.2f}. "
                        f"O volume máximo registrado foi de {max_volume:.2f}. "
                        f"O volume mais recente está {trend}, indicando uma possível {('alta' if trend == 'acima da média' else 'queda')} "
                        f"no número de transações em comparação com a média do período.")

            return analise_onchain
        else:
            return f"Erro ao analisar os dados: {on_chain}"  # Exibe o erro retornado pela função get_onchain_data
