(function () {
  const LESSON_LEN = Math.min(15, window.LETTERS_TOTAL || 15);
  let idx = 0;
  let score = 0;
  let locked = false;

  const letterEl = document.getElementById('flashLetter');
  const optionsEl = document.getElementById('optionsGrid');
  const progressEl = document.getElementById('progress');
  const lessonScoreEl = document.getElementById('lessonScore');
  const gameArea = document.getElementById('gameArea');
  const summary = document.getElementById('summary');

  function setHud() {
    progressEl.textContent = `Буква ${Math.min(idx + 1, LESSON_LEN)} из ${LESSON_LEN}`;
    lessonScoreEl.textContent = `Очки: ${score}`;
  }

  function loadRound() {
    locked = false;
    fetch('/api/bukva/')
      .then((r) => r.json())
      .then((data) => {
        letterEl.textContent = data.letter;
        optionsEl.innerHTML = '';
        data.options.forEach((opt) => {
          const btn = document.createElement('button');
          btn.className = 'option-btn';
          btn.textContent = opt.label;
          btn.addEventListener('click', () => choose(btn, opt.label, data.correct_label));
          optionsEl.appendChild(btn);
        });
      });
  }

  function choose(btn, chosenLabel, correctLabel) {
    if (locked) return;
    locked = true;
    const ok = chosenLabel === correctLabel;
    if (ok) {
      score += 1;
      btn.classList.add('correct');
    } else {
      btn.classList.add('incorrect');
    }
    [...optionsEl.children].forEach((b) => {
      b.disabled = true;
      if (b.textContent === correctLabel) b.classList.add('correct');
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
      body: JSON.stringify({ game_type: 'letters', score: score, max_score: LESSON_LEN }),
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
