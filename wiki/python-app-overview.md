# Python OpenAI-Compatible APIs - Deep Dive

## Read this first
- This folder is one application expressed at multiple complexity levels; choose the tier that matches your experience, test depth, and integration surface area.
- All variants talk to the same Bielik 4.5B Ollama model (`MODEL_NAME` is identical across scripts) and return OpenAI-shaped responses so you can swap tiers without rewriting clients.
- Treat every script as a template for self-learning: clone, edit, and rerun to see how changes affect payloads, token usage, and SQL Server insertion.

## Complexity ladder and what you get
- `python/demo_minimal_embeddings.py` - smallest FastAPI surface; two endpoints, no token bookkeeping. Ideal for verifying Ollama connectivity or teaching the request shapes.
- `python/embeddings_api_basic.py` - adds OpenAI-style `index` + `usage` so you can wire basic clients and observe token counts without the rest of the API surface.
- `python/openai_compatible_api.py` - full drop-in surface (embeddings, completions, chat completions) for OpenAI SDKs or tools that expect `choices`, `usage`, and `message` roles.
- `python/ollama_api_project_with_pca` - modular package layout (routers/models/services) plus PCA-based dimensionality reduction to satisfy SQL Server 2025's `VECTOR(1998)` ceiling while using a model that emits 2,048-dim embeddings.

## Detailed walkthroughs (code-line references)

### demo_minimal_embeddings.py (starter)
- Model is hard-coded once at `python/demo_minimal_embeddings.py:8`, keeping behavior consistent while you experiment with request payloads.
- Request/response models are intentionally tiny (`python/demo_minimal_embeddings.py:10-18`) so you can read them at a glance.
- `/generate` proxies a single prompt straight into `ollama.chat` and returns only the assistant message text (`python/demo_minimal_embeddings.py:21-27`), showing the smallest viable chat pattern.
- `/openai/deployments/local/embeddings` normalizes string vs list input (`python/demo_minimal_embeddings.py:31-37`), loops each text, and calls `ollama.embeddings` (`python/demo_minimal_embeddings.py:40-42`); the response mirrors OpenAI's `data` array but omits usage for simplicity.

### embeddings_api_basic.py (baseline OpenAI payload)
- Same model anchor at `python/embeddings_api_basic.py:8`, but schemas add `index` and `usage` to mimic OpenAI responses (`python/embeddings_api_basic.py:14-25`).
- Embedding route keeps the one-call-per-request pattern: string or list is normalized, then a single `ollama.embed` call handles the batch (`python/embeddings_api_basic.py:28-43`).
- Token accounting is lifted directly from Ollama's counters (`prompt_eval_count`/`eval_count`) and placed into `usage.total_tokens` (`python/embeddings_api_basic.py:46-55`), which is often required by downstream cost tracking or rate-limiters.

### openai_compatible_api.py (full contract)
- Complete OpenAI-style schema block lives at `python/openai_compatible_api.py:10-58`, covering embeddings, plain completions, and chat completions with `choices`, `finish_reason`, and `usage`.
- Embeddings endpoint mirrors the basic version but always uses the default Bielik model (`python/openai_compatible_api.py:61-88`), returning `data[index]` objects with embeddings and usage totals.
- Completions endpoint accepts a prompt, forwards it to `ollama.chat`, surfaces token counts, and wraps the text in `choices[0].text` with `finish_reason="stop"` for SDK compatibility (`python/openai_compatible_api.py:90-125`).
- Chat completions converts OpenAI message objects into Ollama's schema (`python/openai_compatible_api.py:133-139`), executes the chat, and returns a single assistant message in `choices[0].message` with usage bookkeeping (`python/openai_compatible_api.py:142-168`).
- Every route shares the same `MODEL_NAME` (`python/openai_compatible_api.py:8`), so moving a client between endpoints does not change model behavior.

