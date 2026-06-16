/**
 * Word Triage — 词表分类工具
 *
 * 核心逻辑：加载词表文件 → 正则解析 → 卡片逐个判断 → 导出分类结果
 *
 * 注意：此文件为核心代码，Skill 不得修改。
 *       正则式配置请修改 regex-config.txt
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
const $$ = (sel) => document.querySelectorAll(sel);

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
    statusEl.textContent = '✅ 已加载';
    statusEl.className = 'status-badge ok';
    displayEl.textContent = regexStr;
    manualRow.style.display = 'none';
  } catch (e) {
    statusEl.textContent = '⚠ 未加载';
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
    $('#regex-status').textContent = '✅ 手动';
    $('#regex-status').className = 'status-badge ok';
    $('#regex-display').textContent = raw;
    // Re-parse if file already loaded
    if (state.allWords.length > 0) {
      reparseWords();
    }
  } catch (e) {
    alert('正则式无效: ' + e.message);
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

function reparseWords() {
  // Re-parse with new regex (called after manual regex change)
  // We need to re-read the file - trigger a re-select
  // For simplicity, let the user re-select the file
  $('#parse-result').textContent = '请重新选择词表文件以应用新正则式';
  $('#parse-result').className = 'parse-result fail';
}

function parseWordList(text) {
  if (!state.regex) {
    $('#parse-result').textContent = '❌ 请先配置正则式';
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
      // Regex with only 1 capture group — treat as word only
      words.push({
        word: match[1].trim(),
        meaning: '(无释义)',
        line: trimmed,
      });
    } else {
      parseErrors++;
    }
  }

  if (words.length === 0) {
    $('#parse-result').textContent = `❌ 未能解析任何单词（${parseErrors} 行错误）。请检查正则式。`;
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

  const msg = `✅ 成功解析 ${words.length} 个单词`;
  $('#parse-result').textContent = parseErrors > 0
    ? `${msg}（${parseErrors} 行跳过）`
    : msg;
  $('#parse-result').className = 'parse-result success';

  // Show card panel
  $('#card-panel').classList.remove('hidden');
  $('#done-panel').classList.add('hidden');

  updateProgress();
  showCurrentWord();
}

// ====== Card display ======
function showCurrentWord() {
  const total = state.allWords.length;
  if (state.currentIndex >= total) {
    // All done — show done panel
    showDonePanel();
    return;
  }

  const entry = state.allWords[state.currentIndex];
  $('#word-text').textContent = entry.word;
  $('#meaning-text').textContent = entry.meaning;

  // Reset flip
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

  // Update undo button
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

  // If we've gone through everything, bring back skipped words
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

  // Remove from respective array
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

  // Go back
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
  // Don't trigger if user is typing in an input
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
