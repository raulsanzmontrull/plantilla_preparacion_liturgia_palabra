"""Generación de un libro .xlsx sin dependencias externas.

El formato Office Open XML es un ZIP con varios documentos XML. Se escriben
directamente las partes mínimas necesarias y se usan cadenas en línea
(``inlineStr``) para no necesitar una tabla de cadenas compartidas.
"""

from __future__ import annotations

import unicodedata
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Union
from xml.sax.saxutils import escape

from . import books

CATEGORY_COLUMNS = {
    books.HISTORICOS: 1,
    books.PROFETAS: 4,
    books.CARTAS: 7,
    books.EVANGELIOS: 10,
}

COLUMN_HEADERS = {
    1: books.HISTORICOS,
    2: "P",
    3: "T",
    4: books.PROFETAS,
    5: "P",
    6: "T",
    7: books.CARTAS,
    8: "P",
    9: "T",
    10: books.EVANGELIOS,
    11: "P",
    12: "T",
}

MIN_COLUMN_WIDTH = 4.0
MAX_COLUMN_WIDTH = 100.0
COLUMN_PADDING = 2

WORKSHEET_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
)
WORKSHEET_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
)

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""


def _content_types_xml(has_text: bool) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '  <Default Extension="xml" ContentType="application/xml"/>',
        '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        f'  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="{WORKSHEET_CONTENT_TYPE}"/>',
        f'  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="{WORKSHEET_CONTENT_TYPE}"/>',
    ]
    if has_text:
        parts.append(
            f'  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="{WORKSHEET_CONTENT_TYPE}"/>'
        )
    parts.extend(
        [
            '  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
            "</Types>",
        ]
    )
    return "\n".join(parts) + "\n"


def _workbook_xml(has_text: bool) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        "  <sheets>",
        '    <sheet name="Liturgia" sheetId="1" r:id="rId1"/>',
        '    <sheet name="Equipo" sheetId="2" r:id="rId2"/>',
    ]
    if has_text:
        parts.append('    <sheet name="Texto" sheetId="3" r:id="rId4"/>')
    parts.extend(["  </sheets>", "</workbook>"])
    return "\n".join(parts) + "\n"


def _workbook_rels_xml(has_text: bool) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        f'  <Relationship Id="rId1" Type="{WORKSHEET_RELATIONSHIP}" Target="worksheets/sheet1.xml"/>',
        f'  <Relationship Id="rId2" Type="{WORKSHEET_RELATIONSHIP}" Target="worksheets/sheet2.xml"/>',
        '  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
    ]
    if has_text:
        parts.append(
            f'  <Relationship Id="rId4" Type="{WORKSHEET_RELATIONSHIP}" Target="worksheets/sheet3.xml"/>'
        )
    parts.append("</Relationships>")
    return "\n".join(parts) + "\n"


STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"/>
      <right style="thin"/>
      <top style="thin"/>
      <bottom style="thin"/>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="4">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>
