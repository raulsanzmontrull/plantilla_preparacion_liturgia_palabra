import unittest

from liturgia.fetch import build_url, slugify


class SlugifyTests(unittest.TestCase):
    def test_lowercases_and_removes_accents(self):
        self.assertEqual(slugify("Árbol"), "arbol")
        self.assertEqual(slugify("ESPÍRITU"), "espiritu")

    def test_replaces_spaces_with_underscores(self):
        self.assertEqual(slugify("Acción de gracias"), "accion_de_gracias")
        self.assertEqual(slugify("  Bien   y   mal  "), "bien_y_mal")

    def test_removes_punctuation(self):
        self.assertEqual(slugify("¿Quién?"), "quien")


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
