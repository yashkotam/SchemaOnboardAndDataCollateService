import json
import logging
from embeddingUtils import generate_embedding
from sqlUtils import get_sql_connection
from cosmosDbUtils import get_cosmos_db_client
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

def get_tables_schema(server, db, type):
    
    schema_rows = []
    
    if type=="sql server":
        schema_rows = get_sql_tables_schema(server, db)
    elif type=="cosmos db nosql":
        schema_rows = get_cosmos_nosql_tables_schema(server, db)
    
    return schema_rows

def get_cosmos_nosql_tables_schema(server, db):
    
    database_client = get_cosmos_db_client(server, db)

    logging.info("fetching list of containers in cosmos db")
    # List all containers
    containers = database_client.list_containers()
    logging.info("fetched list of containers in cosmos db ")
    
    logging.info("fetching schema of data in each container")
    # Fetch schema of data in each container
    result = []
    for container in containers:
        logging.info("fetching schema of data in container %s", container['id'])
        container_client = database_client.get_container_client(container['id'])
        query = "SELECT * FROM c OFFSET 0 LIMIT 1"
        items = list(container_client.query_items(query=query, enable_cross_partition_query=True))
        logging.info("fetched schema of data in container %s : %s", container['id'], json.dumps(items))
        if items:
            item = items[0]
            schema = [{"columnName": key, "columnType": type(value).__name__} for key, value in item.items()]
            result.append([container['id'], json.dumps(schema)])
    
    logging.info("fetched schema of all containers in cosmos db %s", json.dumps(result))
    return result    
    
def get_sql_tables_schema(server, db):
    
    sql_conn = get_sql_connection(server, db)
    
    cursor = sql_conn.cursor()

    # Define the SQL query
    sql_query = """
    SELECT 
        TABLE_NAME AS [table],
        JSON_QUERY(
            (
                SELECT 
                    COLUMN_NAME AS columnName,
                    DATA_TYPE AS columnType
                FROM 
                    INFORMATION_SCHEMA.COLUMNS 
                WHERE 
                    TABLE_NAME = t.TABLE_NAME
                FOR JSON PATH
            )
        ) AS tableSchema
    FROM 
        INFORMATION_SCHEMA.TABLES t
    WHERE 
        TABLE_TYPE = 'BASE TABLE'
    """

    logging.info("Executing query: %s", sql_query)

    # Execute the query
    cursor.execute(sql_query)
    
    logging.info("Executed query")

    # Fetch the result
    rows = cursor.fetchall()
    result = []

    for row in rows:
        result.append(list(row))

    # Print the result object
    # [['table1','schemaJsonStr1']['table2','schemaJsonStr2']]
    logging.info(result)

    # Close the connection
    cursor.close()
    sql_conn.close()
    
    return result
    
def insert_table_info(conn, server, db, schema_rows, type):
    
    cursor = conn.cursor()

    logging.info("inserting into table info")

    for row in schema_rows:
        server_first_str = server.split('.')[0]
        id = f"{server_first_str}_{db}_{row[0]}"
        
        schemaJson = json.loads(row[1])
        schema_str = f"{row[0]} " + " ".join([f"{col['columnName']} " for col in schemaJson])
        embedding = generate_embedding(schema_str)
        
        insert_query = """INSERT INTO table_info (table_id, table_name, server, database, type, schema, embedding)
         VALUES (%s, %s, %s, %s, %s, %s, %s) 
         ON CONFLICT (table_id) DO UPDATE SET embedding = EXCLUDED.embedding, schema = EXCLUDED.schema, type = EXCLUDED.type;"""
        
        cursor.execute(insert_query, (id, row[0], server, db, type, row[1], embedding.tolist()))
    
    conn.commit()
    cursor.close()
    
    logging.info("inserted into table info")
    
def get_relevant_table_schema(conn, query):
    
    embedding = generate_embedding(query)
    
    cursor = conn.cursor()
    
    embedding_query =  """
    SELECT table_name, server, database, schema, type, 1 - (embedding <=> %s::vector) AS cosine_similarity
    FROM table_info
    ORDER BY cosine_similarity DESC
    LIMIT 5;
    """
    
    logging.info("Executing query: %s", embedding_query)
    
    cursor.execute(embedding_query, (embedding.tolist(),))
    
    logging.info("Executed query")
    
    rows = cursor.fetchall()
    
    result = []

    for row in rows:
        table_info = {}
        table_info["table"] = row[0]
        table_info["server"] = row[1]
        table_info["database"] = row[2]
        table_info["schema"] = row[3]
        table_info["type"] = row[4]
        table_info["cosine_similarity"] = row[5]
        result.append(table_info)

    # Print the result object
    logging.info(result)

    return result
    
    