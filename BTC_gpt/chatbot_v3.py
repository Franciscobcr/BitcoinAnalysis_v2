from database_setting import get_bitcoin_data
from datetime import datetime, timedelta, timezone
import re
import os
from openai import OpenAI
from exec_script import run_all_analyses  
from database_setting import store_prediction
from prompts import prompts

class Conversation:
    def __init__(self):
        api_key = os.getenv('OPENAI_KEY')
        if not api_key:
            raise ValueError("A chave da API OpenAI não foi encontrada nas variáveis de ambiente.")
        self.client = OpenAI(api_key=api_key)
        print("Cliente OpenAI inicializado.")  

    def analyze_output_with_llm(self, output_from_first_llm):
        second_prompt = f"""
        ### Tarefa:
        Você é uma inteligência artificial especializada em analisar previsões de trading. Recebeu o seguinte output de uma análise de swing trading feita por outra IA. Sua tarefa é extrair as seguintes informações de forma precisa:
        
        1. Recomendação (Compra, Venda, Aguardar)
        2. Nível de Confiança (porcentagem)
        3. Valor do Bitcoin Real no momento(valor numérico)
        4. Stop Loss (valor numérico)
        5. Take Profit (valor numérico)
        6. Relação Risco/Recompensa (valor numérico)
        
        ### Output da outra IA:
        {output_from_first_llm}

        ### Resposta esperada:
        Formate a resposta da seguinte forma:
        Recomendação: <valor>
        Nível de Confiança: <valor %>
        Valor do Bitcoin: <valor numérico com . e não ,>
        Stop Loss: <valor numérico com . e não ,> 
        Take Profit: <valor numérico com . e não,>
        Relação Risco/Recompensa: <TEXTO>
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": second_prompt}]
            )
            analyzed_data = response.choices[0].message.content
            print("Dados analisados pela segunda LLM:", analyzed_data)  # Verifica a resposta da LLM
            return analyzed_data
        except Exception as e:
            print(f"Erro ao conectar à API da OpenAI: {e}")
            return None

    def send(self, analysis_date=None):
        if analysis_date is None:
            analysis_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

        prompt = prompts.btc_analysis_prompt()
        messages = [{"role": "system", "content": prompt}]
        
        try:
            analysis_results = run_all_analyses()
            analysis_str = '\n'.join(f"{key}: {value}" for key, value in analysis_results.items())
        except Exception as e:
            print(f"Erro ao executar as análises: {e}")
            return
        
        messages.append({"role": "user", "content": analysis_str})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            output_from_first_llm = response.choices[0].message.content
            print("Resposta da primeira LLM:", output_from_first_llm)  # Verifica a resposta da primeira LLM
        except Exception as e:
            print(f"Erro ao conectar à API da OpenAI: {e}")
            return

        analyzed_data = self.analyze_output_with_llm(output_from_first_llm)
        
        if not analyzed_data:
            print("Nenhum dado analisado foi retornado.")
            return

        recommendation = re.search(r'Recomendação: (.+)', analyzed_data)
        trust_rate = re.search(r'Nível de Confiança: (\d+)%', analyzed_data)
        value_btc = re.search(r'Valor do Bitcoin: ([\d.]+)', analyzed_data)
        stop_loss = re.search(r'Stop Loss: ([\d.]+)', analyzed_data)
        take_profit = re.search(r'Take Profit: ([\d.]+)', analyzed_data)
        risk_return = re.search(r'Relação Risco/Recompensa: (.+)', analyzed_data)

        print(f"Recomendação: {recommendation.group(1) if recommendation else 'N/A'}")
        print(f"Nível de Confiança: {trust_rate.group(1) if trust_rate else 'N/A'}%")
        print(f"Valor do Bitcoin: {value_btc.group(1) if value_btc else 'N/A'}")
        print(f"Stop Loss: {stop_loss.group(1) if stop_loss else 'N/A'}")
        print(f"Take Profit: {take_profit.group(1) if take_profit else 'N/A'}")
        print(f"Relação Risco/Recompensa: {risk_return.group(1) if risk_return else 'N/A'}")

        try:
            btc_high, btc_low, btc_close, btc_open = get_bitcoin_data(analysis_date)
            print(f"BTC High: {btc_high}, BTC Low: {btc_low}, BTC Close: {btc_close}, BTC Open: {btc_open}")
        except Exception as e:
            print(f"Erro ao obter dados do Bitcoin: {e}")
            return

        actual_date = datetime.now(timezone.utc).date()

        try:
            store_prediction(
                prompt,
                response.choices[0].message.content,
                recommendation.group(1) if recommendation else None,
                float(trust_rate.group(1)) if trust_rate else None,
                float(value_btc.group(1)) if value_btc else None,
                float(stop_loss.group(1)) if stop_loss else None,
                float(take_profit.group(1)) if take_profit else None,
                risk_return.group(1) if risk_return else None,
                btc_high,
                btc_low,
                btc_close,
                btc_open,
                actual_date  
            )
        except Exception as e:
            print(f"Erro ao armazenar dados no banco de dados: {e}")
            return

        print(analyzed_data)
        return analyzed_data


