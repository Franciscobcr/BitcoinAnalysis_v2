from psycopg2 import sql
from database_setting import connect_to_db

def update_db():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        # Lista de todas as colunas que devem estar na tabela
        expected_columns = [
            'id', 'datetime', 'prompt', 'response', 'Recommendation', 'Trust_rate',
            'Stop_loss', 'Take_profit', 'Risk_return', 'BTC_high', 'BTC_low',
            'BTC_close', 'BTC_open', 'prediction_date', 'actual_date'
        ]

        # Verifica quais colunas já existem na tabela
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'chatbot_data';
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]

        # Adiciona as colunas que estão faltando
        for column in expected_columns:
            if column.lower() not in [col.lower() for col in existing_columns]:
                # Determina o tipo de dados para a nova coluna
                if column in ['id']:
                    data_type = 'SERIAL PRIMARY KEY'
                elif column in ['datetime']:
                    data_type = 'TIMESTAMP'
                elif column in ['prompt', 'response', 'Recommendation']:
                    data_type = 'TEXT'
                elif column in ['Trust_rate', 'Stop_loss', 'Take_profit', 'Risk_return', 'BTC_high', 'BTC_low', 'BTC_close', 'BTC_open']:
                    data_type = 'NUMERIC'
                elif column in ['prediction_date', 'actual_date']:
                    data_type = 'DATE'
                else:
                    data_type = 'TEXT'  # Tipo padrão para colunas não especificadas

                # Adiciona a nova coluna
                cursor.execute(sql.SQL("ALTER TABLE chatbot_data ADD COLUMN {} {};").format(
                    sql.Identifier(column),
                    sql.SQL(data_type)
                ))
                print(f"Coluna '{column}' adicionada à tabela chatbot_data.")

        connection.commit()
    connection.close()
    print("Atualização do banco de dados concluída.")

# Exemplo de uso
if __name__ == "__main__":
    update_db()