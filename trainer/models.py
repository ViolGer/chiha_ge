from django.db import models


class Word(models.Model):
    """One entry from the ~2000-word Georgian vocabulary database."""

    ka = models.CharField("Грузинское слово", max_length=200, unique=True)
    transcription = models.CharField("Транскрипция", max_length=200)
    ru = models.CharField("Перевод", max_length=300)
    pos = models.CharField("Часть речи", max_length=20)
    theme = models.CharField("Тема", max_length=50, db_index=True)
    emoji = models.CharField("Эмодзи", max_length=16, blank=True, default="")

    class Meta:
        ordering = ["ka"]

    def __str__(self):
        return f"{self.ka} — {self.ru}"


class Sentence(models.Model):
    """A short A1-A2 practice sentence used by the sentence-builder game."""

    ka = models.CharField("Грузинское предложение", max_length=300)
    ru = models.CharField("Перевод", max_length=300)
    transcription = models.CharField("Транскрипция", max_length=300)

    def __str__(self):
        return self.ka


class GameResult(models.Model):
    """One completed round of a game, tied to a browser session (no login needed)."""

    GAME_CHOICES = [
        ("sentence", "Составь предложение"),
        ("pairs", "Пары слов"),
        ("flashcard", "Карточки"),
        ("letters", "Буквы"),
    ]

    session_key = models.CharField(max_length=40, db_index=True)
    game_type = models.CharField(max_length=20, choices=GAME_CHOICES)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-played_at"]

    def __str__(self):
        return f"{self.get_game_type_display()}: {self.score}/{self.max_score}"
