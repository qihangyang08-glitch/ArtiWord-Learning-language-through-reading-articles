---
name: init-wordlist
description: >
  Configure the regex pattern for the Word Triage web tool to parse
  a vocabulary list — then report the results for the user to proceed.
---

# Initialize Word List Regex

Configure the regex pattern used by the Word Triage web tool to parse a vocabulary list — then report the results for the user to proceed.

---

## ⚠️ Encoding Notice (READ FIRST)

On Windows, Claude Code's terminal may use GBK encoding, causing `UnicodeEncodeError`. **ALWAYS** prefix Python commands with:

```bash
PYTHONIOENCODING=utf-8 python ...
```

All project scripts handle this internally. Every Bash code block below uses this prefix.

---

## Constraints (CRITICAL)

- **ONLY modify `tools/word-triage/regex-config.txt`** — do NOT touch any other file.
- Do NOT modify `index.html`, `app.js`, `*.py`, or any file under `data/`.
- The regex must have exactly **2 capture groups**: group 1 = word, group 2 = meaning/definition.
- Write ONLY the raw regex pattern (one line, no quotes, no `pattern:` prefix).

---

## Workflow

### Step 1: Locate the Word List

Ask the user to provide the path to their complete word list file. Read the first 30 lines + last 5 lines.

### Step 2: Analyze the Format

Identify the delimiter and which column is the word vs. the definition. If the format is multi-line (e.g., word on line 1, pronunciation line 2, definition line 3), **preprocess first** — normalize to single-line tab-separated format, save as `data/unfamiliar.txt`, then use the default regex `^(\S+)\s+(.+)$`.

### Step 3: Construct the Regex

The regex must use `^` and `$` anchors with exactly 2 capture groups.

Common patterns:
```
# Tab-separated: "word\tdefinition"
^(\S+)\t(.+)$

# Space-separated: "word  definition"
^(\S+)\s+(.+)$

# Slash-separated with metadata
^(\S+)\s*/\s*(?:[^/]+)\s*/\s*(.+?)\s*/?\s*$

# Vertical bar: "word | definition"
^(\S+)\s*\|\s*(.+)$

# Numbered list: "1. word definition"
^\d+\.?\s*(\S+)\s+(.+)$
```

### Step 4: Write the Regex

Write ONLY the regex pattern to `tools/word-triage/regex-config.txt`.

### Step 5: MANDATORY Self-Testing (Three Phases)

You MUST complete all three phases. If any fails, fix the regex and restart from Phase A.

#### Phase A — Full Parse Test (>=95% pass rate required)

```bash
PYTHONIOENCODING=utf-8 python -c "
import re, sys
regex = r'<YOUR_REGEX>'
with open('<WORDLIST_PATH>', 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
total = len(lines)
passed = 0
failed_lines = []
for i, line in enumerate(lines):
    m = re.match(regex, line)
    if m and m.group(1) and m.group(2):
        passed += 1
    else:
        failed_lines.append(f'  L{i+1}: {line[:80]}')
pass_rate = passed / total * 100 if total > 0 else 0
print(f'Total: {total} | Passed: {passed} ({pass_rate:.1f}%) | Failed: {total-passed}')
if failed_lines:
    print('First 10 failures:')
    for fl in failed_lines[:10]: print(fl)
sys.exit(0 if pass_rate >= 95 else 1)
"
```

#### Phase B — Capture Group Validation (0 errors required)

```bash
PYTHONIOENCODING=utf-8 python -c "
import re, random
regex = r'<YOUR_REGEX>'
with open('<WORDLIST_PATH>', 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
matches = [(l, re.match(regex, l)) for l in lines if re.match(regex, l)]
random.shuffle(matches)
errors = 0
for line, m in matches[:20]:
    w, d = m.group(1).strip(), m.group(2).strip()
    # Language-agnostic: accept any script; reject empty, pure-digits, pure-punctuation
    punct = set('.,;:!?-/\\()[]{}`@#$%^&*+=_~:;|<>')
    word_ok = len(w) >= 1 and not w.isdigit() and not all(c in punct or c.isspace() for c in w)
    def_ok = len(d) >= 2
    issues = []
    if not word_ok: issues.append('word is empty/digits/punctuation-only')
    if not def_ok: issues.append('definition too short')
    status = 'OK' if not issues else 'FAIL'
    if issues: errors += 1
    print(f'{status}: word={w[:30]!r} def={d[:50]!r} {\" | \".join(issues)}')
print(f'Errors: {errors}/20')
sys.exit(0 if errors == 0 else 1)
"
```

#### Phase C — Browser Simulation Test (>=10 words required)

```bash
PYTHONIOENCODING=utf-8 python -c "
import re, sys
regex = r'<YOUR_REGEX>'
with open('<WORDLIST_PATH>', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()
words = []; errors = 0
for line in lines:
    t = line.strip()
    if not t or t.startswith('#'): continue
    m = re.match(regex, t)
    if m and len(m.groups()) >= 2:
        words.append({'word': m.group(1).strip(), 'meaning': m.group(2).strip()})
    elif m and len(m.groups()) == 1:
        words.append({'word': m.group(1).strip(), 'meaning': '(no definition)'})
    else: errors += 1
print(f'Parsed: {len(words)} | Errors: {errors}')
for w in words[:5]: print(f'  {w[\"word\"]} -> {w[\"meaning\"][:60]}')
sys.exit(0 if len(words) >= 10 else 1)
"
```

### Step 6: Report Configuration Results

**Do NOT launch the web tool or browser automatically.** Instead, report the following to the user in English:

---

**📋 Word List Configuration Report**

- **Word list found:** `<YES/NO>` — `<file path>`
- **Word list name:** `<filename>` (e.g., `french-vocabulary.txt`)
- **Sorting method:** `<alphabetical / by frequency / random / by chapter / other>`
- **Detected format:** `<tab-separated / space-separated / slash-separated / etc.>`
- **Regex written:** `<the regex pattern>` → saved to `tools/word-triage/regex-config.txt`

**Test results:**
- Phase A (Full Parse): `<XX.X>%` pass rate (≥95% required)
- Phase B (Capture Group Validation): `<N>` errors / 20 samples (0 required)
- Phase C (Browser Simulation): `<N>` words parsed (≥10 required)

---

**Next steps you can take:**

1. Start the local server:
   ```
   python -m http.server 8080 --directory .
   ```
2. Open the web tool in your browser:
   - Windows: `start http://localhost:8080/tools/word-triage/`
   - macOS: `open http://localhost:8080/tools/word-triage/`
   - Linux: `xdg-open http://localhost:8080/tools/word-triage/`
3. In the web tool, click **"Select word list file"** and load your word list to begin triage.
4. Use keyboard shortcuts to classify words: `←` Unfamiliar, `→` Familiar, `Space` Flip, `↓` Skip.

