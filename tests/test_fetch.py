import unittest

from liturgia.fetch import build_url, extract_words, slugify


class SlugifyTests(unittest.TestCase):
    def test_lowercases_and_removes_accents(self):
        self.assertEqual(slugify("Árbol"), "arbol")
        self.assertEqual(slugify("ESPÍRITU"), "espiritu")

    def test_replaces_spaces_with_underscores(self):
        self.assertEqual(slugify("Acción de gracias"), "accion_de_gracias")
        self.assertEqual(slugify("  Bien   y   mal  "), "bien_y_mal")

    def test_removes_punctuation(self):
        self.assertEqual(slugify("¿Quién?"), "quien")


class ExtractWordsTests(unittest.TestCase):
    def test_extracts_word_links_in_order(self):
        html = """
        <a href="/palabra/arbol">Árbol</a>
        <a href="https://leon-dufour.com/palabra/accion_de_gracias">
            Acción de gracias
        </a>
        <a href="/info">Información</a>
        <a href="/palabra/arbol">Árbol repetido</a>
        """
        self.assertEqual(
            extract_words(html),
            [
                ("arbol", "Árbol"),
                ("accion_de_gracias", "Acción de gracias"),
            ],
        )

    def test_removes_citation_count_from_name(self):
        html = (
            '<a href="/palabra/abraham">'
            "<span>Abraham</span><span>71 citas</span></a>"
            '<a href="/palabra/iglesia">'
            "<span>Iglesia</span><span>1 cita</span></a>"
        )
        self.assertEqual(
            extract_words(html),
            [("abraham", "Abraham"), ("iglesia", "Iglesia")],
        )

    def test_accepts_relative_word_links(self):
        html = '<a href="palabra/iglesia">Iglesia</a>'
        self.assertEqual(extract_words(html), [("iglesia", "Iglesia")])

    def test_uses_slug_when_link_has_no_text(self):
        html = '<a href="/palabra/bien_y_mal"></a>'
        self.assertEqual(extract_words(html), [("bien_y_mal", "bien y mal")])

    def test_returns_empty_list_without_word_links(self):
        self.assertEqual(extract_words("<p>Sin enlaces</p>"), [])


class BuildUrlTests(unittest.TestCase):
    def test_builds_url_from_word(self):
        self.assertEqual(
            build_url("arbol"),
            "https://leon-dufour.com/palabra/arbol",
        )

    def test_builds_url_from_word_with_accents_and_spaces(self):
        self.assertEqual(
            build_url("Acción de gracias"),
            "https://leon-dufour.com/palabra/accion_de_gracias",
        )

    def test_keeps_http_urls(self):
        url = "https://leon-dufour.com/palabra/arbol"
        self.assertEqual(build_url(url), url)
        self.assertEqual(build_url("http://example.com/x"), "http://example.com/x")


if __name__ == "__main__":
    unittest.main()
