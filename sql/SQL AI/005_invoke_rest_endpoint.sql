DECLARE @body nvarchar(max) = N' 

{ 
  "model": "gpt-4o", 
  "messages": [ 
    { "role": "user", "content": "Hello there! Tell me a joke about SQL Server 2025" } 
  ] 

}'; 
  

DECLARE @ret int, 
        @full_response nvarchar(max); 
          

EXEC @ret = sys.sp_invoke_external_rest_endpoint 
  @url = N'https://<your_microsoft_foundry_name>.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-05-01-preview',
  @method = 'POST', 
  @payload = @body, 
  @credential = [https://<your_microsoft_foundry_name>.cognitiveservices.azure.com/],
  @response = @full_response OUTPUT; 

-- Extracting the assistant’s reply and HTTP status code from the JSON response 

SELECT @full_response as full_response, 
    JSON_VALUE(@full_response,'$.result.choices[0].message.content') AS assistant_reply, 
    JSON_VALUE(@full_response,'$.response.status.http.code') AS http_status; 

