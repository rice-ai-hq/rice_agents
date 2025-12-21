#!/usr/bin/env python3
"""
Comprehensive End-to-End Demo for RiceDB
Demonstrates: authentication, connection, insertion, querying, and deletion operations

Usage:
python examples/end_to_end_demo.py

Prerequisites: - RiceDB server running on localhost:50051 (gRPC) and/or localhost:3000 (HTTP) - Dependencies installed: ricedb[grpc,embeddings], sentence-transformers
"""

import time
import sys
import os
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow importing ricedb if not installed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(**file**))))

try:
from ricedb import RiceDBClient
from ricedb.utils import SentenceTransformersEmbeddingGenerator
from ricedb.exceptions import ConnectionError, InsertError, SearchError, RiceDBError, AuthenticationError
except ImportError: # Try importing from src if running from repo root
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(**file**))), "ricedb-python", "src"))
from ricedb import RiceDBClient
from ricedb.utils import SentenceTransformersEmbeddingGenerator
from ricedb.exceptions import ConnectionError, InsertError, SearchError, RiceDBError, AuthenticationError

# Configuration

DEMO_NODE_ID_PREFIX = 90000
SERVER_HOST = "localhost"
GRPC_PORT = 50051
HTTP_PORT = 3000
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SAMPLE_DATA_FILE = "data/train.dat"
USERNAME = "demo_user"
PASSWORD = "demo_password123"

def print_section(title: str):
"""Print a formatted section header"""
print("\n" + "=" _ 60)
print(f" {title}")
print("=" _ 60)

def print_success(message: str):
"""Print a success message"""
print(f"✓ {message}")

def print_error(message: str):
"""Print an error message"""
print(f"✗ {message}")

def print_info(message: str):
"""Print an info message"""
print(f" ℹ {message}")

def generate_dummy_medical_data() -> List[Dict[str, Any]]:
"""Generate dummy medical data if file is missing"""
return [
{"id": DEMO_NODE_ID_PREFIX + 1, "text": "Patient presents with severe myocardial infarction symptoms.", "rating": 5, "category": "cardiology"},
{"id": DEMO_NODE_ID_PREFIX + 2, "text": "Chronic kidney disease stage 3 management.", "rating": 4, "category": "nephrology"},
{"id": DEMO_NODE_ID_PREFIX + 3, "text": "Colonoscopy revealed multiple polyps in the ascending colon.", "rating": 3, "category": "gastroenterology"},
{"id": DEMO_NODE_ID_PREFIX + 4, "text": "Neurological exam shows signs of gaba deficiency.", "rating": 5, "category": "neurology"},
{"id": DEMO_NODE_ID_PREFIX + 5, "text": "Respiratory infection requiring antibiotics.", "rating": 2, "category": "pulmonology"},
{"id": DEMO_NODE_ID_PREFIX + 6, "text": "Vascular surgery required for subclavian artery fistula.", "rating": 4, "category": "vascular"},
]

