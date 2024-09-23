import requests
import logging
from azure.identity import DefaultAzureCredential

instructions = """
    INSTRUCTIONS :
    Generate and give me database query or list of database queries on respective tables, databases to fetch data that user is asking
    If we require querying across multiple tables, databases provide only query syntax for each table separately to fetch required superset of data which can be processed filtered in later process.
    Make sure that we are not generating any queries which are joining tables of different databases or database types.
    Once we get list of all queries to run we insert all data into pandas dataframe to bring it one place and then run the final query to get the final result.
    Final Query on pandas will be in sqlite syntax. Final Query on pandas using sqlite can have joins as the data is in one place.
    If we do not require querying across multiple tables, databases provide only query syntax for the table to fetch required data.
    
    validate the queries syntax if they are correct and can be executed on respective databases.
    For example in cosmos db no sql api we should always use name of collection dot followed by field name in query.
    Similarly check if the query can be executed on sql server. Check syntax correctness.
    
    Also check final query to be executed on pandas using sqlite. 
    Note that for final query the pandas dataframe names will be same as table names in schema provided in context.
    Also for final query check all columns are present in tables in query. 
    The columns present in final query tables are the columns selected as part of queries list that will be generated.
    
    return result in following format :
    
    [
        queries : [
            {
                table : <table_name>,
                query : <query in respective database type>
            }....
        ],
        
        final_query : <final query in sqlite after executing above queries and inserting data into pandas dataframes>
    ]
    
"""

def get_openai_response(prompt):
    # Get the managed identity token
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    # Set up the headers for the request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Set up the payload for the request
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "provide valid json response as requested in instructions"
            },
            {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": prompt
                    }
                ]
            }
        ],
        "temperature": 0.3,
        "top_p": 0.95,
        "max_tokens": 4096
    }

    logging.info("Making request to OpenAI. Prompt: %s", prompt)

    # Make the request to the OpenAI endpoint
    response = requests.post(
        "https://xxx/openai/deployments/gpt-4/chat/completions?api-version=2023-03-15-preview",
        headers=headers,
        json=payload
    )

    logging.info("Received response from OpenAI")

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        logging.error("Open AI Response failed with status code %s: %s", response.status_code, response.text)
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
