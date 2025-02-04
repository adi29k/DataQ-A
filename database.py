import mysql.connector
from typing import Dict

def get_database_connection(connection_params: Dict):
    try:
        connection = mysql.connector.connect(**connection_params)
        print("Successfully connected to database")
        return connection
    except Exception as e:
        raise Exception(f"Database connection error: {str(e)}")