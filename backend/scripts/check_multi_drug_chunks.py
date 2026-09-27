import json
import re

INPUT_PATH = "data/processed/dih_chunks.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)


def is_probable_drug_heading(line):
    """
    Mendeteksi kemungkinan nama obat yang ditulis sebagai heading.
    Fokus awal pada heading uppercase seperti:
    WARFARIN
    AMIODARONE
    INSULIN REGULAR
    """
    line = line.strip()

    if not line:
        return False

    # Terlalu panjang untuk kemungkinan heading
    if len(line) > 100:
        return False

    # Jangan anggap kalimat biasa sebagai heading
    if line.endswith((".", ":", ";", ",")):
        return False

    # Harus mengandung huruf
    if not re.search(r"[A-Za-z]", line):
        return False

    # Minimal sebagian besar karakter alfabet berupa uppercase
    letters = re.findall(r"[A-Za-z]", line)

    if len(letters) < 3:
        return False

    uppercase_ratio = sum(c.isupper() for c in letters) / len(letters)

    return uppercase_ratio >= 0.75


results = []

for chunk in chunks:
    lines = chunk["text"].splitlines()

    headings = []

    for line in lines:
        if is_probable_drug_heading(line):
            # Hindari heading umum
            excluded = {
                "DRUG INTERACTIONS",
                "DOSAGE",
                "DOSAGE FORMS",
                "WARNINGS",
                "PRECAUTIONS",
                "CONTRAINDICATIONS",
                "ADVERSE REACTIONS",
                "MECHANISM",
                "PHARMACOLOGY",
                "INDICATIONS",
                "MONITORING",
            }

            if line.strip().upper() not in excluded:
                headings.append(line.strip())

    # Hapus duplikasi
    headings = list(dict.fromkeys(headings))

    if len(headings) >= 2:
        results.append({
            "chunk_id": chunk["chunk_id"],
            "page_start": chunk["metadata"].get("pdf_page_start"),
            "page_end": chunk["metadata"].get("pdf_page_end"),
            "headings": headings,
        })


print("=" * 100)
print("HASIL PEMERIKSAAN MULTI-DRUG CHUNK")
print("=" * 100)

print("Total chunk:", len(chunks))
print("Chunk dengan >=2 kemungkinan drug heading:", len(results))

if len(chunks) > 0:
    percentage = len(results) / len(chunks) * 100
    print("Persentase:", round(percentage, 2), "%")

print()


for i, item in enumerate(results, 1):
    print("-" * 100)
    print(f"Kasus #{i}")
    print("Chunk ID :", item["chunk_id"])
    print("Page     :", item["page_start"], "-", item["page_end"])
    print("Heading  :")

    for heading in item["headings"]:
        print("  -", heading)
        