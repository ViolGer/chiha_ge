from django.conf import settings
from django.db import models


class Word(models.Model):
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
    ka = models.CharField("Грузинское предложение", max_length=300)
    ru = models.CharField("Перевод", max_length=300)
    transcription = models.CharField("Транскрипция", max_length=300)

    def __str__(self):
        return self.ka


class CourseProgress(models.Model):
    """Отметки «пройдено» на тропе курса.

    Без аккаунта они лежат в localStorage браузера и теряются при смене
    устройства. Для вошедшего пользователя тот же набор отметок хранится
    здесь, и страница курса синхронизируется с сервером.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_progress"
    )
    data = models.JSONField("Отметки на тропе", default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {sum(1 for v in self.data.values() if v)} тем"


class GameResult(models.Model):
    GAME_CHOICES = [
        ("sentence", "Составь предложение"),
        ("pairs", "Пары слов"),
        ("flashcard", "Карточки"),
        ("letters", "Буквы"),
    ]
    # Пока человек не вошёл, результат привязан к сессии браузера. После
    # входа результаты этой сессии переносятся на аккаунт (см. accounts.py).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name="game_results",
    )
    session_key = models.CharField(max_length=40, db_index=True)
    game_type = models.CharField(max_length=20, choices=GAME_CHOICES)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-played_at"]
