import os
import time

import numpy as np
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from ricedb.client.grpc_client import GrpcRiceDBClient

load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "quickstart"
DATASET_SIZE = 1000
QUERY_COUNT = 20


def generate_dataset(size, dim):
    """Generate dataset with text for RiceDB and vectors for Pinecone."""
    print(f"Generating {size} documents (with {dim}-dim vectors for Pinecone)...")
    dataset = []
    for i in range(size):
        # Random vector normalized (only needed for Pinecone)
        vec = np.random.rand(dim).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        dataset.append(
            {
                "id": f"vec_{i}",
                "values": vec.tolist(),  # Only used by Pinecone
                "metadata": {
                    "text": f"Document {i} about machine learning, neural networks, and AI research benchmarks."
                },
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
    client = GrpcRiceDBClient(host=HOST, port=PORT)
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
                "text": item["metadata"]["text"],
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
        query_text = dataset[i]["metadata"]["text"]
        client.search(query_text, user_id=1, k=10)
    query_time = time.time() - start_time
    avg_query = query_time / QUERY_COUNT
    print(f"RiceDB Total Query Time: {query_time:.4f}s")
    print(f"RiceDB Avg Latency: {avg_query * 1000:.2f}ms")

    return ingest_time, avg_query


def benchmark_pinecone(dataset, dim):
    """Benchmark Pinecone using pre-computed vector embeddings."""
    print("\n--- Benchmarking Pinecone ---")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"Pinecone Connection Error: {e}")
        return None, None

    # Ingest
    print(f"Ingesting {len(dataset)} items...")
    start_time = time.time()

    # Pinecone upsert batches of 100
    batch_size = 100
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i : i + batch_size]
        index.upsert(vectors=batch)

    ingest_time = time.time() - start_time
    print(f"Pinecone Ingestion Time: {ingest_time:.4f}s")

    # Query
    print(f"Running {QUERY_COUNT} queries...")
    start_time = time.time()
    for i in range(QUERY_COUNT):
        query_vec = dataset[i]["values"]
        index.query(vector=query_vec, top_k=10)
    query_time = time.time() - start_time
    avg_query = query_time / QUERY_COUNT
    print(f"Pinecone Total Query Time: {query_time:.4f}s")
    print(f"Pinecone Avg Latency: {avg_query * 1000:.2f}ms")

    return ingest_time, avg_query


def main():
    # 1. Determine dimension from Pinecone index to match it
    print("Checking Pinecone Index...")
    dim = 384  # Default for benchmark
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        try:
            idx_desc = pc.describe_index(INDEX_NAME)
            dim = idx_desc.dimension
            print(f"Detected Pinecone Index Dimension: {dim}")
        except Exception:
            raise Exception(  # noqa: B904
                "Failed to describe Pinecone index. Ensure the index exists."
            )

    except Exception as e:
        print(f"Error accessing Pinecone: {e}")
        return

    # 2. Generate Data
    dataset = generate_dataset(DATASET_SIZE, dim)

    # 3. Benchmark
    r_ingest, r_query = benchmark_ricedb(dataset)
    p_ingest, p_query = benchmark_pinecone(dataset, dim)

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
