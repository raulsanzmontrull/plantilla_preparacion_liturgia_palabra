import unittest
from pathlib import Path

from liturgia.books import CARTAS, EVANGELIOS, HISTORICOS, PROFETAS
from liturgia.parser import extract_citations, parse_html

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


class ParseHtmlTests(unittest.TestCase):
    def test_reads_categories_from_data_citas(self):
        page = parse_html(fixture("arbol.html"))
        self.assertEqual(
            page.categories["historicos"][:3],
            ["Gen 1,11s", "Ex 15,27", "Gen 2,9"],
        )
        self.assertIn("Sal 1,3", page.categories["sapienciales"])
        self.assertEqual(page.categories["evangelios"][0], "Mt 24,32")

    def test_ignores_citations_outside_citas_panel(self):
        page = parse_html(fixture("arbol.html"))
        self.assertNotIn("No 1,1", page.raw_citations)

    def test_collects_raw_citations_in_order(self):
        page = parse_html(fixture("arbol.html"))
        self.assertEqual(
            page.raw_citations[:4],
            ["Gen 1,11s", "Ex 15,27", "Gen 3,22", "Gen 3,22ss"],
        )

    def test_fallback_without_data_citas(self):
        html = """
        <div data-panel="citas">
          <button data-cita="Gen 3,22">Gen 3,22</button>
          <button data-cita="Is 41,19">Is 41,19</button>
          <button data-cita="1Pe 2,24">1Pe 2,24</button>
          <button data-cita="Mt 24,32">Mt 24,32</button>
        </div>
        """
        page = parse_html(html)
        self.assertEqual(page.categories, {})
        self.assertEqual(
            page.raw_citations,
            ["Gen 3,22", "Is 41,19", "1Pe 2,24", "Mt 24,32"],
        )


class ExtractCitationsTests(unittest.TestCase):
    def test_extracts_and_classifies_categories(self):
        result = extract_citations(fixture("arbol.html"))
        self.assertEqual(
            result[HISTORICOS],
            [
                "Gen 1,11s",
                "Ex 15,27",
                "Gen 2,9",
                "Gen 2,16s",
                "Gen 3,2-6",
                "Gen 3,22ss",
                "Gen 40,19",
                "Jos 8,29",
                "Jos 10,26",
                "Est 2,23",
                "Est 5,14",
                "Dt 21,22s",
            ],
        )
        self.assertEqual(
            result[PROFETAS],
            [
                "Is 41,19",
                "Jer 17,7s",
                "Os 14,6s",
                "Ez 47,12",
                "Ez 31,1-9",
                "Dan 4,7ss",
                "Ez 31,10-18",
                "Dan 4,10-14",
            ],
        )
        self.assertEqual(result[CARTAS], ["Gal 3,13", "1Pe 2,24", "Col 2,14"])
        self.assertEqual(
            result[EVANGELIOS],
            ["Mt 24,32", "Mt 7,16-20 p", "Mt 3,10 p", "Lc 23,31", "Mt 13,31s p"],
        )

    def test_filters_excluded_books(self):
        result = extract_citations(fixture("arbol.html"))
        all_citations = [c for values in result.values() for c in values]
        self.assertNotIn("Sal 1,3", all_citations)
        self.assertNotIn("Job 14,7ss", all_citations)
        self.assertNotIn("Ap 2,7", all_citations)
        self.assertNotIn("Ap 22,2.14", all_citations)

    def test_fallback_classification_without_json(self):
        html = """
        <div data-panel="citas">
          <button data-cita="Gen 3,22">Gen 3,22</button>
          <button data-cita="Sal 1,3">Sal 1,3</button>
          <button data-cita="Is 41,19">Is 41,19</button>
          <button data-cita="1Pe 2,24">1Pe 2,24</button>
          <button data-cita="Mt 24,32">Mt 24,32</button>
        </div>
        """
        result = extract_citations(html)
        self.assertEqual(result[HISTORICOS], ["Gen 3,22"])
        self.assertEqual(result[PROFETAS], ["Is 41,19"])
        self.assertEqual(result[CARTAS], ["1Pe 2,24"])
        self.assertEqual(result[EVANGELIOS], ["Mt 24,32"])

    def test_merges_overlaps_inside_each_category(self):
        html = """
        <div data-panel="citas">
          <button data-citas="{&quot;evangelios&quot;:[&quot;Mt 24,32&quot;,&quot;Mt 24,30-33&quot;,&quot;Mt 24,32-35&quot;,&quot;Mt 24,36&quot;]}">Exportar</button>
        </div>
        """
        result = extract_citations(html)
        self.assertEqual(result[EVANGELIOS], ["Mt 24,30-35", "Mt 24,36"])


if __name__ == "__main__":
    unittest.main()
