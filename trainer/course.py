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

# Ссылка на Telegram-бота. Впиши сюда адрес вида "https://t.me/имя_бота" —
# и на курсе появится кнопка «Бот в Telegram» (в меню и в подвале страницы).
# Пустая строка — кнопки просто не будет.
BOT_URL = ""

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

# --- 1. ссылка на тренажёр (и на бота) в верхнем меню ----------------------
NAV_ANCHOR = '<div class="topnav-links" id="topnavLinks">'
NAV_PATCH = NAV_ANCHOR + (
    '\n      <a class="topnav-trainer" href="%s">\U0001F3AE Тренажёр слов</a>' % TRAINER_URL
) + (
    '\n      <a class="topnav-bot" href="%s" target="_blank" rel="noopener">'
    '\U0001F916 Бот в Telegram</a>' % BOT_URL if BOT_URL else ""
)

# --- 2. что дописываем в конец страницы ------------------------------------
# Стили и скрипт складываются здесь: плавающая кнопка тренажёра, ссылка на
# бота и сворачивание разделов в «гармошку», чтобы главная не была одной
# бесконечной простынёй.
BOTTOM_STYLES = """
<style>
  .topnav-links a.topnav-trainer {
    color: var(--accent); border: 1.5px solid var(--accent); padding: 5px 12px;
  }
  .topnav-links a.topnav-trainer:hover,
  .topnav-links a.topnav-trainer.active {
    background: var(--accent); color: var(--accent-ink);
  }
  .topnav-links a.topnav-bot { color: var(--accent-3, var(--accent)); font-weight: 700; }

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

  /* ---- разделы-«гармошка» ---- */
  .acc-body[hidden] { display: none !important; }
  .acc-toggle {
    width: 100%; display: flex; align-items: center; gap: 14px;
    margin: 10px 0 0; padding: 18px 22px;
    background: var(--surface); border: 1px solid var(--line); border-radius: 20px;
    font-family: "Baloo 2", "PT Sans", sans-serif; font-size: 19px; font-weight: 700;
    color: var(--ink); text-align: left; cursor: pointer;
    transition: border-color .15s ease, transform .15s ease;
  }
  .acc-toggle:hover { border-color: var(--accent); }
  .acc-toggle .acc-caret {
    margin-left: auto; flex-shrink: 0; color: var(--accent);
    font-size: 15px; transition: transform .2s ease;
  }
  .acc-toggle[aria-expanded="true"] .acc-caret { transform: rotate(90deg); }
  .acc-toggle .acc-num {
    flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
    background: var(--surface-2); color: var(--ink-soft);
    font-size: 13px; display: inline-flex; align-items: center; justify-content: center;
  }
  .acc-section > .acc-body { padding-top: 6px; }
  .acc-section .acc-hidden-title { display: none; }
  .acc-actions { display: flex; justify-content: center; margin: 22px 0 4px; }
  .acc-actions button {
    background: none; border: none; color: var(--ink-soft); font: inherit;
    font-size: 14px; cursor: pointer; text-decoration: underline;
  }
  .bot-cta {
    display: block; max-width: 640px; margin: 26px auto 0; padding: 18px 22px;
    background: var(--surface); border: 1px solid var(--line); border-radius: 20px;
    text-decoration: none; color: inherit; text-align: center;
  }
  .bot-cta b { color: var(--accent); }
  .bot-cta span { display: block; color: var(--ink-soft); font-size: 14px; margin-top: 4px; }
  .spk-playing { opacity: .55; }
</style>
"""

FAB_HTML = (
    '<a class="trainer-fab" href="%s">\U0001F3AE <span>Тренажёр слов</span></a>' % TRAINER_URL
)

BOT_CTA_HTML = (
    '<a class="bot-cta" href="%s" target="_blank" rel="noopener">'
    '\U0001F916 <b>Тот же курс в Telegram-боте</b>'
    '<span>Уроки с озвучкой, квизы и повторение по расписанию — прямо в мессенджере</span>'
    '</a>' % BOT_URL
) if BOT_URL else ""

