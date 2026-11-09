"""Interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path
from typing import Optional, Sequence

from . import __version__, books
from .excel import build_workbook
from .fetch import FetchError, build_url, fetch_html, read_local_html, slugify
from .parser import extract_citations


def default_output_name(entrada: str) -> str:
    value = entrada.strip()
    if value.lower().startswith(("http://", "https://")):
        path = urllib.parse.urlparse(value).path.rstrip("/")
        value = urllib.parse.unquote(path.rsplit("/", 1)[-1]) or "liturgia"
    name = slugify(value) or "liturgia"
    return f"{name}.xlsx"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="liturgia-palabra",
        description=(
            "Genera una plantilla Excel para preparar la Liturgia de la Palabra "
            "a partir de una palabra o URL de leon-dufour.com."
        ),
    )
    parser.add_argument(
        "entrada",
        help="Palabra a consultar (por ejemplo, 'Árbol') o URL completa.",
    )
    parser.add_argument(
        "-o",
        "--salida",
        help="Ruta del archivo .xlsx de salida. Por defecto se usa el nombre de la palabra.",
    )
    parser.add_argument(
        "--html",
        help="Usa un archivo HTML local en lugar de descargar la página.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Tiempo máximo de descarga en segundos (por defecto: 30).",
    )
    parser.add_argument(
        "-a",
        "--ordenar",
        action="store_true",
        help=(
            "Ordena alfabéticamente las citas de cada columna "
            "(por defecto se conserva el orden de aparición)."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.html:
            html = read_local_html(args.html)
        else:
            html = fetch_html(build_url(args.entrada), timeout=args.timeout)
    except FetchError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    categories = extract_citations(html)
    if not any(categories.values()):
        print(
            "Aviso: no se encontraron citas. Revisa la palabra o la URL.",
            file=sys.stderr,
        )

    output = Path(args.salida) if args.salida else Path(default_output_name(args.entrada))
    try:
        build_workbook(
            categories,
            output,
            sort_alphabetically=args.ordenar,
        )
    except OSError as error:
        print(f"Error al escribir {output}: {error}", file=sys.stderr)
        return 1

    print(f"Plantilla generada: {output}")
    for category in books.CATEGORIES:
        print(f"  {category}: {len(categories[category])} citas")
    return 0
