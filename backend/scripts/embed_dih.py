from pathlib import Path
import json
import time

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# PATH
# ============================================================

INPUT_PATH = Path("data/processed/dih_chunks.json")

VECTORSTORE_DIR = Path("data/vectorstore/chroma")
COLLECTION_NAME = "dih"

# Model embedding
EMBEDDING_MODEL = "BAAI/bge-m3"

# Jumlah chunk yang diproses sekaligus
BATCH_SIZE = 16


# ============================================================
# LOAD CHUNKS
# ============================================================

def load_chunks(input_path: Path) -> list[dict]:
    if not input_path.exists():
        raise FileNotFoundError(
            f"File chunk tidak ditemukan: {input_path.resolve()}"
        )

    with input_path.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    if not isinstance(chunks, list):
        raise ValueError("Format dih_chunks.json harus berupa list.")

    return chunks


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

def load_embedding_model() -> SentenceTransformer:
    print("=" * 70)
    print("MEMUAT MODEL EMBEDDING")
    print("=" * 70)
    print(f"Model : {EMBEDDING_MODEL}")
    print()

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Model berhasil dimuat.")
    print()

    return model


# ============================================================
# CHROMADB
# ============================================================

def create_vector_database():
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Drug Interaction Handbook embeddings"
        },
    )

    return client, collection


# ============================================================
# PREPARE METADATA
# ============================================================

def prepare_metadata(chunk: dict) -> dict:
    metadata = chunk.get("metadata", {})

    columns = metadata.get("columns", [])

    return {
        "pdf_page_start": int(metadata.get("pdf_page_start", 0)),
        "pdf_page_end": int(metadata.get("pdf_page_end", 0)),
        "sequence_start": int(metadata.get("sequence_start", 0)),
        "sequence_end": int(metadata.get("sequence_end", 0)),
        "character_count": int(metadata.get("character_count", 0)),
        "source": str(
            metadata.get(
                "source",
                "Drug Interaction Handbook"
            )
        ),
        "source_type": str(
            metadata.get(
                "source_type",
                "book"
            )
        ),
        "columns": ",".join(columns),
    }


# ============================================================
# EMBEDDING
# ============================================================

def embed_chunks(
    chunks: list[dict],
    model: SentenceTransformer,
    collection,
) -> None:

    total_chunks = len(chunks)

    print("=" * 70)
    print("MEMULAI EMBEDDING")
    print("=" * 70)
    print(f"Total chunks : {total_chunks:,}")
    print(f"Batch size   : {BATCH_SIZE}")
    print()

    start_time = time.time()

    for start_index in range(0, total_chunks, BATCH_SIZE):

        batch = chunks[
            start_index:start_index + BATCH_SIZE
        ]

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        ids = [
            chunk["chunk_id"]
            for chunk in batch
        ]

        metadatas = [
            prepare_metadata(chunk)
            for chunk in batch
        ]

        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        embeddings = embeddings.tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        processed = min(
            start_index + len(batch),
            total_chunks,
        )

        elapsed = time.time() - start_time

        print(
            f"Progress: "
            f"{processed:,}/{total_chunks:,} "
            f"({processed / total_chunks * 100:.1f}%) "
            f"| elapsed: {elapsed:.1f}s"
        )

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("EMBEDDING SELESAI")
    print("=" * 70)
    print(f"Total chunks : {total_chunks:,}")
    print(f"Waktu        : {elapsed:.1f} detik")
    print()


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_collection(collection) -> None:
    count = collection.count()

    print("=" * 70)
    print("VERIFIKASI VECTOR DATABASE")
    print("=" * 70)
    print(f"Collection : {COLLECTION_NAME}")
    print(f"Jumlah data: {count:,}")
    print()

    if count > 0:
        sample = collection.get(
            limit=1,
            include=[
                "documents",
                "metadatas",
            ],
        )

        print("Contoh data:")
        print("-" * 70)

        print("ID:")
        print(sample["ids"][0])

        print()
        print("Metadata:")
        print(sample["metadatas"][0])

        print()
        print("Text:")
        print(sample["documents"][0][:500])

        print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("DIH EMBEDDING PIPELINE")
    print("=" * 70)
    print()

    # 1. Load chunks
    print("Memuat chunks...")
    chunks = load_chunks(INPUT_PATH)

    print(f"Chunks ditemukan : {len(chunks):,}")
    print()

    # 2. Load embedding model
    model = load_embedding_model()

    # 3. Create vector database
    print("=" * 70)
    print("MEMBUAT VECTOR DATABASE")
    print("=" * 70)
    print(f"Location   : {VECTORSTORE_DIR.resolve()}")
    print(f"Collection : {COLLECTION_NAME}")
    print()

    _, collection = create_vector_database()

    # 4. Generate embeddings
    embed_chunks(
        chunks=chunks,
        model=model,
        collection=collection,
    )

    # 5. Verify
    verify_collection(collection)

    print("=" * 70)
    print("PIPELINE SELESAI")
    print("=" * 70)
    print()
    print("Output:")
    print(VECTORSTORE_DIR.resolve())
    print()


if __name__ == "__main__":
    main()

