import chromadb
import csv
import os

# ==============================
# KONFIGURASI
# ==============================

CHROMA_PATH = "data/vectorstore/chroma"
COLLECTION_NAME = "dih"
OUTPUT_FILE = "data/dih_export.csv"

# Jumlah data yang dibaca sekali jalan
BATCH_SIZE = 500


# ==============================
# CONNECT KE CHROMADB
# ==============================

print("Menghubungkan ke ChromaDB...")

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

total = collection.count()

print(f"Collection : {COLLECTION_NAME}")
print(f"Total data: {total}")


# ==============================
# AMBIL SEMUA DATA
# ==============================

all_rows = []

for offset in range(0, total, BATCH_SIZE):

    print(f"Mengambil data {offset + 1} - {min(offset + BATCH_SIZE, total)}...")

    result = collection.get(
        limit=BATCH_SIZE,
        offset=offset,
        include=[
            "documents",
            "metadatas"
        ]
    )

    ids = result["ids"]
    documents = result["documents"]
    metadatas = result["metadatas"]

    for i in range(len(ids)):

        metadata = metadatas[i] or {}

        row = {
            "id": ids[i],
            "document": documents[i] or ""
        }

        # Masukkan metadata ke kolom CSV
        for key, value in metadata.items():
            row[key] = value

        all_rows.append(row)


# ==============================
# MENENTUKAN SEMUA KOLOM
# ==============================

columns = set()

for row in all_rows:
    columns.update(row.keys())

# Supaya kolom utama berada di depan
columns = list(columns)

priority_columns = [
    "id",
    "document",
    "source",
    "source_type",
    "pdf_page_start",
    "pdf_page_end",
    "character_count",
    "sequence_start",
    "sequence_end",
    "columns"
]

ordered_columns = []

for column in priority_columns:
    if column in columns:
        ordered_columns.append(column)

for column in columns:
    if column not in ordered_columns:
        ordered_columns.append(column)


# ==============================
# SIMPAN KE CSV
# ==============================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=ordered_columns,
        extrasaction="ignore"
    )

    writer.writeheader()

    for row in all_rows:
        writer.writerow(row)


# ==============================
# SELESAI
# ==============================

print()
print("=" * 50)
print("EXPORT SELESAI")
print("=" * 50)
print(f"Total data : {len(all_rows)}")
print(f"File       : {OUTPUT_FILE}")
print("=" * 50)