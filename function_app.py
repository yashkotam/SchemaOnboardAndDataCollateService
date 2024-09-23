import azure.functions as func
import logging
import traceback
from postgresUtils import create_connection
from schemaTableUtils import *
from openAIUtils import get_openai_response
from dataQueryUtils import execute_queries_list
from openAIUtils import instructions

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="OnboardSchema")
def OnboardSqlSchema(req: func.HttpRequest) -> func.HttpResponse:
    
    try:
        req_body = req.get_json()
        server = req_body.get('server')
        db = req_body.get('db')
        type = req_body.get('type')
      
        logging.info('onboarding schema for server: %s, db: %s', server, db)
        
        postgres_conn = create_connection()
        
        schema_rows = get_tables_schema(server, db, type)
        insert_table_info(postgres_conn, server, db, schema_rows, type)
        
        return func.HttpResponse(
                "onboarded schema for server: %s, db: %s" % (server, db),
                status_code=200
            )
    except Exception as e:
        logging.error('Error onboarding schema: %s', e)
        return func.HttpResponse(
                "Error onboarding schema",
                status_code=500
            )
 
def attempt_fetch_user_query(query, relevant_schema, previous_response):
    
    previous_query_list = None
    stack_trace = None
    
    if previous_response:
        previous_query_list =  previous_response['queries']
        stack_trace = previous_response['stack_trace']
        
    prompt = "The user query is : " + query  
    prompt = prompt  + ". \n Following is the information and schema about relevant tables related to what user might be asking : \n " + json.dumps(relevant_schema, indent=4)
    prompt = prompt + f".\n {instructions}"
    
    if previous_query_list:
        logging.info("previous attempt by Open AI to generate queries failed. This is another attempt")
        prompt = prompt + "NOTE : Previous attempt by Open AI / GPT Failed. This is another attempt. To give more context below are previously identified queries by Open AI / GPT: \n"
        prompt = prompt + f".\n Previous queries list generated : {json.dumps(previous_query_list, indent=4)}"
        prompt = prompt + ".\n with above previous queries identified we got below exception stack trace ."
        prompt = prompt + f".\n {stack_trace}"
        prompt = prompt + ".\n try to identify issue with previous queries generated and this time rectify and generate accurate queries."
        prompt = prompt + ".\n NOTE : Do not give any explanation of issue identified or any explanations. Stick to the response format mentioned in INSTRUCTIONS."
    
    response = get_openai_response(prompt)
    
    response = response['choices'][0]['message']['content']
    
    response = response.replace("```json\n", "").replace("```", "")
    
    queries_list = json.loads(response)
    
    logging.info('queries list : %s', json.dumps(queries_list, indent=4))
    
    previous_response['queries'] = queries_list
    
    try:
        result = execute_queries_list(queries_list, relevant_schema)
    except Exception as e:
        stack_trace = traceback.format_exc()
        previous_response['stack_trace'] = stack_trace
        logging.error('stack trace : %s', stack_trace)
        return None
        
    logging.info('result : %s', json.dumps(result, indent=4, default=str))
    
    return result
        
 
@app.route(route="GetData")
def GetData(req: func.HttpRequest) -> func.HttpResponse:
    
    attempt_threshold = 3
    attempt = 1
    result = None
    previous_response = {}
    
    try:
        req_body = req.get_json()
        query = req_body.get('query')
      
        logging.info('query received %s', query)
        
        postgres_conn = create_connection()
        
        table_info = get_relevant_table_schema(postgres_conn, query)
        
        relevant_schema = []
        
        for row in table_info:
            schema = {}
            schema['server'] = row['server']
            schema['database'] = row['database']
            schema['table'] = row['table']
            schema['schema'] = json.loads(row['schema'])
            schema['type'] = row['type']
            relevant_schema.append(schema)
               
        while attempt <= attempt_threshold:
            logging.info('attempt : %s', attempt)
            result = attempt_fetch_user_query(query, relevant_schema, previous_response)
            if(result):
                break
            attempt = attempt + 1    

        if not result:
            return func.HttpResponse(
                "error fetching data",
                status_code=500
            ) 
            
        return func.HttpResponse(
                "response to query : %s" % (json.dumps(result, indent=4, default=str)),
                status_code=200
            )
    except Exception as e:
        logging.error('Error fetching data: %s', e)
        stack_trace = traceback.format_exc()
        logging.error('stack trace : %s', stack_trace)
        return func.HttpResponse(
                "error fetching data",
                status_code=500
            )
