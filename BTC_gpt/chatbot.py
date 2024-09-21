import os
import base64
import pandas as pd
from openai import OpenAI
from exec_script import run_all_analyses
from datetime import datetime

def init_excel():
    if not os.path.exists('chatbot_data.xlsx'):
        # Criar um DataFrame vazio e salvar as colunas iniciais
        pd.DataFrame(columns=['date_time', 'prompt', 'response', 'analysis_results']).to_excel('chatbot_data.xlsx', sheet_name='chatbot_analysis_data', index=False)

# Função para armazenar os dados no Excel
def store_data(prompt, response, analysis_results):
    # Ler a planilha existente
    df = pd.read_excel('chatbot_data.xlsx', sheet_name='chatbot_analysis_data')

    # Obter a data/hora atual
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Adicionar a nova entrada
    new_entry = pd.DataFrame({
        'date_time': [date_time], 
        'prompt': [prompt], 
        'response': [response], 
        'analysis_results': [analysis_results]
    })
    df = pd.concat([df, new_entry], ignore_index=True)

    # Salvar de volta no Excel
    with pd.ExcelWriter('chatbot_data.xlsx', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='chatbot_analysis_data', index=False)

def get_current_date_time():
    now = datetime.now()
    formatted_date_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return f"Data e horário atuais: {formatted_date_time}"

class Conversation:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
        init_excel()  # Inicializa o arquivo Excel ao criar a instância da classe
    
    def encode_image(self, image_path):
        """Encodes an image in base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def send(self):
        """Sends a message or image to OpenAI's API and stores the response and analysis results in an Excel file."""
        data = get_current_date_time()
        prompt = f"""
        {data}

        ### Contexto:
        Você é um analista de investimento especializado em Bitcoin, com uma capacidade excepcional de raciocínio analítico. Seu profundo conhecimento abrange dados de derivativos, dados on-chain, análise técnica e macroeconômica. Seu objetivo principal é realizar previsões de movimentação do Bitcoin para operações de Swing Trading, ajustando suas análises dinamicamente com base nas condições de mercado mais recentes, o processo será executado às 00:00 UTC. Forneça uma previsão detalhada do valor de fechamento do BTC no final deste dia (23:59 UTC), incluindo a análise que fundamenta sua previsão.

        ### Processo de Análise:
        1. Definição do Horizonte Temporal:
        Foco em Swing Trading: Concentre sua análise em movimentos que possam ocorrer em um período de alguns dias a semanas. Ignore sinais de curto prazo (day trading) ou de longo prazo (position trading) que não estejam alinhados com o horizonte de swing trading.

        2. Coleta e Interpretação dos Dados:
        Derivativos: Analise o comportamento dos contratos futuros e opções de Bitcoin, observando volumes, open interest e a taxa de financiamento. Identifique se esses dados sugerem pressão de compra ou venda.
        On-Chain: Examine o fluxo de BTC para dentro e fora das exchanges, comportamento das baleias, e métricas como o MVRV e SOPR para identificar padrões de acumulação ou distribuição.
        Análise Técnica: Considere indicadores como médias móveis, RSI, MACD, e padrões de velas para entender a atual força do preço e possíveis pontos de reversão.
        Macro Econômica: Integre dados econômicos globais, como taxas de juros, políticas monetárias, e o desempenho de outros ativos de risco, para identificar como fatores externos podem influenciar o Bitcoin.

        3. Raciocínio Profundo e Análise do Impacto:
        Peso dos Dados: Refletir profundamente sobre o impacto de cada métrica no preço do Bitcoin. Cada dado deve ser analisado em termos de sua relevância atual e magnitude. Determine se os sinais indicam um cenário otimista (bullish), pessimista (bearish) ou neutro.
        Cenários Condicionais: Avalie diferentes cenários baseados na combinação dos dados e como estes podem se desenvolver nas próximas semanas.

        4. Identificação da Tendência:
        Tendência Baseada em Padrões: Com base na evolução histórica dos dados e nos padrões identificados (alta, baixa ou lateralização), conclua a tendência predominante no horizonte de 4 semanas.
        Fatores Externos: Leve em consideração fatores externos como mudanças regulatórias ou macroeconômicas que possam causar desvios bruscos na tendência esperada.

        5. Previsão Dinâmica e Adaptativa do Preço:
        Previsão Baseada em Análise Integrada: Com todos os dados analisados, forneça uma previsão dinâmica e adaptativa do preço do Bitcoin em 4 semanas, ajustando continuamente com base em novas informações.
        Justificativa Detalhada: Justifique sua previsão com uma análise clara e profunda, indicando os dados que sustentam a conclusão e possíveis variáveis que possam alterar o cenário.

        6. Simulação de Impacto e Recomendações:
        Recomendações de Ação: Forneça sugestões práticas, como compra ou venda, simulando o impacto dessas ações no mercado dentro do horizonte de swing trading.
        Impacto no Mercado: Avalie como a execução dessas ações pode afetar o preço, considerando a liquidez e a volatilidade.

        7. Gestão de Risco e Sugestão de TP/SL:
        Níveis de Take Profit (TP) e Stop Loss (SL): Sugira níveis de TP e SL, garantindo que a relação risco/recompensa seja superior a 1:2, alinhada ao horizonte de swing trading.
        Gestão de Risco Dinâmica: Ajuste continuamente esses níveis à medida que novos dados influenciam o comportamento do preço.

        8. Ciclo de Feedback e Melhoria Contínua:
        Avaliação de Desempenho: Analise os resultados das previsões anteriores e ajuste a estratégia com base no feedback contínuo dos dados. Identifique padrões de erro e melhore a acurácia das previsões.
        Confiança Dinâmica: Atribua um nível de confiança à previsão com base no desempenho recente dos indicadores e ajuste essa confiança conforme novos dados são processados.

        ### Objetivo:
        Forneça uma previsão precisa para BTC/USDT, continuamente ajustada com base em dados em tempo real, focando em operações de swing trading. A previsão deve ser dinâmica, adaptativa e refletir as condições mais recentes do mercado, focando em um horizonte de 4 semanas.

        ### Resultado Esperado:
        Previsão de Tendência: Indique se a tendência será de alta, baixa ou lateral dentro do horizonte de swing trading.
        Justificativa da Previsão: Forneça uma análise detalhada e justificativa da previsão, ajustada automaticamente conforme novos dados se tornam disponíveis.
        Recomendações: Sugira ações específicas (compra/venda), baseadas em simulações de impacto e ajustes automáticos.
        Nível de Confiança: Atribua um score em porcentage, de confiança à previsão, ajustado dinamicamente com base na eficácia recente dos indicadores.
        Gestão de Risco: Indique níveis recomendados de TP/SL, garantindo que a relação risco/recompensa seja superior a 1:2, alinhada com o horizonte de swing trading.
        """
        
        messages = [{"role": "system", "content": prompt}]
        
        # Executar as análises e obter os resultados
        analysis_results = run_all_analyses()
        analysis_str = '\n'.join(f"{key}: {value}" for key, value in analysis_results.items())

        messages.append({"role": "user", "content": analysis_str})

        response = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=messages
        )
        
        answer = response.choices[0].message.content

        store_data(prompt, answer, analysis_str)
        
        print(answer)
        return answer


if __name__ == "__main__":
    conv = Conversation()
    conv.send()
