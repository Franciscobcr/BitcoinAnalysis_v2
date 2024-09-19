import pandas as pd
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

def analisar_previsao(previsao):
    prompt = f"""
    A previsão a seguir foi gerada por um modelo analítico com base em dados de derivativos, on-chain, análise técnica e macroeconômica para o preço do Bitcoin. Verifique se a previsão faz sentido e se há lógica nas suposições feitas. Caso discorde de algo, aponte os motivos:

    Previsão: {previsao}

    Baseado nisso, analise se as justificativas e a conclusão da previsão são adequadas.
    """
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Você é um analista de mercado especializado em criptoativos."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def processar_previsoes():

    df = pd.read_excel('chatbot_data.xlsx', sheet_name='chatbot_analysis_data')
    analises = []
    
    # Iterar sobre cada linha do DataFrame e enviar para a API
    for index, row in df.iterrows():
        previsao = row['response']
        analise = analisar_previsao(previsao)
        analises.append(analise)  # Adicionar a análise à lista
    
    df['analise_gpt'] = analises
    
    df.to_csv('analise_previsoes.csv', index=False)

    print("Fim")

# Executar o código
if __name__ == "__main__":
    processar_previsoes()
