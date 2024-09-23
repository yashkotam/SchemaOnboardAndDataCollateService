import pyodbc
import logging
from azure.identity import DefaultAzureCredential

def get_sql_connection(server, database):
    # Get a token credential for managed identity
    #credential = DefaultAzureCredential()
    #token = credential.get_token("https://database.windows.net/").token

    # Create a connection string
    connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Authentication=ActiveDirectoryMsi"

    logging.info("creating sql connection") 

    # Establish the connection
    connection = pyodbc.connect(connection_string)
    
    logging.info("sql connection created")
    
    return connection