## PCA-enabled API for SQL Server 2025 (ollama_api_project_with_pca)
- Why PCA: SQL Server 2025 caps `VECTOR` columns at **1,998 dimensions**, but the Bielik model often emits **2,048 dimensions** depending on quantization. Inserts will fail unless you reduce the vector; PCA preserves variance while fitting the DB limit. Always check the output dimension of any model you adopt.
- Package layout: FastAPI entrypoint wires three routers in `python/ollama_api_project_with_pca/app/main.py:1-8`; the shared model name sits in `python/ollama_api_project_with_pca/app/config.py:1`.
- Schemas: OpenAI-compatible request/response models live in `python/ollama_api_project_with_pca/app/models/openai_schemas.py:5-49`, keeping routers thin.
- Ollama service wrapper: `get_model` ensures a requested model falls back to the default (`python/ollama_api_project_with_pca/app/services/ollama_service.py:4-10`), so switching models is centralized.
- PCA service: constants pin the target dimension to 1,998 and original to 2,048, and set the persisted file path (`python/ollama_api_project_with_pca/app/services/dim_reduction.py:6-9`). `train_pca` fits and saves a reducer when you supply sample vectors (`python/ollama_api_project_with_pca/app/services/dim_reduction.py:18-26`). At runtime `reduce_embedding` loads the PCA if present and transforms each vector; if no PCA file exists it falls back to a simple slice of the first 1,998 values (`python/ollama_api_project_with_pca/app/services/dim_reduction.py:28-40`) so your service stays up even before training.
- Embeddings router: normalizes inputs, calls Ollama once, runs PCA reduction per embedding, and returns OpenAI-shaped payload plus usage totals (`python/ollama_api_project_with_pca/app/routers/embeddings.py:8-28`).
- Completions router: forwards the prompt to Ollama chat, assembles `choices[0].text`, and carries usage totals (`python/ollama_api_project_with_pca/app/routers/completions.py:7-21`).
- Chat completions router: converts role/content pairs into Ollama format, executes chat, and returns the assistant message with usage (`python/ollama_api_project_with_pca/app/routers/chat_completions.py:7-24`).
- Run it with `uvicorn app.main:app --reload` from the `python/ollama_api_project_with_pca` folder (add `--host/--port/--ssl-*` flags as needed).
- Start command (TLS-ready) is documented in `python/run_app_command.txt:1` for quick copy/paste:
 `uvicorn app.main:app --host 127.0.0.1 --port 5001 --ssl-certfile "...cert.crt" --ssl-keyfile "...cert.key"`.

## Adaptation and self-learning checklist (use across all tiers)
- Pick your tier: start with `demo_minimal_embeddings.py` to confirm Ollama and Python env, then move to `embeddings_api_basic.py` for usage-aware payloads, and graduate to `openai_compatible_api.py` or the PCA package for full SDK compatibility or SQL storage.
- Swap models safely: change `MODEL_NAME` in the file you are using (`python/demo_minimal_embeddings.py:8`, `python/embeddings_api_basic.py:8`, `python/openai_compatible_api.py:8`, `python/ollama_api_project_with_pca/app/config.py:1`). Immediately verify the embedding dimension by calling `ollama.embed` in a REPL or via the embeddings endpoint; if it exceeds 1,998, train or regenerate a PCA file before inserting into SQL Server.
- Train PCA for a new model: collect a sample of embeddings (a few hundred typical texts), pass them to `train_pca` (`python/ollama_api_project_with_pca/app/services/dim_reduction.py:18-26`), and keep the resulting `pca_2048_to_1998.pkl` alongside the service. Replace `TARGET_DIM`/`ORIGINAL_DIM` if your model differs, and keep the SQL `VECTOR` column in sync.
- Understand the fallback: if the PCA file is missing, `reduce_embedding` slices the vector to 1,998 dims (`python/ollama_api_project_with_pca/app/services/dim_reduction.py:36-40`). This prevents immediate SQL errors but can drop variance; train PCA as soon as possible.
- Extend endpoints: copy or import the schemas in `openai_compatible_api.py` or `app/models/openai_schemas.py` to add moderation, reranking, or hybrid search routes while keeping OpenAI payload shapes for clients.
- Test iteratively: run the minimal tier first, watch for token counters in the basic/full tiers, then move to PCA-backed service once you are confident dimensions and SSL/DB settings align.

## Key takeaway
This is a layered, OpenAI-compatible template you can adapt for learning, prototyping, or production. The main operational constraint is SQL Server 2025's 1,998-dimension limit versus Bielik's 2,048 outputs; PCA (or another reducer) is mandatory when you persist embeddings. Verify vector size any time you change models, quantization, or providers, then pick the tier that matches your current goal.
