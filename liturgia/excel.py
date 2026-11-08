"""Generación de un libro .xlsx sin dependencias externas.

El formato Office Open XML es un ZIP con varios documentos XML. Se escriben
directamente las partes mínimas necesarias y se usan cadenas en línea
(``inlineStr``) para no necesitar una tabla de cadenas compartidas.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union
from xml.sax.saxutils import escape

from . import books

CATEGORY_COLUMNS = {
    books.HISTORICOS: 1,
    books.PROFETAS: 4,
    books.CARTAS: 7,
    books.EVANGELIOS: 10,
}

COLUMN_WIDTHS = [28, 12, 12, 28, 12, 12, 28, 12, 12, 28, 12, 12]

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""

WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Liturgia" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

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
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
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


def _cols_xml() -> str:
    columns = []
    for index, width in enumerate(COLUMN_WIDTHS, start=1):
        columns.append(
            f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        )
    return "<cols>" + "".join(columns) + "</cols>"


def _sheet_xml(categories: Dict[str, List[str]]) -> str:
    longest = max((len(values) for values in categories.values()), default=0)
    last_row = max(longest + 1, 1)

    header_cells = []
    for category, column in CATEGORY_COLUMNS.items():
        reference = f"{column_letter(column)}1"
        header_cells.append(_cell(reference, category, style=1))
    rows = ['<row r="1">' + "".join(header_cells) + "</row>"]

    for index in range(longest):
        row_number = index + 2
        cells = []
        for category, column in CATEGORY_COLUMNS.items():
            values = categories.get(category, [])
            if index < len(values):
                reference = f"{column_letter(column)}{row_number}"
                cells.append(_cell(reference, values[index]))
        rows.append(f'<row r="{row_number}">' + "".join(cells) + "</row>")

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetViews><sheetView workbookViewId=\"0\">"
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f'<dimension ref="A1:L{last_row}"/>'
        + _cols_xml()
        + "<sheetData>"
        + "".join(rows)
        + "</sheetData></worksheet>"
    )


def write_xlsx(
    categories: Dict[str, List[str]],
    target: Union[str, Path, "zipfile.ZipFile"],
) -> None:
    parts = {
        "[Content_Types].xml": CONTENT_TYPES,
        "_rels/.rels": ROOT_RELS,
        "xl/workbook.xml": WORKBOOK,
        "xl/_rels/workbook.xml.rels": WORKBOOK_RELS,
        "xl/styles.xml": STYLES,
        "xl/worksheets/sheet1.xml": _sheet_xml(categories),
    }

    if hasattr(target, "writestr"):
        for name, content in parts.items():
            target.writestr(name, content)
        return

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)


def build_workbook(categories: Dict[str, List[str]], path: Union[str, Path]) -> None:
    write_xlsx(categories, path)
