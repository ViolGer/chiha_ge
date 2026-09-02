# -*- coding: utf-8 -*-
"""Личный кабинет: регистрация, вход, выход, профиль и прогресс курса.

Главное, ради чего кабинет вообще нужен: до него прогресс был привязан
к браузеру — очки к сессионной куке, галочки на тропе к localStorage.
Сменил устройство или почистил браузер — начинай сначала. С аккаунтом
и то и другое живёт в базе и одинаково видно с телефона и с ноутбука.
"""

import json
from datetime import timedelta

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import CourseProgress, GameResult


class SignupForm(UserCreationForm):
    """Штатная форма Django, только подписи по-русски и без англоязычных
    подсказок про «letters and digits»."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Имя пользователя"
        self.fields["username"].help_text = "Латиницей или цифрами, без пробелов"
        self.fields["password1"].label = "Пароль"
        self.fields["password1"].help_text = "Минимум 8 символов, не только цифры"
        self.fields["password2"].label = "Пароль ещё раз"
        self.fields["password2"].help_text = ""
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Имя пользователя"
        self.fields["password"].label = "Пароль"
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"


def _adopt_session_results(request, user):
    """Перенести очки, набранные до входа, на аккаунт.

    Вызывать строго ДО auth_login: при входе Django выдаёт новый ключ
    сессии, и старые результаты после этого уже не найти.
    """
    session_key = request.session.session_key
    if not session_key:
        return 0
    return GameResult.objects.filter(
        session_key=session_key, user__isnull=True
    ).update(user=user)


def signup(request):
    if request.user.is_authenticated:
        return redirect("profile")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            moved = _adopt_session_results(request, user)
            auth_login(request, user)
            request.session["just_adopted"] = moved
            return redirect("profile")
    else:
        form = SignupForm()
    return render(request, "trainer/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            moved = _adopt_session_results(request, user)
            auth_login(request, user)
            request.session["just_adopted"] = moved
            return redirect(request.GET.get("next") or "profile")
    else:
        form = LoginForm(request)
    return render(request, "trainer/login.html", {"form": form})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("course")


def _plural(n, forms):
    """Русские окончания: 1 день, 2 дня, 5 дней."""
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return forms[1]
    return forms[2]


def _streak(dates):
    """Сколько дней подряд, считая от сегодня или вчера, были занятия."""
    if not dates:
        return 0
    days = sorted(set(dates), reverse=True)
    today = timezone.localdate()
    if days[0] < today - timedelta(days=1):
        return 0                       # вчера и сегодня пусто — серия прервалась
    streak = 1
    for prev, cur in zip(days, days[1:]):
        if (prev - cur).days == 1:
            streak += 1
        else:
            break
    return streak


@login_required
def profile(request):
    results = GameResult.objects.filter(user=request.user)
    totals = results.aggregate(total_score=Sum("score"), total_max=Sum("max_score"))

    per_game = []
    for code, label in GameResult.GAME_CHOICES:
        qs = results.filter(game_type=code)
        agg = qs.aggregate(s=Sum("score"), m=Sum("max_score"))
        best = qs.order_by("-score").first()
        per_game.append({
            "label": label,
            "played": qs.count(),
            "total_score": agg["s"] or 0,
            "total_max": agg["m"] or 0,
            "best_score": best.score if best else 0,
            "best_max": best.max_score if best else 0,
        })

    progress = CourseProgress.objects.filter(user=request.user).first()
    done_topics = sum(1 for v in (progress.data if progress else {}).values() if v)

    dates = [timezone.localtime(r.played_at).date() for r in results.only("played_at")]

    return render(request, "trainer/profile.html", {
        "total_score": totals["total_score"] or 0,
        "total_max": totals["total_max"] or 0,
        "games_played": results.count(),
        "per_game": [g for g in per_game if g["played"]],
        "all_games": per_game,
        "done_topics": done_topics,
        "topics_label": _plural(done_topics, ("тема", "темы", "тем")),
        "streak": _streak(dates),
        "streak_label": _plural(_streak(dates), ("день", "дня", "дней")),
        "days_total": len(set(dates)),
        "days_label": _plural(len(set(dates)), ("день", "дня", "дней")),
        "adopted": request.session.pop("just_adopted", 0),
    })


# ---------------------------------------------------------------------------
# Прогресс курса: страница курса синхронизирует с ним свои галочки
# ---------------------------------------------------------------------------

@require_GET
def api_course_progress(request):
    """Страница курса спрашивает это при каждой загрузке.

    Гостю отвечаем `authenticated: false` — он продолжает жить на localStorage,
    как раньше. Вошедшему отдаём его отметки из базы.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False, "data": {}})
    progress = CourseProgress.objects.filter(user=request.user).first()
    return JsonResponse({
        "authenticated": True,
        "username": request.user.username,
        "data": progress.data if progress else {},
    })


@require_POST
def api_save_course_progress(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False, "saved": False})
    try:
        payload = json.loads(request.body.decode("utf-8"))
        data = payload.get("data")
    except (ValueError, AttributeError):
        return HttpResponseBadRequest("bad payload")
    if not isinstance(data, dict):
        return HttpResponseBadRequest("data must be an object")
    # Отметки — это просто «ключ темы → пройдено». Значения приводим к
    # булевым, чтобы в базу не попало ничего постороннего.
    clean = {str(k)[:100]: bool(v) for k, v in list(data.items())[:500]}
    CourseProgress.objects.update_or_create(user=request.user, defaults={"data": clean})
    return JsonResponse({"authenticated": True, "saved": True, "count": len(clean)})
