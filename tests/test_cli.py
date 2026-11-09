import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

from liturgia.cli import default_output_name, display_word, main
from liturgia.fetch import FetchError

FIXTURES = Path(__file__).parent / "fixtures"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def run_main(args):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()


def word_page(citation):
    return (
        '<div data-panel="citas">'
        '<button data-citas=\'{"historicos":["%s"]}\'>' % citation
        + "</button></div>"
    )


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

    def test_todas_generates_one_xlsx_per_word(self):
        words = [("arbol", "Árbol"), ("accion_de_gracias", "Acción de gracias")]
        pages = {
            "arbol": word_page("Gen 1,1"),
            "accion_de_gracias": word_page("Ex 2,2"),
        }

        def fake_fetch_html(url, timeout=30.0):
            return pages[url.rsplit("/", 1)[-1]]

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "documentos"
            with patch("liturgia.cli.fetch_words", return_value=words), patch(
                "liturgia.cli.fetch_html", side_effect=fake_fetch_html
            ):
                code, stdout, stderr = run_main(
                    ["--todas", "--carpeta", str(folder)]
                )

            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            self.assertTrue((folder / "arbol.xlsx").exists())
            self.assertTrue((folder / "accion_de_gracias.xlsx").exists())
            self.assertFalse((folder / "arbol.pdf").exists())
            self.assertIn("Generados 2 de 2 Excel", stdout)

    def test_todas_with_pdf_generates_only_pdfs(self):
        words = [("arbol", "Árbol"), ("accion_de_gracias", "Acción de gracias")]
        pages = {
            "arbol": word_page("Gen 1,1"),
            "accion_de_gracias": word_page("Ex 2,2"),
        }

        def fake_fetch_html(url, timeout=30.0):
            return pages[url.rsplit("/", 1)[-1]]

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "documentos"
            with patch("liturgia.cli.fetch_words", return_value=words), patch(
                "liturgia.cli.fetch_html", side_effect=fake_fetch_html
            ):
                code, stdout, stderr = run_main(
                    ["--todas", "--pdf", "--carpeta", str(folder)]
                )

            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            self.assertTrue((folder / "arbol.pdf").exists())
            self.assertTrue((folder / "accion_de_gracias.pdf").exists())
            self.assertFalse((folder / "arbol.xlsx").exists())
            self.assertIn("Generados 2 de 2 PDF", stdout)
            content = (folder / "arbol.pdf").read_bytes()

        self.assertIn(b"PALABRA: \\301rbol", content)

    def test_todas_reports_partial_failures(self):
        words = [("arbol", "Árbol"), ("falla", "Falla")]

        def fake_fetch_html(url, timeout=30.0):
            if url.endswith("/falla"):
                raise FetchError("sin conexión")
            return word_page("Gen 1,1")

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "documentos"
            with patch("liturgia.cli.fetch_words", return_value=words), patch(
                "liturgia.cli.fetch_html", side_effect=fake_fetch_html
            ):
                code, stdout, stderr = run_main(
                    ["--todas", "--carpeta", str(folder)]
                )

            self.assertEqual(code, 1)
            self.assertIn("sin conexión", stderr)
            self.assertIn("Generados 1 de 2 Excel", stdout)
            self.assertTrue((folder / "arbol.xlsx").exists())
            self.assertFalse((folder / "falla.xlsx").exists())

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
