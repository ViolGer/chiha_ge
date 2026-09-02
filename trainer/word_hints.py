# -*- coding: utf-8 -*-
"""Подсказка перевода для слова из предложения.

Проблема, которую решает этот модуль: в учебных предложениях слова стоят
в склонённой/спряжённой форме (ვმგზავრობთ, სახლში, პურს), а в словаре они
лежат в словарной форме — точное совпадение находит меньше половины слов.

Порядок поиска, от самого надёжного к наименее:

1. Точное совпадение со словарём (Word) — даём словарный перевод и
   выверенную транскрипцию.
2. Разбор форм из `data/word_forms.json` — вручную выписанные переводы всех
   170 форм, которые встречаются в 160 учебных предложениях, но не совпадают
   со словарной формой. Вместе с п.1 это покрывает предложения целиком.
3. Отсечение частых окончаний (-ში, -ზე, -ს, -დან …) и поиск основы в словаре.
   Такой перевод помечается как приблизительный — честнее, чем выдавать
   догадку за точный перевод.
4. Ничего не нашли — отдаём только транскрипцию (она строится посимвольно
   и работает для любого слова).
"""

import json
from pathlib import Path

# Посимвольная транскрипция. Намеренно продублирована здесь, а не берётся из
# game_data: модуль должен работать в любой версии проекта, в том числе там,
# где в game_data ещё нет функции transliterate.
CHAR_MAP = {
    "ა": "а", "ბ": "б", "გ": "г", "დ": "д", "ე": "е", "ვ": "в", "ზ": "з",
    "თ": "т", "ი": "и", "კ": "к’", "ლ": "л", "მ": "м", "ნ": "н", "ო": "о",
    "პ": "п’", "ჟ": "ж", "რ": "р", "ს": "с", "ტ": "т’", "უ": "у", "ფ": "п",
    "ქ": "к", "ღ": "гх", "ყ": "къ", "შ": "ш", "ჩ": "ч", "ც": "ц", "ძ": "дз",
    "წ": "ць", "ჭ": "чь", "ხ": "х", "ჯ": "дж", "ჰ": "һ",
}


def transliterate(text):
    """Грузинское слово → русская транскрипция, буква за буквой.

    Работает для любого слова, в том числе для форм, которых нет в словаре.
    Небуквенные символы проходят насквозь.
    """
    return "".join(CHAR_MAP.get(ch, ch) for ch in text)


DATA_DIR = Path(__file__).resolve().parent / "data"
FORMS_FILE = DATA_DIR / "word_forms.json"

# Частые падежные и послеложные окончания. Порядок важен: сначала длинные,
# иначе «-ს» отрежется раньше, чем «-ში».
SUFFIXES = [
    "ისთვის", "ებში", "ებზე", "ებს", "თან", "დან", "ში", "ზე",
    "ით", "ის", "მა", "ს", "თ",
]

_forms = None


def _load_forms():
    global _forms
    if _forms is None:
        try:
            with open(FORMS_FILE, encoding="utf-8") as f:
                _forms = {r["ka"]: r["ru"] for r in json.load(f)}
        except (OSError, ValueError):
            _forms = {}
    return _forms


def clean_token(raw):
    return (raw or "").strip().strip(".,!?;:—…\"'()«»")


def lookup(token, find_word):
    """token — слово из предложения, find_word(ka) -> Word | None.

    Возвращает dict для JSON-ответа.
    """
    token = clean_token(token)
    if not token:
        return {"found": False, "ru": None, "transcription": "", "exact": False}

    w = find_word(token)
    if w is not None:
        return {"found": True, "ru": w.ru, "transcription": w.transcription, "exact": True}

    form_ru = _load_forms().get(token)
    if form_ru:
        return {"found": True, "ru": form_ru, "transcription": transliterate(token), "exact": True}

    for suf in SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            stem = token[: -len(suf)]
            for candidate in (stem, stem + "ი", stem + "ე"):
                w = find_word(candidate)
                if w is not None:
                    return {
                        "found": True,
                        "ru": f"похоже на форму слова «{w.ru}»",
                        "transcription": transliterate(token),
                        "exact": False,
                    }

    return {"found": False, "ru": None, "transcription": transliterate(token), "exact": False}
