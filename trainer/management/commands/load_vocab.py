import json
from pathlib import Path

from django.core.management.base import BaseCommand

from trainer.models import Word, Sentence

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class Command(BaseCommand):
    help = "Load the Georgian vocabulary, emoji tags and practice sentences into the database."

    def handle(self, *args, **options):
        self._load_words("words.json")
        # Базовые слова, которых не оказалось в основном наборе: приветствия,
        # части суток, страны, «мужчина/женщина» и т.п.
        self._load_words("words_extra.json", label="Extra words")
        self._load_emoji()
        self._load_sentences()

    def _load_words(self, filename, label="Words"):
        path = DATA_DIR / filename
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"{filename} не найден — пропускаю"))
            return
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        created = 0
        for r in rows:
            _, was_created = Word.objects.get_or_create(
                ka=r["ka"],
                defaults={
                    "transcription": r["tr"],
                    "ru": r["ru"],
                    "pos": r["pos"],
                    "theme": r["theme"],
                },
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"{label}: {created} created, {len(rows)} total in file"))

    def _load_emoji(self):
        with open(DATA_DIR / "emoji_words.json", encoding="utf-8") as f:
            rows = json.load(f)
        updated = 0
        for r in rows:
            updated += Word.objects.filter(ka=r["ka"]).update(emoji=r["emoji"])
        self.stdout.write(self.style.SUCCESS(f"Emoji tags applied: {updated}"))

    def _load_sentences(self):
        Sentence.objects.all().delete()
        objs = []
        with open(DATA_DIR / "sentences.txt", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                parts = line.split("|")
                if len(parts) != 3:
                    continue
                ka, ru, tr = [p.strip() for p in parts]
                objs.append(Sentence(ka=ka, ru=ru, transcription=tr))
        Sentence.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(f"Sentences: {len(objs)} loaded"))
