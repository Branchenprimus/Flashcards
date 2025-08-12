// Configuration toggle (default simple mode removes learned cards)
// You can change the default here; users can also toggle via the checkbox in the UI.
let REMOVE_ON_GOT_IT_DEFAULT = true;

(function () {
    const section = document.querySelector('section[data-token]');
    if (!section) return;

    const token = section.getAttribute('data-token');
    const deckId = section.getAttribute('data-deck-id');
    const deckTitle = section.getAttribute('data-deck-title');

    const progressEl = document.getElementById('progress');
    const cardEl = document.getElementById('card');
    const faceEl = document.getElementById('card-face');

    const showBtn = document.getElementById('show-btn');
    const gotBtn = document.getElementById('got-btn');
    const againBtn = document.getElementById('again-btn');
    const restartBtn = document.getElementById('restart-btn');
    const toggleRemove = document.getElementById('toggle-remove');

    // Session state
    let cards = [];
    let queue = [];         // holds indices into cards, current card is queue[0]
    let showingAnswer = false;
    let removeOnGotIt = REMOVE_ON_GOT_IT_DEFAULT;

    // Respect UI initial checkbox (default checked)
    if (toggleRemove) removeOnGotIt = toggleRemove.checked;

    // Accessible focus states
    function setButtonsEnabled(isAnswerShown) {
        showBtn.disabled = isAnswerShown || queue.length === 0;
        gotBtn.disabled = !isAnswerShown || queue.length === 0;
        againBtn.disabled = !isAnswerShown || queue.length === 0;
    }

    function renderProgress() {
        const total = cards.length;
        const remaining = queue.length;
        const done = total - remaining;
        const currentIdx = total === 0 || remaining === 0 ? 0 : (done + 1);
        progressEl.textContent = remaining > 0
            ? `Card ${currentIdx} of ${total} — ${remaining} remaining`
            : `Session complete. ${total} / ${total} learned.`;
    }

    function renderCard() {
        if (queue.length === 0) {
            faceEl.textContent = '🎉 All done!';
            setButtonsEnabled(true);
            return;
        }
        const current = cards[queue[0]];
        if (showingAnswer) {
            faceEl.textContent = current.a;
            cardEl.setAttribute('aria-pressed', 'true');
        } else {
            faceEl.textContent = current.q;
            cardEl.setAttribute('aria-pressed', 'false');
        }
        setButtonsEnabled(showingAnswer);
    }

    function flip() {
        if (queue.length === 0) return;
        showingAnswer = !showingAnswer;
        renderCard();
    }

    function grade(result) {
        if (queue.length === 0) return;

        const idx = queue.shift(); // remove current
        if (result === 'again') {
            // Requeue within next 3 positions
            const insertPos = Math.min(3, queue.length);
            queue.splice(insertPos, 0, idx);
        } else if (result === 'got_it') {
            if (!removeOnGotIt) {
                // Move to end instead of removing
                queue.push(idx);
            }
            // else: removed (simple mode)
        }
        showingAnswer = false;
        renderProgress();
        renderCard();
    }

    function restart() {
        if (cards.length === 0) return;
        queue = cards.map((_, i) => i);
        showingAnswer = false;
        renderProgress();
        renderCard();
        showBtn.focus();
    }

    async function loadDeck() {
        const url = `/api/deck?token=${encodeURIComponent(token)}&deck_id=${encodeURIComponent(deckId)}`;
        const res = await fetch(url);
        if (!res.ok) {
            faceEl.textContent = 'Failed to load deck.';
            return;
        }
        const payload = await res.json();
        cards = payload.cards || [];
        queue = cards.map((_, i) => i); // initial order
        renderProgress();
        renderCard();
    }

    // Event wiring
    cardEl.addEventListener('click', () => {
        if (!showBtn.disabled) flip();
    });

    cardEl.addEventListener('keydown', (e) => {
        if (e.code === 'Space' || e.key === ' ') {
            e.preventDefault();
            if (!showBtn.disabled) flip();
        }
    });

    showBtn.addEventListener('click', () => flip());
    gotBtn.addEventListener('click', () => grade('got_it'));
    againBtn.addEventListener('click', () => grade('again'));
    restartBtn.addEventListener('click', () => restart());
    toggleRemove.addEventListener('change', () => {
        removeOnGotIt = toggleRemove.checked;
    });

    // Global keyboard shortcuts
    window.addEventListener('keydown', (e) => {
        if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
        if (e.code === 'Space' || e.key === ' ') {
            e.preventDefault();
            if (!showBtn.disabled) flip();
        } else if (e.key === 'g' || e.key === 'G') {
            if (!gotBtn.disabled) grade('got_it');
        } else if (e.key === 'a' || e.key === 'A') {
            if (!againBtn.disabled) grade('again');
        }
    });

    // Reduced motion: avoid transitions if user prefers
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--shadow', 'none');
    }

    // Kick off
    loadDeck();
})();
