# -*- coding: utf-8 -*-
"""Где лежит озвучка и как называется файл для конкретного слова.

Модуль намеренно не импортирует Django: его же использует скрипт
`generate_audio.py`, который запускается сам по себе, без сервера.
"""

import hashlib
import re
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "static" / "trainer" / "audio"

# Грузинские буквы (мхедрули) — по ним отличаем текст, который нужно озвучивать
GEORGIAN_RE = re.compile(r"[Ⴀ-ჿ]")


def normalize(text):
    """Приводим к одному виду, чтобы «ერთი» и «ერთი » дали один и тот же файл."""
    return " ".join((text or "").split()).strip(" .,!?;:—…\"'()«»")


def slug(text):
    """Имя файла для фразы. Хэш, а не сам текст: грузинские имена файлов
    на разных системах и в git ведут себя по-разному, а хэш безопасен везде."""
    return hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()[:20]


def audio_path(text):
    return AUDIO_DIR / (slug(text) + ".mp3")


def is_georgian(text):
    return bool(GEORGIAN_RE.search(text or ""))
