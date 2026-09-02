# -*- coding: utf-8 -*-
"""Главная страница сайта — курс «Тропа к грузинскому».

Файл `trainer/site/georgian_trail.html` — это ровно тот же HTML, что публиковался
как Claude Artifact. Он НЕ шаблон Django: мы его не обрабатываем шаблонизатором,
а отдаём как есть, только:

  1) оборачиваем в полноценный HTML-документ (в артефакте <!doctype>, <head> и
     <body> добавлялись автоматически, поэтому в самом файле их нет);
  2) дописываем ссылку на тренажёр (в меню + плавающая кнопка);
  3) чиним сохранение прогресса: в артефакте прогресс сохранялся через
     механизм Claude (window.claude), которого на своём хостинге нет, —
     переключаем его на localStorage браузера.

Все три правки — аккуратные точечные замены по тексту. Если файл когда-нибудь
поменяется и «якорь» для замены не найдётся, страница всё равно откроется,
просто без соответствующей мелочи. Чтобы обновить курс, достаточно положить
новый georgian_trail.html на то же место — трогать код не нужно.
"""

from pathlib import Path

from django.http import HttpResponse

COURSE_FILE = Path(__file__).resolve().parent / "site" / "georgian_trail.html"

# Адрес главной страницы тренажёра (см. trainer/urls.py)
TRAINER_URL = "/trener/"

# Ключ, под которым прогресс курса хранится в браузере
STORAGE_KEY = "georgian_trail_progress_v1"


DOC_TOP = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#x1F410;</text></svg>">
</head>
<body>
"""

DOC_BOTTOM = """
</body>
</html>
"""

# --- 1. ссылка на тренажёр в верхнем меню ----------------------------------
NAV_ANCHOR = '<div class="topnav-links" id="topnavLinks">'
NAV_PATCH = NAV_ANCHOR + (
    '\n      <a class="topnav-trainer" href="%s">\U0001F3AE Тренажёр слов</a>' % TRAINER_URL
)

# --- 2. плавающая кнопка + её стили ----------------------------------------
FLOATING_BUTTON = """
<style>
  .topnav-links a.topnav-trainer {
    color: var(--accent); border: 1.5px solid var(--accent); padding: 5px 12px;
  }
  .topnav-links a.topnav-trainer:hover,
  .topnav-links a.topnav-trainer.active {
    background: var(--accent); color: var(--accent-ink);
  }
  .trainer-fab {
    position: fixed; z-index: 998;
    right: max(16px, env(safe-area-inset-right));
    bottom: max(16px, env(safe-area-inset-bottom));
    display: inline-flex; align-items: center; gap: 8px;
    padding: 12px 18px; border-radius: 999px;
    background: var(--accent); color: var(--accent-ink);
    font-family: "Baloo 2", "PT Sans", sans-serif; font-weight: 700; font-size: 15px;
    text-decoration: none; box-shadow: 0 12px 28px -10px rgba(0, 0, 0, .45);
    transition: transform .15s ease;
  }
  .trainer-fab:hover { transform: translateY(-2px); }
  @media (max-width: 480px) { .trainer-fab { padding: 11px 15px; font-size: 14px; } }
</style>
<a class="trainer-fab" href="%s">\U0001F3AE <span>Тренажёр слов</span></a>
""" % TRAINER_URL

# --- 3. прогресс: читаем из localStorage при загрузке -----------------------
SEED_ANCHOR = "var __SEED__ = {};"
SEED_PATCH = (
    'var __SEED__ = (function () { try { return JSON.parse('
    'localStorage.getItem("%s")) || {}; } catch (e) { return {}; } })();' % STORAGE_KEY
)

# --- 3b. прогресс: пишем в localStorage при изменении -----------------------
SAVE_ANCHOR = "  function doSave() {"
SAVE_PATCH = """  function doSave() {
    try {
      localStorage.setItem("%s", JSON.stringify(PROGRESS));
      saveState = "saved";
    } catch (e) {
      saveState = "local";
    }
    renderProgressSummary();
    return;
""" % STORAGE_KEY


def _patch(html, anchor, replacement):
    """Заменить якорь, если он есть. Нет якоря — оставляем как было."""
    if anchor in html:
        return html.replace(anchor, replacement, 1)
    return html


def build_course_page():
    html = COURSE_FILE.read_text(encoding="utf-8")

    html = _patch(html, SEED_ANCHOR, SEED_PATCH)
    html = _patch(html, SAVE_ANCHOR, SAVE_PATCH)
    html = _patch(html, NAV_ANCHOR, NAV_PATCH)

    if "<html" in html[:2000].lower():
        # файл уже полноценный HTML-документ — вставляем кнопку перед </body>
        if "</body>" in html:
            return html.replace("</body>", FLOATING_BUTTON + "\n</body>", 1)
        return html + FLOATING_BUTTON

    return DOC_TOP + html + FLOATING_BUTTON + DOC_BOTTOM


# Страница большая (~600 КБ) и не меняется во время работы сервера,
# поэтому собираем её один раз и держим в памяти.
_cached_page = None


def course_page(request):
    global _cached_page
    if _cached_page is None:
        _cached_page = build_course_page()
    return HttpResponse(_cached_page)
