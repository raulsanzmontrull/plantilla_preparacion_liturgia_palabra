import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from liturgia.cli import default_output_name, display_word, main

FIXTURES = Path(__file__).parent / "fixtures"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def run_main(args):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()


def cells_by_reference(path):
    with zipfile.ZipFile(path) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml")
    root = ET.fromstring(sheet)
    cells = {}
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib["r"]
        text = cell.findtext(".//m:t", default="", namespaces=NS)
        cells[ref] = text
    return cells


class DefaultOutputNameTests(unittest.TestCase):
    def test_derives_name_from_word(self):
        self.assertEqual(default_output_name("Árbol"), "arbol.xlsx")
        self.assertEqual(default_output_name("Acción de gracias"), "accion_de_gracias.xlsx")

    def test_derives_name_from_url(self):
        self.assertEqual(
            default_output_name("https://leon-dufour.com/palabra/accion_de_gracias"),
            "accion_de_gracias.xlsx",
        )


class DisplayWordTests(unittest.TestCase):
    def test_keeps_word_as_given(self):
        self.assertEqual(display_word("Árbol"), "Árbol")

    def test_extracts_word_from_url(self):
        self.assertEqual(
            display_word("https://leon-dufour.com/palabra/accion_de_gracias"),
            "accion de gracias",
        )


class MainTests(unittest.TestCase):
    def test_generates_xlsx_from_local_html(self):
        fixture = FIXTURES / "arbol.html"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "arbol.xlsx"
            code, stdout, stderr = run_main(
                ["arbol", "--html", str(fixture), "-o", str(output)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            self.assertIn("Plantilla generada", stdout)
            self.assertTrue(output.exists())
            with zipfile.ZipFile(output) as archive:
                self.assertIn("xl/worksheets/sheet1.xml", archive.namelist())

    def test_ordenar_flag_sorts_citations_alphabetically(self):
        html = (
            '<div data-panel="citas">'
            "<button data-citas='{\"historicos\":[\"Gen 2,9\",\"Ex 15,27\"]}'>"
            "</button></div>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "entrada.html"
            fixture.write_text(html, encoding="utf-8")
            output = Path(tmp) / "salida.xlsx"
            code, _, stderr = run_main(
                [
                    "arbol",
                    "--html",
                    str(fixture),
                    "-o",
                    str(output),
                    "--ordenar",
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            cells = cells_by_reference(output)

        self.assertEqual(cells["A2"], "Ex 15,27")
        self.assertEqual(cells["A3"], "Gen 2,9")

    def test_pdf_flag_generates_pdf_next_to_xlsx(self):
        fixture = FIXTURES / "arbol.html"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "arbol.xlsx"
            code, stdout, stderr = run_main(
                ["Árbol", "--html", str(fixture), "-o", str(output), "--pdf"]
            )
            pdf_output = output.with_suffix(".pdf")
            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            self.assertTrue(output.exists())
            self.assertTrue(pdf_output.exists())
            self.assertIn("PDF generado", stdout)
            content = pdf_output.read_bytes()

        self.assertIn(b"PALABRA: \\301rbol", content)

    def test_returns_error_for_missing_local_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "arbol.xlsx"
            code, _, stderr = run_main(
                [
                    "arbol",
                    "--html",
                    str(Path(tmp) / "no-existe.html"),
                    "-o",
                    str(output),
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("Error", stderr)
            self.assertFalse(output.exists())

    def test_default_output_name_is_derived_from_word(self):
        fixture = FIXTURES / "arbol.html"
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_main(
                ["Árbol", "--html", str(fixture), "-o", str(Path(tmp) / "arbol.xlsx")]
            )
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
