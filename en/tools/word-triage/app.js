/**
 * Word Triage (English Edition) — Vocabulary Classifier
 *
 * Core logic: load word list → regex parse → card-by-card judgment → export results
 *
 * NOTE: This file is CORE CODE. Skills must NOT modify it.
 *       Regex configuration → modify regex-config.txt only.
 */

// ====== State ======
const state = {
  regex: null,            // Compiled RegExp
  allWords: [],           // [{word, meaning, line}, ...]
  currentIndex: 0,        // Current card position
  familiar: [],           // Words marked familiar
  unfamiliar: [],         // Words marked unfamiliar
  skipped: [],            // Words skipped for later
  history: [],            // Undo stack: [{word, action: 'familiar'|'unfamiliar'|'skip'}]
  flipped: false,
};

// ====== DOM refs ======
const $ = (sel) => document.querySelector(sel);

// ====== English strings ======
const STR = {
  regexLoading: 'Loading...',
  regexLoaded: '✅ Loaded',
  regexNotLoaded: '⚠ Not loaded',
  regexManual: '✅ Manual',
  noMeaning: '(no definition)',
  parseFail: '❌ Failed to parse any words. Check your regex.',
  parseFailRegex: '❌ Please configure the regex first.',
  parseSuccess: '✅ Successfully parsed {n} words',
  parseSuccessSkipped: '✅ Successfully parsed {n} words ({e} lines skipped)',
  reparseHint: 'Please re-select the word list file to apply the new regex.',
  invalidRegex: 'Invalid regex: ',
};

// ====== Regex loading ======
async function loadRegex() {
  const statusEl = $('#regex-status');
  const displayEl = $('#regex-display');
  const manualRow = $('#manual-regex-row');

  try {
    const resp = await fetch('regex-config.txt');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    let text = (await resp.text()).trim();

    // Support "pattern: ..." format or raw regex
    const match = text.match(/^pattern:\s*(.+)$/i);
    const rawRegex = match ? match[1].trim() : text;

    // Remove surrounding quotes if present
    const regexStr = rawRegex.replace(/^["']|["']$/g, '');

    // Validate
    try {
      new RegExp(regexStr);
    } catch (e) {
      throw new Error(`Invalid regex: ${e.message}`);
    }

    state.regex = regexStr;
    statusEl.textContent = STR.regexLoaded;
    statusEl.className = 'status-badge ok';
    displayEl.textContent = regexStr;
    manualRow.style.display = 'none';
  } catch (e) {
    statusEl.textContent = STR.regexNotLoaded;
    statusEl.className = 'status-badge error';
    displayEl.textContent = e.message;
    manualRow.style.display = 'flex';
    // Pre-fill with default
    $('#manual-regex').value = '^(\\S+)\\s+(.+)$';
  }
}

// Manual regex apply
$('#apply-regex-btn').addEventListener('click', () => {
  const raw = $('#manual-regex').value.trim();
  if (!raw) return;
  try {
    new RegExp(raw);
    state.regex = raw;
    $('#regex-status').textContent = STR.regexManual;
    $('#regex-status').className = 'status-badge ok';
    $('#regex-display').textContent = raw;
    if (state.allWords.length > 0) {
      $('#parse-result').textContent = STR.reparseHint;
      $('#parse-result').className = 'parse-result fail';
    }
  } catch (e) {
    alert(STR.invalidRegex + e.message);
  }
});

// ====== File handling ======
$('#wordlist-file').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  $('#file-name').textContent = file.name;
  const reader = new FileReader();

  reader.onload = (ev) => {
    const text = ev.target.result;
    parseWordList(text);
  };

  reader.readAsText(file, 'UTF-8');
});

function parseWordList(text) {
  if (!state.regex) {
    $('#parse-result').textContent = STR.parseFailRegex;
    $('#parse-result').className = 'parse-result fail';
    return;
  }

  const lines = text.split(/\r?\n/);
  const regex = new RegExp(state.regex);
  const words = [];
  let parseErrors = 0;

  for (const line of lines) {
    const trimmed = line.trim();
    // Skip empty lines and comments
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//')) continue;

    const match = trimmed.match(regex);
    if (match && match.length >= 3) {
      words.push({
        word: match[1].trim(),
        meaning: match[2].trim(),
        line: trimmed,
      });
    } else if (match && match.length === 2) {
      words.push({
        word: match[1].trim(),
        meaning: STR.noMeaning,
        line: trimmed,
      });
    } else {
      parseErrors++;
    }
  }

  if (words.length === 0) {
    $('#parse-result').textContent = STR.parseFail;
    $('#parse-result').className = 'parse-result fail';
    return;
  }

  state.allWords = words;
  state.currentIndex = 0;
  state.familiar = [];
  state.unfamiliar = [];
  state.skipped = [];
  state.history = [];
  state.flipped = false;

  const msg = STR.parseSuccess.replace('{n}', words.length);
  $('#parse-result').textContent = parseErrors > 0
    ? STR.parseSuccessSkipped.replace('{n}', words.length).replace('{e}', parseErrors)
    : msg;
  $('#parse-result').className = 'parse-result success';

  $('#card-panel').classList.remove('hidden');
  $('#done-panel').classList.add('hidden');

  updateProgress();
  showCurrentWord();
}

