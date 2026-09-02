(function () {
  const LESSON_LEN = 8;
  let lessonIndex = 0;
  let lessonScore = 0;
  let current = null;
  let placed = []; // array of {word, bankIndex}
  let bankState = []; // array of {word, used}

  const promptBox = document.getElementById('promptBox');
  const answerArea = document.getElementById('answerArea');
  const wordBank = document.getElementById('wordBank');
  const checkBtn = document.getElementById('checkBtn');
  const nextBtn = document.getElementById('nextBtn');
  const feedback = document.getElementById('feedback');
  const progressEl = document.getElementById('progress');
  const lessonScoreEl = document.getElementById('lessonScore');
  const hintBubble = document.getElementById('hintBubble');

  function setProgress() {
    progressEl.textContent = `Предложение ${Math.min(lessonIndex + 1, LESSON_LEN)} из ${LESSON_LEN}`;
    lessonScoreEl.textContent = `Очки: ${lessonScore}`;
  }

  function renderPrompt() {
    promptBox.innerHTML = '';
    promptBox.classList.toggle('static', current.prompt_lang !== 'ka');
    const line = document.createElement('div');
    current.prompt_words.forEach((w) => {
      const span = document.createElement('span');
      span.className = 'word-tok';
      span.textContent = w + ' ';
      if (current.prompt_lang === 'ka') {
        span.addEventListener('click', (e) => showHint(e, w));
      }
      line.appendChild(span);
    });
    promptBox.appendChild(line);
    // Транскрипция всей фразы — только когда задание на грузинском:
    // в обратную сторону она бы выдала порядок слов в ответе.
    if (current.prompt_lang === 'ka' && current.transcription) {
      const tr = document.createElement('div');
      tr.className = 'prompt-tr';
      tr.textContent = current.transcription;
      promptBox.appendChild(tr);
    }
  }

  // Фишка со словом: сверху грузинское слово, под ним транскрипция.
  function makeChip(word, tr, cls) {
    const btn = document.createElement('button');
    btn.className = cls;
    const main = document.createElement('span');
    main.className = 'chip-main';
    main.textContent = word;
    btn.appendChild(main);
    if (tr) {
      const sub = document.createElement('span');
      sub.className = 'chip-tr';
      sub.textContent = tr;
      btn.appendChild(sub);
    }
    return btn;
  }

  function showHint(e, word) {
    fetch(`/api/podskazka/?w=${encodeURIComponent(word)}`)
      .then((r) => r.json())
      .then((data) => {
        hintBubble.style.display = 'block';
        hintBubble.style.left = Math.min(e.clientX, window.innerWidth - 230) + 'px';
        hintBubble.style.top = (e.clientY + 16) + 'px';
        const transcriptionPart = data.transcription ? ` [${data.transcription}]` : '';
        hintBubble.textContent = data.found
          ? `${word}${transcriptionPart} — ${data.ru}`
          : `${word}${transcriptionPart} — перевод не найден в базе`;
        clearTimeout(showHint._t);
        showHint._t = setTimeout(() => (hintBubble.style.display = 'none'), 2500);
      });
  }

  function renderBank() {
    wordBank.innerHTML = '';
    bankState.forEach((item, i) => {
      const btn = makeChip(item.word, item.tr, 'word-chip');
      btn.disabled = item.used;
      btn.style.visibility = item.used ? 'hidden' : 'visible';
      btn.addEventListener('click', () => placeWord(i));
      wordBank.appendChild(btn);
    });
  }

  function renderAnswer() {
    answerArea.innerHTML = '';
    placed.forEach((item, pIdx) => {
      const btn = makeChip(item.word, item.tr, 'word-chip placed');
      btn.addEventListener('click', () => removeWord(pIdx));
      answerArea.appendChild(btn);
    });
  }

  function placeWord(bankIdx) {
    const item = bankState[bankIdx];
    if (item.used) return;
    item.used = true;
    placed.push({ word: item.word, tr: item.tr, bankIndex: bankIdx });
    renderBank();
    renderAnswer();
    checkBtn.disabled = placed.length !== current.answer_words.length;
  }

  function removeWord(pIdx) {
    const item = placed[pIdx];
    bankState[item.bankIndex].used = false;
    placed.splice(pIdx, 1);
    renderBank();
    renderAnswer();
    checkBtn.disabled = placed.length !== current.answer_words.length;
  }

  function loadNext() {
    feedback.textContent = '';
    feedback.className = 'feedback-line';
    checkBtn.style.display = 'inline-block';
    nextBtn.style.display = 'none';
    checkBtn.disabled = true;
    fetch('/api/predlozhenie/')
      .then((r) => r.json())
      .then((data) => {
        current = data;
        placed = [];
        bankState = data.shuffled_words.map((w, i) => ({
          word: w,
          tr: (data.shuffled_tr && data.shuffled_tr[i]) || '',
          used: false,
        }));
        renderPrompt();
        renderBank();
        renderAnswer();
        setProgress();
      });
  }

  checkBtn.addEventListener('click', () => {
    const given = placed.map((p) => p.word).join(' ');
    const answer = current.answer_words.join(' ');
    const ok = given === answer;
    if (ok) {
      lessonScore += 10;
      feedback.textContent = '✅ Верно!';
      feedback.className = 'feedback-line good';
    } else {
      feedback.textContent = `❌ Правильный ответ: ${answer}`;
      feedback.className = 'feedback-line bad';
    }
    setProgress();
    checkBtn.style.display = 'none';
    nextBtn.style.display = 'inline-block';
  });

  nextBtn.addEventListener('click', () => {
    lessonIndex += 1;
    if (lessonIndex >= LESSON_LEN) {
      finishLesson();
    } else {
      loadNext();
    }
  });

  function finishLesson() {
    const maxScore = LESSON_LEN * 10;
    fetch('/api/ochki/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
      body: JSON.stringify({ game_type: 'sentence', score: lessonScore, max_score: maxScore }),
    })
      .then((r) => r.json())
      .then((data) => {
        document.getElementById('gameArea').style.display = 'none';
        const summary = document.getElementById('summary');
        summary.style.display = 'block';
        summary.innerHTML = `
          <div class="summary-box">
            <div class="big-num">${lessonScore} / ${maxScore}</div>
            <p>Очков за урок. Всего накоплено: <b>${data.total_score}</b></p>
            <div class="actions-row" style="justify-content:center">
              <button class="check-btn" onclick="location.reload()">Играть ещё раз</button>
              <a class="next-btn" style="text-decoration:none;display:inline-block" href="/trener/">К играм</a>
            </div>
          </div>`;
      });
  }

  setProgress();
  loadNext();
})();
