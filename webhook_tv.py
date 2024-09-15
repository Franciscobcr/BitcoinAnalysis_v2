import json
import os
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f"Dados recebidos: {data}")
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    data_atual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"data/dados_recebidos_{data_atual}.json"
    
    with open(nome_arquivo, 'w') as f:
        json.dump(data, f, indent=4)
    
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