// ====== Card display ======
function showCurrentWord() {
  const total = state.allWords.length;
  if (state.currentIndex >= total) {
    showDonePanel();
    return;
  }

  const entry = state.allWords[state.currentIndex];
  $('#word-text').textContent = entry.word;
  $('#meaning-text').textContent = entry.meaning;

  state.flipped = false;
  $('#word-card').classList.remove('flipped');

  updateProgress();
}

function updateProgress() {
  const total = state.allWords.length;
  const done = state.familiar.length + state.unfamiliar.length;
  const pct = total > 0 ? (done / total * 100) : 0;

  $('#progress-bar').style.width = pct + '%';
  $('#progress-text').textContent = `${done} / ${total}`;
  $('#familiar-count').textContent = state.familiar.length;
  $('#unfamiliar-count').textContent = state.unfamiliar.length;
  $('#remaining-count').textContent = total - done - state.skipped.length;

  $('#btn-undo').disabled = state.history.length === 0;
}

// ====== Actions ======
function classifyWord(action) {
  if (state.currentIndex >= state.allWords.length) return;

  const entry = state.allWords[state.currentIndex];

  if (action === 'familiar') {
    state.familiar.push(entry);
    state.history.push({ word: entry, action: 'familiar' });
    state.currentIndex++;
  } else if (action === 'unfamiliar') {
    state.unfamiliar.push(entry);
    state.history.push({ word: entry, action: 'unfamiliar' });
    state.currentIndex++;
  } else if (action === 'skip') {
    state.skipped.push(entry);
    state.history.push({ word: entry, action: 'skip' });
    state.currentIndex++;
  }

  // Bring back skipped words at the end
  if (state.currentIndex >= state.allWords.length && state.skipped.length > 0) {
    state.allWords = [...state.skipped];
    state.skipped = [];
    state.currentIndex = 0;
  }

  updateProgress();
  showCurrentWord();
}

function undo() {
  if (state.history.length === 0) return;
  const last = state.history.pop();

  if (last.action === 'familiar') {
    const idx = state.familiar.lastIndexOf(last.word);
    if (idx >= 0) state.familiar.splice(idx, 1);
  } else if (last.action === 'unfamiliar') {
    const idx = state.unfamiliar.lastIndexOf(last.word);
    if (idx >= 0) state.unfamiliar.splice(idx, 1);
  } else if (last.action === 'skip') {
    const idx = state.skipped.lastIndexOf(last.word);
    if (idx >= 0) state.skipped.splice(idx, 1);
  }

  state.currentIndex = Math.max(0, state.currentIndex - 1);
  updateProgress();
  showCurrentWord();
}

// ====== Done panel ======
function showDonePanel() {
  $('#card-panel').classList.add('hidden');
  $('#done-panel').classList.remove('hidden');
  $('#done-familiar').textContent = state.familiar.length;
  $('#done-unfamiliar').textContent = state.unfamiliar.length;
  $('#done-skipped').textContent = state.skipped.length;
}

// ====== Export ======
function downloadFile(filename, words) {
  const content = words.map(w => w.line).join('\n');
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

$('#btn-export-familiar').addEventListener('click', () => {
  downloadFile('familiar.txt', state.familiar);
});

$('#btn-export-unfamiliar').addEventListener('click', () => {
  downloadFile('unfamiliar.txt', state.unfamiliar);
});

$('#btn-export-both').addEventListener('click', () => {
  downloadFile('familiar.txt', state.familiar);
  downloadFile('unfamiliar.txt', state.unfamiliar);
});

$('#btn-restart').addEventListener('click', () => {
  state.allWords = [];
  state.currentIndex = 0;
  state.familiar = [];
  state.unfamiliar = [];
  state.skipped = [];
  state.history = [];
  state.flipped = false;
  $('#card-panel').classList.add('hidden');
  $('#done-panel').classList.add('hidden');
  $('#file-name').textContent = '';
  $('#parse-result').textContent = '';
  $('#wordlist-file').value = '';
});

// ====== Event listeners ======
$('#word-card').addEventListener('click', () => {
  state.flipped = !state.flipped;
  $('#word-card').classList.toggle('flipped', state.flipped);
});

$('#btn-familiar').addEventListener('click', () => classifyWord('familiar'));
$('#btn-unfamiliar').addEventListener('click', () => classifyWord('unfamiliar'));
$('#btn-skip').addEventListener('click', () => classifyWord('skip'));
$('#btn-undo').addEventListener('click', undo);

// ====== Keyboard shortcuts ======
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;

  switch (e.key) {
    case 'ArrowRight':
      e.preventDefault();
      classifyWord('familiar');
      break;
    case 'ArrowLeft':
      e.preventDefault();
      classifyWord('unfamiliar');
      break;
    case 'ArrowDown':
      e.preventDefault();
      classifyWord('skip');
      break;
    case ' ':
      e.preventDefault();
      state.flipped = !state.flipped;
      $('#word-card').classList.toggle('flipped', state.flipped);
      break;
    case 'z':
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        undo();
      }
      break;
  }
});

// ====== Init ======
loadRegex();
