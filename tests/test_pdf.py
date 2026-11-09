import tempfile
import unittest
from pathlib import Path

from liturgia.pdf import build_pdf


class BuildPdfTests(unittest.TestCase):
    def test_creates_pdf_with_title_and_both_tables(self):
        categories = {
            "Históricos": ["Gen 1,11s"],
            "Profetas": ["Is 41,19"],
            "Cartas": ["1Pe 2,24"],
            "Evangelios": ["Mt 24,32"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.pdf"
            build_pdf(categories, path, "Árbol")
            content = path.read_bytes()

        self.assertTrue(content.startswith(b"%PDF-1.4"))
        self.assertTrue(content.endswith(b"%%EOF\n"))
        self.assertIn(b"PALABRA: \\301rbol", content)
        self.assertIn(b"Gen 1,11s", content)
        self.assertIn(b"Is 41,19", content)
        self.assertIn(b"1Pe 2,24", content)
        self.assertIn(b"Mt 24,32", content)
        self.assertIn(b"Equipo", content)
        self.assertIn(b"Monici\\363n ambiental", content)
        self.assertIn(b"Cita b\\355blica m\\341s votada", content)

    def test_sorts_citations_when_requested(self):
        categories = {
            "Históricos": ["Gen 3,1", "Ex 1,1"],
            "Profetas": [],
            "Cartas": [],
            "Evangelios": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "salida.pdf"
            build_pdf(categories, path, "Árbol", sort_alphabetically=True)
            content = path.read_bytes()

        self.assertLess(content.index(b"Ex 1,1"), content.index(b"Gen 3,1"))


if __name__ == "__main__":
    unittest.main()
