# Example 12: RiceDB vs Pinecone Retrieval Benchmark

A fair, apples-to-apples comparison between **RiceDB** (Hyperdimensional Computing) and **Pinecone** (Vector Database) for text retrieval workloads.

## Overview

This benchmark compares both databases using **text-only input**, where each database handles encoding/embedding server-side:

| Database     | Encoding Method                  | Model                           |
| ------------ | -------------------------------- | ------------------------------- |
| **RiceDB**   | Hyperdimensional Computing (HDC) | Server-side HDC encoder         |
| **Pinecone** | Dense Vector Embeddings          | llama-text-embed-v2 (1024 dims) |

## What's Being Measured

1. **Ingestion Time**: Time to insert 1,000 text documents
2. **Query Latency**: Average time for semantic search queries (20 queries)

## Sample Results

```
=== RESULTS ===
Metric               | RiceDB          | Pinecone
--------------------------------------------------------
Ingestion (1k)       | 28.35s          | 6.33s
Avg Query Latency    | 60.74ms         | 168.08ms
```

### Key Observations

- **Query Performance**: RiceDB is ~2.8x faster at query time
- **Ingestion Performance**: Pinecone is ~4.5x faster at ingestion (see note below)

## ⚠️ Important: RiceDB Beta Limitations

In the current **beta version** of RiceDB, the HDC encoding layer is deployed alongside the main RiceDB server as a co-located service. This architecture creates **scaling bottlenecks** during ingestion:

- The encoding service processes documents sequentially
- Network round-trips between the encoding layer and storage add latency
- The encoding layer does not yet support horizontal scaling

This explains the ingestion time difference compared to Pinecone, which has a highly optimized, distributed embedding pipeline.

**Future releases** of RiceDB will decouple the encoding layer, enabling:

- Independent scaling of encoding and storage
- Parallel encoding pipelines
- Significantly improved ingestion throughput

Despite the ingestion bottleneck, RiceDB's query performance demonstrates the efficiency of HDC for similarity search.

## Prerequisites

1. **RiceDB Server**: Access to a RiceDB instance (remote or local)
2. **Pinecone Account**: With an index configured for integrated embeddings

### Pinecone Index Setup

Create an index named `demo` with integrated embeddings:

- Model: `llama-text-embed-v2`
- Dimension: 1024
- Metric: cosine

## Configuration

Create a `.env` file:

```env
# Pinecone
PINECONE_API_KEY=your_pinecone_api_key

# RiceDB
RICEDB_HOST=grpc.ricedb-test-2.ricedb.tryrice.com
RICEDB_PORT=80
RICEDB_PASSWORD=your_ricedb_password
RICEDB_SSL=false
```

## Running the Benchmark

```bash
# Install dependencies
make install

# Run the benchmark
make run
```

Or directly:

```bash
uv run main.py
```

## Testing Pinecone Separately

A test script is included to verify Pinecone's integrated embedding API:

```bash
uv run test_pinecone.py
```

## Files

| File               | Description                 |
| ------------------ | --------------------------- |
| `main.py`          | Main benchmark script       |
| `test_pinecone.py` | Pinecone API test script    |
| `.env`             | Configuration (credentials) |

## Technical Details

### RiceDB Approach

- Uses `batch_insert()` with batch size of 100
- Text is encoded to HDC vectors server-side
- Search uses text queries directly

### Pinecone Approach

- Uses `upsert_records()` with batch size of 96 (API limit)
- Text is embedded via llama-text-embed-v2 server-side
- Search uses `index.search()` with text inputs

## Dependencies

- `ricedb[grpc]` - RiceDB Python client
- `pinecone` - Pinecone Python client
- `python-dotenv` - Environment variable management
