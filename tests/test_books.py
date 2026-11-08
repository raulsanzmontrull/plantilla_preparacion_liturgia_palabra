import unittest

from liturgia.books import (
    CARTAS,
    EVANGELIOS,
    HISTORICOS,
    PROFETAS,
    classify_citation,
    is_excluded_citation,
    lookup_book,
    normalize_book_name,
    split_book_from_citation,
)


class NormalizeBookNameTests(unittest.TestCase):
    def test_removes_accents_and_lowercases(self):
        self.assertEqual(normalize_book_name("Génesis"), "genesis")
        self.assertEqual(normalize_book_name("ÉXODO"), "exodo")

    def test_normalizes_numbered_books(self):
        self.assertEqual(normalize_book_name("1Pe"), "1 pe")
        self.assertEqual(normalize_book_name(" 1 Pe "), "1 pe")
        self.assertEqual(normalize_book_name("2 Corintios"), "2 corintios")

    def test_removes_periods_and_collapses_spaces(self):
        self.assertEqual(normalize_book_name("Cantar  de  los  Cantares"), "cantar de los cantares")
        self.assertEqual(normalize_book_name("Gen."), "gen")


class SplitBookTests(unittest.TestCase):
    def test_simple_citation(self):
        self.assertEqual(split_book_from_citation("Gen 1,11s"), ("Gen", "1,11s"))

    def test_numbered_book_without_space(self):
        self.assertEqual(split_book_from_citation("1Pe 2,24"), ("1Pe", "2,24"))

    def test_full_book_name_with_spaces(self):
        self.assertEqual(
            split_book_from_citation("Cantar de los Cantares 1,2"),
            ("Cantar de los Cantares", "1,2"),
        )

    def test_parallel_marker_is_kept_in_reference(self):
        self.assertEqual(split_book_from_citation("Mt 7,16-20 p"), ("Mt", "7,16-20 p"))

    def test_returns_original_when_no_reference(self):
        self.assertEqual(split_book_from_citation("Texto raro"), ("Texto raro", ""))


class LookupBookTests(unittest.TestCase):
    def test_historical_books(self):
        self.assertEqual(lookup_book("Gen").key, "gen")
        self.assertEqual(lookup_book("Génesis").key, "gen")
        self.assertEqual(lookup_book("Gen").category, HISTORICOS)
        self.assertEqual(lookup_book("Jos").category, HISTORICOS)
        self.assertEqual(lookup_book("2 Mac").category, HISTORICOS)
        self.assertEqual(lookup_book("1Sa").category, HISTORICOS)

    def test_prophetic_books(self):
        self.assertEqual(lookup_book("Is").category, PROFETAS)
        self.assertEqual(lookup_book("Daniel").category, PROFETAS)
        self.assertEqual(lookup_book("Zac").category, PROFETAS)
        self.assertEqual(lookup_book("Mal").category, PROFETAS)

    def test_letters_and_acts(self):
        self.assertEqual(lookup_book("1 Cor").category, CARTAS)
        self.assertEqual(lookup_book("Hch").category, CARTAS)
        self.assertEqual(lookup_book("Act").category, CARTAS)
        self.assertEqual(lookup_book("Jud").category, CARTAS)

    def test_gospels(self):
        self.assertEqual(lookup_book("Mt").category, EVANGELIOS)
        self.assertEqual(lookup_book("Juan").category, EVANGELIOS)

    def test_excluded_books(self):
        for name in ["Job", "Sal", "Prov", "Ecl", "Cant", "Sab", "Eclo", "Ap"]:
            with self.subTest(name=name):
                self.assertTrue(lookup_book(name).excluded)

    def test_unknown_book(self):
        self.assertIsNone(lookup_book("LibroInventado"))


class ClassifyCitationTests(unittest.TestCase):
    def test_classifies_by_book(self):
        self.assertEqual(classify_citation("Gen 3,22"), HISTORICOS)
        self.assertEqual(classify_citation("Is 41,19"), PROFETAS)
        self.assertEqual(classify_citation("1Pe 2,24"), CARTAS)
        self.assertEqual(classify_citation("Mt 24,32"), EVANGELIOS)

    def test_excluded_books_are_not_classified(self):
        self.assertIsNone(classify_citation("Sal 1,3"))
        self.assertIsNone(classify_citation("Ap 2,7"))
        self.assertIsNone(classify_citation("Eclo 24,12-22"))

    def test_unknown_citation_is_not_classified(self):
        self.assertIsNone(classify_citation("Texto raro"))


class ExcludedCitationTests(unittest.TestCase):
    def test_excluded(self):
        self.assertTrue(is_excluded_citation("Ap 2,7"))
        self.assertTrue(is_excluded_citation("Job 14,7ss"))

    def test_not_excluded(self):
        self.assertFalse(is_excluded_citation("Gen 3,22"))
        self.assertFalse(is_excluded_citation("Texto raro"))


if __name__ == "__main__":
    unittest.main()
