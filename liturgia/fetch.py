"""Descarga del HTML de León Dufour usando solo la biblioteca estándar."""

from __future__ import annotations

import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import List, Optional, Tuple

DEFAULT_BASE_URL = "https://leon-dufour.com/palabra/"
DEFAULT_SITE_URL = "https://leon-dufour.com/"
USER_AGENT = "liturgia-palabra/1.0 (+https://leon-dufour.com)"


class FetchError(RuntimeError):
    """Error controlado al descargar o leer el HTML."""


def slugify(word: str) -> str:
    decomposed = unicodedata.normalize("NFKD", word)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    text = without_accents.lower().strip()
    text = re.sub(r"[^a-z0-9_]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace(" ", "_")


def build_url(user_input: str) -> str:
    value = user_input.strip()
    if value.lower().startswith(("http://", "https://")):
        return value
    return DEFAULT_BASE_URL + slugify(value)


def _word_slug(href: str) -> Optional[str]:
    path = urllib.parse.urlparse(href).path.rstrip("/")
    match = re.search(r"(?:^|/)palabra/([^/]+)$", path)
    if not match:
        return None
    return urllib.parse.unquote(match.group(1))


_CITATION_COUNT = re.compile(r"\s*\d+\s+citas?\s*$", re.IGNORECASE)


def _clean_word_name(name: str) -> str:
    return _CITATION_COUNT.sub("", name).strip()


class _WordListExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._slug: Optional[str] = None
        self._text: List[str] = []
        self.words: List[Tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            slug = _word_slug(href)
            if slug:
                self._slug = slug
                self._text = []

    def handle_data(self, data):
        if self._slug is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or self._slug is None:
            return
        name = _clean_word_name(" ".join("".join(self._text).split()))
        self.words.append((self._slug, name or self._slug.replace("_", " ")))
        self._slug = None
        self._text = []


def extract_words(html: str) -> List[Tuple[str, str]]:
    extractor = _WordListExtractor()
    extractor.feed(html)
    extractor.close()

    words: List[Tuple[str, str]] = []
    seen = set()
    for slug, name in extractor.words:
        if slug in seen:
            continue
        seen.add(slug)
        words.append((slug, name))
    return words


def fetch_html(url: str, timeout: float = 30.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as error:
        raise FetchError(
            f"No se pudo descargar {url}: HTTP {error.code} {error.reason}"
        ) from error
    except urllib.error.URLError as error:
        raise FetchError(f"No se pudo descargar {url}: {error.reason}") from error
    except OSError as error:
        raise FetchError(f"No se pudo descargar {url}: {error}") from error


def fetch_words(timeout: float = 30.0) -> List[Tuple[str, str]]:
    return extract_words(fetch_html(DEFAULT_SITE_URL, timeout=timeout))


def read_local_html(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        raise FetchError(f"No se pudo leer {path}: {error}") from error
