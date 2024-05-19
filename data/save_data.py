from sqlalchemy import create_engine


class DataSaver:
    def __init__(self, db_name='trading_data.db'):
        self.engine = create_engine(f'sqlite:///{db_name}')

    def save_to_db(self, data, table_name):
        if data.empty:
            print(f"No data to save for table {table_name}")
            return
        data.to_sql(table_name, self.engine, if_exists='replace', index=False)
