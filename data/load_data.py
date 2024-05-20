from sqlalchemy import create_engine
import pandas as pd


class DataLoader:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{self.db_path}")

    def load_data(self, table_name):
        try:
            data = pd.read_sql_table(table_name, self.engine)
        except Exception as e:
            print(f"Error loading data: {e}")
            data = pd.DataFrame()
        return data
