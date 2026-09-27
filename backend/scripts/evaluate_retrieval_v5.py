from pathlib import Path
import json
import re

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_PATH = Path("data/vectorstore/chroma")
COLLECTION_NAME = "dih"

CHUNKS_PATH = Path("data/processed/dih_chunks.json")

EMBEDDING_MODEL = "BAAI/bge-m3"

TOP_K_VALUES = [1, 3, 5, 10]

NEIGHBOR_WINDOW = 1


# ============================================================
# TEST QUERIES
# ============================================================

QUERIES = [
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

ALIASES = {
    "warfarin": [
        "warfarin",
        "vitamin k antagonist",
        "vitamin k antagonists",
    ],

    "aspirin": [
        "aspirin",
        "acetylsalicylic acid",
    ],

    "rifampicin": [
        "rifampicin",
        "rifampin",
    ],

    "clarithromycin": [
        "clarithromycin",
        "c/arithromycin",
        "c/larithromycin",
    ],

    "metformin": [
        "metformin",
    ],

    "amiodarone": [
        "amiodarone",
    ],

    "digoxin": [
        "digoxin",
    ],

    "clopidogrel": [
        "clopidogrel",
    ],

    "omeprazole": [
        "omeprazole",
    ],

    "lithium": [
        "lithium",
    ],

    "ibuprofen": [
        "ibuprofen",
    ],

    "fluconazole": [
        "fluconazole",
    ],

    "simvastatin": [
        "simvastatin",
    ],

    "cimetidine": [
        "cimetidine",
    ],
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
# SECTION HEADINGS TO IGNORE
# ============================================================

IGNORED_HEADINGS = {
    "DRUG INTERACTIONS",
    "METABOLISM/TRANSPORT EFFECTS",
    "INCREASED EFFECT",
    "INCREASED EFFECT/TOXICITY",
    "DECREASED EFFECT",
    "DECREASED EFFECT/TOXICITY",
    "ETHANOL/NUTRITION/HERB INTERACTIONS",
    "FOOD",
    "HERB/NUTRACEUTICAL",
    "STABILITY",
    "PHARMACOLOGY",
    "PHARMACOKINETICS",
    "PHARMACODYNAMICS",
    "WARNINGS",
    "PRECAUTIONS",
    "CONTRAINDICATIONS",
    "ADVERSE REACTIONS",
    "DOSING",
    "DOSAGE",
    "ADMINISTRATION",
    "MECHANISM OF ACTION",
    "USES",
    "INDICATIONS",
    "MONITORING",
    "PREGNANCY",
    "LACTATION",
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_for_ocr(text):
    """
    Digunakan untuk OCR seperti:

    MetFORM I N
    Met FORMIN
    METFORM I N

    menjadi bentuk yang lebih mudah dicocokkan.
    """

    if not text:
        return ""

    text = text.lower()

    # Hilangkan karakter non-alphanumeric.
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


# ============================================================
# DRUG DETECTION
# ============================================================

def detect_drug(text, drug):
    """
    Return:

    DIRECT
    OCR
    ALIAS
    NONE
    """

    if not text:
        return "NONE"

    normalized = normalize_text(text)
    ocr_normalized = normalize_for_ocr(text)

    drug_key = drug.lower()

    aliases = ALIASES.get(
        drug_key,
        [drug_key],
    )

    # --------------------------------------------------------
    # DIRECT
    # --------------------------------------------------------

    for alias in aliases:

        if alias.lower() in normalized:

            if alias.lower() == drug_key:

                return "DIRECT"

            return "ALIAS"

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    normalized_drug = normalize_for_ocr(drug_key)

    if normalized_drug and normalized_drug in ocr_normalized:

        return "OCR"

    return "NONE"


# ============================================================
# DDI INDICATOR
# ============================================================

def has_ddi_indicator(text):

    normalized = normalize_text(text)

    for indicator in DDI_INDICATORS:

        if indicator in normalized:

            return True

    return False


# ============================================================
# HEADING DETECTION
# ============================================================

def clean_heading(line):

    line = line.strip()

    # Hilangkan karakter OCR tertentu.
    line = line.replace("\xad", "")
    line = re.sub(r"\s+", " ", line)

    return line.strip()


def is_probable_heading(line):

    line = clean_heading(line)

    if not line:
        return False

    if len(line) < 3:
        return False

    if len(line) > 80:
        return False

    upper = line.upper()

    # Jangan anggap angka sebagai heading.
    if re.fullmatch(r"[\d\s\-–—]+", line):
        return False

    # Section heading.
    if upper in IGNORED_HEADINGS:
        return False

    # Heading biasanya uppercase.
    letters = re.sub(r"[^A-Za-z]", "", line)

    if not letters:
        return False

    uppercase_letters = re.sub(
        r"[^A-Z]",
        "",
        line,
    )

    uppercase_ratio = (
        len(uppercase_letters) / len(letters)
    )

    if uppercase_ratio < 0.75:
        return False

    # Jangan ambil kalimat panjang.
    if line.endswith("."):
        return False

    # Jangan ambil baris yang jelas berupa daftar.
    if ";" in line and len(line) > 40:
        return False

    # Hindari heading yang sebenarnya hanya section.
    ignored_prefixes = [
        "THE LEVELS/EFFECTS",
        "MAY INCREASE",
        "MAY DECREASE",
        "INCREASED EFFECT",
        "DECREASED EFFECT",
    ]

    for prefix in ignored_prefixes:

        if upper.startswith(prefix):

            return False

    return True


def extract_headings_from_text(text):

    headings = []

    lines = text.splitlines()

    for line in lines:

        heading = clean_heading(line)

        if is_probable_heading(heading):

            headings.append(heading)

    return headings


# ============================================================
# BUILD ENTRY MAP
# ============================================================

def build_entry_map(chunks):

    """
    Menentukan subject/entry drug untuk setiap chunk.

    Karena heading dapat berada pada chunk sebelumnya,
    kita menggunakan heading terakhir yang ditemukan.

    Contoh:

    CHUNK 100
        DIGOXIN

    CHUNK 101
        Drug Interactions
        ...
        Amiodarone

    Maka CHUNK 101 tetap memiliki subject:
        DIGOXIN
    """

    entry_subjects = {}

    current_subject = None
    current_subject_chunk = None

    for index, chunk in enumerate(chunks):

        text = chunk.get("text", "")

        headings = extract_headings_from_text(text)

        # Ambil heading terakhir dalam chunk.
        if headings:

            # Pilih heading yang paling menyerupai nama obat.
            selected_heading = None

            for heading in headings:

                # Hindari heading yang jelas bukan nama obat.
                if heading.upper() in IGNORED_HEADINGS:
                    continue

                selected_heading = heading

            if selected_heading:

                current_subject = selected_heading
                current_subject_chunk = index

        entry_subjects[index] = {
            "subject": current_subject,
            "subject_chunk_index": current_subject_chunk,
        }

    return entry_subjects


# ============================================================
# SUBJECT MATCHING
# ============================================================

def subject_matches_drug(subject, drug):

    if not subject:
        return False

    result = detect_drug(
        subject,
        drug,
    )

    return result != "NONE"


# ============================================================
# ENTRY-AWARE PAIR VALIDATION
# ============================================================

def validate_pair_in_chunk(
    chunks,
    chunk_index,
    drug_a,
    drug_b,
    entry_map,
):
    """
    Validasi utama V5.

    Syarat utama:

    1. Subject entry = Drug A
       dan Drug B muncul dalam konteks.

    ATAU

    2. Subject entry = Drug B
       dan Drug A muncul dalam konteks.

    Chunk aktual + neighbor digunakan untuk menangani
    potongan entry yang terpisah.
    """

    current = chunks[chunk_index]

    current_text = current.get("text", "")

    current_subject_info = entry_map.get(
        chunk_index,
        {},
    )

    current_subject = current_subject_info.get(
        "subject"
    )

    # ========================================================
    # CURRENT CHUNK
    # ========================================================

    subject_a = subject_matches_drug(
        current_subject,
        drug_a,
    )

    subject_b = subject_matches_drug(
        current_subject,
        drug_b,
    )

    detection_a = detect_drug(
        current_text,
        drug_a,
    )

    detection_b = detect_drug(
        current_text,
        drug_b,
    )

    current_ddi = has_ddi_indicator(
        current_text
    )

    # --------------------------------------------------------
    # Valid direct evidence
    # --------------------------------------------------------

    if subject_a and detection_b != "NONE":

        return {
            "relevant": True,
            "type": determine_type(
                detection_a,
                detection_b,
                context=False,
            ),
            "subject": current_subject,
            "subject_index": current_subject_info.get(
                "subject_chunk_index"
            ),
            "reason": (
                f"Entry subject = {drug_a}, "
                f"{drug_b} ditemukan dalam chunk"
            ),
        }

    if subject_b and detection_a != "NONE":

        return {
            "relevant": True,
            "type": determine_type(
                detection_a,
                detection_b,
                context=False,
            ),
            "subject": current_subject,
            "subject_index": current_subject_info.get(
                "subject_chunk_index"
            ),
            "reason": (
                f"Entry subject = {drug_b}, "
                f"{drug_a} ditemukan dalam chunk"
            ),
        }

    # ========================================================
    # CONTEXT WINDOW
    # ========================================================

    for offset in range(
        -NEIGHBOR_WINDOW,
        NEIGHBOR_WINDOW + 1,
    ):

        if offset == 0:
            continue

        neighbor_index = chunk_index + offset

        if neighbor_index < 0:
            continue

        if neighbor_index >= len(chunks):
            continue

        neighbor = chunks[neighbor_index]

        neighbor_text = neighbor.get(
            "text",
            "",
        )

        neighbor_subject_info = entry_map.get(
            neighbor_index,
            {},
        )

        neighbor_subject = neighbor_subject_info.get(
            "subject"
        )

        # ----------------------------------------------------
        # Pastikan subject tetap salah satu target.
        # ----------------------------------------------------

        neighbor_subject_a = subject_matches_drug(
            neighbor_subject,
            drug_a,
        )

        neighbor_subject_b = subject_matches_drug(
            neighbor_subject,
            drug_b,
        )

        # ----------------------------------------------------
        # Gabungkan current + neighbor.
        # ----------------------------------------------------

        combined_text = (
            current_text
            + "\n"
            + neighbor_text
        )

        combined_a = detect_drug(
            combined_text,
            drug_a,
        )

        combined_b = detect_drug(
            combined_text,
            drug_b,
        )

        if (
            neighbor_subject_a
            and combined_b != "NONE"
        ):

            return {
                "relevant": True,
                "type": determine_type(
                    combined_a,
                    combined_b,
                    context=True,
                ),
                "subject": neighbor_subject,
                "subject_index": neighbor_subject_info.get(
                    "subject_chunk_index"
                ),
                "reason": (
                    f"Context entry subject = {drug_a}, "
                    f"{drug_b} ditemukan pada "
                    f"chunk berdekatan"
                ),
            }

        if (
            neighbor_subject_b
            and combined_a != "NONE"
        ):

            return {
                "relevant": True,
                "type": determine_type(
                    combined_a,
                    combined_b,
                    context=True,
                ),
                "subject": neighbor_subject,
                "subject_index": neighbor_subject_info.get(
                    "subject_chunk_index"
                ),
                "reason": (
                    f"Context entry subject = {drug_b}, "
                    f"{drug_a} ditemukan pada "
                    f"chunk berdekatan"
                ),
            }

    # ========================================================
    # PARTIAL
    # ========================================================

    if (
        detection_a != "NONE"
        or detection_b != "NONE"
    ):

        return {
            "relevant": False,
            "type": "PARTIAL",
            "subject": current_subject,
            "subject_index": current_subject_info.get(
                "subject_chunk_index"
            ),
            "reason": (
                "Salah satu target ditemukan, "
                "tetapi entry-aware pair tidak tervalidasi"
            ),
        }

    return {
        "relevant": False,
        "type": "NONE",
        "subject": current_subject,
        "subject_index": current_subject_info.get(
            "subject_chunk_index"
        ),
        "reason": (
            "Tidak ditemukan pair yang tervalidasi"
        ),
    }


# ============================================================
# CLASSIFICATION
# ============================================================

def determine_type(
    detection_a,
    detection_b,
    context=False,
):

    detections = {
        detection_a,
        detection_b,
    }

    if context:

        if "OCR" in detections:
            return "CONTEXT_OCR"

        if "ALIAS" in detections:
            return "CONTEXT_ALIAS"

        return "CONTEXT"

    if "OCR" in detections:
        return "OCR"

    if "ALIAS" in detections:
        return "ALIAS"

    return "DIRECT"


# ============================================================
# LOAD CHUNKS
# ============================================================

def load_chunks():

    with open(
        CHUNKS_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("RETRIEVAL EVALUATION V5 - ENTRY AWARE")
    print("=" * 80)

    # --------------------------------------------------------
    # Load chunks
    # --------------------------------------------------------

    chunks = load_chunks()

    print()
    print(
        f"Jumlah chunks : {len(chunks):,}"
    )

    # --------------------------------------------------------
    # Build entry map
    # --------------------------------------------------------

    print()
    print("Membangun entry-aware map...")

    entry_map = build_entry_map(
        chunks
    )

    print("Entry-aware map selesai.")

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("MEMUAT MODEL EMBEDDING")
    print("=" * 80)

    print(
        f"Model : {EMBEDDING_MODEL}"
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    # --------------------------------------------------------
    # Chroma
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("MEMUAT CHROMADB")
    print("=" * 80)

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
        f"Jumlah vector : {collection.count():,}"
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    recall_results = {
        k: 0
        for k in TOP_K_VALUES
    }

    first_relevant_ranks = []

    type_counts = {
        "DIRECT": 0,
        "OCR": 0,
        "ALIAS": 0,
        "CONTEXT": 0,
        "CONTEXT_OCR": 0,
        "CONTEXT_ALIAS": 0,
        "PARTIAL": 0,
        "NONE": 0,
    }

    query_results = []

    # --------------------------------------------------------
    # Evaluate each query
    # --------------------------------------------------------

    for query_number, (
        drug_a,
        drug_b,
    ) in enumerate(
        QUERIES,
        start=1,
    ):

        query = (
            f"{drug_a} and {drug_b}"
        )

        print()
        print("=" * 80)
        print(
            f"QUERY {query_number}/{len(QUERIES)}"
        )
        print("=" * 80)

        print(
            f"Query : {query}"
        )

        # ----------------------------------------------------
        # Query embedding
        # ----------------------------------------------------

        query_embedding = model.encode(
            [query],
            normalize_embeddings=True,
        )

        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=max(TOP_K_VALUES),
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

        # ----------------------------------------------------
        # Evaluate ranks
        # ----------------------------------------------------

        relevant_ranks = []

        for rank in range(len(ids)):

            chunk_id = ids[rank]

            # ------------------------------------------------
            # Cari chunk index berdasarkan chunk_id.
            # Jangan mengasumsikan index = number ID.
            # ------------------------------------------------

            chunk_index = None

            for i, chunk in enumerate(chunks):

                if chunk.get("chunk_id") == chunk_id:

                    chunk_index = i
                    break

            if chunk_index is None:

                continue

            validation = validate_pair_in_chunk(
                chunks=chunks,
                chunk_index=chunk_index,
                drug_a=drug_a,
                drug_b=drug_b,
                entry_map=entry_map,
            )

            result_type = validation["type"]

            type_counts[result_type] += 1

            if validation["relevant"]:

                relevant_ranks.append(
                    rank + 1
                )

            # ------------------------------------------------
            # Print top results
            # ------------------------------------------------

            print()
            print(
                f"RANK {rank + 1}"
            )
            print("-" * 80)

            print(
                f"Chunk       : {chunk_id}"
            )

            print(
                f"Distance    : {distances[rank]:.6f}"
            )

            print(
                f"PDF Page    : "
                f"{metadatas[rank].get('pdf_page_start')} - "
                f"{metadatas[rank].get('pdf_page_end')}"
            )

            print(
                f"Classification : {result_type}"
            )

            print(
                f"Relevant    : "
                f"{validation['relevant']}"
            )

            print(
                f"Entry Subject : "
                f"{validation.get('subject')}"
            )

            print(
                f"Subject Chunk : "
                f"{validation.get('subject_index')}"
            )

            print(
                f"Reason      : "
                f"{validation.get('reason')}"
            )

        # ----------------------------------------------------
        # Query metrics
        # ----------------------------------------------------

        print()
        print("-" * 80)

        if relevant_ranks:

            first_rank = min(
                relevant_ranks
            )

            first_relevant_ranks.append(
                first_rank
            )

            print(
                f"Relevant ranks : "
                f"{relevant_ranks}"
            )

            print(
                f"First relevant : "
                f"Rank {first_rank}"
            )

        else:

            print(
                "Tidak ada relevant evidence "
                "yang tervalidasi."
            )

        for k in TOP_K_VALUES:

            if any(
                rank <= k
                for rank in relevant_ranks
            ):

                recall_results[k] += 1

        query_results.append(
            {
                "query": query,
                "relevant_ranks": relevant_ranks,
            }
        )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print()
    print("=" * 80)
    print("HASIL EVALUASI RETRIEVAL V5")
    print("=" * 80)

    print()
    print(
        f"Jumlah query : {len(QUERIES)}"
    )

    print()
    print("RECALL")
    print("-" * 80)

    for k in TOP_K_VALUES:

        count = recall_results[k]

        percentage = (
            count
            / len(QUERIES)
            * 100
        )

        print(
            f"Recall@{k:<2}: "
            f"{count}/{len(QUERIES)} "
            f"({percentage:.2f}%)"
        )

    print()
    print("JENIS RELEVANSI")
    print("-" * 80)

    for key, value in type_counts.items():

        print(
            f"{key:<15}: {value}"
        )

    print()
    print("FIRST RELEVANT RANK")
    print("-" * 80)

    if first_relevant_ranks:

        mean_rank = (
            sum(first_relevant_ranks)
            / len(first_relevant_ranks)
        )

        print(
            f"Query dengan relevant evidence : "
            f"{len(first_relevant_ranks)}/{len(QUERIES)}"
        )

        print(
            f"Rata-rata first relevant rank : "
            f"{mean_rank:.2f}"
        )

    else:

        print(
            "Tidak ada relevant evidence."
        )

    print()
    print("=" * 80)
    print("EVALUASI V5 SELESAI")
    print("=" * 80)


if __name__ == "__main__":
    main()