"""


def column_letter(number: int) -> str:
    letters = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _text(value: str) -> str:
    return escape(value)


def _cell(reference: str, value: str, style: Optional[int] = None) -> str:
    style_attribute = f' s="{style}"' if style is not None else ""
    return (
        f'<c r="{reference}"{style_attribute} t="inlineStr">'
        f"<is><t>{_text(value)}</t></is></c>"
    )


def _auto_width(values: Sequence[Optional[str]]) -> float:
    longest = max(
        (len(value) for value in values if value is not None),
        default=0,
    )
    return min(
        MAX_COLUMN_WIDTH,
        max(MIN_COLUMN_WIDTH, float(longest + COLUMN_PADDING)),
    )


def _cols_xml(widths: Sequence[float]) -> str:
    columns = []
    for index, width in enumerate(widths, start=1):
        columns.append(
            f'<col min="{index}" max="{index}" width="{width:g}" customWidth="1"/>'
        )
    return "<cols>" + "".join(columns) + "</cols>"


def _row_xml(
    row_number: int,
    values: Sequence[Optional[str]],
    header: bool,
    body_style: int = 2,
) -> str:
    cells = []
    style = 1 if header else body_style
    for index, value in enumerate(values, start=1):
        reference = f"{column_letter(index)}{row_number}"
        cells.append(_cell(reference, value or "", style=style))
    return f'<row r="{row_number}">' + "".join(cells) + "</row>"


def _worksheet_xml(
    rows: Sequence[Sequence[Optional[str]]],
    header_rows: Set[int],
    freeze_rows: int = 0,
    merges: Sequence[str] = (),
    body_style: int = 2,
) -> str:
    column_count = max((len(row) for row in rows), default=1)
    padded_rows = [
        list(row) + [None] * (column_count - len(row)) for row in rows
    ]
    widths = [
        _auto_width([row[index] for row in padded_rows])
        for index in range(column_count)
    ]
    last_row = max(len(padded_rows), 1)
    last_column = column_letter(column_count)

    sheet_views = ""
    if freeze_rows > 0:
        sheet_views = (
            "<sheetViews><sheetView workbookViewId=\"0\">"
            f'<pane ySplit="{freeze_rows}" topLeftCell="A{freeze_rows + 1}" '
            'activePane="bottomLeft" state="frozen"/>'
            "</sheetView></sheetViews>"
        )

    rows_xml = "".join(
        _row_xml(row_number, row, row_number in header_rows, body_style)
        for row_number, row in enumerate(padded_rows, start=1)
    )

    merges_xml = ""
    if merges:
        merge_cells = "".join(
            f'<mergeCell ref="{reference}"/>' for reference in merges
        )
        merges_xml = f'<mergeCells count="{len(merges)}">{merge_cells}</mergeCells>'

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{last_column}{last_row}"/>'
        + sheet_views
        + _cols_xml(widths)
        + "<sheetData>"
        + rows_xml
        + "</sheetData>"
        + merges_xml
        + "</worksheet>"
    )


def _sort_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _liturgia_rows(
    categories: Dict[str, List[str]], sort_alphabetically: bool = False
) -> List[List[Optional[str]]]:
    if sort_alphabetically:
        categories = {
            category: sorted(values, key=_sort_key)
            for category, values in categories.items()
        }
    longest = max((len(values) for values in categories.values()), default=0)
    rows: List[List[Optional[str]]] = [
        [COLUMN_HEADERS[column] for column in range(1, 13)]
    ]
    for index in range(longest):
        row: List[Optional[str]] = [None] * 12
        for category, column in CATEGORY_COLUMNS.items():
            values = categories.get(category, [])
            if index < len(values):
                row[column - 1] = values[index]
        rows.append(row)
    return rows


def _equipo_rows() -> List[List[Optional[str]]]:
    rows: List[List[Optional[str]]] = [
        ["Monición ambiental", None, None, None],
        [None, None, None, None],
        ["Lectura", "Cita bíblica más votada", "Monición", "Proclamación"],
    ]
    for category in books.CATEGORIES:
        rows.append([category, None, None, None])
    return rows


def _sheet_xml(
    categories: Dict[str, List[str]], sort_alphabetically: bool = False
) -> str:
    return _worksheet_xml(
        _liturgia_rows(categories, sort_alphabetically),
        header_rows={1},
        freeze_rows=1,
    )


def _equipo_sheet_xml() -> str:
    return _worksheet_xml(
        _equipo_rows(),
        header_rows={1, 3},
        freeze_rows=3,
        merges=("B1:D1",),
    )


def _text_sheet_xml(text: Sequence[str]) -> str:
    rows: List[List[Optional[str]]] = [[paragraph] for paragraph in text if paragraph]
    return _worksheet_xml(
        rows,
        header_rows=set(),
        body_style=3,
    )


def write_xlsx(
    categories: Dict[str, List[str]],
    target: Union[str, Path, "zipfile.ZipFile"],
    sort_alphabetically: bool = False,
    text: Optional[Sequence[str]] = None,
) -> None:
    has_text = bool(text)
    parts = {
        "[Content_Types].xml": _content_types_xml(has_text),
        "_rels/.rels": ROOT_RELS,
        "xl/workbook.xml": _workbook_xml(has_text),
        "xl/_rels/workbook.xml.rels": _workbook_rels_xml(has_text),
        "xl/styles.xml": STYLES,
        "xl/worksheets/sheet1.xml": _sheet_xml(categories, sort_alphabetically),
        "xl/worksheets/sheet2.xml": _equipo_sheet_xml(),
    }
    if has_text:
        parts["xl/worksheets/sheet3.xml"] = _text_sheet_xml(text or [])

    if hasattr(target, "writestr"):
        for name, content in parts.items():
            target.writestr(name, content)
        return

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)


def build_workbook(
    categories: Dict[str, List[str]],
    path: Union[str, Path],
    sort_alphabetically: bool = False,
    text: Optional[Sequence[str]] = None,
) -> None:
    write_xlsx(categories, path, sort_alphabetically, text)
