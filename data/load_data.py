import pandas as pd
import sqlite3


class DataLoader:
    def __init__(self, db_name):
        self.db_name = db_name

    def load_data(self, table_name):
        try:
            conn = sqlite3.connect(self.db_name)
            query = f"SELECT * FROM {table_name}"
            data = pd.read_sql(query, conn)
            conn.close()
        except sqlite3.OperationalError as e:
            print(f"Error loading data: {e}")
            data = pd.DataFrame()
        return data
