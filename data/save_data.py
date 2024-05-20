from sqlalchemy import create_engine
import pandas as pd


class DataSaver:
    def __init__(self, db_path):
        self.engine = create_engine(db_path)

    def save_to_db(self, data, table_name):
        data.to_sql(table_name, self.engine, if_exists='replace', index=False)
