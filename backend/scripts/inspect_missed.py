import json
from pathlib import Path


INPUT_PATH = Path("data/processed/dih_chunks.json")

TARGET_IDS = [
    "dih_chunk_000397",
    "dih_chunk_002001",
    "dih_chunk_002870",
    "dih_chunk_000979",
    "dih_chunk_002240",
]


with open(INPUT_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)


# Buat mapping ID -> index
id_to_index = {
    chunk["chunk_id"]: i
    for i, chunk in enumerate(chunks)
}


print("=" * 100)
print("INSPEKSI CHUNK YANG TERDETEKSI SEBAGAI MISS")
print("=" * 100)


for target_id in TARGET_IDS:

    if target_id not in id_to_index:
        print(f"\n{target_id} TIDAK DITEMUKAN")
        continue

    index = id_to_index[target_id]

    print("\n")
    print("#" * 100)
    print(f"TARGET : {target_id}")
    print(f"INDEX  : {index}")
    print("#" * 100)

    # Tampilkan chunk sebelum
    start = max(0, index - 1)

    # Tampilkan target + 2 chunk setelahnya
    end = min(len(chunks), index + 3)

    for j in range(start, end):

        chunk = chunks[j]

        print("\n" + "=" * 100)
        print(f"CHUNK INDEX : {j}")
        print(f"CHUNK ID    : {chunk.get('chunk_id')}")
        print(f"PDF PAGE    : {chunk.get('pdf_page_start')} - {chunk.get('pdf_page_end')}")
        print(f"SEQUENCE    : {chunk.get('sequence_start')} - {chunk.get('sequence_end')}")
        print(f"COLUMNS     : {chunk.get('columns')}")
        print("=" * 100)

        print(chunk.get("text", ""))


print("\n")
print("=" * 100)
print("INSPEKSI SELESAI")
print("=" * 100)