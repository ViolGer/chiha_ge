from django.urls import path

from . import views
from .course import course_page

urlpatterns = [
    # Главная страница сайта — курс «Тропа к грузинскому» (georgian_trail.html)
    path("", course_page, name="course"),
    # Тренажёр слов
    path("trener/", views.home, name="home"),
    path("igra/predlozheniya/", views.sentence_game, name="sentence_game"),
    path("igra/pary/", views.pairs_game, name="pairs_game"),
    path("igra/kartochki/", views.flashcard_game, name="flashcard_game"),
    path("igra/bukvy/", views.letters_game, name="letters_game"),
    # Словарь и разговорник
    path("slovar/", views.dictionary, name="dictionary"),
    path("api/slovar/", views.api_dictionary, name="api_dictionary"),
    path("api/frazy/", views.api_phrases, name="api_phrases"),
    # Озвучка грузинских слов (заранее сгенерированные файлы)
    path("ozvuchka/", views.audio, name="audio"),
    # JSON API used by the game front-ends
    path("api/predlozhenie/", views.api_sentence, name="api_sentence"),
    path("api/podskazka/", views.api_word_hint, name="api_word_hint"),
    path("api/pary/", views.api_pairs, name="api_pairs"),
    path("api/kartochka/", views.api_flashcard, name="api_flashcard"),
    path("api/bukva/", views.api_letter, name="api_letter"),
    path("api/ochki/", views.api_submit_score, name="api_submit_score"),
]
