from pathlib import Path
import json
import re


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = Path("data/processed/dih_preprocessed.json")
OUTPUT_PATH = Path("data/processed/dih_chunks.json")

# Target ukuran chunk dalam karakter
CHUNK_SIZE = 3000

# Overlap antar chunk
CHUNK_OVERLAP = 500

# Chunk terlalu kecil akan digabung dengan chunk berikutnya
MIN_CHUNK_SIZE = 500


# ============================================================
# TEXT UTILITIES
# ============================================================

def normalize_text(text: str) -> str:
    """
    Membersihkan whitespace ringan tanpa mengubah isi klinis.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Hilangkan spasi berlebih
    text = re.sub(r"[ \t]+", " ", text)

    # Rapikan newline
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_long_text(text: str, max_length: int) -> list[str]:
    """
    Membagi block yang sangat panjang menjadi beberapa bagian.

    Prioritas pemotongan:
    1. paragraf
    2. kalimat
    3. spasi
    4. hard cut jika memang diperlukan
    """
    text = normalize_text(text)

    if len(text) <= max_length:
        return [text]

    parts = []

    remaining = text

    while len(remaining) > max_length:
        candidate = remaining[:max_length]

        # Prioritas 1: newline
        split_position = candidate.rfind("\n\n")

        # Prioritas 2: akhir kalimat
        if split_position < max_length * 0.5:
            sentence_positions = [
                candidate.rfind(". "),
                candidate.rfind("; "),
                candidate.rfind(": "),
            ]
            sentence_positions = [
                pos for pos in sentence_positions
                if pos >= int(max_length * 0.5)
            ]

            if sentence_positions:
                split_position = max(sentence_positions)

        # Prioritas 3: spasi
        if split_position < int(max_length * 0.5):
            split_position = candidate.rfind(" ")

        # Fallback
        if split_position < int(max_length * 0.5):
            split_position = max_length

        part = remaining[:split_position].strip()

        if part:
            parts.append(part)

        remaining = remaining[split_position:].strip()

    if remaining:
        parts.append(remaining)

    return parts


# ============================================================
# STRUCTURAL BOUNDARY DETECTION
# ============================================================

def is_probable_entry_heading(text: str) -> bool:
    """
    Mendeteksi block yang secara STRUKTURAL terlihat seperti
    heading/awal entri.

    Penting:
    Fungsi ini TIDAK mencoba mengenali nama obat berdasarkan
    database eksternal atau menebak nama obat.

    Yang diperiksa hanya karakteristik format:
    - satu baris
    - relatif pendek
    - dominan huruf kapital
    - tidak terlihat seperti kalimat biasa
    - tidak berakhir dengan tanda baca kalimat

    Tujuannya hanya mencegah chunk memotong heading penting.
    """

    text = normalize_text(text)

    if not text:
        return False

    # Jangan perlakukan block panjang sebagai heading
    if len(text) > 120:
        return False

    # Heading biasanya hanya satu baris
    if "\n" in text:
        return False

    # Hindari angka panjang / dosis
    if len(re.findall(r"\d", text)) > 4:
        return False

    # Harus memiliki huruf
    letters = re.findall(r"[A-Za-z]", text)

    if len(letters) < 3:
        return False

    # Rasio huruf kapital
    uppercase_letters = [
        char for char in letters
        if char.isupper()
    ]

    uppercase_ratio = len(uppercase_letters) / len(letters)

    if uppercase_ratio < 0.75:
        return False

    # Jangan anggap label umum sebagai entry heading
    excluded = {
        "WARNING",
        "WARNINGS",
        "PRECAUTIONS",
        "CONTRAINDICATIONS",
        "ADVERSE EFFECTS",
        "DRUG INTERACTIONS",
        "INTERACTIONS",
        "PHARMACOLOGY",
        "PHARMACOKINETICS",
        "DOSAGE",
        "DOSAGE FORMS",
        "DESCRIPTION",
        "INDICATIONS",
        "CLINICAL EFFECTS",
        "MECHANISM",
        "REFERENCES",
        "INDEX",
        "INTRODUCTION",
        "TABLE OF CONTENTS",
    }

    normalized = re.sub(r"\s+", " ", text).strip().upper()

    if normalized in excluded:
        return False

    # Heading tidak biasanya diakhiri tanda baca
    if text.endswith((".", ",", ";", ":")):
        return False

    return True


# ============================================================
# BLOCK REPRESENTATION
# ============================================================

def prepare_units(page: dict) -> list[dict]:
    """
    Mengubah ordered_blocks menjadi unit-unit chunking.

    Satu block normal = satu unit.

    Jika block terlalu panjang, block dipecah menjadi beberapa unit.
    """

    ordered_blocks = page.get("ordered_blocks", [])

    units = []

    for block in ordered_blocks:
        original_text = normalize_text(block.get("text", ""))

        if not original_text:
            continue

        pieces = split_long_text(
            original_text,
            CHUNK_SIZE,
        )

        for piece_index, piece in enumerate(pieces):
            unit = {
                "text": piece,
                "pdf_page": page.get("pdf_page"),
                "sequence": block.get("sequence"),
                "block_id": block.get("block_id"),
                "column": block.get("column"),
                "piece_index": piece_index,
                "original_block_length": len(original_text),
            }

            units.append(unit)

    return units


# ============================================================
# CHUNK CREATION
# ============================================================

def build_chunk(
    units: list[dict],
    chunk_number: int,
    overlap_from: str | None = None,
) -> dict:
    """
    Membuat satu object chunk.
    """

    texts = [
        unit["text"]
        for unit in units
        if unit["text"]
    ]

    text = "\n\n".join(texts).strip()

    pages = [
        unit["pdf_page"]
        for unit in units
        if unit["pdf_page"] is not None
    ]

    sequences = [
        unit["sequence"]
        for unit in units
        if unit["sequence"] is not None
    ]

    block_ids = [
        unit["block_id"]
        for unit in units
        if unit["block_id"] is not None
    ]

    columns = list(
        dict.fromkeys(
            unit["column"]
            for unit in units
            if unit["column"] is not None
        )
    )

    chunk = {
        "chunk_id": f"dih_chunk_{chunk_number:06d}",
        "text": text,
        "metadata": {
            "pdf_page_start": min(pages) if pages else None,
            "pdf_page_end": max(pages) if pages else None,
            "sequence_start": min(sequences) if sequences else None,
            "sequence_end": max(sequences) if sequences else None,
            "block_ids": block_ids,
            "columns": columns,
            "character_count": len(text),
            "source": "Drug Interaction Handbook",
            "source_type": "book",
        },
    }

    if overlap_from is not None:
        chunk["metadata"]["overlap_from"] = overlap_from

    return chunk


def get_overlap_units(
    units: list[dict],
    overlap_size: int,
) -> list[dict]:
    """
    Mengambil unit dari bagian akhir chunk untuk overlap.

    Overlap dihitung berdasarkan karakter, tetapi unit/block
    tetap dipertahankan utuh selama memungkinkan.
    """

    if not units:
        return []

    selected = []
    current_length = 0

    for unit in reversed(units):
        unit_length = len(unit["text"])

        if selected and current_length + unit_length > overlap_size:
            break

        selected.insert(0, unit)
        current_length += unit_length

        if current_length >= overlap_size:
            break

    return selected


def create_chunks_from_page(
    page: dict,
    chunk_number_start: int,
) -> tuple[list[dict], int]:
    """
    Membuat chunk dari satu halaman.

    Chunk tidak dipaksa berhenti di akhir halaman.
    Namun setiap block dipertahankan sebagai unit.
    """

    units = prepare_units(page)

    if not units:
        return [], chunk_number_start

    chunks = []

    current_units = []
    current_length = 0

    chunk_number = chunk_number_start

    for unit in units:
        unit_length = len(unit["text"])

        # ----------------------------------------------------
        # Jika unit sendiri lebih besar dari target
        # ----------------------------------------------------
        if unit_length > CHUNK_SIZE:
            if current_units:
                chunk_number += 1

                chunk = build_chunk(
                    current_units,
                    chunk_number,
                )

                chunks.append(chunk)

                current_units = []
                current_length = 0

            chunk_number += 1

            chunk = build_chunk(
                [unit],
                chunk_number,
            )

            chunks.append(chunk)

            continue

        # ----------------------------------------------------
        # Apakah unit akan membuat chunk terlalu besar?
        # ----------------------------------------------------
        would_exceed = (
            current_length > 0
            and current_length + unit_length + 2 > CHUNK_SIZE
        )

        if would_exceed:

            # Simpan chunk sekarang
            chunk_number += 1

            previous_chunk_id = (
                f"dih_chunk_{chunk_number:06d}"
            )

            chunk = build_chunk(
                current_units,
                chunk_number,
            )

            chunks.append(chunk)

            # Ambil overlap
            overlap_units = get_overlap_units(
                current_units,
                CHUNK_OVERLAP,
            )

            current_units = overlap_units + [unit]

            current_length = sum(
                len(item["text"]) + 2
                for item in current_units
            )

            # Update metadata overlap
            if chunks:
                chunks[-1]["metadata"]["has_overlap_to_next"] = bool(
                    overlap_units
                )

            # Catat sumber overlap pada chunk baru nanti
            pending_overlap_from = previous_chunk_id

            continue

        # ----------------------------------------------------
        # Tambahkan unit ke chunk sekarang
        # ----------------------------------------------------
        current_units.append(unit)

        current_length += unit_length

        if len(current_units) > 1:
            current_length += 2

    # --------------------------------------------------------
    # Simpan chunk terakhir
    # --------------------------------------------------------
    if current_units:
        chunk_number += 1

        chunk = build_chunk(
            current_units,
            chunk_number,
        )

        chunks.append(chunk)

    return chunks, chunk_number


# ============================================================
# GLOBAL CHUNKING
# ============================================================

def create_chunks(data: list[dict]) -> list[dict]:
    """
    Membuat chunk berdasarkan seluruh dokumen.

    Chunking tetap berjalan mengikuti sequence global.
    """

    all_units = []

    for page in data:
        units = prepare_units(page)

        if units:
            all_units.extend(units)

    if not all_units:
        return []

    # Pastikan urutan global benar
    all_units.sort(
        key=lambda unit: (
            unit["sequence"]
            if unit["sequence"] is not None
            else 999999999
        )
    )

    chunks = []

    current_units = []
    current_length = 0

    chunk_number = 0
    previous_chunk_id = None

    for unit in all_units:

        unit_length = len(unit["text"])

        # ----------------------------------------------------
        # Unit sangat panjang
        # ----------------------------------------------------
        if unit_length > CHUNK_SIZE:

            if current_units:
                chunk_number += 1

                chunk = build_chunk(
                    current_units,
                    chunk_number,
                )

                chunks.append(chunk)

                previous_chunk_id = chunk["chunk_id"]

                overlap_units = get_overlap_units(
                    current_units,
                    CHUNK_OVERLAP,
                )

                current_units = overlap_units

                current_length = sum(
                    len(item["text"]) + 2
                    for item in current_units
                )

            # Unit panjang sudah dipecah oleh prepare_units,
            # sehingga seharusnya tidak sering masuk ke sini.
            current_units.append(unit)

            current_length += unit_length

            continue

        # ----------------------------------------------------
        # Cek structural heading
        # ----------------------------------------------------
        is_heading = is_probable_entry_heading(
            unit["text"]
        )

        # ----------------------------------------------------
        # Jika heading baru muncul dan chunk sebelumnya
        # sudah cukup besar, tutup chunk sebelum heading.
        #
        # Ini membantu mencegah satu chunk mencampurkan
        # bagian akhir satu entri dengan awal entri berikutnya.
        # ----------------------------------------------------
        if (
            is_heading
            and current_units
            and current_length >= MIN_CHUNK_SIZE
        ):
            chunk_number += 1

            chunk = build_chunk(
                current_units,
                chunk_number,
            )

            chunks.append(chunk)

            previous_chunk_id = chunk["chunk_id"]

            overlap_units = get_overlap_units(
                current_units,
                CHUNK_OVERLAP,
            )

            # Jangan membawa heading sebelumnya ke chunk baru.
            # Overlap hanya digunakan dari unit sebelum heading.
            current_units = overlap_units

            current_length = sum(
                len(item["text"]) + 2
                for item in current_units
            )

        # ----------------------------------------------------
        # Jika penambahan unit membuat chunk terlalu besar
        # ----------------------------------------------------
        would_exceed = (
            current_length > 0
            and current_length + unit_length + 2 > CHUNK_SIZE
        )

        if would_exceed:

            chunk_number += 1

            chunk = build_chunk(
                current_units,
                chunk_number,
            )

            chunks.append(chunk)

            previous_chunk_id = chunk["chunk_id"]

            overlap_units = get_overlap_units(
                current_units,
                CHUNK_OVERLAP,
            )

            current_units = overlap_units + [unit]

            current_length = sum(
                len(item["text"]) + 2
                for item in current_units
            )

            continue

        # ----------------------------------------------------
        # Tambahkan unit
        # ----------------------------------------------------
        current_units.append(unit)

        current_length += unit_length

        if len(current_units) > 1:
            current_length += 2

    # --------------------------------------------------------
    # Chunk terakhir
    # --------------------------------------------------------
    if current_units:

        chunk_number += 1

        chunk = build_chunk(
            current_units,
            chunk_number,
        )

        chunks.append(chunk)

    return chunks


# ============================================================
# POST PROCESSING
# ============================================================

def merge_tiny_chunks(chunks: list[dict]) -> list[dict]:
    """
    Menggabungkan chunk yang sangat kecil dengan chunk berikutnya
    jika memungkinkan.

    Tidak dilakukan jika hasil penggabungan akan terlalu besar.
    """

    if not chunks:
        return []

    result = []

    index = 0

    while index < len(chunks):

        current = chunks[index]

        if (
            current["metadata"]["character_count"] < MIN_CHUNK_SIZE
            and index + 1 < len(chunks)
        ):
            next_chunk = chunks[index + 1]

            combined_text = (
                current["text"]
                + "\n\n"
                + next_chunk["text"]
            )

            if len(combined_text) <= CHUNK_SIZE * 1.15:

                merged = {
                    "chunk_id": next_chunk["chunk_id"],
                    "text": combined_text,
                    "metadata": {
                        "pdf_page_start": min(
                            current["metadata"]["pdf_page_start"],
                            next_chunk["metadata"]["pdf_page_start"],
                        ),
                        "pdf_page_end": max(
                            current["metadata"]["pdf_page_end"],
                            next_chunk["metadata"]["pdf_page_end"],
                        ),
                        "sequence_start": min(
                            current["metadata"]["sequence_start"],
                            next_chunk["metadata"]["sequence_start"],
                        ),
                        "sequence_end": max(
                            current["metadata"]["sequence_end"],
                            next_chunk["metadata"]["sequence_end"],
                        ),
                        "block_ids": (
                            current["metadata"]["block_ids"]
                            + next_chunk["metadata"]["block_ids"]
                        ),
                        "columns": list(
                            dict.fromkeys(
                                current["metadata"]["columns"]
                                + next_chunk["metadata"]["columns"]
                            )
                        ),
                        "character_count": len(combined_text),
                        "source": "Drug Interaction Handbook",
                        "source_type": "book",
                    },
                }

                result.append(merged)
                index += 2
                continue

        result.append(current)
        index += 1

    return result


def renumber_chunks(chunks: list[dict]) -> list[dict]:
    """
    Menjamin chunk_id berurutan setelah post-processing.
    """

    for index, chunk in enumerate(chunks, start=1):
        chunk["chunk_id"] = f"dih_chunk_{index:06d}"

    return chunks


# ============================================================
# STATISTICS
# ============================================================

def calculate_statistics(chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "total_chunks": 0,
            "total_characters": 0,
            "average_characters": 0,
            "min_characters": 0,
            "max_characters": 0,
        }

    character_counts = [
        chunk["metadata"]["character_count"]
        for chunk in chunks
    ]

    return {
        "total_chunks": len(chunks),
        "total_characters": sum(character_counts),
        "average_characters": round(
            sum(character_counts) / len(character_counts),
            2,
        ),
        "min_characters": min(character_counts),
        "max_characters": max(character_counts),
    }


def print_statistics(chunks: list[dict]) -> None:

    stats = calculate_statistics(chunks)

    print()
    print("=" * 60)
    print("HASIL CHUNKING DIH")
    print("=" * 60)

    print(
        f"Total chunk        : "
        f"{stats['total_chunks']:,}"
    )

    print(
        f"Total karakter     : "
        f"{stats['total_characters']:,}"
    )

    print(
        f"Rata-rata karakter : "
        f"{stats['average_characters']:,}"
    )

    print(
        f"Minimum karakter   : "
        f"{stats['min_characters']:,}"
    )

    print(
        f"Maksimum karakter  : "
        f"{stats['max_characters']:,}"
    )

    print("=" * 60)


# ============================================================
# PREVIEW
# ============================================================

def print_preview(chunks: list[dict], count: int = 3) -> None:

    print()
    print("=" * 60)
    print(f"PREVIEW {min(count, len(chunks))} CHUNK")
    print("=" * 60)

    for chunk in chunks[:count]:

        metadata = chunk["metadata"]

        print()
        print("-" * 60)

        print(
            f"Chunk ID     : "
            f"{chunk['chunk_id']}"
        )

        print(
            f"Halaman      : "
            f"{metadata['pdf_page_start']} - "
            f"{metadata['pdf_page_end']}"
        )

        print(
            f"Sequence     : "
            f"{metadata['sequence_start']} - "
            f"{metadata['sequence_end']}"
        )

        print(
            f"Karakter     : "
            f"{metadata['character_count']}"
        )

        print(
            f"Kolom        : "
            f"{', '.join(metadata['columns'])}"
        )

        preview = chunk["text"][:800]

        print()
        print(preview)

        if len(chunk["text"]) > 800:
            print("...")


# ============================================================
# SAVE
# ============================================================

def save_chunks(
    chunks: list[dict],
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("CHUNKING DIH")
    print("=" * 60)

    print(
        f"Input : "
        f"{INPUT_PATH.resolve()}"
    )

    print(
        f"Output: "
        f"{OUTPUT_PATH.resolve()}"
    )

    print(
        f"Chunk size    : "
        f"{CHUNK_SIZE}"
    )

    print(
        f"Chunk overlap  : "
        f"{CHUNK_OVERLAP}"
    )

    # --------------------------------------------------------
    # Check input
    # --------------------------------------------------------

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "File input tidak ditemukan:\n"
            f"{INPUT_PATH.resolve()}"
        )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Format dih_preprocessed.json "
            "harus berupa list."
        )

    print()
    print(
        f"Jumlah halaman input: "
        f"{len(data):,}"
    )

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

    print()
    print("Membuat chunk...")

    chunks = create_chunks(data)

    print(
        f"Chunk awal: "
        f"{len(chunks):,}"
    )

    # --------------------------------------------------------
    # Merge tiny chunks
    # --------------------------------------------------------

    chunks = merge_tiny_chunks(chunks)

    # --------------------------------------------------------
    # Renumber
    # --------------------------------------------------------

    chunks = renumber_chunks(chunks)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_chunks(
        chunks=chunks,
        output_path=OUTPUT_PATH,
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print_statistics(chunks)

    print_preview(
        chunks,
        count=3,
    )

    print()
    print("=" * 60)
    print("SELESAI")
    print("=" * 60)

    print(
        f"Output tersimpan di:\n"
        f"{OUTPUT_PATH.resolve()}"
    )


if __name__ == "__main__":
    main()
