from chatbot import Conversation
import streamlit as st
from PIL import Image
import os
import pandas as pd


# Configurações da página
os.environ["TOKENIZERS_PARALLELISM"] = "false"
st.set_page_config(page_title="GPT_BTC", page_icon="🪙", layout="centered")

# Exibir a imagem
image = Image.open('BTC_gpt/DALL·E 2024-09-16 23.13.45 - A detailed and dynamic illustration showing Bitcoin analysis. The central focus is a large Bitcoin symbol surrounded by charts, graphs, and data eleme.jpg')
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

generate_button = st.button("💡 Gerar Análise")


if generate_button:
    prompt = "Análise de swing trading para Bitcoin com base nos dados atuais"
    
    ai_response = Conversation()
    response = ai_response.send()

    st.write(response)
