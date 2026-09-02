(function () {
  const PAGE = 120; // сколько слов показываем за раз

  const searchEl = document.getElementById('search');
  const themeEl = document.getElementById('themeSelect');
  const counterEl = document.getElementById('counter');
  const listEl = document.getElementById('wordList');
  const moreRow = document.getElementById('moreRow');
  const moreBtn = document.getElementById('moreBtn');
  const paneWords = document.getElementById('paneWords');
  const panePhrases = document.getElementById('panePhrases');
  const tabWords = document.getElementById('tabWords');
  const tabPhrases = document.getElementById('tabPhrases');

  let words = [];
  let sections = [];
  let shown = PAGE;
  let mode = 'words';

  // ---- поиск: без учёта регистра, по грузинскому, русскому и транскрипции ----
  function norm(s) {
    // Транскрипция в разных источниках пишется чуть по-разному: «цькъали»,
    // «цкъали» и «цкали». Для поиска приводим к общему виду, иначе
    // человек не найдёт слово, набрав его так, как запомнил.
    return (s || '').toLowerCase().replace(/ё/g, 'е').replace(/[’'ъь]/g, '');
  }
  function matches(hay, needle) {
    return norm(hay).indexOf(needle) !== -1;
  }

  // Насколько хорошо запись отвечает запросу: 0 — точное совпадение,
  // дальше по убыванию. Без этого на «хлеб» первым выпадает «переезжать»,
  // внутри транскрипции которого случайно нашлось «хлеб».
  function rank(w, q) {
    const ru = norm(w.ru), ka = norm(w.ka), tr = norm(w.tr);
    if (ru === q || ka === q || tr === q) return 0;
    if (ru.indexOf(q) === 0 || ka.indexOf(q) === 0 || tr.indexOf(q) === 0) return 1;
    if (ru.split(/[\s,;/()]+/).some((part) => part.indexOf(q) === 0)) return 2;
    if (ru.indexOf(q) !== -1) return 3;
    if (ka.indexOf(q) !== -1 || tr.indexOf(q) !== -1) return 4;
    return -1;
  }

  // ---- озвучка: тот же файл, что и на странице курса ----
  let currentAudio = null;
  function sayButton(text) {
    const btn = document.createElement('button');
    btn.className = 'say-btn';
    btn.type = 'button';
    btn.textContent = '🔊';
    btn.title = 'Послушать';
    btn.setAttribute('aria-label', 'Послушать: ' + text);
    btn.addEventListener('click', () => play(btn, text));
    return btn;
  }
  function play(btn, text) {
    if (currentAudio) {
      try { currentAudio.pause(); } catch (e) { /* уже остановлено */ }
    }
    btn.classList.add('playing');
    const audio = new Audio('/ozvuchka/?w=' + encodeURIComponent(text));
    currentAudio = audio;
    const done = () => btn.classList.remove('playing');
    audio.addEventListener('ended', done);
    audio.addEventListener('error', () => { done(); fallback(text); });
    audio.play().catch(() => { done(); fallback(text); });
  }
  function fallback(text) {
    // Файла озвучки нет — пробуем браузерный синтез. В Windows грузинского
    // голоса обычно нет, тогда кнопка просто промолчит.
    if (!('speechSynthesis' in window)) return;
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'ka-GE';
      u.rate = 0.85;
      speechSynthesis.speak(u);
    } catch (e) { /* озвучка необязательна */ }
  }

  function entryRow(ka, tr, ru, meta) {
    const row = document.createElement('div');
    row.className = 'entry';

    const kaSide = document.createElement('div');
    kaSide.className = 'ka-side';
    const kaWord = document.createElement('span');
    kaWord.className = 'ka-word';
    kaWord.textContent = ka;
    kaSide.appendChild(kaWord);
    if (tr) {
      const kaTr = document.createElement('span');
      kaTr.className = 'ka-tr';
      kaTr.textContent = tr;
      kaSide.appendChild(kaTr);
    }

    const ruSide = document.createElement('div');
    ruSide.className = 'ru-side';
    const ruWord = document.createElement('span');
    ruWord.className = 'ru-word';
    ruWord.textContent = ru;
    ruSide.appendChild(ruWord);
    if (meta) {
      const m = document.createElement('span');
      m.className = 'meta';
      m.innerHTML = meta;
      ruSide.appendChild(m);
    }

    row.appendChild(kaSide);
    row.appendChild(ruSide);
    row.appendChild(sayButton(ka));
    return row;
  }

  // ---- вкладка «Слова» ----
  function filteredWords() {
    const q = norm(searchEl.value.trim());
    const theme = themeEl.value;
    const base = theme ? words.filter((w) => w.theme === theme) : words;
    if (!q) return base;
    const scored = [];
    base.forEach((w) => {
      const r = rank(w, q);
      if (r >= 0) scored.push({ w: w, r: r });
    });
    scored.sort((a, b) => a.r - b.r || a.w.ka.localeCompare(b.w.ka));
    return scored.map((x) => x.w);
  }

  function renderWords() {
    const list = filteredWords();
    listEl.innerHTML = '';
    if (!list.length) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'Ничего не нашлось. Попробуй другое слово или сними фильтр по теме.';
      listEl.appendChild(empty);
      moreRow.style.display = 'none';
      counterEl.textContent = 'Найдено: 0';
      return;
    }
    const slice = list.slice(0, shown);
    const frag = document.createDocumentFragment();
    slice.forEach((w) => {
      const meta = (w.emoji ? '<span class="emoji">' + w.emoji + '</span>' : '') + w.theme + ' · ' + w.pos;
      frag.appendChild(entryRow(w.ka, w.tr, w.ru, meta));
    });
    listEl.appendChild(frag);
    counterEl.textContent = 'Найдено: ' + list.length +
      (list.length > slice.length ? ' · показано ' + slice.length : '');
    moreRow.style.display = list.length > slice.length ? 'flex' : 'none';
  }

  // ---- вкладка «Фразы» ----
  function renderPhrases() {
    const q = norm(searchEl.value.trim());
    panePhrases.innerHTML = '';
    let total = 0;
    sections.forEach((section) => {
      const items = section.items.filter((it) =>
        !q || rank({ ru: it.ru, ka: it.ka, tr: it.tr }, q) >= 0);
      if (!items.length) return;
      total += items.length;

      const wrap = document.createElement('section');
      wrap.className = 'phrase-section';
      const h = document.createElement('h2');
      h.textContent = section.title;
      wrap.appendChild(h);
      if (section.note) {
        const note = document.createElement('p');
        note.className = 'note';
        note.textContent = section.note;
        wrap.appendChild(note);
      }
      const box = document.createElement('div');
      box.className = 'entries';
      items.forEach((it) => box.appendChild(entryRow(it.ka, it.tr, it.ru, '')));
      wrap.appendChild(box);
      panePhrases.appendChild(wrap);
    });

    if (!total) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'Среди фраз ничего не нашлось. Поищи это слово на вкладке «Слова».';
      panePhrases.appendChild(empty);
    }
    counterEl.textContent = 'Найдено фраз: ' + total;
  }

  function render() {
    if (mode === 'words') renderWords();
    else renderPhrases();
  }

  function setMode(next) {
    mode = next;
    const isWords = mode === 'words';
    tabWords.setAttribute('aria-selected', isWords ? 'true' : 'false');
    tabPhrases.setAttribute('aria-selected', isWords ? 'false' : 'true');
    paneWords.hidden = !isWords;
    panePhrases.hidden = isWords;
    themeEl.style.display = isWords ? '' : 'none';
    searchEl.placeholder = isWords
      ? 'Поиск по-русски, по-грузински или по транскрипции'
      : 'Поиск по фразам';
    shown = PAGE;
    render();
  }

  searchEl.addEventListener('input', () => { shown = PAGE; render(); });
  themeEl.addEventListener('change', () => { shown = PAGE; render(); });
  moreBtn.addEventListener('click', () => { shown += PAGE * 2; render(); });
  tabWords.addEventListener('click', () => setMode('words'));
  tabPhrases.addEventListener('click', () => setMode('phrases'));

  Promise.all([
    fetch('/api/slovar/').then((r) => r.json()),
    fetch('/api/frazy/').then((r) => r.json()),
  ])
    .then(([dict, phr]) => {
      words = dict.words || [];
      sections = phr.sections || [];
      const themes = [...new Set(words.map((w) => w.theme).filter(Boolean))].sort();
      themes.forEach((t) => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        themeEl.appendChild(opt);
      });
      render();
    })
    .catch(() => {
      counterEl.textContent = 'Не удалось загрузить словарь. Обнови страницу.';
    });
})();
