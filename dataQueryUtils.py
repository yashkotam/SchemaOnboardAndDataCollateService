import logging
import pandas as pd
import json
import pandasql as psql
from decimal import Decimal
from sqlUtils import get_sql_connection
from cosmosDbUtils import get_cosmos_db_client

# Function to convert `decimal.Decimal` to float as sqlite does not support decimal
def decimal_to_float(x):
    if isinstance(x, Decimal):
        return float(x)
    return x

def execute_queries_list(total_queries_list, tables):
    
    queries_list = total_queries_list['queries']
    
    result = []
    
    table_map = {}
    table_df_map = {}
    
    for table in tables:
        table_map[table['table']] = table
    
    for query in queries_list:
       table = query['table']
       query_str = query['query']
       table_type = table_map[table]['type']
       server = table_map[table]['server']
       database = table_map[table]['database']
       rows = []
       if table_type == "sql server":
           rows = execute_sql_query(server, database, query_str)
       elif table_type == "cosmos db nosql":
           rows = execute_cosmos_query(server, database, table, query_str)
           
       if(len(queries_list)==1):
           return rows
           
       logging.info("inserting into dataframe %s", table)
       table_df_map[table] = pd.DataFrame(rows)
       table_df_map[table] = table_df_map[table].applymap(decimal_to_float)
       logging.info(table_df_map[table])
       logging.info("inserted into dataframe %s", table)
    
    final_query = total_queries_list['final_query']
    
    logging.info("executing final query : %s", final_query)
    result = psql.sqldf(final_query, table_df_map)
    logging.info("executed final query")
    
    result = result.to_json(orient='records')
    
    logging.info("final result : %s", json.dumps(result, default=str))
    
    return result      

def execute_sql_query(server, database, query):
    # Get a token credential for managed identity
    
    sql_conn = get_sql_connection(server, database)
    
    # Create a cursor from the connection
    cursor = sql_conn.cursor()
    
    logging.info("executing sql query : %s", query)
    
    # Execute the query
    cursor.execute(query)
    
    logging.info("executed sql query")
    
    # Fetch the results
    rows = cursor.fetchall()
    
    # Get column names from the cursor description
    columns = [column[0] for column in cursor.description]
    
    # Convert rows to list of dictionaries
    data = [dict(zip(columns, row)) for row in rows]
    
    logging.info("fetched data from sql query :  %s", json.dumps(data, default=str))
    
    # Close the cursor and connection
    cursor.close()
    sql_conn.close()
    
    return data

def execute_cosmos_query(server, database, container, query):

    database_client = get_cosmos_db_client(server, database)
    
    result = []
    
    container_client = database_client.get_container_client(container)
    
    logging.info("executing cosmos query : %s", query)
    
    items = list(container_client.query_items(query=query, enable_cross_partition_query=True))
    
    logging.info("executed cosmos query")
    
    data = [
        {key: value for key, value in item.items() if not key.startswith('_')}
        for item in items
    ]
    
    logging.info("fetched data from cosmos query :  %s", json.dumps(data, default=str))
    
    result.extend(data)
    
    return result