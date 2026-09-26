from pathlib import Path
import json
import re


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = Path("data/processed/dih_preprocessed.json")
OUTPUT_PATH = Path("data/processed/dih_chunks.json")

# Target ukuran chunk dalam karakter.
# Nantinya akan kita evaluasi lagi berdasarkan hasil chunking.
CHUNK_SIZE = 3000

# Overlap antar-chunk dalam karakter.
CHUNK_OVERLAP = 500

# Minimum karakter agar chunk dianggap valid.
MIN_CHUNK_SIZE = 300


# ============================================================
# TEXT UTILITIES
# ============================================================

def normalize_text(text: str) -> str:
    """
    Membersihkan whitespace tambahan tanpa mengubah
    isi klinis dari teks.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Spasi/tab berulang
    text = re.sub(r"[ \t]+", " ", text)

    # Baris kosong berlebihan
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_text_into_units(text: str) -> list[str]:
    """
    Memecah teks menjadi unit yang relatif aman untuk digabungkan.

    Prioritas:
    1. Paragraf
    2. Baris
    3. Kalimat
    """
    text = normalize_text(text)

    if not text:
        return []

    # Pertahankan paragraf sebagai unit utama
    paragraphs = re.split(r"\n\s*\n", text)

    units = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # Jika paragraf terlalu panjang, pecah berdasarkan baris.
        if len(paragraph) > CHUNK_SIZE:
            lines = [
                line.strip()
                for line in paragraph.split("\n")
                if line.strip()
            ]

            for line in lines:
                if line:
                    units.append(line)
        else:
            units.append(paragraph)

    return units


def split_long_text(text: str, max_size: int) -> list[str]:
    """
    Memecah teks yang masih terlalu panjang.
    Pemotongan dilakukan berdasarkan spasi agar tidak
    memotong kata di tengah.
    """
    words = text.split()

    if not words:
        return []

    parts = []
    current = []

    current_length = 0

    for word in words:
        additional_length = len(word)

        if current:
            additional_length += 1

        if (
            current
            and current_length + additional_length > max_size
        ):
            parts.append(" ".join(current))
            current = [word]
            current_length = len(word)
        else:
            current.append(word)
            current_length += additional_length

    if current:
        parts.append(" ".join(current))

    return parts


# ============================================================
# BLOCK HANDLING
# ============================================================

def get_page_blocks(page: dict) -> list[dict]:
    """
    Mengambil ordered_blocks dari satu halaman.

    ordered_blocks sudah merupakan hasil preprocessing:
    left column → right column.

    Sequence tetap dipertahankan sebagai metadata.
    """
    blocks = page.get("ordered_blocks", [])

    valid_blocks = []

    for block in blocks:
        text = normalize_text(block.get("text", ""))

        if not text:
            continue

        valid_blocks.append(
            {
                "pdf_page": page.get("pdf_page"),
                "block_id": block.get("block_id"),
                "bbox": block.get("bbox"),
                "sequence": block.get("sequence"),
                "column": block.get("column"),
                "text": text,
            }
        )

    return valid_blocks


def collect_blocks(data: list[dict]) -> list[dict]:
    """
    Menggabungkan seluruh block dari seluruh halaman
    berdasarkan sequence global.

    Tidak menggabungkan konteks drug secara otomatis.
    """
    all_blocks = []

    for page in data:
        page_blocks = get_page_blocks(page)
        all_blocks.extend(page_blocks)

    # Pastikan urutan berdasarkan sequence
    all_blocks.sort(
        key=lambda block: (
            block["sequence"]
            if block["sequence"] is not None
            else float("inf")
        )
    )

    return all_blocks


# ============================================================
# CHUNK CREATION
# ============================================================

def create_chunk(
    blocks: list[dict],
    text: str,
    chunk_number: int,
) -> dict:
    """
    Membuat satu objek chunk dengan metadata lengkap.
    """

    pages = [
        block["pdf_page"]
        for block in blocks
        if block["pdf_page"] is not None
    ]

    sequences = [
        block["sequence"]
        for block in blocks
        if block["sequence"] is not None
    ]

    block_ids = [
        block["block_id"]
        for block in blocks
        if block["block_id"] is not None
    ]

    columns = []

    for block in blocks:
        column = block.get("column")

        if column and column not in columns:
            columns.append(column)

    return {
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


def create_chunks(blocks: list[dict]) -> list[dict]:
    """
    Membuat chunk dari block secara berurutan.

    Prinsip:
    - Block tidak dipisahkan secara sembarangan.
    - Chunk dibentuk hingga mendekati CHUNK_SIZE.
    - Chunk yang terlalu panjang dipecah berdasarkan kata.
    - Overlap dibuat menggunakan teks dari chunk sebelumnya.
    """

    chunks = []

    current_blocks = []
    current_units = []
    current_length = 0

    chunk_number = 1

    for block in blocks:

        block_text = block["text"]

        units = split_text_into_units(block_text)

        if not units:
            continue

        for unit in units:

            # Jika satu unit terlalu panjang,
            # pecah terlebih dahulu.
            if len(unit) > CHUNK_SIZE:

                long_parts = split_long_text(
                    unit,
                    CHUNK_SIZE,
                )

                for part in long_parts:

                    if current_units:
                        candidate_length = (
                            current_length
                            + len(part)
                            + 2
                        )
                    else:
                        candidate_length = len(part)

                    if (
                        current_units
                        and candidate_length > CHUNK_SIZE
                    ):
                        chunk_text = "\n\n".join(
                            current_units
                        )

                        chunks.append(
                            create_chunk(
                                blocks=current_blocks,
                                text=chunk_text,
                                chunk_number=chunk_number,
                            )
                        )

                        chunk_number += 1

                        # Buat overlap dari akhir chunk
                        overlap_text = build_overlap(
                            current_units
                        )

                        current_units = (
                            [overlap_text]
                            if overlap_text
                            else []
                        )

                        current_blocks = (
                            current_blocks[-1:]
                            if overlap_text
                            else []
                        )

                        current_length = (
                            len(overlap_text)
                            if overlap_text
                            else 0
                        )

                    current_units.append(part)

                    current_length = (
                        sum(len(item) for item in current_units)
                        + 2 * (len(current_units) - 1)
                    )

                continue

            # Kandidat chunk berikutnya
            separator_length = 2 if current_units else 0

            candidate_length = (
                current_length
                + separator_length
                + len(unit)
            )

            if (
                current_units
                and candidate_length > CHUNK_SIZE
            ):
                chunk_text = "\n\n".join(
                    current_units
                )

                chunks.append(
                    create_chunk(
                        blocks=current_blocks,
                        text=chunk_text,
                        chunk_number=chunk_number,
                    )
                )

                chunk_number += 1

                # Ambil overlap dari chunk sebelumnya
                overlap_text = build_overlap(
                    current_units
                )

                current_units = (
                    [overlap_text]
                    if overlap_text
                    else []
                )

                current_blocks = (
                    current_blocks[-1:]
                    if overlap_text
                    else []
                )

                current_length = (
                    len(overlap_text)
                    if overlap_text
                    else 0
                )

            current_units.append(unit)

            if block not in current_blocks:
                current_blocks.append(block)

            current_length = (
                sum(len(item) for item in current_units)
                + 2 * (len(current_units) - 1)
            )

    # Simpan chunk terakhir
    if current_units:

        chunk_text = "\n\n".join(
            current_units
        )

        if len(chunk_text) >= MIN_CHUNK_SIZE:
            chunks.append(
                create_chunk(
                    blocks=current_blocks,
                    text=chunk_text,
                    chunk_number=chunk_number,
                )
            )

    return chunks


# ============================================================
# OVERLAP
# ============================================================

def build_overlap(units: list[str]) -> str:
    """
    Mengambil bagian akhir chunk untuk overlap.

    Overlap dibatasi sekitar CHUNK_OVERLAP karakter.
    """
    if not units:
        return ""

    selected = []
    total_length = 0

    for unit in reversed(units):

        additional_length = (
            len(unit)
            + (2 if selected else 0)
        )

        if (
            selected
            and total_length + additional_length
            > CHUNK_OVERLAP
        ):
            break

        selected.insert(0, unit)
        total_length += additional_length

    return "\n\n".join(selected)


# ============================================================
# STATISTICS
# ============================================================

def calculate_statistics(
    chunks: list[dict],
) -> dict:

    if not chunks:
        return {
            "total_chunks": 0,
            "total_characters": 0,
            "average_characters": 0,
            "minimum_characters": 0,
            "maximum_characters": 0,
        }

    lengths = [
        len(chunk["text"])
        for chunk in chunks
    ]

    return {
        "total_chunks": len(chunks),
        "total_characters": sum(lengths),
        "average_characters": round(
            sum(lengths) / len(lengths)
        ),
        "minimum_characters": min(lengths),
        "maximum_characters": max(lengths),
    }


def print_statistics(chunks: list[dict]) -> None:

    stats = calculate_statistics(chunks)

    print()
    print("=" * 60)
    print("HASIL CHUNKING DIH")
    print("=" * 60)

    print(
        f"Total chunk          : "
        f"{stats['total_chunks']:,}"
    )

    print(
        f"Total karakter       : "
        f"{stats['total_characters']:,}"
    )

    print(
        f"Rata-rata karakter   : "
        f"{stats['average_characters']:,}"
    )

    print(
        f"Minimum karakter     : "
        f"{stats['minimum_characters']:,}"
    )

    print(
        f"Maximum karakter     : "
        f"{stats['maximum_characters']:,}"
    )

    print("=" * 60)


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
# PREVIEW
# ============================================================

def print_preview(
    chunks: list[dict],
    number: int = 3,
) -> None:

    print()
    print("=" * 60)
    print("PREVIEW CHUNK")
    print("=" * 60)

    for chunk in chunks[:number]:

        metadata = chunk["metadata"]

        print()
        print(
            f"Chunk ID       : "
            f"{chunk['chunk_id']}"
        )

        print(
            f"Halaman        : "
            f"{metadata['pdf_page_start']} - "
            f"{metadata['pdf_page_end']}"
        )

        print(
            f"Sequence       : "
            f"{metadata['sequence_start']} - "
            f"{metadata['sequence_end']}"
        )

        print(
            f"Jumlah karakter : "
            f"{metadata['character_count']}"
        )

        print("-" * 60)

        preview = chunk["text"]

        if len(preview) > 800:
            preview = preview[:800] + "..."

        print(preview)

    print()
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("CHUNKING DIH")
    print("=" * 60)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "File input tidak ditemukan:\n"
            f"{INPUT_PATH.resolve()}"
        )

    print(
        f"Input : "
        f"{INPUT_PATH.resolve()}"
    )

    print(
        f"Chunk size : "
        f"{CHUNK_SIZE} karakter"
    )

    print(
        f"Overlap    : "
        f"{CHUNK_OVERLAP} karakter"
    )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    print(
        f"Jumlah halaman input : "
        f"{len(data):,}"
    )

    # --------------------------------------------------------
    # COLLECT BLOCKS
    # --------------------------------------------------------

    blocks = collect_blocks(data)

    print(
        f"Total block           : "
        f"{len(blocks):,}"
    )

    # --------------------------------------------------------
    # CREATE CHUNKS
    # --------------------------------------------------------

    chunks = create_chunks(blocks)

    print(
        f"Total chunk           : "
        f"{len(chunks):,}"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_chunks(
        chunks=chunks,
        output_path=OUTPUT_PATH,
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    print_statistics(chunks)

    # --------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------

    print_preview(
        chunks,
        number=3,
    )

    print()
    print(
        "Output:"
    )
    print(
        OUTPUT_PATH.resolve()
    )


if __name__ == "__main__":
    main()
