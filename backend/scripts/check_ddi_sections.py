import json

INPUT_PATH = "data/processed/dih_chunks.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print("=" * 100)
print("CHECK DRUG INTERACTIONS SECTIONS")
print("=" * 100)

found = 0

for chunk in chunks:
    text = chunk["text"]

    position = text.find("Drug Interactions")

    if position == -1:
        continue

    found += 1

    start = max(0, position - 300)
    end = min(len(text), position + 1000)

    print("\n" + "-" * 100)
    print("Chunk ID :", chunk["chunk_id"])
    print(
        "Page     :",
        chunk["metadata"].get("pdf_page_start"),
        "-",
        chunk["metadata"].get("pdf_page_end")
    )
    print("Posisi   :", position)
    print("\nKonteks:")
    print(text[start:end])

print("\n" + "=" * 100)
print("Total chunk dengan 'Drug Interactions':", found)
print("=" * 100)