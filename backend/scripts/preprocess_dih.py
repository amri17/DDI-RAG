from pathlib import Path

import json

import re


# ============================================================
# PATH
# ============================================================
INPUT_PATH = Path("data/processed/dih_extracted.json")

OUTPUT_PATH = Path("data/processed/dih_preprocessed.json")


# ============================================================
# TEXT CLEANING
# ============================================================
def normalize_unicode(text: str) -> str:
    """
    Menormalisasi beberapa karakter Unicode yang umum muncul
    pada hasil ekstraksi PDF.
    """
    replacements = {
        "\u00a0": " ",   # non-breaking space
        "\u2010": "-",   # hyphen
        "\u2011": "-",   # non-breaking hyphen
        "\u2012": "-",   # figure dash
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2212": "-",   # minus sign
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def normalize_hyphenation(text: str) -> str:
    """
    Menggabungkan kata yang terpotong karena pergantian baris.

    Contoh:
        interac-
        tions

    menjadi:
        interactions

    Hanya hyphen yang berada di antara karakter kata dan
    terputus oleh newline yang digabungkan.
    """
    return re.sub(
        r"(\w)-\s*\n\s*(\w)",
        r"\1\2",
        text,
    )


def normalize_line_breaks(text: str) -> str:
    """
    Menormalisasi line break tanpa menghilangkan struktur
    paragraf secara agresif.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Hilangkan spasi/tab di akhir baris
    lines = [
        line.rstrip()
        for line in text.split("\n")
    ]

    text = "\n".join(lines)

    return text


def remove_pdf_noise(text: str) -> str:
    """
    Menghilangkan noise header/footer tertentu dari PDF DIH.

    Hanya menghapus teks yang secara eksplisit diketahui
    sebagai elemen website/header/footer PDF, bukan angka
    atau istilah medis.
    """
    noise_patterns = [
        r"(?im)^\s*Kaduse\.com\s*$",
        r"(?im)^\s*www\.Kaduse\.com\s*$",
        r"(?im)^\s*www\.kaduse\.com\s*$",
    ]

    for pattern in noise_patterns:
        text = re.sub(
            pattern,
            "",
            text,
        )

    return text


def normalize_numeric_spacing(text: str) -> str:
    """
    Memperbaiki spasi yang jelas merupakan artefak ekstraksi
    di dalam angka.

    Contoh:
        1 6.2  -> 16.2
        0 . 0 1 94 -> 0.0194

    Tidak mencoba menggabungkan sembarang kata.
    """

    # Angka yang terpisah oleh spasi.
    # Contoh: 1 6 -> 16
    text = re.sub(
        r"(?<=\d)\s+(?=\d)",
        "",
        text,
    )

    # Spasi di sekitar decimal point.
    # Contoh: 0 . 0194 -> 0.0194
    text = re.sub(
        r"(?<=\d)\s+\.\s*(?=\d)",
        ".",
        text,
    )

    # Kasus: angka + spasi + decimal point
    # setelah digit sebelumnya sudah dinormalisasi.
    text = re.sub(
        r"(\d)\s+\.\s*(\d)",
        r"\1.\2",
        text,
    )

    return text


def normalize_common_units(text: str) -> str:
    """
    Menggabungkan satuan yang sangat umum dan aman
    untuk dinormalisasi.

    Contoh:
        5 m g  -> 5 mg
        10 m L -> 10 mL
        2 m L  -> 2 mL

    Hanya pola satuan yang eksplisit yang diperbaiki.
    """
    unit_patterns = {
        r"\bm\s+g\b": "mg",
        r"\bm\s+L\b": "mL",
        r"\bmcg\b": "mcg",
        r"\bμg\b": "mcg",
        r"\bµg\b": "mcg",
        r"\bg\b": "g",
        r"\bkg\b": "kg",
        r"\bmg/mL\b": "mg/mL",
    }

    for pattern, replacement in unit_patterns.items():
        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    return text


def normalize_slashes(text: str) -> str:
    """
    Membersihkan spasi yang tidak diperlukan di sekitar slash.

    Contoh:
        mg / mL -> mg/mL
    """
    text = re.sub(
        r"\s*/\s*",
        "/",
        text,
    )

    return text


def normalize_parentheses(text: str) -> str:
    """
    Membersihkan spasi yang tidak diperlukan di dalam tanda
    kurung.

    Contoh:
        ( 120 mL ) -> (120 mL)
    """
    text = re.sub(
        r"\(\s+",
        "(",
        text,
    )

    text = re.sub(
        r"\s+\)",
        ")",
        text,
    )

    return text


def normalize_spaces(text: str) -> str:
    """
    Membersihkan spasi berulang tetapi tetap mempertahankan
    line break/paragraf.
    """

    # Spasi atau tab berulang
    text = re.sub(
        r"[ \t]{2,}",
        " ",
        text,
    )

    # Spasi di awal baris
    text = re.sub(
        r"\n[ \t]+",
        "\n",
        text,
    )

    # Spasi sebelum newline
    text = re.sub(
        r"[ \t]+\n",
        "\n",
        text,
    )

    # Lebih dari dua newline menjadi dua
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def clean_text(text: str) -> str:
    """
    Pipeline cleaning utama.

    Cleaning dilakukan secara konservatif agar tidak merusak
    istilah medis.
    """
    if not text:
        return ""

    # 1. Unicode
    text = normalize_unicode(text)

    # 2. Hyphenation akibat pergantian baris
    text = normalize_hyphenation(text)

    # 3. Line break
    text = normalize_line_breaks(text)

    # 4. PDF noise
    text = remove_pdf_noise(text)

    # 5. Angka
    text = normalize_numeric_spacing(text)

    # 6. Satuan
    text = normalize_common_units(text)

    # 7. Slash
    text = normalize_slashes(text)

    # 8. Parentheses
    text = normalize_parentheses(text)

    # 9. Whitespace
    text = normalize_spaces(text)

    return text


# ============================================================
# BLOCK PROCESSING
# ============================================================
def clean_block(block: dict) -> dict | None:
    """
    Membersihkan satu block hasil extraction.
    Informasi posisi dan identitas block tetap dipertahankan.
    """
    original_text = block.get("text", "")

    cleaned_text = clean_text(
        original_text
    )

    if not cleaned_text:
        return None

    return {
        "block_id": block.get("block_id"),
        "bbox": block.get("bbox"),
        "text": cleaned_text,
    }


def process_column(
    blocks: list[dict],
    column_name: str,
    sequence_start: int,
) -> tuple[list[dict], int]:
    """
    Membersihkan block dalam satu kolom.
    Urutan block TIDAK diubah.
    """
    processed_blocks = []

    sequence = sequence_start

    for block in blocks:
        cleaned = clean_block(block)

        if cleaned is None:
            continue

        cleaned["sequence"] = sequence
        cleaned["column"] = column_name

        processed_blocks.append(
            cleaned
        )

        sequence += 1

    return processed_blocks, sequence


# ============================================================
# PAGE PROCESSING
# ============================================================
def process_page(
    page: dict,
    sequence_start: int,
) -> tuple[dict, int]:
    """
    Memproses satu halaman.

    Urutan:
        1. halaman
        2. kolom kiri dari atas ke bawah
        3. kolom kanan dari atas ke bawah

    Struktur kiri dan kanan tetap disimpan.
    """
    pdf_page = page["pdf_page"]

    left_column = page.get(
        "left_column",
        [],
    )

    right_column = page.get(
        "right_column",
        [],
    )

    # --------------------------------------------------------
    # LEFT COLUMN
    # --------------------------------------------------------
    processed_left, sequence = process_column(
        blocks=left_column,
        column_name="left",
        sequence_start=sequence_start,
    )

    # --------------------------------------------------------
    # RIGHT COLUMN
    # --------------------------------------------------------
    processed_right, sequence = process_column(
        blocks=right_column,
        column_name="right",
        sequence_start=sequence,
    )

    # --------------------------------------------------------
    # ORDERED BLOCKS
    # --------------------------------------------------------
    ordered_blocks = (
        processed_left
        + processed_right
    )

    # --------------------------------------------------------
    # PAGE TEXT
    # --------------------------------------------------------
    page_text_parts = [
        block["text"]
        for block in ordered_blocks
    ]

    page_text = "\n\n".join(
        page_text_parts
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------
    result = {
        "pdf_page": pdf_page,
        "page_size": page.get(
            "page_size"
        ),
        "block_count": len(
            ordered_blocks
        ),

        # Struktur kolom asli
        "left_column": processed_left,
        "right_column": processed_right,

        # Urutan seluruh block
        "ordered_blocks": ordered_blocks,

        # Teks gabungan halaman
        "text": page_text,
    }

    return result, sequence


# ============================================================
# DOCUMENT PROCESSING
# ============================================================
def preprocess_document(
    data: list[dict],
) -> list[dict]:
    """
    Memproses seluruh dokumen DIH.
    Nomor halaman dipertahankan.
    Urutan block dipertahankan.
    """
    processed_pages = []

    sequence = 1
    total_pages = len(data)

    for page in data:
        processed_page, sequence = process_page(
            page=page,
            sequence_start=sequence,
        )

        processed_pages.append(
            processed_page
        )

        if (
            processed_page["pdf_page"] % 100 == 0
            or processed_page["pdf_page"] == total_pages
        ):
            print(
                f"Memproses halaman "
                f"{processed_page['pdf_page']}/"
                f"{total_pages}"
            )

    return processed_pages


# ============================================================
# STATISTICS
# ============================================================
def calculate_statistics(
    data: list[dict],
) -> dict:
    """
    Menghitung statistik hasil preprocessing.
    """
    total_pages = len(data)

    total_blocks = 0
    total_characters = 0
    left_blocks = 0
    right_blocks = 0

    for page in data:
        total_blocks += page[
            "block_count"
        ]

        total_characters += len(
            page["text"]
        )

        left_blocks += len(
            page["left_column"]
        )

        right_blocks += len(
            page["right_column"]
        )

    return {
        "total_pages": total_pages,
        "total_blocks": total_blocks,
        "left_blocks": left_blocks,
        "right_blocks": right_blocks,
        "total_characters": total_characters,
    }


def print_statistics(
    data: list[dict],
) -> None:
    stats = calculate_statistics(
        data
    )

    print()

    print("=" * 60)
    print("HASIL PREPROCESSING DIH")
    print("=" * 60)

    print(
        f"Total halaman       : "
        f"{stats['total_pages']:,}"
    )

    print(
        f"Total block         : "
        f"{stats['total_blocks']:,}"
    )

    print(
        f"Block kolom kiri    : "
        f"{stats['left_blocks']:,}"
    )

    print(
        f"Block kolom kanan   : "
        f"{stats['right_blocks']:,}"
    )

    print(
        f"Total karakter      : "
        f"{stats['total_characters']:,}"
    )

    print("=" * 60)


# ============================================================
# SAVE JSON
# ============================================================
def save_json(
    data: list[dict],
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
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# MAIN
# ============================================================
def main():

    # --------------------------------------------------------
    # CHECK INPUT
    # --------------------------------------------------------
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "File input tidak ditemukan:\n"
            f"{INPUT_PATH.resolve()}"
        )

    print("=" * 60)
    print("PREPROCESSING DIH")
    print("=" * 60)

    print(
        f"Input : "
        f"{INPUT_PATH.resolve()}"
    )

    # --------------------------------------------------------
    # LOAD EXTRACTION
    # --------------------------------------------------------
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        extracted_data = json.load(
            file
        )

    print(
        f"Jumlah halaman input: "
        f"{len(extracted_data):,}"
    )

    # --------------------------------------------------------
    # PREPROCESS
    # --------------------------------------------------------
    preprocessed_data = (
        preprocess_document(
            extracted_data
        )
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------
    save_json(
        data=preprocessed_data,
        output_path=OUTPUT_PATH,
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------
    print_statistics(
        preprocessed_data
    )

    print()

    print(
        f"Output: "
        f"{OUTPUT_PATH.resolve()}"
    )


if __name__ == "__main__":
    main()

