"""Generación de un PDF básico sin dependencias externas.

Se construye directamente un documento PDF con las fuentes estándar
Helvetica/Helvetica-Bold y codificación WinAnsi, suficiente para escribir el
título y las dos tablas de la plantilla.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

from .excel import _equipo_rows, _liturgia_rows

PAGE_WIDTH = 595.28
PAGE_HEIGHT = 841.89
MARGIN = 36.0

CELL_PADDING = 3.0
LINE_HEIGHT = 12.0
FONT_SIZE = 9.0
HEADER_FONT_SIZE = 9.0
TITLE_FONT_SIZE = 16.0
SECTION_FONT_SIZE = 12.0


def _pdf_string(text: str) -> str:
    data = text.encode("cp1252", "replace")
    result = []
    for byte in data:
        if byte in (0x28, 0x29, 0x5C):
            result.append("\\" + chr(byte))
        elif 32 <= byte <= 126:
            result.append(chr(byte))
        else:
            result.append("\\%03o" % byte)
    return "".join(result)


def _text_width(text: str, size: float) -> float:
    return len(text) * size * 0.52


def _break_word(word: str, max_width: float, size: float) -> List[str]:
    chunks: List[str] = []
    current = ""
    for character in word:
        candidate = current + character
        if current and _text_width(candidate, size) > max_width:
            chunks.append(current)
            current = character
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [""]


def _wrap_text(text: str, max_width: float, size: float) -> List[str]:
    if not text:
        return [""]

    lines: List[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if _text_width(candidate, size) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
        chunks = _break_word(word, max_width, size)
        lines.extend(chunks[:-1])
        current = chunks[-1]

    if current or not lines:
        lines.append(current)
    return lines


class _PdfDocument:
    def __init__(self) -> None:
        self.pages: List[List[str]] = [["0.5 w"]]
        self.y = PAGE_HEIGHT - MARGIN

    def new_page(self) -> None:
        self.pages.append(["0.5 w"])
        self.y = PAGE_HEIGHT - MARGIN

    def ensure_space(self, height: float) -> bool:
        if self.y - height < MARGIN:
            self.new_page()
            return True
        return False

    def text(
        self,
        x: float,
        y: float,
        value: str,
        font: str = "F1",
        size: float = FONT_SIZE,
    ) -> None:
        if not value:
            return
        self.pages[-1].append(
            f"BT /{font} {size:g} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm "
            f"({_pdf_string(value)}) Tj ET"
        )

    def rect(self, x: float, top: float, width: float, height: float) -> None:
        bottom = top - height
        self.pages[-1].append(
            f"{x:.2f} {bottom:.2f} {width:.2f} {height:.2f} re S"
        )


def _row_layout(
    row_index: int,
    row: Sequence[Optional[str]],
    widths: Sequence[float],
    bold_rows: Set[int],
    merges: Dict[Tuple[int, int], int],
) -> Tuple[List[Tuple[int, float, float, List[str]]], float]:
    cells: List[Tuple[int, float, float, List[str]]] = []
    column = 0
    while column < len(widths):
        colspan = merges.get((row_index, column), 1)
        colspan = max(1, min(colspan, len(widths) - column))
        value = row[column] if column < len(row) and row[column] is not None else ""
        width = sum(widths[column : column + colspan])
        size = HEADER_FONT_SIZE if row_index in bold_rows else FONT_SIZE
        usable_width = max(width - 2 * CELL_PADDING, 1.0)
        lines = _wrap_text(value, usable_width, size)
        cells.append((colspan, width, size, lines))
        column += colspan

    height = (
        max((len(cell[3]) for cell in cells), default=1) * LINE_HEIGHT
        + 2 * CELL_PADDING
    )
    return cells, height


def _draw_row(
    document: _PdfDocument,
    cells: Sequence[Tuple[int, float, float, List[str]]],
    height: float,
    bold: bool,
) -> None:
    top = document.y
    x = MARGIN
    font = "F2" if bold else "F1"
    for _, width, size, lines in cells:
        document.rect(x, top, width, height)
        baseline = top - CELL_PADDING - size
        for line_index, line in enumerate(lines):
            document.text(
                x + CELL_PADDING,
                baseline - line_index * LINE_HEIGHT,
                line,
                font=font,
                size=size,
            )
        x += width
    document.y = top - height


def _draw_table(
    document: _PdfDocument,
    rows: Sequence[Sequence[Optional[str]]],
    widths: Sequence[float],
    bold_rows: Set[int],
    merges: Dict[Tuple[int, int], int],
) -> None:
    for row_index, row in enumerate(rows):
        cells, height = _row_layout(row_index, row, widths, bold_rows, merges)
        document.ensure_space(height)
        _draw_row(document, cells, height, row_index in bold_rows)


def _draw_title(document: _PdfDocument, title: str) -> None:
    available_width = PAGE_WIDTH - 2 * MARGIN
    for line in _wrap_text(title, available_width, TITLE_FONT_SIZE):
        document.ensure_space(TITLE_FONT_SIZE + 12)
        document.text(
            MARGIN,
            document.y - TITLE_FONT_SIZE,
            line,
            font="F2",
            size=TITLE_FONT_SIZE,
        )
        document.y -= TITLE_FONT_SIZE + 12


def _draw_section(document: _PdfDocument, title: str) -> None:
    document.y -= 14
    document.ensure_space(SECTION_FONT_SIZE + 8)
    document.text(
        MARGIN,
        document.y - SECTION_FONT_SIZE,
        title,
        font="F2",
        size=SECTION_FONT_SIZE,
    )
    document.y -= SECTION_FONT_SIZE + 8


def _liturgia_widths() -> List[float]:
    available_width = PAGE_WIDTH - 2 * MARGIN
    narrow = 18.0
    wide = (available_width - 8 * narrow) / 4
    return [
        wide,
        narrow,
        narrow,
        wide,
        narrow,
        narrow,
        wide,
        narrow,
        narrow,
        wide,
        narrow,
        narrow,
    ]


def _equipo_widths() -> List[float]:
    available_width = PAGE_WIDTH - 2 * MARGIN
    return [available_width / 4] * 4


def _stream(content: str) -> bytes:
    data = content.encode("ascii")
    return b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream"


def _write_pdf(
    path: Union[str, Path], pages: Sequence[Sequence[str]], title: str
) -> None:
    page_count = len(pages)
    first_page_id = 5
    page_ids = [first_page_id + index for index in range(page_count)]
    first_content_id = first_page_id + page_count
    content_ids = [first_content_id + index for index in range(page_count)]
    info_id = first_content_id + page_count

    objects: Dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (
            f"<< /Type /Pages /Kids ["
            + " ".join(f"{page_id} 0 R" for page_id in page_ids)
            + f"] /Count {page_count} >>"
        ).encode("ascii"),
        3: (
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            b"/Encoding /WinAnsiEncoding >>"
        ),
        4: (
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
            b"/Encoding /WinAnsiEncoding >>"
        ),
    }

    for page_id, content_id, page_lines in zip(page_ids, content_ids, pages):
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH:.2f} {PAGE_HEIGHT:.2f}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects[content_id] = _stream("\n".join(page_lines))

    objects[info_id] = (
        f"<< /Title ({_pdf_string(title)}) /Producer (liturgia-palabra) >>"
    ).encode("ascii")

    max_id = info_id
    body = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: Dict[int, int] = {}
    for object_id in range(1, max_id + 1):
        offsets[object_id] = len(body)
        body += f"{object_id} 0 obj\n".encode("ascii")
        body += objects[object_id]
        body += b"\nendobj\n"

    xref_offset = len(body)
    body += f"xref\n0 {max_id + 1}\n".encode("ascii")
    body += b"0000000000 65535 f \n"
    for object_id in range(1, max_id + 1):
        body += f"{offsets[object_id]:010d} 00000 n \n".encode("ascii")

    body += (
        f"trailer\n<< /Size {max_id + 1} /Root 1 0 R /Info {info_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    Path(path).write_bytes(bytes(body))


def build_pdf(
    categories: Dict[str, List[str]],
    path: Union[str, Path],
    word: str,
    sort_alphabetically: bool = False,
) -> None:
    document = _PdfDocument()
    title = f"PALABRA: {word}"
    _draw_title(document, title)
    _draw_table(
        document,
        _liturgia_rows(categories, sort_alphabetically),
        _liturgia_widths(),
        bold_rows={0},
        merges={},
    )
    _draw_section(document, "Equipo")
    _draw_table(
        document,
        _equipo_rows(),
        _equipo_widths(),
        bold_rows={0, 2},
        merges={(0, 1): 3},
    )
    _write_pdf(path, document.pages, title)
