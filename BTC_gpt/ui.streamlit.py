from chatbot import Conversation
import streamlit as st
from PIL import Image
import os
import pandas as pd


# Configurações da página
os.environ["TOKENIZERS_PARALLELISM"] = "false"
st.set_page_config(page_title="GPT_BTC", page_icon="🪙", layout="centered")

# Exibir a imagem
image = Image.open('C:/Users/Francisco/Pictures/linkedin.jfif')
st.image(image, use_column_width=True)

# Título da página
st.title("📈 GPT Analista de BTC")

# Descrição com markdown e CSS
st.markdown("""
<style>
    .main-description {
        font-size: 18px;
        font-weight: 500;
        line-height: 1.6;
    }
</style>
<div class="main-description">
    Um chatbot inteligente especializado em análise de Bitcoin para operações de swing trading. 
    Ele utiliza dados em tempo real de derivativos, on-chain, análise técnica e macroeconômica para fornecer previsões dinâmicas e recomendações ajustadas conforme as condições do mercado.
</div>
""", unsafe_allow_html=True)

# Botão para gerar a análise
generate_button = st.button("💡 Gerar Análise")

# Se o botão for clicado, gerar a resposta do Chatbot e salvar no CSV
if generate_button:
    # Exemplo de prompt enviado ao chatbot
    prompt = "Análise de swing trading para Bitcoin com base nos dados atuais"
    
    # Gerar a resposta do chatbot
    ai_response = Conversation()
    response = ai_response.send()

    # Exibir a resposta do Chatbot no Streamlit
    st.write(response)
