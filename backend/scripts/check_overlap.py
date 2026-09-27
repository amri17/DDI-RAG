import json

INPUT_PATH = "data/processed/dih_chunks.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print("=" * 100)
print("CHECK CHUNK OVERLAP")
print("=" * 100)

total_pairs = 0
overlap_found = 0

for i in range(len(chunks) - 1):

    current = chunks[i]["text"]
    next_chunk = chunks[i + 1]["text"]

    # Ambil 500 karakter terakhir dari chunk sekarang
    tail = current[-500:]

    if tail in next_chunk:
        overlap_found += 1

        if overlap_found <= 20:
            print("\n" + "-" * 100)
            print("Chunk sekarang :", chunks[i]["chunk_id"])
            print("Chunk berikutnya:", chunks[i + 1]["chunk_id"])
            print("\nOverlap ditemukan:")
            print(tail)

    total_pairs += 1

print("\n" + "=" * 100)
print("Total pasangan chunk :", total_pairs)
print("Overlap ditemukan    :", overlap_found)
print(
    "Persentase           :",
    round(overlap_found / total_pairs * 100, 2),
    "%"
)
print("=" * 100)