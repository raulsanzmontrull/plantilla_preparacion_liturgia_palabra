"""Catálogo de libros bíblicos y clasificación de citas.

Las abreviaturas y nombres siguen el uso habitual en español. La normalización
elimina acentos, mayúsculas, puntos y espacios sobrantes para que las citas de
la web se puedan reconocer con independencia de su forma exacta.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

HISTORICOS = "Históricos"
PROFETAS = "Profetas"
CARTAS = "Cartas"
EVANGELIOS = "Evangelios"

CATEGORIES = (HISTORICOS, PROFETAS, CARTAS, EVANGELIOS)


@dataclass(frozen=True)
class Book:
    key: str
    name: str
    category: Optional[str]
    excluded: bool = False


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    text = without_accents.lower().strip()
    text = text.replace(".", "")
    text = re.sub(r"\s+", " ", text)
    numbered = re.match(r"^([1-3])\s*(.+)$", text)
    if numbered:
        text = f"{numbered.group(1)} {numbered.group(2).strip()}"
    return text


normalize_book_name = _normalize


def _register(
    registry: Dict[str, Book],
    key: str,
    name: str,
    category: Optional[str],
    aliases: Iterable[str],
    excluded: bool = False,
) -> None:
    book = Book(key=key, name=name, category=category, excluded=excluded)
    for alias in aliases:
        registry[_normalize(alias)] = book
    registry[_normalize(name)] = book


def _build_registry() -> Dict[str, Book]:
    registry: Dict[str, Book] = {}

    historical = [
        ("gen", "Génesis", ["Gen", "Gn"]),
        ("ex", "Éxodo", ["Ex", "Éx"]),
        ("lev", "Levítico", ["Lev", "Lv"]),
        ("num", "Números", ["Num", "Nm"]),
        ("deut", "Deuteronomio", ["Deut", "Dt"]),
        ("jos", "Josué", ["Jos"]),
        ("jue", "Jueces", ["Jue", "Jc"]),
        ("rut", "Rut", ["Rut", "Rt"]),
        ("1 sam", "1 Samuel", ["1 Sam", "1 Sm", "1 Sa"]),
        ("2 sam", "2 Samuel", ["2 Sam", "2 Sm", "2 Sa"]),
        ("1 re", "1 Reyes", ["1 Re", "1 Rey", "1 Reyes"]),
        ("2 re", "2 Reyes", ["2 Re", "2 Rey", "2 Reyes"]),
        ("1 cr", "1 Crónicas", ["1 Cr", "1 Cronica", "1 Crónicas"]),
        ("2 cr", "2 Crónicas", ["2 Cr", "2 Cronica", "2 Crónicas"]),
        ("esd", "Esdras", ["Esd"]),
        ("neh", "Nehemías", ["Neh"]),
        ("tob", "Tobías", ["Tob", "Tb"]),
        ("jdt", "Judit", ["Jdt", "Judit"]),
        ("est", "Ester", ["Est"]),
        ("1 mac", "1 Macabeos", ["1 Mac", "1 Mq"]),
        ("2 mac", "2 Macabeos", ["2 Mac", "2 Mq"]),
    ]
    for key, name, aliases in historical:
        _register(registry, key, name, HISTORICOS, aliases)

    prophets = [
        ("is", "Isaías", ["Is", "Isa"]),
        ("jer", "Jeremías", ["Jer", "Jr"]),
        ("lam", "Lamentaciones", ["Lam", "Lm"]),
        ("bar", "Baruc", ["Bar"]),
        ("ez", "Ezequiel", ["Ez"]),
        ("dan", "Daniel", ["Dan", "Dn"]),
        ("os", "Oseas", ["Os"]),
        ("joel", "Joel", ["Joel", "Jl"]),
        ("am", "Amós", ["Am"]),
        ("abd", "Abdías", ["Abd", "Ob"]),
        ("jon", "Jonás", ["Jon"]),
        ("miq", "Miqueas", ["Miq", "Mi"]),
        ("nah", "Nahúm", ["Nah", "Na"]),
        ("hab", "Habacuc", ["Hab", "Ha"]),
        ("sof", "Sofonías", ["Sof", "So"]),
        ("ageo", "Ageo", ["Ageo", "Ag", "Hageo"]),
        ("zac", "Zacarías", ["Zac", "Za"]),
        ("mal", "Malaquías", ["Mal", "Malaquias"]),
    ]
    for key, name, aliases in prophets:
        _register(registry, key, name, PROFETAS, aliases)

    letters = [
        ("rom", "Romanos", ["Rom", "Ro"]),
        ("1 cor", "1 Corintios", ["1 Cor", "1 Co"]),
        ("2 cor", "2 Corintios", ["2 Cor", "2 Co"]),
        ("gal", "Gálatas", ["Gal", "Ga"]),
        ("ef", "Efesios", ["Ef"]),
        ("flp", "Filipenses", ["Flp", "Fil"]),
        ("col", "Colosenses", ["Col"]),
        ("1 tes", "1 Tesalonicenses", ["1 Tes", "1 Ts"]),
        ("2 tes", "2 Tesalonicenses", ["2 Tes", "2 Ts"]),
        ("1 tim", "1 Timoteo", ["1 Tim", "1 Ti"]),
        ("2 tim", "2 Timoteo", ["2 Tim", "2 Ti"]),
        ("tit", "Tito", ["Tit"]),
        ("flm", "Filemón", ["Flm", "Filemon"]),
        ("heb", "Hebreos", ["Heb"]),
        ("sant", "Santiago", ["Sant", "Stg"]),
        ("1 pe", "1 Pedro", ["1 Pe", "1 Ped"]),
        ("2 pe", "2 Pedro", ["2 Pe", "2 Ped"]),
        ("1 jn", "1 Juan", ["1 Jn"]),
        ("2 jn", "2 Juan", ["2 Jn"]),
        ("3 jn", "3 Juan", ["3 Jn"]),
        ("jud", "Judas", ["Jud"]),
        ("hch", "Hechos", ["Hch", "Hech", "Act", "Hechos de los Apóstoles"]),
    ]
    for key, name, aliases in letters:
        _register(registry, key, name, CARTAS, aliases)

    gospels = [
        ("mt", "Mateo", ["Mt"]),
        ("mc", "Marcos", ["Mc"]),
        ("lc", "Lucas", ["Lc"]),
        ("jn", "Juan", ["Jn"]),
    ]
    for key, name, aliases in gospels:
        _register(registry, key, name, EVANGELIOS, aliases)

    excluded = [
        ("job", "Job", ["Job", "Jb"]),
        ("sal", "Salmos", ["Sal", "Salmo", "Salmos"]),
        ("prov", "Proverbios", ["Prov", "Pr"]),
        ("ecl", "Eclesiastés", ["Ecl", "Eccl", "Ec", "Qo", "Qoh", "Qohelet", "Eclesiastés"]),
        ("cant", "Cantar de los Cantares", ["Cant", "Ct", "Cantar", "Cantares"]),
        ("sab", "Sabiduría", ["Sab"]),
        ("eclo", "Eclesiástico", ["Eclo", "Sir", "Sirac", "Siracides", "Eclesiástico"]),
        ("ap", "Apocalipsis", ["Ap", "Apoc", "Apocalipsis", "Rev"]),
    ]
    for key, name, aliases in excluded:
        _register(registry, key, name, None, aliases, excluded=True)

    return registry


_REGISTRY = _build_registry()


def split_book_from_citation(citation: str) -> Tuple[str, str]:
    """Separa el nombre del libro de la referencia (capítulo, versículos)."""

    text = citation.strip()
    match = re.match(
        r"^\s*((?:[1-3]\s*)?[^\W\d_][\w.\s]*?)\s+(\d.*)$",
        text,
        flags=re.UNICODE,
    )
    if not match:
        return text, ""
    return match.group(1).strip(), match.group(2).strip()


def lookup_book(raw: str) -> Optional[Book]:
    key, _ = split_book_from_citation(raw)
    return _REGISTRY.get(_normalize(key))


def classify_citation(citation: str) -> Optional[str]:
    book = lookup_book(citation)
    if book is None or book.excluded:
        return None
    return book.category


def is_excluded_citation(citation: str) -> bool:
    book = lookup_book(citation)
    return bool(book and book.excluded)
