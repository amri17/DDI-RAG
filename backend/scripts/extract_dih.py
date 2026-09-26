from pathlib import Path
import json
import pymupdf


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = Path("data/raw/dih/DIH.pdf")
OUTPUT_PATH = Path("data/processed/dih_extracted.json")


# ============================================================
# EXTRACT TEXT BLOCKS
# ============================================================

def extract_text_blocks(
    page,
    page_number: int,
) -> list[dict]:
    """
    Extract semua text block dari satu halaman PDF.

    Setiap block menyimpan:
    - pdf_page : nomor halaman PDF
    - block_id : ID block
    - bbox     : posisi block [x0, y0, x1, y1]
    - text     : isi teks block
    """

    raw_blocks = page.get_text("blocks")

    blocks = []

    for block_number, block in enumerate(
        raw_blocks,
        start=1,
    ):

        # Struktur block PyMuPDF:
        #
        # x0, y0, x1, y1, text,
        # block_no, block_type

        x0, y0, x1, y1, text, block_no, block_type = block[:7]

        # Hanya ambil text block.
        # block_type == 0 berarti text.
        if block_type != 0:
            continue

        text = text.strip()

        # Abaikan block kosong
        if not text:
            continue

        blocks.append(
            {
                "pdf_page": page_number,

                "block_id": block_number,

                "bbox": [
                    round(x0, 2),
                    round(y0, 2),
                    round(x1, 2),
                    round(y1, 2),
                ],

                "text": text,
            }
        )

    return blocks


# ============================================================
# SPLIT INTO TWO COLUMNS
# ============================================================

def split_into_columns(
    blocks: list[dict],
    page_width: float,
) -> tuple[list[dict], list[dict]]:
    """
    Membagi block menjadi dua kolom:

        left_column
        right_column

    Pembagian berdasarkan titik tengah halaman.
    """

    middle_x = page_width / 2

    left_column = []
    right_column = []

    for block in blocks:

        x0, y0, x1, y1 = block["bbox"]

        # Titik tengah horizontal block
        center_x = (x0 + x1) / 2

        if center_x < middle_x:
            left_column.append(block)
        else:
            right_column.append(block)

    # --------------------------------------------------------
    # Urutkan setiap kolom dari atas ke bawah
    # --------------------------------------------------------

    left_column.sort(
        key=lambda block: (
            block["bbox"][1],
            block["bbox"][0],
        )
    )

    right_column.sort(
        key=lambda block: (
            block["bbox"][1],
            block["bbox"][0],
        )
    )

    return left_column, right_column


# ============================================================
# EXTRACT ONE PAGE
# ============================================================

def extract_page(
    page,
    page_number: int,
) -> dict:
    """
    Extract satu halaman PDF.

    Struktur hasil:

    {
        "pdf_page": ...,
        "page_size": ...,
        "left_column": [...],
        "right_column": [...]
    }
    """

    page_width = round(
        page.rect.width,
        2,
    )

    page_height = round(
        page.rect.height,
        2,
    )

    # Extract semua block
    blocks = extract_text_blocks(
        page=page,
        page_number=page_number,
    )

    # Pisahkan menjadi dua kolom
    left_column, right_column = split_into_columns(
        blocks=blocks,
        page_width=page_width,
    )

    return {
        "pdf_page": page_number,

        "page_size": {
            "width": page_width,
            "height": page_height,
        },

        "left_column": left_column,

        "right_column": right_column,

        "left_block_count": len(
            left_column
        ),

        "right_block_count": len(
            right_column
        ),
    }


# ============================================================
# EXTRACT ENTIRE PDF
# ============================================================

def extract_pdf(
    pdf_path: Path,
) -> list[dict]:
    """
    Extract seluruh halaman PDF.
    """

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF tidak ditemukan: "
            f"{pdf_path.resolve()}"
        )

    document = pymupdf.open(
        pdf_path
    )

    pages = []

    print(
        f"PDF           : "
        f"{pdf_path.resolve()}"
    )

    print(
        f"Jumlah halaman : "
        f"{len(document)}"
    )

    print()

    for page_number, page in enumerate(
        document,
        start=1,
    ):

        page_data = extract_page(
            page=page,
            page_number=page_number,
        )

        pages.append(
            page_data
        )

        if page_number % 100 == 0:
            print(
                f"Memproses halaman "
                f"{page_number}/"
                f"{len(document)}"
            )

    document.close()

    return pages


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    data: list[dict],
    output_path: Path,
) -> None:
    """
    Simpan hasil extraction ke JSON.
    """

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
# STATISTICS
# ============================================================

def print_statistics(
    pages: list[dict],
) -> None:
    """
    Tampilkan statistik extraction.
    """

    total_pages = len(pages)

    empty_pages = sum(
        1
        for page in pages
        if (
            page["left_block_count"] == 0
            and page["right_block_count"] == 0
        )
    )

    total_left_blocks = sum(
        page["left_block_count"]
        for page in pages
    )

    total_right_blocks = sum(
        page["right_block_count"]
        for page in pages
    )

    total_blocks = (
        total_left_blocks
        + total_right_blocks
    )

    total_characters = 0

    for page in pages:

        for block in page["left_column"]:
            total_characters += len(
                block["text"]
            )

        for block in page["right_column"]:
            total_characters += len(
                block["text"]
            )

    print()
    print("=" * 60)
    print("HASIL EKSTRAKSI DIH")
    print("=" * 60)

    print(
        f"Total halaman       : "
        f"{total_pages:,}"
    )

    print(
        f"Halaman kosong      : "
        f"{empty_pages:,}"
    )

    print(
        f"Block kolom kiri    : "
        f"{total_left_blocks:,}"
    )

    print(
        f"Block kolom kanan   : "
        f"{total_right_blocks:,}"
    )

    print(
        f"Total block         : "
        f"{total_blocks:,}"
    )

    print(
        f"Total karakter      : "
        f"{total_characters:,}"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    # 1. Extract PDF
    pages = extract_pdf(
        PDF_PATH
    )

    # 2. Save JSON
    save_json(
        data=pages,
        output_path=OUTPUT_PATH,
    )

    # 3. Print statistics
    print_statistics(
        pages
    )

    print()

    print(
        "Output:"
    )

    print(
        OUTPUT_PATH.resolve()
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

