# SchemaOnboardAndDataCollateService
Service which onboards all tables data schema and creates and store vector embeddings to provide better context to Open AI / LLM for building database queries. Also once all necessary tables are onboarded we can build queries to collate necessary data at one place and query using pandas sqlite 

**Prerequisites to Delpoy the Service**

1. Function App Account to deploy Function Apps.
2. Azure Key Vault. Add role "Key Vault Secrets User" to Function App's Managed Identity. Update the Key Vault URI in "keyVaultUtils.py".
3. Cosmos Db Postgres to store Schema data along with Embeddings. Make sure to install pgvector extension. check : [Enable Pgvector Extension](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-use-pgvector#enable-extension) Also current code uses user "citus" and database "citus" as per [documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/introduction#always-the-latest-postgresql-features). We use Account Key based Authentication to connect to Postgres. Hence we use Key Vault to store and retrieve Account Key as Secret. Observed issues with Managed Identity. Will need to migrate to Managed Identity in future. Update Postgres host in "postgresUtils.py".
4. Azure Open AI with Chat Completion type. Add "Azure AI Developer" role to Function App's Managed Identity. Update Open AI Endpoint in "openAIUtils.py".
5. Function App uses Managed Identity to read data from respective Databases. So before Onboarding and fetching data via APIs mentioned below we need to add relevant roles for Databases for Function App's Managed Identity.
   
   a. For Azure SQL check :

   [Connect a function app to Azure SQL with managed identity ](https://learn.microsoft.com/en-us/azure/azure-functions/functions-identity-access-azure-sql-with-managed-identity)

   b. For Cosmos DB we need to add "Cosmos DB Built-in Data Reader" Role. check : [Built-in role definitions](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-setup-rbac#built-in-role-definitions)

    Execute below command to add Managed Identity with "Cosmos DB Built-in Data Reader" Role via Azure Cli :
   
    ``
    az cosmosdb sql role assignment create     --resource-group <resource_group>     --account-name <cosmos_db_account_name>  --role-definition-name "Cosmos DB Built-in Data Reader"  --principal-id     
    <principal_id_of_functiona_app_managed_identity>  --scope "/dbs/<cosmos_db_database>"
    ``

   
## Function App REST APIs
1. /OnboardSchema POST

  sample body 1 :
  ``{
    "server" : "abc.database.windows.net",
    "db": "db-test",
    "type" : "sql server"
  }``

  sample body 2 :
  ``{
    "server" : "xyz.documents.azure.com",
    "db": "db-test",
    "type" : "cosmos db nosql"
  }``

currently supported database types are : "sql server", "cosmos db nosql"

Returns Success Response after Onbaording is completed.


2. /GetData POST

sample body :
``{
  "query" : "give me details of orders with ratings less than 2"
}``

Response will return relevant data by querying required tables collating data and returns data in JSON String


**NOTE**

For testing APIs we can use Function App Test Code + Test Playground once Function App is deployed.
For accessing APIs from internet we might require additional Security Credentials. Check : [Securing Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/security-concepts)

