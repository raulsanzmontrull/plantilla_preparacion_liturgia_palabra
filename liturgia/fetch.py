"""Descarga del HTML de León Dufour usando solo la biblioteca estándar."""

from __future__ import annotations

import re
import unicodedata
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://leon-dufour.com/palabra/"
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


def read_local_html(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        raise FetchError(f"No se pudo leer {path}: {error}") from error
