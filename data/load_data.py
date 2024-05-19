import pandas as pd
import sqlite3


class DataLoader:
    def __init__(self, db_name='trading_data.db'):
        self.db_name = db_name

    def load_data(self, table_name):
        conn = sqlite3.connect(self.db_name)
        query = f"SELECT * FROM {table_name}"
        data = pd.read_sql_query(query, conn)
        conn.close()
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        return data