def load_medical_data(filepath: str) -> List[Dict[str, Any]]:
"""Load medical documents from the train.dat file or generate dummy data"""
documents = []

    if not os.path.exists(filepath):
        print_info(f"Sample data file not found: {filepath}")
        print_info("Generating dummy medical data...")
        documents = generate_dummy_medical_data()
        print_success(f"Generated {len(documents)} dummy documents")
        return documents

    print_info(f"Loading medical documents from {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    rating = int(parts[0])
                    # The rest of the line after rating is the text content
                    text = '\t'.join(parts[1:])

                    documents.append({
                        "id": DEMO_NODE_ID_PREFIX + i,
                        "text": text,
                        "rating": rating,
                        "category": categorize_medical_text(text)
                    })

    print_success(f"Loaded {len(documents)} medical documents")
    return documents

def categorize_medical_text(text: str) -> str:
"""Simple categorization of medical text based on keywords"""
text_lower = text.lower()

    if any(word in text_lower for word in ['heart', 'cardiac', 'myocardial', 'infarction']):
        return 'cardiology'
    elif any(word in text_lower for word in ['kidney', 'renal', 'abscess']):
        return 'nephrology'
    elif any(word in text_lower for word in ['colon', 'polyp', 'endoscopy']):
        return 'gastroenterology'
    elif any(word in text_lower for word in ['artery', 'fistula', 'subclavian']):
        return 'vascular'
    elif any(word in text_lower for word in ['brain', 'neurological', 'gaba']):
        return 'neurology'
    elif any(word in text_lower for word in ['infection', 'epidural', 'catheter']):
        return 'infectious_disease'
    elif any(word in text_lower for word in ['tracheostomy', 'mediastinal']):
        return 'pulmonology'
    elif any(word in text_lower for word in ['asthma', 'respiratory']):
        return 'respiratory'
    else:
        return 'general'

def demonstrate_connection(client: RiceDBClient) -> bool:
"""Demonstrate connecting to RiceDB"""
print_section("1. CONNECTING TO RICEDB")

    try:
        print_info(f"Attempting to connect to {SERVER_HOST}:{GRPC_PORT} (gRPC) / {HTTP_PORT} (HTTP)...")
        if client.connect():
            transport_info = client.get_transport_info()
            print_success(f"Connected to RiceDB server via {transport_info['type'].upper()}")
            return True
        else:
            print_error("Failed to connect to RiceDB server")
            return False

    except ConnectionError as e:
        print_error(f"Failed to connect: {e}")
        print_info("Please ensure the RiceDB server is running:")
        print_info("  - cargo run --bin ricedb-server-grpc --features grpc-server")
        print_info("  - cargo run --bin ricedb-server-http --features http-server")
        return False
    except Exception as e:
        print_error(f"Unexpected error during connection: {e}")
        return False

def demonstrate_authentication(client: RiceDBClient) -> bool:
"""Demonstrate registration and login"""
print_section("2. AUTHENTICATION")

    # 1. Register
    print_info(f"Registering user '{USERNAME}'...")
    try:
        user_id = client.register(USERNAME, PASSWORD)
        print_success(f"User registered successfully (ID: {user_id})")
    except Exception as e:
        if "already exists" in str(e) or "Status.ALREADY_EXISTS" in str(e):
            print_info(f"User '{USERNAME}' already exists, proceeding to login")
        else:
            print_error(f"Registration failed: {e}")
            # Try to login anyway in case it failed because of existence but error message differed
            pass

    # 2. Login
    print_info(f"Logging in as '{USERNAME}'...")
    try:
        token = client.login(USERNAME, PASSWORD)
        print_success(f"Login successful. Token obtained (len={len(token)})")
        return True
    except Exception as e:
        print_error(f"Login failed: {e}")
        return False

def demonstrate_single_insert(client: RiceDBClient, document: Dict[str, Any]) -> bool:
"""Demonstrate inserting a single document"""
print_section("3. SINGLE DOCUMENT INSERTION")

    try:
        print_info(f"Inserting document ID: {document['id']}")
        print_info(f"Category: {document['category']}")
        print_info(f"Text preview: {document['text'][:100]}...")

        start_time = time.time()
        client.insert_text(
            node_id=document['id'],
            text=document['text'],
            metadata={
                'rating': document['rating'],
                'source': 'end_to_end_demo',
                'category': document['category'],
                'timestamp': time.time()
            },
            embedding_generator=embedding_generator
        )
        elapsed = time.time() - start_time

        print_success(f"Document inserted successfully in {elapsed:.3f}s")
        return True

    except InsertError as e:
        print_error(f"Failed to insert document: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during insertion: {e}")
        return False

def demonstrate_batch_insert(client: RiceDBClient, documents: List[Dict[str, Any]]) -> bool:
"""Demonstrate batch insertion of multiple documents"""
print_section("4. BATCH DOCUMENT INSERTION")

    if not documents:
        print_error("No documents to insert")
        return False

    print_info(f"Preparing to insert {len(documents)} documents...")

    # Prepare documents for batch insert
    batch_docs = []
    for doc in documents:
        batch_docs.append({
            "id": doc['id'],
            "text": doc['text'],
            "metadata": {
                'rating': doc['rating'],
                'source': 'end_to_end_demo',
                'category': doc['category'],
                'timestamp': time.time()
            }
        })

    try:
        print_info("Starting batch insertion...")
        start_time = time.time()

        # Insert in batches
        batch_size = 5
        total_inserted = 0

        for i in range(0, len(batch_docs), batch_size):
            batch = batch_docs[i:i + batch_size]
            print_info(f"Inserting batch {i//batch_size + 1}/{(len(batch_docs) + batch_size - 1)//batch_size} ({len(batch)} documents)...")

            # Use batch_insert_texts helper if available, or manual batch insert
            # Assuming UnifiedClient has batch_insert_texts or we do it manually
            # The previous code in prompt used client.batch_insert with manual embedding.
            # Let's do that for clarity and control.

            embedded_batch = []
            for doc in batch:
                embedding = embedding_generator.generate_embedding(doc['text'])
                # Ensure text is in metadata
                meta = doc['metadata'].copy()
                meta['text'] = doc['text']

                embedded_batch.append({
                    "id": doc['id'],
                    "vector": embedding,
                    "metadata": meta
                })

            result = client.batch_insert(embedded_batch)
            if result:
                total_inserted += len(batch)
                print_success(f"Batch {i//batch_size + 1} inserted successfully")
            else:
                print_error(f"Batch {i//batch_size + 1} failed")

        elapsed = time.time() - start_time
        print_success(f"Batch insertion completed: {total_inserted}/{len(batch_docs)} documents in {elapsed:.3f}s")
        return total_inserted > 0

    except Exception as e:
        print_error(f"Batch insertion failed: {e}")
        return False

def demonstrate_queries(client: RiceDBClient) -> bool:
"""Demonstrate various search queries"""
print_section("5. SEMANTIC SEARCH QUERIES")

    # Sample medical queries
    queries = [
        ("heart attack treatment", "cardiology-related documents"),
        ("neurological disorders", "neurology and brain-related content"),
        ("respiratory disease", "pulmonology and respiratory content"),
    ]

    all_successful = True

    # Use authenticated user from client state (handled internally by token)
    # We pass user_id=0 or any ID, the server validates the token.
    # However, client methods still ask for user_id for ACL checking context (if not using token for ID).
    # With the new auth system, the token contains the user_id.
    # But the client signature still requires user_id for some methods.
    # We should pass the ID we got from login if possible, or 1 as fallback.

    # Actually, let's fetch 'me' or just use 1. The token is what matters for server Auth.
    # The user_id param in search/insert is often for "owner" assignment or ACL check.
    # If the token user differs from passed user_id, server might reject or ignore passed ID.
    # Our implementation ignores passed user_id in favor of token user_id for actions.

    search_user_id = 1

    for query, description in queries:
        print(f"\n🔍 Query: '{query}'")
        print_info(f"Looking for: {description}")

        try:
            start_time = time.time()
            results = client.search_text(
                query=query,
                k=3,
                embedding_generator=embedding_generator,
                user_id=search_user_id
            )
            elapsed = time.time() - start_time

            if results:
                print_success(f"Found {len(results)} results in {elapsed:.3f}s")

                for i, result in enumerate(results):
                    similarity = result.get('similarity', 0)
                    metadata = result.get('metadata', {})
                    text = metadata.get('text', 'No text available')
                    category = metadata.get('category', 'unknown')

                    print(f"\n  Result {i + 1}:")
                    print(f"    Similarity: {similarity:.4f}")
                    print(f"    Category: {category}")
                    print(f"    Text: {text[:100]}...")
            else:
                print_info("No results found")

        except SearchError as e:
            print_error(f"Search failed: {e}")
            all_successful = False
        except Exception as e:
            print_error(f"Unexpected error during search: {e}")
            all_successful = False

    return all_successful

def demonstrate_delete_operations(client: RiceDBClient) -> bool:
"""Demonstrate delete operations"""
print_section("6. DELETE OPERATIONS")

    # Try to delete the first demo document
    node_id_to_delete = DEMO_NODE_ID_PREFIX + 1

    print_info(f"Attempting to delete node {node_id_to_delete}...")

    try:
        start_time = time.time()
        result = client.delete(node_id=node_id_to_delete)
        elapsed = time.time() - start_time

        if result:
            print_success(f"Node {node_id_to_delete} deleted successfully in {elapsed:.3f}s")
        else:
            print_error(f"Failed to delete node {node_id_to_delete}")
            return False

    except RiceDBError as e:
        print_error(f"Delete operation failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during deletion: {e}")
        return False

    # Verify deletion
    print_info("\nVerifying deletion via search...")
    try:
        # Search for the specific text of the deleted node
        results = client.search_text(
            query="myocardial infarction",
            k=5,
            embedding_generator=embedding_generator,
            user_id=1
        )

        found = False
        for res in results:
            if res['id'] == node_id_to_delete:
                found = True
                break

        if not found:
            print_success(f"Verified: Node {node_id_to_delete} not found in search results")
        else:
            print_error(f"Node {node_id_to_delete} still found in search results!")
            return False

    except Exception as e:
        print_error(f"Verification failed: {e}")

    return True

def print_summary(start_time: float, operations_success: Dict[str, bool]):
"""Print a summary of all operations"""
elapsed = time.time() - start_time

    print_section("DEMO SUMMARY")

    print(f"\n⏱️  Total execution time: {elapsed:.2f} seconds")

    print("\n📊 Operation Results:")
    for operation, success in operations_success.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {operation:20} : {status}")

    total_ops = len(operations_success)
    successful_ops = sum(operations_success.values())

    print(f"\n📈 Overall Success Rate: {successful_ops}/{total_ops} operations ({100*successful_ops/total_ops:.1f}%)")

    if successful_ops == total_ops:
        print_success("All operations completed successfully!")
    else:
        print_info("Some operations failed - check error messages above")

def main():
"""Main demo execution"""
print("🍚 RiceDB End-to-End Demo with Authentication")
print("This demo showcases the full lifecycle: Auth -> Connect -> Insert -> Search -> Delete")

    # Track operation success
    operations_success = {}
    start_time = time.time()

    # Initialize embedding generator
    global embedding_generator
    try:
        print_info(f"Loading embedding model: {EMBEDDING_MODEL}")
        embedding_generator = SentenceTransformersEmbeddingGenerator(
            model_name=EMBEDDING_MODEL
        )
        print_success("Embedding model loaded successfully")
    except Exception as e:
        print_error(f"Failed to load embedding model: {e}")
        print_info("Falling back to DummyEmbeddingGenerator for demo purposes...")
        from ricedb.utils import DummyEmbeddingGenerator
        embedding_generator = DummyEmbeddingGenerator()

    # Create Client (Auto-detect transport)
    print_info("Creating RiceDB client...")
    # Use auto transport to pick best available (gRPC or HTTP)
    client = RiceDBClient(
        transport="auto",
        host=SERVER_HOST,
        http_port=HTTP_PORT,
        grpc_port=GRPC_PORT
    )

    # Step 1: Connect
    operations_success['Connection'] = demonstrate_connection(client)
    if not operations_success['Connection']:
        print_error("Cannot proceed without connection")
        sys.exit(1)

    # Step 2: Authenticate
    operations_success['Authentication'] = demonstrate_authentication(client)
    if not operations_success['Authentication']:
        print_error("Cannot proceed without authentication")
        sys.exit(1)

    # Step 3: Load/Generate data
    documents = load_medical_data(SAMPLE_DATA_FILE)
    if not documents:
        print_error("Cannot proceed without data")
        sys.exit(1)

    # Step 4: Single insert
    if documents:
        operations_success['Single Insert'] = demonstrate_single_insert(client, documents[0])

    # Step 5: Batch insert
    if len(documents) > 1:
        operations_success['Batch Insert'] = demonstrate_batch_insert(client, documents[1:])

    # Step 6: Queries
    operations_success['Search Queries'] = demonstrate_queries(client)

    # Step 7: Delete operations
    operations_success['Delete Operations'] = demonstrate_delete_operations(client)

    # Cleanup
    try:
        client.disconnect()
        print_info("\nDisconnected from RiceDB")
    except:
        pass

    # Print summary
    print_summary(start_time, operations_success)

if **name** == "**main**":
main()
