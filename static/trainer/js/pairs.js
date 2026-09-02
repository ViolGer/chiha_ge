(function () {
  const DURATION = 120; // 2 minutes
  let timeLeft = DURATION;
  let score = 0;
  let offered = 0;
  let timerId = null;
  let selected = null; // {side, id, el}
  let solvedIds = new Set();

  const leftCol = document.getElementById('leftCol');
  const rightCol = document.getElementById('rightCol');
  const timerEl = document.getElementById('timer');
  const scoreEl = document.getElementById('pairScore');
  const gameArea = document.getElementById('gameArea');
  const summary = document.getElementById('summary');

  function fmtTime(s) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, '0')}`;
  }

  function updateHud() {
    timerEl.textContent = fmtTime(timeLeft);
    timerEl.classList.toggle('low', timeLeft <= 20);
    scoreEl.textContent = `Пар собрано: ${score}`;
  }

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function loadRound() {
    fetch('/api/pary/')
      .then((r) => r.json())
      .then((data) => {
        offered += data.pairs.length;
        renderRound(data.pairs);
      });
  }

  function renderRound(pairs) {
    leftCol.innerHTML = '';
    rightCol.innerHTML = '';
    selected = null;
    solvedIds = new Set();
    const rightShuffled = shuffle(pairs);
    pairs.forEach((p) => {
      const tile = makeTile(p.ka, p.id, 'left');
      leftCol.appendChild(tile);
    });
    rightShuffled.forEach((p) => {
      const tile = makeTile(p.ru, p.id, 'right');
      rightCol.appendChild(tile);
    });
  }

  function makeTile(text, id, side) {
    const div = document.createElement('div');
    div.className = 'pair-tile';
    div.textContent = text;
    div.dataset.id = id;
    div.dataset.side = side;
    div.addEventListener('click', () => onTileClick(div, id, side));
    return div;
  }

  function onTileClick(el, id, side) {
    if (el.classList.contains('solved') || !timerId) return;
    if (selected && selected.side === side) {
      selected.el.classList.remove('selected');
      selected = { el, id, side };
      el.classList.add('selected');
      return;
    }
    if (!selected) {
      selected = { el, id, side };
      el.classList.add('selected');
      return;
    }
    // different side clicked -> check match
    if (selected.id === id) {
      el.classList.add('solved');
      selected.el.classList.add('solved');
      score += 1;
      updateHud();
      solvedIds.add(id);
      selected = null;
      const remaining = leftCol.querySelectorAll('.pair-tile:not(.solved)');
      if (remaining.length === 0) {
        loadRound();
      }
    } else {
      el.classList.add('wrong');
      selected.el.classList.add('wrong');
      setTimeout(() => {
        el.classList.remove('wrong', 'selected');
        selected.el.classList.remove('wrong', 'selected');
        selected = null;
      }, 400);
    }
  }

  function startTimer() {
    timerId = setInterval(() => {
      timeLeft -= 1;
      updateHud();
      if (timeLeft <= 0) {
        clearInterval(timerId);
        timerId = null;
        finish();
      }
    }, 1000);
  }

  function finish() {
    fetch('/api/ochki/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
      body: JSON.stringify({ game_type: 'pairs', score: score, max_score: Math.max(offered, score) }),
    })
      .then((r) => r.json())
      .then((data) => {
        gameArea.style.display = 'none';
        summary.style.display = 'block';
        summary.innerHTML = `
          <div class="summary-box">
            <div class="big-num">${score}</div>
            <p>Пар собрано за 2 минуты. Всего накоплено очков: <b>${data.total_score}</b></p>
            <div class="actions-row" style="justify-content:center">
              <button class="check-btn" onclick="location.reload()">Играть ещё раз</button>
              <a class="next-btn" style="text-decoration:none;display:inline-block" href="/trener/">К играм</a>
            </div>
          </div>`;
      });
  }

  updateHud();
  loadRound();
  startTimer();
})();
