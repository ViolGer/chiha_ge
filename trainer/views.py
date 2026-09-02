import json
import random

from django.db.models import Sum
from django.http import FileResponse, Http404, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .audio import audio_path, is_georgian
from .game_data import LETTERS
from .models import GameResult, Sentence, Word
from .word_hints import clean_token, lookup as lookup_hint, transliterate


def _tr_for(token, cache):
    """Транскрипция слова: выверенная из словаря, иначе посимвольная."""
    key = clean_token(token)
    if not key:
        return ""
    if key not in cache:
        w = Word.objects.filter(ka=key).first()
        cache[key] = w.transcription if w else transliterate(key)
    return cache[key]


def _is_georgian(text):
    return any("Ⴀ" <= ch <= "ჿ" for ch in text)


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


GAME_LABELS = dict(GameResult.GAME_CHOICES)


def home(request):
    session_key = _ensure_session(request)
    results = GameResult.objects.filter(session_key=session_key)
    totals = results.aggregate(total_score=Sum("score"), total_max=Sum("max_score"))
    per_game = []
    for code, label in GameResult.GAME_CHOICES:
        qs = results.filter(game_type=code)
        agg = qs.aggregate(s=Sum("score"), m=Sum("max_score"))
        best = qs.order_by("-score").first()
        per_game.append({"code": code, "label": label, "played": qs.count(),
                         "total_score": agg["s"] or 0, "total_max": agg["m"] or 0,
                         "best_score": best.score if best else 0,
                         "best_max": best.max_score if best else 0})
    return render(request, "trainer/home.html", {
        "word_count": Word.objects.count(), "sentence_count": Sentence.objects.count(),
        "total_score": totals["total_score"] or 0, "total_max": totals["total_max"] or 0,
        "games_played": results.count(), "per_game": per_game})


def sentence_game(request):
    return render(request, "trainer/sentence_game.html")


def pairs_game(request):
    return render(request, "trainer/pairs_game.html")


def flashcard_game(request):
    return render(request, "trainer/flashcard_game.html")


def letters_game(request):
    return render(request, "trainer/letters_game.html", {"letters_total": len(LETTERS)})


@require_GET
def api_sentence(request):
    count = Sentence.objects.count()
    if not count:
        return JsonResponse({"error": "no sentences"}, status=404)
    s = Sentence.objects.all()[random.randint(0, count - 1)]
    direction = random.choice(["ru2ka", "ka2ru"])
    if direction == "ru2ka":
        prompt_text, prompt_lang, target_words = s.ru, "ru", s.ka.split()
    else:
        prompt_text, prompt_lang, target_words = s.ka, "ka", s.ru.split()
    shuffled = target_words[:]
    random.shuffle(shuffled)
    if shuffled == target_words and len(target_words) > 1:
        shuffled[0], shuffled[1] = shuffled[1], shuffled[0]
    # Транскрипция для грузинских слов: под фишками и под словами задания,
    # чтобы было понятно, как читается, без клика по каждому слову.
    cache = {}
    prompt_words = prompt_text.split()
    prompt_tr = [_tr_for(w, cache) if _is_georgian(w) else "" for w in prompt_words]
    shuffled_tr = [_tr_for(w, cache) if _is_georgian(w) else "" for w in shuffled]

    return JsonResponse({"id": s.id, "direction": direction, "prompt_text": prompt_text,
                         "prompt_lang": prompt_lang, "prompt_words": prompt_words,
                         "prompt_tr": prompt_tr,
                         "shuffled_words": shuffled, "shuffled_tr": shuffled_tr,
                         "answer_words": target_words,
                         "transcription": s.transcription, "ru": s.ru, "ka": s.ka})


@require_GET
def api_pairs(request):
    words = list(Word.objects.order_by("?")[:6])
    return JsonResponse({"pairs": [{"id": w.id, "ka": w.ka, "ru": w.ru,
                                    "transcription": w.transcription} for w in words]})


@require_GET
def api_flashcard(request):
    correct = Word.objects.exclude(emoji="").order_by("?").first()
    if correct is None:
        return JsonResponse({"error": "not enough emoji words"}, status=404)
    # Один и тот же эмодзи стоит у нескольких слов (☕ — и «кофе», и «чашка»,
    # и «кафе»). Если такое слово попадёт в варианты, у карточки окажется два
    # правильных ответа, поэтому слова с тем же эмодзи из вариантов убираем.
    distractors = list(
        Word.objects.exclude(emoji="").exclude(emoji=correct.emoji).order_by("?")[:3]
    )
    if len(distractors) < 3:
        return JsonResponse({"error": "not enough emoji words"}, status=404)
    options = [correct] + distractors
    random.shuffle(options)
    return JsonResponse({"emoji": correct.emoji, "correct_id": correct.id,
                         "correct_ru": correct.ru,
                         "options": [{"id": w.id, "ka": w.ka, "transcription": w.transcription}
                                     for w in options]})


def _letter_pair(item):
    """(буква, чтение) — переживает и список кортежей, и список словарей."""
    if isinstance(item, dict):
        return (item.get("ka") or item.get("letter") or "",
                item.get("label") or item.get("ru") or item.get("sound") or "")
    return item[0], item[1]


@require_GET
def api_letter(request):
    pairs = [_letter_pair(x) for x in LETTERS]
    correct = random.choice(pairs)
    distractors = random.sample([p for p in pairs if p[0] != correct[0]], 3)
    options = [correct] + distractors
    random.shuffle(options)
    return JsonResponse({"letter": correct[0], "correct_label": correct[1],
                         "options": [{"label": lbl} for (_, lbl) in options]})


@require_GET
def api_word_hint(request):
    return JsonResponse(
        lookup_hint(request.GET.get("w"), lambda ka: Word.objects.filter(ka=ka).first())
    )


@require_POST
def api_submit_score(request):
    session_key = _ensure_session(request)
    try:
        data = json.loads(request.body.decode("utf-8"))
        game_type = data["game_type"]
        score = int(data["score"])
        max_score = int(data["max_score"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return HttpResponseBadRequest("bad payload")
    if game_type not in GAME_LABELS:
        return HttpResponseBadRequest("unknown game_type")
    GameResult.objects.create(session_key=session_key, game_type=game_type,
                              score=score, max_score=max_score)
    totals = GameResult.objects.filter(session_key=session_key).aggregate(
        total_score=Sum("score"), total_max=Sum("max_score"))
    return JsonResponse({"ok": True, "lesson_score": score, "lesson_max": max_score,
                         "total_score": totals["total_score"] or 0,
                         "total_max": totals["total_max"] or 0})


@require_GET
def audio(request):
    """Озвучка грузинского слова заранее сгенерированным файлом.

    Браузерный синтез речи для грузинского работает не везде: в Windows
    голоса ka-GE обычно нет вообще, и кнопка «послушать» молчит. Поэтому
    произношение заранее генерируется скриптом generate_audio.py (edge-tts,
    тот же голос, что в Telegram-боте) и раздаётся отсюда.

    Файла нет — отвечаем 404, и страница тихо откатывается на браузерный
    синтез: кнопка не ломается, просто может промолчать.
    """
    text = (request.GET.get("w") or "").strip()
    if not text or not is_georgian(text):
        raise Http404("нечего озвучивать")
    path = audio_path(text)
    if not path.exists():
        raise Http404("озвучка не сгенерирована")
    return FileResponse(open(path, "rb"), content_type="audio/mpeg")
