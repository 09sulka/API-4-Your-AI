USE pubmed;
GO

-- Enable server-level support for external endpoints and scoped credentials.
EXECUTE sp_configure 'allow server scoped db credentials', 1;
EXECUTE sp_configure 'external rest endpoint enabled', 1;
RECONFIGURE WITH OVERRIDE;
GO


-- In theory it isn�t necessary, but if a database has been migrated from earlier versions of SQL Server, 
-- sometimes you need to enable preview features for everything to work correctly. 
-- I think this is probably a bug.
ALTER DATABASE SCOPED CONFIGURATION SET PREVIEW_FEATURES = ON;
GO


--DROP EXTERNAL MODEL BielikLocalhost
--DROP DATABASE SCOPED CREDENTIAL  [https://127.0.0.1:5001]
--DROP MASTER KEY



-- Create the master key protecting database-scoped credentials.
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'MySuperSecretPassword2025!';
GO

-- Credential for Azure OpenAI embedding endpoint.
CREATE DATABASE SCOPED CREDENTIAL [https://<your_microsoft_foundry_name>.cognitiveservices.azure.com/]
    WITH IDENTITY = 'HTTPEndpointHeaders',
         SECRET = '{"api-key":"my-azure-openai-api-key"}';
GO

-- External embedding model pointing to Azure OpenAI deployment.
CREATE EXTERNAL MODEL AzureTextEmbeddingSmall
WITH (
    LOCATION = 'https://<your_microsoft_foundry_name>.cognitiveservices.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-05-15',
    API_FORMAT = 'Azure OpenAI',
    MODEL_TYPE = EMBEDDINGS,
    MODEL = 'text-embedding-3-small',
    CREDENTIAL = [https://<your_microsoft_foundry_name>.cognitiveservices.azure.com/]
);
GO

-- Credential for the local Bielik embedding endpoint.
CREATE DATABASE SCOPED CREDENTIAL [https://127.0.0.1:5001]
    WITH IDENTITY = 'HTTPEndpointHeaders',
         SECRET = '{"api-key":"not important"}';
GO

-- External embedding model pointing to the local Bielik deployment.
CREATE EXTERNAL MODEL BielikLocal
WITH (
    LOCATION = 'https://127.0.0.1:5001/openai/deployments/local/embeddings',
    API_FORMAT = 'Azure OpenAI', --Ollama also works here but has different URL for accessing embeddings. check Ollama documentation for details 
    MODEL_TYPE = EMBEDDINGS,
    MODEL = 'local',
    CREDENTIAL = [https://127.0.0.1:5001]
);
GO

-- Quick smoke test to verify the Bielik model responds.
SELECT AI_GENERATE_EMBEDDINGS('test' USE MODEL BielikLocal);
GO

-- Table naming convention:
--   pubmed_article_chunk_vector   -> embeddings from BielikLocal (PCA-reduced 1998 dims)
--   pubmed_article_chunk_vector_2 -> embeddings from text-embedding-3-small (Azure/OpenAI)

-- What happens when we exceed the token limit?
-- http 400 error is returned from the endpoint, no details what exactly happened
SELECT TOP (8) a.id,
       AI_GENERATE_EMBEDDINGS(a.article_text USE MODEL AzureTextEmbeddingSmall)
FROM [dbo].[pubmed_article] AS a;
GO
