import pandas as pd
from datetime import datetime, timedelta
from database_setting import connect_to_db
    
    
def calculate_cumulative_return():
    connection = connect_to_db()
    query = """
    SELECT 
        datetime,
        prediction_date,
        actual_date,
        btc_open,
        btc_high,
        btc_low,
        btc_close,
        stop_loss,
        take_profit,
        recommendation
    FROM 
        chatbot_data
    WHERE 
        actual_date IS NOT NULL
        AND stop_loss IS NOT NULL
        AND take_profit IS NOT NULL
        AND recommendation IS NOT NULL
    ORDER BY 
        prediction_date
    """
    df = pd.read_sql_query(query, connection)
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['prediction_date'] = pd.to_datetime(df['prediction_date'])
    df['actual_date'] = pd.to_datetime(df['actual_date'])
    
    df = df.sort_values('datetime')
    
    # Initialize variables
    cumulative_return = 0
    current_position = None
    entry_price = None
    results = []

    for i, row in df.iterrows():
        date = row['prediction_date']
        recommendation = row['recommendation']
        btc_open = row['btc_open']
        btc_high = row['btc_high']
        btc_low = row['btc_low']
        btc_close = row['btc_close']
        stop_loss = row['stop_loss']
        take_profit = row['take_profit']

        if current_position:
            if current_position == 'Buy':
                if btc_low <= stop_loss:
                    return_pct = (stop_loss - entry_price) / entry_price
                    cumulative_return += return_pct
                    current_position = None
                elif btc_high >= take_profit:
                    return_pct = (take_profit - entry_price) / entry_price
                    cumulative_return += return_pct
                    current_position = None
                else:
                    return_pct = (btc_close - entry_price) / entry_price
                    cumulative_return += return_pct
            elif current_position == 'Sell':
                if btc_high >= stop_loss:
                    return_pct = (entry_price - stop_loss) / entry_price
                    cumulative_return += return_pct
                    current_position = None
                elif btc_low <= take_profit:
                    return_pct = (entry_price - take_profit) / entry_price
                    cumulative_return += return_pct
                    current_position = None
                else:
                    return_pct = (entry_price - btc_close) / entry_price
                    cumulative_return += return_pct

        # Open new position
        if recommendation == 'Compra' and not current_position:
            current_position = 'Buy'
            entry_price = btc_open
        elif recommendation == 'Venda' and not current_position:
            current_position = 'Sell'
            entry_price = btc_open

        results.append({
            'date': date,
            'cumulative_return': cumulative_return
        })

    return results


cumulative_returns = calculate_cumulative_return()
for result in cumulative_returns:
    print(f"Date: {result['date']}, Cumulative Return: {result['cumulative_return']:.4f}")