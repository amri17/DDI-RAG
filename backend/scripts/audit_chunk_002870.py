from pathlib import Path
import json


INPUT_PATH = Path("data/processed/dih_chunks.json")
TARGET_ID = "dih_chunk_002870"

DRUG_A = "Warfarin"
DRUG_B = "Rifampicin"


def normalize_text(text):
    return " ".join(text.lower().split())


def contains_drug(text, drug):
    return normalize_text(text).find(drug.lower()) >= 0


def main():

    print("=" * 90)
    print("AUDIT CHUNK")
    print("=" * 90)
    print(f"Target : {TARGET_ID}")
    print(f"Drug A : {DRUG_A}")
    print(f"Drug B : {DRUG_B}")
    print()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    target = None
    target_index = None

    for i, chunk in enumerate(chunks):
        if chunk.get("id") == TARGET_ID:
            target = chunk
            target_index = i
            break

    if target is None:
        print(f"CHUNK {TARGET_ID} TIDAK DITEMUKAN")
        return

    print(f"Index dalam file : {target_index}")
    print()

    print("=" * 90)
    print("METADATA TARGET")
    print("=" * 90)

    for key, value in target.items():
        if key != "text":
            print(f"{key:20}: {value}")

    text = target.get("text", "")

    print()
    print("=" * 90)
    print("DETEKSI TARGET DRUG")
    print("=" * 90)

    print(f"{DRUG_A:15}: {contains_drug(text, DRUG_A)}")
    print(f"{DRUG_B:15}: {contains_drug(text, DRUG_B)}")

    print()
    print("=" * 90)
    print("TEKS LENGKAP TARGET")
    print("=" * 90)
    print(text)

    # ---------------------------------------------------------
    # Cari chunk sebelum dan sesudah
    # ---------------------------------------------------------

    print()
    print("=" * 90)
    print("CHUNK SEBELUMNYA")
    print("=" * 90)

    if target_index > 0:

        previous = chunks[target_index - 1]

        print(f"ID       : {previous.get('id')}")
        print(
            f"PDF Page : "
            f"{previous.get('pdf_page_start')} - "
            f"{previous.get('pdf_page_end')}"
        )
        print(
            f"Sequence : "
            f"{previous.get('sequence_start')} - "
            f"{previous.get('sequence_end')}"
        )

        previous_text = previous.get("text", "")

        print()
        print(
            f"{DRUG_A} : "
            f"{contains_drug(previous_text, DRUG_A)}"
        )
        print(
            f"{DRUG_B} : "
            f"{contains_drug(previous_text, DRUG_B)}"
        )

        print()
        print(previous_text)

    print()
    print("=" * 90)
    print("CHUNK SESUDAHNYA")
    print("=" * 90)

    if target_index < len(chunks) - 1:

        next_chunk = chunks[target_index + 1]

        print(f"ID       : {next_chunk.get('id')}")
        print(
            f"PDF Page : "
            f"{next_chunk.get('pdf_page_start')} - "
            f"{next_chunk.get('pdf_page_end')}"
        )
        print(
            f"Sequence : "
            f"{next_chunk.get('sequence_start')} - "
            f"{next_chunk.get('sequence_end')}"
        )

        next_text = next_chunk.get("text", "")

        print()
        print(
            f"{DRUG_A} : "
            f"{contains_drug(next_text, DRUG_A)}"
        )
        print(
            f"{DRUG_B} : "
            f"{contains_drug(next_text, DRUG_B)}"
        )

        print()
        print(next_text)

    print()
    print("=" * 90)
    print("AUDIT SELESAI")
    print("=" * 90)


if __name__ == "__main__":
    main()