ACCORDION_SCRIPT = """
<script>
(function () {
  // Разделы курса сворачиваются в «гармошку»: страница перестаёт быть
  // бесконечной простынёй, открыт только тот раздел, который читаешь.
  // Разметку не переносим и не удаляем — содержимое раздела просто
  // заворачивается в контейнер, поэтому весь остальной скрипт страницы
  // продолжает находить свои элементы через getElementById.
  var KEY = "georgian_trail_open_sections_v1";
  var sections = [].slice.call(document.querySelectorAll("section[id]"));
  if (!sections.length) return;

  var open = {};
  try { open = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { open = {}; }
  var nothingRemembered = !Object.keys(open).length;

  sections.forEach(function (section, i) {
    var title = section.querySelector("h2");
    if (!title) return;
    section.classList.add("acc-section");

    var body = document.createElement("div");
    body.className = "acc-body";
    while (section.firstChild) body.appendChild(section.firstChild);

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "acc-toggle";
    btn.innerHTML =
      '<span class="acc-num">' + (i + 1) + '</span>' +
      '<span class="acc-title"></span>' +
      '<span class="acc-caret">\\u25B6</span>';
    btn.querySelector(".acc-title").textContent = title.textContent.trim();
    title.classList.add("acc-hidden-title");

    section.appendChild(btn);
    section.appendChild(body);

    // По умолчанию открыт только первый раздел
    var isOpen = nothingRemembered ? i === 0 : !!open[section.id];
    apply(btn, body, isOpen);

    btn.addEventListener("click", function () {
      var willOpen = btn.getAttribute("aria-expanded") !== "true";
      apply(btn, body, willOpen);
      open[section.id] = willOpen;
      try { localStorage.setItem(KEY, JSON.stringify(open)); } catch (e) {}
      if (!willOpen) btn.scrollIntoView({ block: "nearest" });
    });
  });

  function apply(btn, body, isOpen) {
    btn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    body.hidden = !isOpen;
  }

  function openSection(id) {
    var section = document.getElementById(id);
    if (!section || !section.classList.contains("acc-section")) return false;
    var btn = section.querySelector(".acc-toggle");
    var body = section.querySelector(".acc-body");
    if (btn && body && btn.getAttribute("aria-expanded") !== "true") {
      apply(btn, body, true);
      open[id] = true;
      try { localStorage.setItem(KEY, JSON.stringify(open)); } catch (e) {}
    }
    return true;
  }

  // Ссылки в меню и на странице должны разворачивать нужный раздел
  document.addEventListener("click", function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute("href").slice(1);
    if (!id) return;
    if (openSection(id)) {
      setTimeout(function () {
        var el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 30);
    }
  }, true);

  // Кнопка «развернуть всё / свернуть всё»
  var bar = document.createElement("div");
  bar.className = "acc-actions wrap";
  var toggleAll = document.createElement("button");
  toggleAll.type = "button";
  toggleAll.textContent = "Развернуть все разделы";
  bar.appendChild(toggleAll);
  var last = sections[sections.length - 1];
  if (last && last.parentNode) last.parentNode.insertBefore(bar, last.nextSibling);

  toggleAll.addEventListener("click", function () {
    var expand = toggleAll.textContent.indexOf("Развернуть") === 0;
    sections.forEach(function (section) {
      var btn = section.querySelector(".acc-toggle");
      var body = section.querySelector(".acc-body");
      if (!btn || !body) return;
      apply(btn, body, expand);
      open[section.id] = expand;
    });
    try { localStorage.setItem(KEY, JSON.stringify(open)); } catch (e) {}
    toggleAll.textContent = expand ? "Свернуть все разделы" : "Развернуть все разделы";
  });
})();
</script>
"""


AUDIO_SCRIPT = """
<script>
(function () {
  // Кнопка «послушать» на странице курса пользовалась браузерным синтезом речи.
  // В Windows грузинского голоса (ka-GE) в системе обычно нет, и кнопка просто
  // молчала. Теперь сначала пробуем заранее сгенерированный файл с сервера
  // (см. generate_audio.py), и только если его нет — старый синтез.
  var current = null;

  function fallbackSpeak(text) {
    if (!("speechSynthesis" in window)) return;
    try {
      speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = "ka-GE";
      u.rate = 0.85;
      var voices = speechSynthesis.getVoices() || [];
      var v = voices.find(function (x) { return /^ka(-|_)?GE/i.test(x.lang); });
      if (v) u.voice = v;
      speechSynthesis.speak(u);
    } catch (e) { /* озвучка необязательна */ }
  }

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-speak]");
    if (!t) return;
    var text = t.getAttribute("data-speak");
    if (!text) return;
    e.stopPropagation();          // страница не должна включить синтез поверх файла
    if (current) { try { current.pause(); } catch (err) {} }
    t.classList.add("spk-playing");
    var a = new Audio("/ozvuchka/?w=" + encodeURIComponent(text));
    current = a;
    var done = function () { t.classList.remove("spk-playing"); };
    a.addEventListener("ended", done);
    a.addEventListener("error", function () { done(); fallbackSpeak(text); });
    a.play().catch(function () { done(); fallbackSpeak(text); });
  }, true);
})();
</script>
"""

FLOATING_BUTTON = BOTTOM_STYLES + FAB_HTML + ACCORDION_SCRIPT + AUDIO_SCRIPT

# Блок со ссылкой на бота ставим перед подвалом страницы, а не в самый низ
FOOTER_ANCHOR = "<footer>"
FOOTER_PATCH = BOT_CTA_HTML + "\n<footer>"

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
    if BOT_CTA_HTML:
        html = _patch(html, FOOTER_ANCHOR, FOOTER_PATCH)

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
