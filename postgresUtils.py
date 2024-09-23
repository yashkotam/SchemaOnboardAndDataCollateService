import psycopg2
import logging
from keyVaultUtils import get_secret

# Connection details
host = 'xxx.postgres.cosmos.azure.com'
port = '5432'
database = 'citus'
user = 'citus'

def create_connection():
    
    logging.info("creating connection")
    
    password = get_secret("postgreskey")
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    logging.info("connection created successfully")
    
    return conn

