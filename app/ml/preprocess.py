"""Препроцессинг текста для ML.

Нормализация и токенизация вынесены отдельно, чтобы использовать одинаковую
подготовку и при обучении, и при инференсе.
"""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

# Частая маскировка символов (обход фильтров): приводим к обычным буквам.
_LEET = str.maketrans({"0": "о", "3": "е", "4": "а", "@": "а", "$": "s"})


def normalize_text(text: str) -> str:
    """Привести текст к нижнему регистру, убрать лишние пробелы и маскировку.

    Args:
        text: Исходный текст сообщения.

    Returns:
        Нормализованную строку.
    """
    lowered = text.lower().translate(_LEET)
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def tokenize(text: str) -> list[str]:
    """Разбить нормализованный текст на слова-токены."""
    return _TOKEN_RE.findall(normalize_text(text))
