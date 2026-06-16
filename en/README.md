# Word-Lerning (English)

AI-powered vocabulary memorization & translation practice. For users learning **any language** (French, Spanish, Japanese, German, etc.).

Generate authentic articles in your target language that seamlessly embed vocabulary words — with uncommon meanings, idiomatic collocations, and natural native-level writing.

---

## Quick Start

### 1. Install

```bash
# Windows
install.bat

# macOS / Linux
bash install.sh
```

Skills are copied to `~/.claude/skills/` — available from any directory in Claude Code.

### 2. Initialize Your Word List

In Claude Code:

```
/init-wordlist
```

Provide your word list file. The skill auto-detects the format, configures the regex, self-tests, and opens the web tool in your browser.

### 3. Triage Your Words

Browser opens to `http://localhost:8080/tools/word-triage/`:
- Load your word list file
- Click card to flip and see the definition
- `←` Unfamiliar / `→` Familiar / `Space` Flip / `↓` Skip
- Export `familiar.txt` and `unfamiliar.txt` → place in `data/`

### 4. Generate Articles

```
/generate-article
```

The skill will ask which language you're learning, then:
1. Extract 200 words (low-frequency first) from your unfamiliar list
2. Search authentic articles **in your target language**
3. **Run dedup check** against previously used articles
4. Rewrite the article, embedding target words naturally (uncommon meanings preferred)
5. Add translation exercises + vocabulary table + reading comprehension
6. Save the article and update word counters

---

## Directory Structure

```
en/
├── tools/
│   ├── word-triage/          # Web card triage tool
│   │   ├── index.html        # 🔒 Core code (Skill must NOT modify)
│   │   ├── style.css
│   │   ├── app.js            # 🔒 Core code
│   │   └── regex-config.txt  # 🔧 Regex config (only file Skill may edit)
│   ├── extract-words.py      # Weighted random extraction
│   ├── count-words.py        # Counter + history recording
│   └── check-similarity.py   # Semantic dedup checker
├── .claude/skills/
│   ├── init-wordlist.md      # Init skill
│   └── generate-article.md   # Article generation skill
├── data/                     # Word lists + counters + history
├── articles/                 # Generated articles
├── install.bat / install.sh  # One-click install
├── serve.bat / serve.sh      # Local server
└── README.md
```

## Troubleshooting

### UnicodeEncodeError (Windows)

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py ...
# or
chcp 65001
```

All scripts internally call `sys.stdout.reconfigure(encoding='utf-8')` — direct execution usually works. Only inline `python -c "..."` tests need the env var prefix.
