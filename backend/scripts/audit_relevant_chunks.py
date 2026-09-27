from pathlib import Path
import re

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIG
# ============================================================

CHROMA_PATH = Path("data/vectorstore/chroma")
COLLECTION_NAME = "dih"

EMBEDDING_MODEL = "BAAI/bge-m3"

TOP_K = 10
NEIGHBOR_WINDOW = 1


# ============================================================
# TEST QUERIES
# ============================================================

TEST_QUERIES = [
    ("Warfarin", "Amiodarone"),
    ("Warfarin", "Aspirin"),
    ("Amiodarone", "Digoxin"),
    ("Clopidogrel", "Omeprazole"),
    ("Lithium", "Ibuprofen"),
    ("Warfarin", "Fluconazole"),
    ("Simvastatin", "Clarithromycin"),
    ("Digoxin", "Amiodarone"),
    ("Warfarin", "Rifampicin"),
    ("Metformin", "Cimetidine"),
]


# ============================================================
# ALIASES
# ============================================================

DRUG_ALIASES = {
    "Warfarin": [
        "warfarin",
        "vitamin k antagonist",
        "vitamin k antagonists",
    ],
    "Amiodarone": ["amiodarone"],
    "Aspirin": [
        "aspirin",
        "acetylsalicylic acid",
    ],
    "Digoxin": ["digoxin"],
    "Clopidogrel": ["clopidogrel"],
    "Omeprazole": ["omeprazole"],
    "Lithium": ["lithium"],
    "Ibuprofen": ["ibuprofen"],
    "Fluconazole": ["fluconazole"],
    "Simvastatin": ["simvastatin"],
    "Clarithromycin": ["clarithromycin"],
    "Rifampicin": [
        "rifampicin",
        "rifampin",
    ],
    "Metformin": ["metformin"],
    "Cimetidine": ["cimetidine"],
}


# ============================================================
# DDI INDICATORS
# ============================================================

