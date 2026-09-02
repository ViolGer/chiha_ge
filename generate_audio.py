# -*- coding: utf-8 -*-
"""Генерация озвучки грузинских слов для сайта.

Зачем: браузерный синтез речи для грузинского работает не везде — в Windows
голоса ka-GE в системе обычно нет, и кнопка «послушать» молчит. Поэтому
произношение генерируется заранее — тем же бесплатным edge-tts и тем же
голосом, что в Telegram-боте, — и раздаётся сайтом как обычные mp3.

Запуск (из папки проекта):

    venv\\Scripts\\python.exe -m pip install edge-tts
    venv\\Scripts\\python.exe generate_audio.py

По умолчанию озвучивается всё грузинское со страницы курса и все фразы
разговорника — около 380 фрагментов, несколько минут. Дополнительно:

    python generate_audio.py --words       # + все слова словаря (~1900, дольше)
    python generate_audio.py --sentences   # + 160 учебных фраз
    python generate_audio.py --all         # всё сразу

Скрипт идемпотентный: уже готовые файлы пропускаются, так что его можно
запускать повторно после того, как в словарь добавились новые слова.
Готовые mp3 лежат в trainer/static/trainer/audio/ — их нужно закоммитить
в git вместе с кодом, тогда озвучка появится и на сервере.
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from trainer.audio import AUDIO_DIR, audio_path, normalize  # noqa: E402

VOICE = "ka-GE-EkaNeural"          # женский; мужской — ka-GE-GiorgiNeural
COURSE_FILE = BASE_DIR / "trainer" / "site" / "georgian_trail.html"
DATA_DIR = BASE_DIR / "trainer" / "data"

# Грузинский текст: буквы мхедрули плюс пробелы и простая пунктуация внутри фразы
GEORGIAN_RUN = re.compile(r"[Ⴀ-ჿ][Ⴀ-ჿ '’!?.,\-]*")


def from_course_page():
    """Все грузинские фразы, которые встречаются на странице курса."""
    if not COURSE_FILE.exists():
        return []
    html = COURSE_FILE.read_text(encoding="utf-8")
    found = (normalize(m) for m in GEORGIAN_RUN.findall(html))
    # Отдельные буквы тоже озвучиваются (в разделе про алфавит
    # каждая буква — своя кнопка), поэтому по длине не отсеиваем.
    return [t for t in found if t]


def from_phrases():
    """Разговорник: все фразы из data/phrases.json."""
    path = DATA_DIR / "phrases.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        sections = json.load(f)
    return [normalize(it["ka"]) for s in sections for it in s.get("items", [])]


def from_words():
    out = []
    for name in ("words.json", "words_extra.json"):
        path = DATA_DIR / name
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            out += [normalize(r["ka"]) for r in json.load(f)]
    return out


def from_sentences():
    path = DATA_DIR / "sentences.txt"
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split("|")
            if parts and parts[0].strip():
                out.append(normalize(parts[0]))
    return out


async def synth(text, path, tries=2):
    import edge_tts

    for attempt in range(tries):
        try:
            await edge_tts.Communicate(text, VOICE).save(str(path))
            return True
        except Exception as exc:                      # noqa: BLE001
            if attempt + 1 == tries:
                print(f"    не получилось: {text} — {exc}")
                return False
            await asyncio.sleep(2)
    return False


async def main():
    parser = argparse.ArgumentParser(description="Озвучка грузинских слов для сайта")
    parser.add_argument("--words", action="store_true", help="плюс все слова словаря")
    parser.add_argument("--sentences", action="store_true", help="плюс учебные фразы")
    parser.add_argument("--all", action="store_true", help="всё сразу")
    args = parser.parse_args()

    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("Нет библиотеки edge-tts. Установи её:")
        print(r"    venv\Scripts\python.exe -m pip install edge-tts")
        return 1

    texts = list(from_course_page()) + from_phrases()
    if args.words or args.all:
        texts += from_words()
    if args.sentences or args.all:
        texts += from_sentences()

    # порядок сохраняем, дубли убираем
    seen, queue = set(), []
    for t in texts:
        if t and t not in seen:
            seen.add(t)
            queue.append(t)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    todo = [t for t in queue if not audio_path(t).exists()]
    print(f"Всего фраз: {len(queue)} | уже озвучено: {len(queue) - len(todo)} | "
          f"осталось: {len(todo)}")
    if not todo:
        print("Всё уже готово.")
        return 0

    done = 0
    for i, text in enumerate(todo, 1):
        ok = await synth(text, audio_path(text))
        done += ok
        if i % 25 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}…")

    print(f"Готово: {done} файлов в {AUDIO_DIR}")
    print("Не забудь закоммитить папку с озвучкой, чтобы она попала на сервер.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
