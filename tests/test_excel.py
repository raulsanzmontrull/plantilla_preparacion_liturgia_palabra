import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from liturgia.excel import build_workbook

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheet(path, name="xl/worksheets/sheet1.xml"):
    with zipfile.ZipFile(path) as archive:
        return archive.read(name).decode("utf-8")


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
                self.assertIn("xl/worksheets/sheet2.xml", names)
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

    def test_column_widths_fit_longest_content(self):
        longest = "1 Tesalonicenses 4,13-18"
        categories = {
            "Históricos": [longest],
            "Profetas": ["Is 1,1"],
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
        self.assertEqual(widths[1], len(longest) + 2)
        self.assertEqual(widths[4], len("Profetas") + 2)
        self.assertEqual(widths[7], len("Cartas") + 2)
        self.assertEqual(widths[10], len("Evangelios") + 2)

    def test_column_widths_include_header_when_it_is_longest(self):
        categories = {
            "Históricos": ["Gen 1,1"],
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
        self.assertEqual(widths[1], len("Históricos") + 2)

    def test_personal_and_total_columns_are_narrow(self):
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
        for column in [2, 3, 5, 6, 8, 9, 11, 12]:
            self.assertEqual(widths[column], 4)

    def test_equipo_sheet_contains_assignment_table(self):
        categories = {
            "Históricos": [],
            "Profetas": [],
            "Cartas": [],
            "Evangelios": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            sheet = read_sheet(path, "xl/worksheets/sheet2.xml")
            cells = cells_by_reference(sheet)

        self.assertEqual(cells["A1"], "Monición ambiental")
        self.assertEqual(cells["A3"], "Lectura")
        self.assertEqual(cells["B3"], "Cita bíblica más votada")
        self.assertEqual(cells["C3"], "Monición")
        self.assertEqual(cells["D3"], "Proclamación")
        self.assertEqual(cells["A4"], "Históricos")
        self.assertEqual(cells["A5"], "Profetas")
        self.assertEqual(cells["A6"], "Cartas")
        self.assertEqual(cells["A7"], "Evangelios")
        self.assertIn('<mergeCell ref="B1:D1"/>', sheet)

    def test_equipo_sheet_has_auto_fitted_widths(self):
        categories = {
            "Históricos": [],
            "Profetas": [],
            "Cartas": [],
            "Evangelios": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.xlsx"
            build_workbook(categories, path)
            root = ET.fromstring(read_sheet(path, "xl/worksheets/sheet2.xml"))

        widths = {
            int(column.attrib["min"]): float(column.attrib["width"])
            for column in root.findall(".//m:col", NS)
        }
        self.assertEqual(widths[1], len("Monición ambiental") + 2)
        self.assertEqual(widths[2], len("Cita bíblica más votada") + 2)
        self.assertEqual(widths[3], len("Monición") + 2)
        self.assertEqual(widths[4], len("Proclamación") + 2)

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
