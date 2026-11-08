import contextlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from liturgia.cli import default_output_name, main

FIXTURES = Path(__file__).parent / "fixtures"


def run_main(args):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()


class DefaultOutputNameTests(unittest.TestCase):
    def test_derives_name_from_word(self):
        self.assertEqual(default_output_name("Árbol"), "arbol.xlsx")
        self.assertEqual(default_output_name("Acción de gracias"), "accion_de_gracias.xlsx")

    def test_derives_name_from_url(self):
        self.assertEqual(
            default_output_name("https://leon-dufour.com/palabra/accion_de_gracias"),
            "accion_de_gracias.xlsx",
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
