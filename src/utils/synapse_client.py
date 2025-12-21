import pyodbc
import os

class SynapseClient:
    def __init__(self):
        self.connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={os.getenv('SYNAPSE_SERVER')};"
            f"Database={os.getenv('SYNAPSE_DATABASE')};"
            f"Authentication=ActiveDirectoryMsi;"
        )
    
    def execute_query(self, query: str):
        with pyodbc.connect(self.connection_string) as conn:
            return conn.execute(query).fetchall()
    
    def create_external_table(self, table_name: str, adls_path: str):
        query = f"""
        CREATE EXTERNAL TABLE {table_name} (
            date DATE,
            location VARCHAR(100),
            pollutant VARCHAR(50),
            value FLOAT
        )
        WITH (
            LOCATION = '{adls_path}',
            DATA_SOURCE = adls_data_source,
            FILE_FORMAT = parquet_format
        )
        """
        self.execute_query(query)