DDI_INDICATORS = [
    "drug interactions",
    "metabolism/transport effects",
    "metabolismltransport effects",
    "avoid concomitant use",
    "increased effect",
    "increased effect/toxicity",
    "increased effectitoxicity",
    "decreased effect",
    "decreased effect/toxicity",
    "the levels/effects of",
    "may increase the levels/effects",
    "may decrease the levels/effects",
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:

    text = text.lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("’", "'")
    text = text.replace("“", '"')
    text = text.replace("”", '"')

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_for_ocr(text: str) -> str:

    text = text.lower()

    return re.sub(
        r"[^a-z0-9]",
        "",
        text,
    )


# ============================================================
# DRUG MATCH
# ============================================================

def drug_mentioned(text: str, drug: str):

    normalized = normalize_text(text)
    normalized_ocr = normalize_for_ocr(text)

    aliases = DRUG_ALIASES.get(
        drug,
        [drug],
    )

    for alias in aliases:

        alias_normalized = normalize_text(alias)

        if alias_normalized in normalized:

            if normalize_text(drug) in normalized:

                return True, "DIRECT"

            return True, "ALIAS"

    drug_ocr = normalize_for_ocr(drug)

    if drug_ocr in normalized_ocr:

        return True, "OCR"

    return False, "NONE"


# ============================================================
# DDI DETECTION
# ============================================================

def ddi_content_present(text: str) -> bool:

    normalized = normalize_text(text)

    for indicator in DDI_INDICATORS:

        if normalize_text(indicator) in normalized:

            return True

    return False


# ============================================================
# BUILD SEQUENCE INDEX
# ============================================================

def build_sequence_index(collection):

    print("Mengambil seluruh chunk dari ChromaDB...")

    data = collection.get(
        include=[
            "documents",
            "metadatas",
        ],
    )

    documents = data["documents"]
    metadatas = data["metadatas"]

    sequence_index = {}

    for document, metadata in zip(
        documents,
        metadatas,
    ):

        sequence_start = metadata.get(
            "sequence_start"
        )

        if sequence_start is None:
            continue

        try:
            sequence_start = int(sequence_start)
        except (TypeError, ValueError):
            continue

        sequence_index[sequence_start] = {
            "document": document,
            "metadata": metadata,
        }

    return sequence_index


# ============================================================
# FIND NEIGHBORS
# ============================================================

def get_neighbors(
    metadata,
    sequence_index,
    window=1,
):

    current_sequence = metadata.get(
        "sequence_start"
    )

    if current_sequence is None:
        return []

    try:
        current_sequence = int(
            current_sequence
        )
    except (TypeError, ValueError):
        return []

    sorted_sequences = sorted(
        sequence_index.keys()
    )

    try:
        current_position = sorted_sequences.index(
            current_sequence
        )
    except ValueError:
        return []

    neighbors = []

    start = max(
        0,
        current_position - window,
    )

    end = min(
        len(sorted_sequences),
        current_position + window + 1,
    )

    for position in range(start, end):

        if position == current_position:
            continue

        sequence = sorted_sequences[position]

        neighbors.append(
            sequence_index[sequence]
        )

    return neighbors


# ============================================================
# CLASSIFY DIRECT CHUNK
# ============================================================

def classify_direct(
    document,
    drug_a,
    drug_b,
):

    a_found, a_type = drug_mentioned(
        document,
        drug_a,
    )

    b_found, b_type = drug_mentioned(
        document,
        drug_b,
    )

    ddi = ddi_content_present(
        document
    )

    if a_found and b_found and ddi:

        if (
            a_type == "OCR"
            or b_type == "OCR"
        ):
            return True, "OCR"

        if (
            a_type == "ALIAS"
            or b_type == "ALIAS"
        ):
            return True, "ALIAS"

        return True, "DIRECT"

    return False, "NONE"


# ============================================================
# CLASSIFY CONTEXT
# ============================================================

def classify_context(
    current_document,
    current_metadata,
    sequence_index,
    drug_a,
    drug_b,
):

    neighbors = get_neighbors(
        current_metadata,
        sequence_index,
        NEIGHBOR_WINDOW,
    )

    for neighbor in neighbors:

        neighbor_document = neighbor[
            "document"
        ]

        combined = (
            current_document
            + "\n"
            + neighbor_document
        )

        if not ddi_content_present(combined):
            continue

        a_found, a_type = drug_mentioned(
            combined,
            drug_a,
        )

        b_found, b_type = drug_mentioned(
            combined,
            drug_b,
        )

        if not (a_found and b_found):
            continue

        current_a, _ = drug_mentioned(
            current_document,
            drug_a,
        )

        current_b, _ = drug_mentioned(
            current_document,
            drug_b,
        )

        neighbor_a, _ = drug_mentioned(
            neighbor_document,
            drug_a,
        )

        neighbor_b, _ = drug_mentioned(
            neighbor_document,
            drug_b,
        )

        separated_evidence = (
            (current_a and neighbor_b)
            or
            (current_b and neighbor_a)
        )

        if not separated_evidence:
            continue

        if (
            a_type == "OCR"
            or b_type == "OCR"
        ):
            context_type = "CONTEXT_OCR"

        elif (
            a_type == "ALIAS"
            or b_type == "ALIAS"
        ):
            context_type = "CONTEXT_ALIAS"

        else:
            context_type = "CONTEXT"

        return {
            "relevant": True,
            "type": context_type,
            "neighbor": neighbor,
        }

    return {
        "relevant": False,
        "type": "NONE",
        "neighbor": None,
    }


# ============================================================
# MAIN
# ============================================================

print()
print("=" * 90)
print("AUDIT RELEVANT CHUNKS - RETRIEVAL V4")
print("=" * 90)

print()
print("Memuat embedding model...")

model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Model berhasil dimuat.")

print()
print("Menghubungkan ke ChromaDB...")

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print(
    f"Collection : {COLLECTION_NAME}"
)

print(
    f"Jumlah chunk : {collection.count():,}"
)


# ============================================================
# BUILD INDEX
# ============================================================

sequence_index = build_sequence_index(
    collection
)

print(
    f"Sequence index : "
    f"{len(sequence_index):,}"
)


# ============================================================
# AUDIT
# ============================================================

for query_number, (drug_a, drug_b) in enumerate(
    TEST_QUERIES,
    start=1,
):

    query = f"{drug_a} dan {drug_b}"

    print()
    print()
    print("#" * 90)
    print(
        f"QUERY {query_number}: "
        f"{query}"
    )
    print("#" * 90)

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=TOP_K,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    found_relevant = False

    for rank in range(len(ids)):

        document = documents[rank]
        metadata = metadatas[rank]

        # ----------------------------------------------------
        # DIRECT
        # ----------------------------------------------------

        relevant, classification = classify_direct(
            document,
            drug_a,
            drug_b,
        )

        context_neighbor = None

        # ----------------------------------------------------
        # CONTEXT
        # ----------------------------------------------------

        if not relevant:

            context = classify_context(
                current_document=document,
                current_metadata=metadata,
                sequence_index=sequence_index,
                drug_a=drug_a,
                drug_b=drug_b,
            )

            if context["relevant"]:

                relevant = True

                classification = context[
                    "type"
                ]

                context_neighbor = context[
                    "neighbor"
                ]

        # ----------------------------------------------------
        # Only print relevant
        # ----------------------------------------------------

        if not relevant:
            continue

        found_relevant = True

        print()
        print()
        print("=" * 90)
        print(
            f"RELEVANT RESULT "
            f"(RANK {rank + 1})"
        )
        print("=" * 90)

        print()
        print(
            f"Classification : "
            f"{classification}"
        )

        print(
            f"Chunk ID       : "
            f"{ids[rank]}"
        )

        print(
            f"Distance       : "
            f"{distances[rank]}"
        )

        print(
            f"PDF Page       : "
            f"{metadata.get('pdf_page_start')} - "
            f"{metadata.get('pdf_page_end')}"
        )

        print(
            f"Sequence       : "
            f"{metadata.get('sequence_start')} - "
            f"{metadata.get('sequence_end')}"
        )

        print(
            f"Source         : "
            f"{metadata.get('source')}"
        )

        print(
            f"Columns        : "
            f"{metadata.get('columns')}"
        )

        # ----------------------------------------------------
        # Drug detection
        # ----------------------------------------------------

        a_found, a_type = drug_mentioned(
            document,
            drug_a,
        )

        b_found, b_type = drug_mentioned(
            document,
            drug_b,
        )

        print()
        print("DETEKSI OBAT PADA CURRENT CHUNK")
        print("-" * 90)

        print(
            f"{drug_a} : "
            f"{a_found} ({a_type})"
        )

        print(
            f"{drug_b} : "
            f"{b_found} ({b_type})"
        )

        print(
            f"DDI indicator : "
            f"{ddi_content_present(document)}"
        )

        # ----------------------------------------------------
        # Current document
        # ----------------------------------------------------

        print()
        print("=" * 90)
        print("TEKS LENGKAP CURRENT CHUNK")
        print("=" * 90)

        print(document)

        # ----------------------------------------------------
        # Neighbor
        # ----------------------------------------------------

        if context_neighbor is not None:

            neighbor_metadata = (
                context_neighbor["metadata"]
            )

            neighbor_document = (
                context_neighbor["document"]
            )

            print()
            print()
            print("=" * 90)
            print("TEKS LENGKAP CONTEXT NEIGHBOR")
            print("=" * 90)

            print(
                f"Neighbor ID : "
                f"{neighbor_metadata.get('id')}"
            )

            print(
                f"PDF Page    : "
                f"{neighbor_metadata.get('pdf_page_start')} - "
                f"{neighbor_metadata.get('pdf_page_end')}"
            )

            print(
                f"Sequence    : "
                f"{neighbor_metadata.get('sequence_start')} - "
                f"{neighbor_metadata.get('sequence_end')}"
            )

            print()

            print(neighbor_document)

        print()
        print("=" * 90)

    if not found_relevant:

        print()
        print(
            "TIDAK ADA RELEVANT CHUNK "
            "DI TOP-10"
        )


print()
print()
print("=" * 90)
print("AUDIT SELESAI")
print("=" * 90)