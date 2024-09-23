from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging

def get_secret(secret_name):    
    # Create an instance of the DefaultAzureCredential class
    credential = DefaultAzureCredential()

    # Specify your Azure Key Vault URL
    key_vault_url = "https://xxx.vault.azure.net/"

    logging.info("creating secret client")

    # Create an instance of the SecretClient class
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    logging.info("created secret client")

    # Specify the name of the secret you want to fetch
    secret_name = "postgreskey"

    logging.info("fetching secret")

    # Fetch the secret value from Azure Key Vault
    secret = secret_client.get_secret(secret_name).value
    
    logging.info("fetched secret")
    
    return secret

