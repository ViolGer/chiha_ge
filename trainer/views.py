import json
import random

from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .game_data import LETTERS
from .models import GameResult, Sentence, Word


def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


GAME_LABELS = dict(GameResult.GAME_CHOICES)


def home(request):
    session_key = _ensure_session(request)
    results = GameResult.objects.filter(session_key=session_key)

    totals = results.aggregate(total_score=Sum("score"), total_max=Sum("max_score"))
    total_score = totals["total_score"] or 0
    total_max = totals["total_max"] or 0

    per_game = []
    for code, label in GameResult.GAME_CHOICES:
        qs = results.filter(game_type=code)
        agg = qs.aggregate(s=Sum("score"), m=Sum("max_score"))
        best = qs.order_by("-score").first()
        per_game.append(
            {
                "code": code,
                "label": label,
                "played": qs.count(),
                "total_score": agg["s"] or 0,
                "total_max": agg["m"] or 0,
                "best_score": best.score if best else 0,
                "best_max": best.max_score if best else 0,
            }
        )

    context = {
        "word_count": Word.objects.count(),
        "sentence_count": Sentence.objects.count(),
        "total_score": total_score,
        "total_max": total_max,
        "games_played": results.count(),
        "per_game": per_game,
    }
    return render(request, "trainer/home.html", context)


def sentence_game(request):
    return render(request, "trainer/sentence_game.html")


def pairs_game(request):
    return render(request, "trainer/pairs_game.html")


def flashcard_game(request):
    return render(request, "trainer/flashcard_game.html")


def letters_game(request):
    return render(request, "trainer/letters_game.html", {"letters_total": len(LETTERS)})


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------


@require_GET
def api_sentence(request):
    count = Sentence.objects.count()
    if not count:
        return JsonResponse({"error": "no sentences"}, status=404)
    s = Sentence.objects.all()[random.randint(0, count - 1)]
    direction = random.choice(["ru2ka", "ka2ru"])

    if direction == "ru2ka":
        prompt_text = s.ru
        prompt_lang = "ru"
        target_words = s.ka.split()
    else:
        prompt_text = s.ka
        prompt_lang = "ka"
        target_words = s.ru.split()

    shuffled = target_words[:]
    random.shuffle(shuffled)
    # Guarantee the shuffle actually differs from the answer when possible
    if shuffled == target_words and len(target_words) > 1:
        shuffled[0], shuffled[1] = shuffled[1], shuffled[0]

    return JsonResponse(
        {
            "id": s.id,
            "direction": direction,
            "prompt_text": prompt_text,
            "prompt_lang": prompt_lang,
            "prompt_words": prompt_text.split(),
            "shuffled_words": shuffled,
            "answer_words": target_words,
            "transcription": s.transcription,
            "ru": s.ru,
            "ka": s.ka,
        }
    )


@require_GET
def api_pairs(request):
    words = list(Word.objects.order_by("?")[:6])
    data = [{"id": w.id, "ka": w.ka, "ru": w.ru} for w in words]
    return JsonResponse({"pairs": data})


@require_GET
def api_flashcard(request):
    pool = list(Word.objects.exclude(emoji="").order_by("?")[:4])
    if len(pool) < 4:
        return JsonResponse({"error": "not enough emoji words"}, status=404)
    correct = pool[0]
    options = pool[:]
    random.shuffle(options)
    return JsonResponse(
        {
            "emoji": correct.emoji,
            "correct_id": correct.id,
            "options": [{"id": w.id, "ru": w.ru} for w in options],
        }
    )


@require_GET
def api_letter(request):
    correct = random.choice(LETTERS)
    distractor_pool = [l for l in LETTERS if l[0] != correct[0]]
    distractors = random.sample(distractor_pool, 3)
    options = [correct] + distractors
    random.shuffle(options)
    return JsonResponse(
        {
            "letter": correct[0],
            "correct_label": correct[1],
            "options": [{"label": lbl} for (_, lbl) in options],
        }
    )


@require_GET
def api_word_hint(request):
    raw = (request.GET.get("w") or "").strip()
    # strip common trailing punctuation from a sentence token before lookup
    cleaned = raw.strip(".,!?;:—…\"'()")
    # Exact match only — many sentence words are inflected forms of the
    # dictionary entry, so this intentionally won't cover every word;
    # the UI shows "перевод не найден" rather than guess wrong.
    w = Word.objects.filter(ka=cleaned).first()
    if not w:
        return JsonResponse({"found": False})
    return JsonResponse({"found": True, "ru": w.ru, "transcription": w.transcription})


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

    GameResult.objects.create(
        session_key=session_key, game_type=game_type, score=score, max_score=max_score
    )

    totals = GameResult.objects.filter(session_key=session_key).aggregate(
        total_score=Sum("score"), total_max=Sum("max_score")
    )
    return JsonResponse(
        {
            "ok": True,
            "lesson_score": score,
            "lesson_max": max_score,
            "total_score": totals["total_score"] or 0,
            "total_max": totals["total_max"] or 0,
        }
    )
