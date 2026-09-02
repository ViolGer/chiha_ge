(function () {
  const LESSON_LEN = 10;
  let idx = 0;
  let score = 0;
  let locked = false;

  const emojiEl = document.getElementById('flashEmoji');
  const promptRuEl = document.getElementById('flashWord');
  const optionsEl = document.getElementById('optionsGrid');
  const progressEl = document.getElementById('progress');
  const lessonScoreEl = document.getElementById('lessonScore');
  const gameArea = document.getElementById('gameArea');
  const summary = document.getElementById('summary');
  const feedback = document.getElementById('feedback');

  // Мелкие элементы шапки/подписей могут отсутствовать в старом шаблоне —
  // из-за этого раньше игра молча падала и не рисовала варианты ответа.
  // Поэтому все обращения к необязательным элементам идут через setText.
  function setText(el, text) {
    if (el) el.textContent = text;
  }

  function setHud() {
    setText(progressEl, `Карточка ${Math.min(idx + 1, LESSON_LEN)} из ${LESSON_LEN}`);
    setText(lessonScoreEl, `Очки: ${score}`);
  }

  function showError(text) {
    if (!optionsEl) return;
    optionsEl.innerHTML = '<div class="flash-error">' + text + '</div>';
  }

  function loadRound() {
    locked = false;
    fetch('/api/kartochka/')
      .then((r) => r.json())
      .then((data) => {
        if (!data || !data.options || !data.options.length) {
          setText(emojiEl, '😕');
          showError('Не удалось загрузить карточку. Проверь, что база слов загружена: <code>manage.py load_vocab</code>');
          return;
        }
        setText(emojiEl, data.emoji || '❓');
        // Эмодзи бывает неоднозначным (🎁 — «подарок»? «коробка»?), поэтому
        // под ним показываем русское слово: задача — вспомнить грузинское.
        setText(promptRuEl, data.correct_ru || '');
        optionsEl.innerHTML = '';
        setText(feedback, '');
        if (feedback) feedback.className = 'feedback-line';
        data.options.forEach((opt) => {
          const btn = document.createElement('button');
          btn.className = 'option-btn';
          const ka = document.createElement('span');
          ka.className = 'opt-ka ka-text';
          ka.textContent = opt.ka || opt.ru || '';
          btn.appendChild(ka);
          if (opt.transcription) {
            const tr = document.createElement('span');
            tr.className = 'opt-tr';
            tr.textContent = opt.transcription;
            btn.appendChild(tr);
          }
          btn.addEventListener('click', () => choose(btn, opt, data));
          optionsEl.appendChild(btn);
        });
      })
      .catch(() => {
        setText(emojiEl, '😕');
        showError('Сервер не ответил. Открыт ли он на этой вкладке?');
      });
  }

  function choose(btn, opt, data) {
    if (locked) return;
    locked = true;
    const ok = opt.id === data.correct_id;
    if (ok) {
      score += 1;
      btn.classList.add('correct');
      setText(feedback, '✅ Верно');
      if (feedback) feedback.className = 'feedback-line good';
    } else {
      btn.classList.add('incorrect');
      setText(feedback, `❌ Правильно: ${correctLabel(data)}`);
      if (feedback) feedback.className = 'feedback-line bad';
    }
    // Подсветить верный вариант, чтобы было видно, что именно было ответом
    [...optionsEl.children].forEach((b) => {
      b.disabled = true;
    });
    const correctBtn = [...optionsEl.children][indexOfCorrect(data)];
    if (correctBtn) correctBtn.classList.add('correct');
    setHud();
    setTimeout(() => {
      idx += 1;
      if (idx >= LESSON_LEN) {
        finish();
      } else {
        loadRound();
        setHud();
      }
    }, ok ? 700 : 1400);
  }

  function indexOfCorrect(data) {
    return data.options.findIndex((o) => o.id === data.correct_id);
  }

  function correctLabel(data) {
    const o = data.options[indexOfCorrect(data)];
    if (!o) return '';
    return o.transcription ? `${o.ka} (${o.transcription})` : o.ka || o.ru || '';
  }

  function finish() {
    fetch('/api/ochki/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
      body: JSON.stringify({ game_type: 'flashcard', score: score, max_score: LESSON_LEN }),
    })
      .then((r) => r.json())
      .then((data) => {
        gameArea.style.display = 'none';
        summary.style.display = 'block';
        summary.innerHTML = `
          <div class="summary-box">
            <div class="big-num">${score} / ${LESSON_LEN}</div>
            <p>Правильных ответов. Всего накоплено очков: <b>${data.total_score}</b></p>
            <div class="actions-row" style="justify-content:center">
              <button class="check-btn" onclick="location.reload()">Играть ещё раз</button>
              <a class="next-btn" style="text-decoration:none;display:inline-block" href="/trener/">К играм</a>
            </div>
          </div>`;
      });
  }

  setHud();
  loadRound();
})();
