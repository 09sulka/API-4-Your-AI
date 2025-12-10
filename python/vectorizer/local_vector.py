import pyodbc
import json
import logging
import sys
import time
import asyncio
import aiohttp
import tiktoken
import ssl
from concurrent.futures import ThreadPoolExecutor

# ------------------------------------------------------------
# LOGGING SETUP
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger()

# ------------------------------------------------------------
# REAL TOKENIZER (o200k_base for text-embedding-3-small)
# ------------------------------------------------------------
tokenizer = tiktoken.get_encoding("o200k_base")

def count_tokens(text: str) -> int:
    """Return number of real GPT tokens."""
    return len(tokenizer.encode(text))

# ------------------------------------------------------------
# SQL CONNECTION
# ------------------------------------------------------------
db_connection_parameters = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost;"
    "Database=pubmed;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

database_connection = pyodbc.connect(db_connection_parameters)
cursor = database_connection.cursor()

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
select_batch_size   = 50       # SELECT 50 rows per iteration
embed_micro_batch   = 10       # embedding model receives 10 texts per POST
max_concurrent_embed_requests = 1
max_concurrent_inserts = 4

field_to_be_vectorized = "t.text_chunk"
source_table = "pubmed_article_chunk"
vector_table = "pubmed_article_chunk_vector"  # UPDATED TABLE NAME

vector_size = 1998  # dimension of your embedding model

embedding_api_url = (
    "https://localhost:5001/openai/deployments/local/embeddings"
)

# ------------------------------------------------------------
# ASYNC EMBEDDING WORKERS
# ------------------------------------------------------------
async def embed_microbatch(session, texts, batch_index):
    """
    Sends a micro-batch to embedding server with retry logic.
    """
    for attempt in range(3):
        try:
            async with session.post(embedding_api_url, json={"input": texts}) as resp:
                if resp.status != 200:
                    raise RuntimeError(await resp.text())

                data = await resp.json()
                embs = [d["embedding"] for d in data["data"]]
                return batch_index, embs

        except Exception as e:
            logger.error(f"Microbatch {batch_index} failed attempt {attempt+1}: {e}")
            await asyncio.sleep(1)

    raise RuntimeError(f"Microbatch {batch_index} failed after retries.")


async def embed_full_batch(texts):
    """
    Splits into micro-batches and processes them in parallel.
    """
    chunks = []
    for i in range(0, len(texts), embed_micro_batch):
        chunks.append((i // embed_micro_batch, texts[i:i + embed_micro_batch]))

    ssl_context = ssl.create_default_context(cafile="C:/SelfSSL/MyCert/cert.crt")
    connector = aiohttp.TCPConnector(limit=max_concurrent_embed_requests, ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            embed_microbatch(session, chunk, idx)
            for idx, chunk in chunks
        ]
        results = await asyncio.gather(*tasks)

    # Sort micro-batches by original order
    results.sort(key=lambda x: x[0])

    # Flatten embeddings
    final_embeddings = []
    for _, emb_list in results:
        final_embeddings.extend(emb_list)

    return final_embeddings

# ------------------------------------------------------------
# PARALLEL SQL INSERT WORKER
# ------------------------------------------------------------
executor = ThreadPoolExecutor(max_workers=max_concurrent_inserts)

def insert_batch_sync(rows, embeddings):
    """Builds a single multi-row INSERT and executes it."""
    values = []
    for row, emb in zip(rows, embeddings):
        vec_json = json.dumps(emb).replace("'", "''")
        values.append(
            f"({row.id}, CAST(CAST('{vec_json}' AS NVARCHAR(MAX)) AS VECTOR({vector_size})))"
        )

    sql = f"""
        INSERT INTO {vector_table} (id, vector)
        VALUES
        {",\n".join(values)}
    """

    cursor.execute(sql)
    database_connection.commit()


async def insert_batch(rows, embeddings):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, insert_batch_sync, rows, embeddings)


# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------
async def pipeline():
    last_id = 0
    total_processed = 0
    batch_number = 0
    start_time = time.time()

    logger.info("🚀 Starting ultra-fast vectorization pipeline with REAL token counting...")

    while True:

        # --------------------------------------------------------
        # SELECT BATCH
        # --------------------------------------------------------
        select_sql = f"""
            SELECT TOP ({select_batch_size})
                t.id,
                {field_to_be_vectorized} AS text_to_vectorize
            FROM {source_table} AS t
            WHERE t.id > {last_id}
              AND NOT EXISTS (
                    SELECT 1 FROM {vector_table} vt WHERE vt.id = t.id
              )
            ORDER BY t.id ASC;
        """

        cursor.execute(select_sql)
        rows = cursor.fetchall()

        if not rows:
            logger.info("✔ All rows processed.")
            break

        batch_number += 1
        batch_start = time.time()

        texts = [row.text_to_vectorize for row in rows]

        # REAL TOKEN COUNTING
        batch_tokens = sum(count_tokens(t) for t in texts)

        # --------------------------------------------------------
        # EMBEDDINGS (ASYNC PARALLEL MICRO-BATCHES)
        # --------------------------------------------------------
        embeddings = await embed_full_batch(texts)

        # --------------------------------------------------------
        # INSERT INTO SQL (PARALLEL THREAD EXECUTION)
        # --------------------------------------------------------
        await insert_batch(rows, embeddings)

        # Update counters
        last_id = rows[-1].id
        total_processed += len(rows)

        # Logging
        batch_time = time.time() - batch_start
        overall_time = time.time() - start_time
        speed = total_processed / overall_time if overall_time > 0 else 0

        logger.info(
            f"[BATCH {batch_number}] Rows: {len(rows)} | "
            f"Tokens: {batch_tokens} | "
            f"Total Rows: {total_processed} | "
            f"Batch Time: {batch_time:.2f}s | "
            f"Speed: {speed:.2f} rows/s"
        )
        sys.stdout.flush()

    logger.info("🏁 Pipeline completed successfully.")


# ------------------------------------------------------------
# RUN PIPELINE
# ------------------------------------------------------------
asyncio.run(pipeline())
cursor.close()
database_connection.close()
