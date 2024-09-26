import pandas as pd
from datetime import datetime, timedelta
from database_setting import connect_to_db
import requests
import streamlit as st
import plotly.graph_objs as go
    
def calculate_cumulative_return():
    connection = connect_to_db()
    query = """
    SELECT 
        prediction_date,
        btc_open,
        btc_close,
        recommendation
    FROM 
        chatbot_data
    WHERE 
        actual_date IS NOT NULL
    ORDER BY 
        prediction_date
    """
    df = pd.read_sql_query(query, connection)
    
    df['prediction_date'] = pd.to_datetime(df['prediction_date'])
    df = df.sort_values('prediction_date')
    
    cumulative_return = 0
    results = []
    previous_close = df['btc_open'].iloc[0]  # Use the first open price as the starting point

    for _, row in df.iterrows():
        date = row['prediction_date']
        close = row['btc_close']
        recommendation = row['recommendation']

        if recommendation.lower() != 'aguardar':
            daily_return = (close - previous_close) / previous_close
            cumulative_return += daily_return
        else:
            daily_return = 0  # No change in return for 'Aguardar'

        results.append({
            'date': date.strftime('%Y-%m-%d'),
            'cumulative_return': cumulative_return
        })

        previous_close = close

    return results

def calculate_btc_cumulative_return():
    connection = connect_to_db()
    query = """
    SELECT MIN(prediction_date) as start_date, MAX(prediction_date) as end_date
    FROM chatbot_data
    WHERE actual_date IS NOT NULL
    """
    date_range = pd.read_sql_query(query, connection)
    start_date = date_range['start_date'].iloc[0]
    end_date = date_range['end_date'].iloc[0]

    # Convert date to datetime at midnight UTC
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)

    # Convert datetimes to Unix timestamps
    start_timestamp = int(start_datetime.timestamp())
    end_timestamp = int(end_datetime.timestamp())

    # CoinGecko API request for the entire date range
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=usd&from={start_timestamp}&to={end_timestamp}"
    response = requests.get(url)
    data = response.json()

    if 'prices' in data:
        prices_df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        prices_df['date'] = pd.to_datetime(prices_df['timestamp'], unit='ms').dt.date
        
        # Group by date and take the last price of each day
        daily_prices = prices_df.groupby('date')['price'].last().reset_index()
        
        cumulative_return = 0
        results = []
        previous_price = daily_prices['price'].iloc[0]

        for _, row in daily_prices.iterrows():
            date = row['date']
            price = row['price']
            
            daily_return = (price - previous_price) / previous_price
            cumulative_return += daily_return

            results.append({
                'date': date.strftime('%Y-%m-%d'),
                'cumulative_return': cumulative_return
            })

            previous_price = price

        return results
    else:
        print("Error fetching data from CoinGecko API")
        return []

def prepare_data_for_graph(ai_returns, btc_returns):
    ai_df = pd.DataFrame(ai_returns)
    ai_df['date'] = pd.to_datetime(ai_df['date'])
    ai_df = ai_df.rename(columns={'date': 'prediction_date'})

    btc_df = pd.DataFrame(btc_returns)
    btc_df['date'] = pd.to_datetime(btc_df['date'])

    # Ensure both dataframes cover the same date range
    start_date = max(ai_df['prediction_date'].min(), btc_df['date'].min())
    end_date = min(ai_df['prediction_date'].max(), btc_df['date'].max())

    ai_df = ai_df[(ai_df['prediction_date'] >= start_date) & (ai_df['prediction_date'] <= end_date)]
    btc_df = btc_df[(btc_df['date'] >= start_date) & (btc_df['date'] <= end_date)]

    return ai_df, btc_df

def display_comparison_graph(ai_returns, btc_returns):
    operation_data, btc_data = prepare_data_for_graph(ai_returns, btc_returns)

    st.header("Comparação de Rentabilidade")
    
    fig = go.Figure()

    if not operation_data.empty:
        fig.add_trace(go.Scatter(
            x=operation_data['prediction_date'], 
            y=operation_data['cumulative_return'] * 100, 
            mode='markers+lines', 
            name='Rentabilidade das Operações'
        ))

    if not btc_data.empty:
        fig.add_trace(go.Scatter(
            x=btc_data['date'], 
            y=btc_data['cumulative_return'] * 100, 
            mode='markers+lines', 
            name='Rentabilidade do Bitcoin'
        ))

    fig.update_layout(
        title='Comparação de Rentabilidade: Operações vs Bitcoin',
        xaxis_title='Data',
        yaxis_title='Retorno Cumulativo (%)',
        showlegend=True
    )

    y_min = min(operation_data['cumulative_return'].min() if not operation_data.empty else 0,
                btc_data['cumulative_return'].min() if not btc_data.empty else 0) * 100
    y_max = max(operation_data['cumulative_return'].max() if not operation_data.empty else 0,
                btc_data['cumulative_return'].max() if not btc_data.empty else 0) * 100
    y_range = y_max - y_min
    fig.update_yaxes(range=[y_min - 0.1 * y_range, y_max + 0.1 * y_range])

    st.plotly_chart(fig)

    st.write(f"Número de registros de operações: {len(operation_data)}")
    st.write(f"Número de registros de retornos do Bitcoin: {len(btc_data)}")

# Main execution
def main():
    ai_returns = calculate_cumulative_return()
    btc_returns = calculate_btc_cumulative_return()
    display_comparison_graph(ai_returns, btc_returns)

if __name__ == "__main__":
    main()