from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_PATH = Path("data/vectorstore/chroma")
COLLECTION_NAME = "dih"

EMBEDDING_MODEL = "BAAI/bge-m3"

QUERY = "Warfarin dan amiodarone"

TOP_K = 5


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("=" * 70)
print("MEMUAT MODEL EMBEDDING")
print("=" * 70)
print(f"Model : {EMBEDDING_MODEL}")
print()

model = SentenceTransformer(EMBEDDING_MODEL)

print("Model berhasil dimuat.")
print()


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

print("=" * 70)
print("MENGHUBUNGKAN KE CHROMADB")
print("=" * 70)
print(f"Path       : {CHROMA_PATH.resolve()}")
print(f"Collection : {COLLECTION_NAME}")
print()

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print(f"Jumlah data dalam collection: {collection.count():,}")
print()


# ============================================================
# CREATE QUERY EMBEDDING
# ============================================================

print("=" * 70)
print("MEMBUAT QUERY EMBEDDING")
print("=" * 70)
print(f"Query : {QUERY}")
print()

query_embedding = model.encode(
    [QUERY],
    normalize_embeddings=True,
)

print(f"Dimensi embedding query: {len(query_embedding[0])}")
print()


# ============================================================
# RETRIEVAL
# ============================================================

print("=" * 70)
print("MELAKUKAN RETRIEVAL")
print("=" * 70)
print(f"Top-K : {TOP_K}")
print()

results = collection.query(
    query_embeddings=query_embedding.tolist(),
    n_results=TOP_K,
    include=[
        "documents",
        "metadatas",
        "distances",
    ],
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("=" * 70)
print("HASIL RETRIEVAL")
print("=" * 70)

ids = results["ids"][0]
documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]

for i in range(len(ids)):

    print()
    print("=" * 70)
    print(f"RANK {i + 1}")
    print("=" * 70)

    print(f"ID       : {ids[i]}")
    print(f"Distance : {distances[i]}")

    metadata = metadatas[i]

    print(
        f"PDF Page : "
        f"{metadata.get('pdf_page_start')} - "
        f"{metadata.get('pdf_page_end')}"
    )

    print(
        f"Sequence : "
        f"{metadata.get('sequence_start')} - "
        f"{metadata.get('sequence_end')}"
    )

    print(f"Source   : {metadata.get('source')}")
    print(f"Columns  : {metadata.get('columns')}")

    print()
    print("DOCUMENT:")
    print("-" * 70)
    print(documents[i])


print()
print("=" * 70)
print("RETRIEVAL SELESAI")
print("=" * 70)