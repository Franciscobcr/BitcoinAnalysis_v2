from database_setting import get_bitcoin_data  # Importar a função para pegar os dados de Bitcoin
from datetime import datetime
import re
from openai import OpenAI
import os
import psycopg2
from openai import OpenAI
from exec_script import run_all_analyses  
from datetime import datetime, timedelta, timezone
import schedule
import time
from compare_predict import process_predictions
from database_setting import store_prediction
import base64
from prompts import prompts

class Conversation:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

    def analyze_output_with_llm(self, output_from_first_llm):
        second_prompt = f"""
        ### Tarefa:
        Você é uma inteligência artificial especializada em analisar previsões de trading. Recebeu o seguinte output de uma análise de swing trading feita por outra IA. Sua tarefa é extrair as seguintes informações de forma precisa:
        
        1. Recomendação (Compra, Venda, Aguardar)
        2. Nível de Confiança (porcentagem)
        3. Stop Loss (valor numérico)
        4. Take Profit (valor numérico)
        5. Relação Risco/Recompensa (valor numérico)
        
        ### Output da outra IA:
        {output_from_first_llm}

        ### Resposta esperada:
        Formate a resposta da seguinte forma:
        Recomendação: <valor>
        Nível de Confiança: <valor em decimal>
        Stop Loss: <valor numérico com . > 
        Take Profit: <valor numérico com . >
        Relação Risco/Recompensa: <TEXTO>
        """
        
        # Enviando o prompt para a segunda LLM
        response = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": second_prompt}]
        )
        
        # Captura da resposta da segunda LLM
        analyzed_data = response.choices[0].message.content
        return analyzed_data

    def send(self, analysis_date=None):
        if analysis_date is None:
            # Obter a data de amanhã
            analysis_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

        # Primeiro prompt enviado para a API
        prompt = prompts.btc_analysis_prompt()
        messages = [{"role": "system", "content": prompt}]
        
        # Executar as análises e obter os resultados
        analysis_results = run_all_analyses()
        analysis_str = '\n'.join(f"{key}: {value}" for key, value in analysis_results.items())

        messages.append({"role": "user", "content": analysis_str})

        # Enviar o prompt para a primeira LLM e capturar a resposta
        response = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=messages
        )
        
        # Capturar o output da primeira LLM
        output_from_first_llm = response.choices[0].message.content
        
        # Agora enviaremos o output da primeira LLM para a segunda LLM
        analyzed_data = self.analyze_output_with_llm(output_from_first_llm)
        
        # Usando expressões regulares para capturar os dados específicos do analyzed_data
        recommendation = re.search(r'Recomendação: (.+)', analyzed_data)
        trust_rate = re.search(r'Nível de Confiança: (\d+)', analyzed_data)
        stop_loss = re.search(r'Stop Loss: ([\d.]+)', analyzed_data)
        take_profit = re.search(r'Take Profit: ([\d.]+)', analyzed_data)
        risk_return = re.search(r'Relação Risco/Recompensa: (.+)', analyzed_data)

        # Obter os dados do Bitcoin para o dia anterior
        btc_high, btc_low, btc_close, btc_open = get_bitcoin_data(analysis_date)

        # Data atual
        actual_date = datetime.now(timezone.utc).date()

        # Armazenar os dados no banco de dados
        store_prediction(
            prompt,
            response.choices[0].message.content,  # Captura a resposta da primeira LLM
            recommendation.group(1) if recommendation else None,
            float(trust_rate.group(1)) if trust_rate else None,
            float(stop_loss.group(1)) if stop_loss else None,
            float(take_profit.group(1)) if take_profit else None,
            risk_return.group(1) if risk_return else None,  # Armazena como texto
            btc_high,
            btc_low,
            btc_close,
            btc_open,
            actual_date  
        )

        print(analyzed_data)
        return analyzed_data

if __name__ == "__main__":
    conv = Conversation()
    conv.send()
