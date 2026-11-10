"""Interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path
from typing import Optional, Sequence

from . import __version__, books
from .excel import build_workbook
from .fetch import (
    FetchError,
    build_url,
    fetch_html,
    fetch_words,
    read_local_html,
    slugify,
)
from .parser import extract_citations, extract_word_text
from .pdf import build_pdf


def default_output_name(entrada: str) -> str:
    value = entrada.strip()
    if value.lower().startswith(("http://", "https://")):
        path = urllib.parse.urlparse(value).path.rstrip("/")
        value = urllib.parse.unquote(path.rsplit("/", 1)[-1]) or "liturgia"
    name = slugify(value) or "liturgia"
    return f"{name}.xlsx"


def display_word(entrada: str) -> str:
    value = entrada.strip()
    if value.lower().startswith(("http://", "https://")):
        path = urllib.parse.urlparse(value).path.rstrip("/")
        value = urllib.parse.unquote(path.rsplit("/", 1)[-1])
        value = value.replace("_", " ")
    return value or "liturgia"


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
        nargs="?",
        help="Palabra a consultar (por ejemplo, 'Árbol') o URL completa.",
    )
    parser.add_argument(
        "-o",
        "--salida",
        help="Ruta del archivo .xlsx de salida. Por defecto se usa el nombre de la palabra.",
    )
    parser.add_argument(
        "--todas",
        action="store_true",
        help="Genera los documentos de todas las palabras del vocabulario.",
    )
    parser.add_argument(
        "--carpeta",
        default="salida",
        help="Carpeta de salida para --todas (por defecto: salida).",
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
        "--pdf",
        action="store_true",
        help=(
            "Exporta también el documento a PDF con el mismo nombre que el .xlsx. "
            "Con --todas, genera únicamente PDFs."
        ),
    )
    parser.add_argument(
        "--texto",
        action="store_true",
        help=(
            "Incluye en el .xlsx una pestaña adicional con el texto de la palabra. "
            "No se añade por defecto."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _generate_single(args) -> int:
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

    word_text = extract_word_text(html) if args.texto else None

    output = Path(args.salida) if args.salida else Path(default_output_name(args.entrada))
    try:
        build_workbook(
            categories,
            output,
            sort_alphabetically=args.ordenar,
            text=word_text,
        )
    except OSError as error:
        print(f"Error al escribir {output}: {error}", file=sys.stderr)
        return 1

    if args.pdf:
        pdf_output = output.with_suffix(".pdf")
        try:
            build_pdf(
                categories,
                pdf_output,
                display_word(args.entrada),
                sort_alphabetically=args.ordenar,
            )
        except OSError as error:
            print(f"Error al escribir {pdf_output}: {error}", file=sys.stderr)
            return 1
        print(f"PDF generado: {pdf_output}")

    print(f"Plantilla generada: {output}")
    for category in books.CATEGORIES:
        print(f"  {category}: {len(categories[category])} citas")
    return 0


def _generate_all(args) -> int:
    folder = Path(args.carpeta)
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"Error al crear {folder}: {error}", file=sys.stderr)
        return 1

    try:
        words = fetch_words(timeout=args.timeout)
    except FetchError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if not words:
        print("Error: no se encontraron palabras en el vocabulario.", file=sys.stderr)
        return 1

    failures = 0
    total = len(words)
    for index, (slug, name) in enumerate(words, start=1):
        safe_slug = slugify(slug) or f"palabra_{index}"
        print(f"[{index}/{total}] {name}")
        try:
            html = fetch_html(build_url(slug), timeout=args.timeout)
        except FetchError as error:
            print(f"  Error: {error}", file=sys.stderr)
            failures += 1
            continue

        categories = extract_citations(html)
        if not any(categories.values()):
            print(
                "  Aviso: no se encontraron citas.",
                file=sys.stderr,
            )

        try:
            if args.pdf:
                build_pdf(
                    categories,
                    folder / f"{safe_slug}.pdf",
                    name,
                    sort_alphabetically=args.ordenar,
                )
            else:
                build_workbook(
                    categories,
                    folder / f"{safe_slug}.xlsx",
                    sort_alphabetically=args.ordenar,
                    text=extract_word_text(html) if args.texto else None,
                )
        except OSError as error:
            print(f"  Error al escribir {safe_slug}: {error}", file=sys.stderr)
            failures += 1

    document_type = "PDF" if args.pdf else "Excel"
    print(
        f"Generados {total - failures} de {total} {document_type} en {folder}"
    )
    return 1 if failures else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.todas:
        if args.entrada:
            parser.error("No se puede indicar una palabra junto con --todas.")
        if args.html:
            parser.error("--html no se puede usar junto con --todas.")
        if args.salida:
            parser.error("--salida no se puede usar con --todas; usa --carpeta.")
        return _generate_all(args)

    if not args.entrada:
        parser.error("Debes indicar una palabra o URL, o usar --todas.")

    return _generate_single(args)
