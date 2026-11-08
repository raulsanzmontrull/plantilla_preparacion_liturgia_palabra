"""Análisis, normalización y solapamiento de citas bíblicas."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import books


@dataclass(frozen=True)
class VerseInterval:
    chapter: int
    start: int
    end: int


@dataclass(frozen=True)
class ParsedCitation:
    original: str
    book: str
    book_key: str
    intervals: Tuple[VerseInterval, ...]
    parallel: bool = False


_PARALLEL_RE = re.compile(r"\s+p\b\.?$", re.IGNORECASE)
_CHAPTER_RE = re.compile(r"^(\d+)\s*,\s*(.+)$")
_VERSE_RE = re.compile(r"^(\d+)\s*(?:-\s*(\d+))?\s*(ss|s)?$", re.IGNORECASE)


def parse_citation(citation: str) -> Optional[ParsedCitation]:
    original = citation.strip()
    if not original:
        return None

    parallel = bool(_PARALLEL_RE.search(original))
    reference = _PARALLEL_RE.sub("", original).strip().replace("–", "-")

    book_token, rest = books.split_book_from_citation(reference)
    if not book_token or not rest:
        return None

    intervals: List[VerseInterval] = []
    for part in rest.split(";"):
        part = part.strip()
        if not part:
            continue
        chapter_match = _CHAPTER_RE.match(part)
        if not chapter_match:
            return None
        chapter = int(chapter_match.group(1))
        verses = chapter_match.group(2).strip()
        for verse_part in verses.split("."):
            verse_match = _VERSE_RE.match(verse_part.strip())
            if not verse_match:
                return None
            start = int(verse_match.group(1))
            end = int(verse_match.group(2)) if verse_match.group(2) else start
            suffix = (verse_match.group(3) or "").lower()
            if suffix == "s":
                end = max(end, start + 1)
            elif suffix == "ss":
                end = max(end, start + 2)
            intervals.append(VerseInterval(chapter, start, end))

    if not intervals:
        return None

    book = books.lookup_book(book_token)
    book_key = book.key if book is not None else books.normalize_book_name(book_token)
    return ParsedCitation(
        original=original,
        book=book_token,
        book_key=book_key,
        intervals=tuple(intervals),
        parallel=parallel,
    )


def union_intervals(
    interval_groups: Iterable[Sequence[VerseInterval]],
) -> Tuple[VerseInterval, ...]:
    by_chapter: Dict[int, List[Tuple[int, int]]] = {}
    for group in interval_groups:
        for interval in group:
            by_chapter.setdefault(interval.chapter, []).append(
                (interval.start, interval.end)
            )

    result: List[VerseInterval] = []
    for chapter in sorted(by_chapter):
        merged: List[Tuple[int, int]] = []
        for start, end in sorted(by_chapter[chapter]):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        for start, end in merged:
            result.append(VerseInterval(chapter, start, end))
    return tuple(result)


def normalize_intervals(
    intervals: Sequence[VerseInterval],
) -> Tuple[VerseInterval, ...]:
    return union_intervals([intervals])


def intervals_overlap(
    first: Sequence[VerseInterval], second: Sequence[VerseInterval]
) -> bool:
    for a in first:
        for b in second:
            if a.chapter == b.chapter and a.start <= b.end and b.start <= a.end:
                return True
    return False


def is_subset(
    subset: Sequence[VerseInterval], superset: Sequence[VerseInterval]
) -> bool:
    normalized = union_intervals([superset])
    for interval in subset:
        current = interval.start
        for candidate in normalized:
            if candidate.chapter != interval.chapter:
                continue
            if candidate.end < current:
                continue
            if candidate.start > current:
                break
            current = max(current, candidate.end + 1)
            if current > interval.end:
                break
        if current <= interval.end:
            return False
    return True


def render_intervals(
    book: str, intervals: Sequence[VerseInterval]
) -> str:
    by_chapter: Dict[int, List[Tuple[int, int]]] = {}
    for interval in union_intervals([intervals]):
        by_chapter.setdefault(interval.chapter, []).append(
            (interval.start, interval.end)
        )

    parts: List[str] = []
    for chapter in sorted(by_chapter):
        verse_parts: List[str] = []
        for start, end in sorted(by_chapter[chapter]):
            if start == end:
                verse_parts.append(str(start))
            else:
                verse_parts.append(f"{start}-{end}")
        parts.append(f"{chapter}," + ".".join(verse_parts))
    return f"{book} " + "; ".join(parts)


def _components(indices: Sequence[int], items: Sequence[Tuple[int, str, ParsedCitation]]):
    parent = {index: index for index in indices}

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        root_first = find(first)
        root_second = find(second)
        if root_first != root_second:
            parent[root_second] = root_first

    for position, first in enumerate(indices):
        first_parsed = items[first][2]
        for second in indices[position + 1 :]:
            second_parsed = items[second][2]
            if first_parsed.book_key != second_parsed.book_key:
                continue
            if intervals_overlap(first_parsed.intervals, second_parsed.intervals):
                union(first, second)

    grouped: Dict[int, List[int]] = {}
    for index in indices:
        grouped.setdefault(find(index), []).append(index)
    return grouped.values()


def _choose_representation(
    generators: Sequence[Tuple[int, str, ParsedCitation]],
    combined: Tuple[VerseInterval, ...],
) -> str:
    exact = [
        item
        for item in generators
        if normalize_intervals(item[2].intervals) == combined
    ]
    if exact:
        return max(exact, key=lambda item: len(item[1]))[1]
    return render_intervals(generators[0][2].book, combined)


def dedupe_citations(citations: Sequence[str]) -> List[str]:
    """Elimina redundancias y unifica solapamientos conservando el orden.

    Una cita contenida en otra se descarta. Si dos citas se solapan
    parcialmente, se sustituyen por su unión. La cita resultante ocupa la
    posición de la primera cita que la genera, salvo que la unión coincida
    exactamente con una cita ya existente: en ese caso se conserva esa cita
    en su posición original.
    """

    items: List[Tuple[int, str, Optional[ParsedCitation]]] = [
        (index, citation, parse_citation(citation))
        for index, citation in enumerate(citations)
    ]

    outputs: List[Tuple[int, str]] = []
    parseable_indices: List[int] = []
    for index, citation, parsed in items:
        if parsed is None:
            outputs.append((index, citation))
        else:
            parseable_indices.append(index)

    for component in _components(parseable_indices, items):
        component_items = [items[index] for index in component]

        unique_items: List[Tuple[int, str, ParsedCitation]] = []
        seen_intervals = set()
        for item in component_items:
            key = normalize_intervals(item[2].intervals)
            if key in seen_intervals:
                continue
            seen_intervals.add(key)
            unique_items.append(item)

        generators: List[Tuple[int, str, ParsedCitation]] = []
        for position, item in enumerate(unique_items):
            other_groups = [
                other[2].intervals
                for other_position, other in enumerate(unique_items)
                if other_position != position
            ]
            if other_groups and is_subset(
                item[2].intervals, union_intervals(other_groups)
            ):
                continue
            generators.append(item)

        if not generators:
            generators = [unique_items[0]]

        combined = union_intervals([item[2].intervals for item in generators])
        text = _choose_representation(generators, combined)
        anchor = min(item[0] for item in generators)
        outputs.append((anchor, text))

    outputs.sort(key=lambda item: item[0])
    return [text for _, text in outputs]
