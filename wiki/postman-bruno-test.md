
# 🧪 Manual Postman/Bruno Test  
Quick‑test your **local OpenAI‑compatible FastAPI model** using Postman, Bruno, or raw `curl`.  
Endpoints assume the gateway is running at **https://127.0.0.1:5001**.

---

## ✏️ Text Completions (one‑shot)

```bash
curl --request POST \
  --url https://127.0.0.1:5001/openai/deployments/local/completions \
  --header 'content-type: application/json' \
  --data '{
  "prompt": "Hi Bielik. Tell me a joke about SQL Server"
}'
```

---

## 💬 Chat Completions (system + user)

```bash
curl --request POST \
  --url https://127.0.0.1:5001/openai/deployments/local/chat/completions \
  --header 'content-type: application/json' \
  --data '{
  "messages": [
    {
      "role": "developer",
      "content": "You are a super helpful AI assistant. You only answer in English and always add a fun fact or joke about SQL Server."
    },
    {
      "role": "user",
      "content": "Cześć Bielik! Powiedz mi jak życ?"
    }
  ]
}'
```

---

## 🔡 Embeddings (multi‑input)

```bash
curl --request POST \
  --url https://127.0.0.1:5001/openai/deployments/local/embeddings \
  --header 'content-type: application/json' \
  --data '{
  "input": [
    "hello",
    "world"
  ]
}'
```

---

### 💡 Pro Tip  
If TLS causes issues in Postman/Bruno, enable **“Allow insecure/self‑signed certificates”** for the collection and retry.
