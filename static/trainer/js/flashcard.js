(function () {
  const LESSON_LEN = 10;
  let idx = 0;
  let score = 0;
  let locked = false;

  const emojiEl = document.getElementById('flashEmoji');
  const optionsEl = document.getElementById('optionsGrid');
  const progressEl = document.getElementById('progress');
  const lessonScoreEl = document.getElementById('lessonScore');
  const gameArea = document.getElementById('gameArea');
  const summary = document.getElementById('summary');
  const feedback = document.getElementById('feedback');

  function setHud() {
    progressEl.textContent = `Карточка ${Math.min(idx + 1, LESSON_LEN)} из ${LESSON_LEN}`;
    lessonScoreEl.textContent = `Очки: ${score}`;
  }

  function loadRound() {
    locked = false;
    fetch('/api/kartochka/')
      .then((r) => r.json())
      .then((data) => {
        emojiEl.textContent = data.emoji;
        optionsEl.innerHTML = '';
        feedback.textContent = '';
        feedback.className = 'feedback-line';
        data.options.forEach((opt) => {
          const btn = document.createElement('button');
          btn.className = 'option-btn';
          btn.innerHTML =
            `<span class="opt-ka ka-text">${opt.ka}</span>` +
            `<span class="opt-tr">${opt.transcription}</span>`;
          btn.addEventListener('click', () => choose(btn, opt.id, data.correct_id, data.correct_ru));
          optionsEl.appendChild(btn);
        });
      });
  }

  function choose(btn, chosenId, correctId, correctRu) {
    if (locked) return;
    locked = true;
    const ok = chosenId === correctId;
    if (ok) {
      score += 1;
      btn.classList.add('correct');
      feedback.textContent = `✅ Верно — это «${correctRu}»`;
      feedback.className = 'feedback-line good';
    } else {
      btn.classList.add('incorrect');
      feedback.textContent = `❌ Это «${correctRu}»`;
      feedback.className = 'feedback-line bad';
    }
    // reveal correct one too
    [...optionsEl.children].forEach((b) => {
      b.disabled = true;
    });
    setHud();
    setTimeout(() => {
      idx += 1;
      if (idx >= LESSON_LEN) {
        finish();
      } else {
        loadRound();
        setHud();
      }
    }, 700);
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
