from django.contrib import admin

from .models import GameResult, Sentence, Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("ka", "transcription", "ru", "pos", "theme", "emoji")
    list_filter = ("pos", "theme")
    search_fields = ("ka", "ru", "transcription")


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    list_display = ("ka", "ru")
    search_fields = ("ka", "ru")


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ("session_key", "game_type", "score", "max_score", "played_at")
    list_filter = ("game_type",)
