import logging
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

def get_cosmos_db_client(server, db):
    # Acquire a credential object using managed identity
    credential = DefaultAzureCredential()

    logging.info("creating cosmos db client")
    # Create a CosmosClient object using the managed identity credential
    cosmos_client = CosmosClient(url=f"https://{server}:443/", credential=credential)
    logging.info("created cosmos db client")

    return cosmos_client.get_database_client(db)