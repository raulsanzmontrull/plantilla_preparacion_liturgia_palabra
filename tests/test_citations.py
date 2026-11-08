import unittest

from liturgia.citations import (
    VerseInterval,
    dedupe_citations,
    parse_citation,
)


class ParseCitationTests(unittest.TestCase):
    def test_single_verse(self):
        parsed = parse_citation("Gen 3,22")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.book, "Gen")
        self.assertEqual(parsed.book_key, "gen")
        self.assertEqual(parsed.intervals, (VerseInterval(3, 22, 22),))
        self.assertFalse(parsed.parallel)

    def test_verse_and_following(self):
        self.assertEqual(
            parse_citation("Gen 3,22ss").intervals,
            (VerseInterval(3, 22, 24),),
        )
        self.assertEqual(
            parse_citation("Gen 1,11s").intervals,
            (VerseInterval(1, 11, 12),),
        )

    def test_verse_range(self):
        self.assertEqual(
            parse_citation("Mt 7,16-20").intervals,
            (VerseInterval(7, 16, 20),),
        )

    def test_parallel_marker(self):
        parsed = parse_citation("Mt 7,16-20 p")
        self.assertTrue(parsed.parallel)
        self.assertEqual(parsed.intervals, (VerseInterval(7, 16, 20),))

    def test_multiple_verse_segments(self):
        self.assertEqual(
            parse_citation("Ap 22,2.14").intervals,
            (VerseInterval(22, 2, 2), VerseInterval(22, 14, 14)),
        )

    def test_multiple_chapter_segments(self):
        self.assertEqual(
            parse_citation("Mt 5,3-12; 6,9-13").intervals,
            (VerseInterval(5, 3, 12), VerseInterval(6, 9, 13)),
        )

    def test_full_and_numbered_book_names(self):
        self.assertEqual(parse_citation("1 Corintios 13,1").book_key, "1 cor")
        self.assertEqual(parse_citation("Hechos 2,1").book_key, "hch")
        self.assertEqual(
            parse_citation("Cantar de los Cantares 1,2").book_key,
            "cant",
        )

    def test_unparseable(self):
        self.assertIsNone(parse_citation("Texto raro"))
        self.assertIsNone(parse_citation("Gen"))


class DedupeCitationsTests(unittest.TestCase):
    def test_removes_contained_shorter_citation(self):
        self.assertEqual(
            dedupe_citations(["Gen 3,22", "Gen 3,22ss"]),
            ["Gen 3,22ss"],
        )

    def test_keeps_superset_at_its_original_position(self):
        self.assertEqual(
            dedupe_citations(["Gen 1,11s", "Gen 3,22", "Gen 2,16s", "Gen 3,22ss"]),
            ["Gen 1,11s", "Gen 2,16s", "Gen 3,22ss"],
        )

    def test_merges_partial_overlaps(self):
        self.assertEqual(
            dedupe_citations(
                ["Mt 24,32", "Mt 24,30-33", "Mt 24,32-35", "Mt 24,36"]
            ),
            ["Mt 24,30-35", "Mt 24,36"],
        )

    def test_merges_partial_overlaps_preserving_book_token(self):
        self.assertEqual(
            dedupe_citations(["Mt 24,30-33", "Mt 24,32-35"]),
            ["Mt 24,30-35"],
        )

    def test_does_not_merge_different_books(self):
        self.assertEqual(
            dedupe_citations(["Gen 3,22", "Ex 3,22"]),
            ["Gen 3,22", "Ex 3,22"],
        )

    def test_does_not_merge_adjacent_ranges(self):
        self.assertEqual(
            dedupe_citations(["Mt 24,30-31", "Mt 24,32-35"]),
            ["Mt 24,30-31", "Mt 24,32-35"],
        )

    def test_duplicate_identical_citations_keep_one(self):
        self.assertEqual(
            dedupe_citations(["Gen 3,22", "Gen 3,22"]),
            ["Gen 3,22"],
        )

    def test_unparseable_citations_are_preserved(self):
        self.assertEqual(
            dedupe_citations(["Texto raro", "Gen 3,22"]),
            ["Texto raro", "Gen 3,22"],
        )

    def test_removes_citation_contained_in_multiple_segments(self):
        self.assertEqual(
            dedupe_citations(["Ap 22,2.14", "Ap 22,14"]),
            ["Ap 22,2.14"],
        )


if __name__ == "__main__":
    unittest.main()
