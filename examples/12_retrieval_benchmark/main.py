import os
import time

from dotenv import load_dotenv
from pinecone import Pinecone
from ricedb import RiceDBClient

load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "demo"  # Index with integrated llama-text-embed-v2
DATASET_SIZE = 1000
QUERY_COUNT = 20


def generate_dataset(size):
    """Generate dataset with text documents for both RiceDB and Pinecone."""
    print(f"Generating {size} text documents...")
    dataset = []
    for i in range(size):
        dataset.append(
            {
                "id": f"doc_{i}",
                "text": f"Document {i} about machine learning, neural networks, and AI research benchmarks.",
            }
        )
    return dataset


def benchmark_ricedb(dataset):
    """Benchmark RiceDB using text-only inserts (server handles HDC encoding)."""
    print("\n--- Benchmarking RiceDB ---")

    HOST = os.environ.get("RICEDB_HOST", "grpc.ricedb-test-2.ricedb.tryrice.com")
    PORT = int(os.environ.get("RICEDB_PORT", "80"))
    PASSWORD = os.environ.get("RICEDB_PASSWORD", "ed294b4085f0959974cd6e0ca7dfffbd")
    SSL = os.environ.get("RICEDB_SSL", "false").lower() == "true"

    print(f"Connecting to {HOST}:{PORT} (SSL={SSL})...")
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL

    try:
        client.connect()
    except Exception as e:
        print(f"Failed to connect to RiceDB: {e}")
        return None, None

    # Auth
    try:
        client.login("admin", PASSWORD)
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None

    # Ingest using batch_insert (RiceDB handles HDC encoding server-side)
    print(f"Ingesting {len(dataset)} items (text-only, server handles HDC encoding)...")
    start_time = time.time()

    # Prepare batch documents
    batch_docs = []
    for i, item in enumerate(dataset):
        batch_docs.append(
            {
                "id": i + 100000,  # Offset to avoid collision with other demos
                "text": item["text"],
                "metadata": {"title": f"Document {i}"},
                "user_id": 1,
            }
        )

    # Batch insert in chunks
    BATCH_SIZE = 100
    total_inserted = 0
    for i in range(0, len(batch_docs), BATCH_SIZE):
        chunk = batch_docs[i : i + BATCH_SIZE]
        try:
            result = client.batch_insert(chunk)
            count = result.get("count", len(chunk))
            total_inserted += count
        except Exception as e:
            print(f"RiceDB Insert Error in batch {i // BATCH_SIZE + 1}: {e}")

    ingest_time = time.time() - start_time
    print(f"RiceDB Ingestion Time: {ingest_time:.4f}s ({total_inserted} docs)")

    # Query
    print(f"Running {QUERY_COUNT} queries...")
    start_time = time.time()
    for i in range(QUERY_COUNT):
        query_text = dataset[i]["text"]
        client.search(query_text, user_id=1, k=10)
    query_time = time.time() - start_time
    avg_query = query_time / QUERY_COUNT
    print(f"RiceDB Total Query Time: {query_time:.4f}s")
    print(f"RiceDB Avg Latency: {avg_query * 1000:.2f}ms")

    return ingest_time, avg_query


def benchmark_pinecone(dataset):
    """Benchmark Pinecone using integrated embeddings (text-only, server handles embedding)."""
    print("\n--- Benchmarking Pinecone ---")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"Pinecone Connection Error: {e}")
        return None, None

    # Ingest using text (Pinecone handles embedding via llama-text-embed-v2)
    print(f"Ingesting {len(dataset)} items (text-only, server handles embedding)...")
    start_time = time.time()

    # Pinecone upsert_records has a batch size limit of 96
    batch_size = 96
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i : i + batch_size]
        # Use upsert_records for integrated embedding
        records = [{"_id": item["id"], "text": item["text"]} for item in batch]
        index.upsert_records(namespace="benchmark", records=records)

    ingest_time = time.time() - start_time
    print(f"Pinecone Ingestion Time: {ingest_time:.4f}s")

    # Query using text
    print(f"Running {QUERY_COUNT} queries...")
    start_time = time.time()
    for i in range(QUERY_COUNT):
        query_text = dataset[i]["text"]
        index.search(
            namespace="benchmark", query={"top_k": 10, "inputs": {"text": query_text}}
        )
    query_time = time.time() - start_time
    avg_query = query_time / QUERY_COUNT
    print(f"Pinecone Total Query Time: {query_time:.4f}s")
    print(f"Pinecone Avg Latency: {avg_query * 1000:.2f}ms")

    return ingest_time, avg_query


def main():
    # 1. Verify Pinecone index exists
    print("Checking Pinecone Index...")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx_desc = pc.describe_index(INDEX_NAME)
        print(
            f"Using Pinecone Index: {INDEX_NAME} (dim={idx_desc.dimension}, model=llama-text-embed-v2)"
        )
    except Exception as e:
        print(f"Error accessing Pinecone: {e}")
        return

    # 2. Generate Data (text-only, no vectors needed)
    dataset = generate_dataset(DATASET_SIZE)

    # 3. Benchmark
    r_ingest, r_query = benchmark_ricedb(dataset)
    p_ingest, p_query = benchmark_pinecone(dataset)

    print("\n=== RESULTS ===")
    print(f"{'Metric':<20} | {'RiceDB':<15} | {'Pinecone':<15}")
    print("-" * 56)
    if r_ingest is not None and p_ingest is not None:
        print(f"{'Ingestion (1k)':<20} | {r_ingest:.4f}s        | {p_ingest:.4f}s")
        print(
            f"{'Avg Query Latency':<20} | {r_query * 1000:.2f}ms         | {p_query * 1000:.2f}ms"
        )
    else:
        print("Benchmark incomplete due to errors.")


if __name__ == "__main__":
    main()
