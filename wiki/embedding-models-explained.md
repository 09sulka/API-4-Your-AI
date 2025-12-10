# Why Two Models Are Used

This repository demonstrates how to generate embeddings and perform semantic search with two very different language models:

- **OpenAI text-embedding-3-small** — a dedicated embedding model.
- **Bielik-4.5B-v3.0-Instruct**, quantized GGUF version **Q8_0** from HuggingFace: https://hf.co/speakleash/Bielik-4.5B-v3.0-Instruct-GGUF.

The pairing is intentional and serves an educational, comparative purpose. It shows both the correct use of a specialized embedding model and the practical limits of using a generative LLM for embeddings.

## text-embedding-3-small — proper semantic search embeddings

`text-embedding-3-small` is trained specifically for semantic search, ranking, clustering, classification, RAG, and multilingual workloads (including Polish).

**Advantages**

- High-quality, contrastively trained embeddings in a normalized vector space (great for cosine similarity).
- Strong performance on European languages, often outperforming open-source models.
- Lightweight, inexpensive, and fast for production use.
- Stable results regardless of input length.

**Limitations**

- Requires the OpenAI API; cannot run fully offline.
- For niche domains, the large variant may deliver higher accuracy.

## Bielik-4.5B-v3.0-Instruct (GGUF Q8_0) — intentionally non-embedding

`Bielik-4.5B-v3.0-Instruct-GGUF:Q8_0` is a quantized, instruction-tuned, decoder-only Polish LLM meant for text generation and instruction following, not embeddings. It is included to prove a point:

> You can extract embeddings from almost any LLM, but that does not mean they will be good for semantic search.

In this repo, Bielik is used to:

- Run a local GGUF model from HuggingFace with no external API calls.
- Demonstrate integration with SQL Server in an end-to-end pipeline.
- Contrast embeddings from a generative model against a dedicated embedding model.

**Advantages in this demo**

- Fully local execution.
- Helpful for showing the pipeline (local model → API → SQL Server).
- Provides a clear counterpoint to a proper embedding model.

**Limitations as an embedding model**

- No contrastive training, so semantic similarity is weak.
- Vectors are not normalized or arranged semantically.
- Cosine similarity does not reflect true meaning.
- Accuracy is low for semantic search tasks.
- Embeddings are unstable and sensitive to prompt phrasing and context.

## Summary

| Model                                     | Intended use    | Embedding quality | Purpose in this project                                      |
| ----------------------------------------- | --------------- | ----------------- | ------------------------------------------------------------ |
| text-embedding-3-small                    | Embedding model | High              | Proper semantic search implementation                        |
| Bielik-4.5B-v3.0-Instruct (GGUF Q8_0)     | Generative LLM  | Very low          | Demonstration of offline execution and SQL Server integration |
