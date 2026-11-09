import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from liturgia.excel import build_workbook

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheet(path):
    with zipfile.ZipFile(path) as archive:
        return archive.read("xl/worksheets/sheet1.xml").decode("utf-8")


def cells_by_reference(sheet_xml):
    root = ET.fromstring(sheet_xml)
    cells = {}
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib["r"]
        text = cell.findtext(".//m:t", default="", namespaces=NS)
        cells[ref] = text
    return cells


class BuildWorkbookTests(unittest.TestCase):
    def test_creates_valid_xlsx_package(self):
        categories = {
            "Históricos": ["Gen 1,11s"],
            "Profetas": ["Is 41,19"],
            "Cartas": ["1Pe 2,24"],
            "Evangelios": ["Mt 24,32"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                self.assertIn("[Content_Types].xml", names)
                self.assertIn("_rels/.rels", names)
                self.assertIn("xl/workbook.xml", names)
                self.assertIn("xl/worksheets/sheet1.xml", names)
                for name in names:
                    if name.endswith(".xml") or name.endswith(".rels"):
                        ET.fromstring(archive.read(name))

    def test_writes_headers_and_citations_in_expected_columns(self):
        categories = {
            "Históricos": ["Gen 1,11s", "Gen 3,22ss"],
            "Profetas": ["Is 41,19"],
            "Cartas": ["1Pe 2,24"],
            "Evangelios": ["Mt 24,30-35", "Mt 24,36"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            cells = cells_by_reference(read_sheet(path))

        self.assertEqual(cells["A1"], "Históricos")
        self.assertEqual(cells["D1"], "Profetas")
        self.assertEqual(cells["G1"], "Cartas")
        self.assertEqual(cells["J1"], "Evangelios")

        self.assertEqual(cells["A2"], "Gen 1,11s")
        self.assertEqual(cells["A3"], "Gen 3,22ss")
        self.assertEqual(cells["D2"], "Is 41,19")
        self.assertEqual(cells["G2"], "1Pe 2,24")
        self.assertEqual(cells["J2"], "Mt 24,30-35")
        self.assertEqual(cells["J3"], "Mt 24,36")

    def test_personal_and_total_columns_have_headers(self):
        categories = {
            "Históricos": ["Gen 1,11s"],
            "Profetas": [],
            "Cartas": [],
            "Evangelios": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            cells = cells_by_reference(read_sheet(path))

        for column in ["B", "E", "H", "K"]:
            self.assertEqual(cells[f"{column}1"], "P")
        for column in ["C", "F", "I", "L"]:
            self.assertEqual(cells[f"{column}1"], "T")

    def test_column_widths_are_compact(self):
        categories = {
            "Históricos": ["Gen 1,11s"],
            "Profetas": [],
            "Cartas": [],
            "Evangelios": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            root = ET.fromstring(read_sheet(path))

        widths = {
            int(column.attrib["min"]): float(column.attrib["width"])
            for column in root.findall(".//m:col", NS)
        }
        for column in [1, 4, 7, 10]:
            self.assertEqual(widths[column], 24)
        for column in [2, 3, 5, 6, 8, 9, 11, 12]:
            self.assertEqual(widths[column], 6)

    def test_escapes_xml_special_characters(self):
        categories = {
            "Históricos": ["Gen 1,1 <&>"],
            "Profetas": [],
            "Cartas": [],
            "Evangelios": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            cells = cells_by_reference(read_sheet(path))

        self.assertEqual(cells["A2"], "Gen 1,1 <&>")


if __name__ == "__main__":
    unittest.main()
