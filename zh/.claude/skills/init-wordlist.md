---
name: init-wordlist
description: >
  Configure the regex pattern for the Word Triage web tool to parse
  a vocabulary list — then report the results for the user to proceed.
---

# Initialize Word List Regex

Configure the regex pattern used by the word-triage web tool to parse a user's vocabulary list — then report the results for the user to proceed.

---

## ⚠️ Encoding Notice (READ FIRST)

On Windows, Claude Code's terminal often uses GBK encoding, which causes `UnicodeEncodeError` with emoji/Chinese output. **ALWAYS** prefix Python commands with the environment variable:

```bash
PYTHONIOENCODING=utf-8 python ...
```

Or set the console code page first:

```bash
chcp 65001
```

All project scripts already call `sys.stdout.reconfigure(encoding='utf-8')` internally, but one-liner `python -c "..."` tests still need the env var. **Every Bash code block below that calls Python includes this prefix.**

---

## Constraints (CRITICAL)

- **ONLY modify `tools/word-triage/regex-config.txt`** — do NOT touch any other file.
- **Do NOT modify** `index.html`, `app.js`, `style.css`, `*.py`, or any file under `data/`.
- The regex must have exactly **2 capture groups**: group 1 = word, group 2 = meaning.
- Write ONLY the raw regex pattern to regex-config.txt (one line, no quotes, no `pattern:` prefix).

---

## Workflow

### Step 1: Locate the Word List

Ask the user to provide the path to their complete word list file. If the user doesn't specify, check common locations:
- Any `.txt` file under `data/`
- Any file the user drags or pastes the path of

Read the file (first 30 lines + last 5 lines to understand the full structure).

### Step 2: Analyze the Format

Identify:
- **Delimiter**: Tab (`\t`), space, `|`, `/`, `—`, `：`, comma, or fixed-width?
- **Word position**: Which column contains the English/foreign word?
- **Meaning position**: Which column contains the definition?
- **Multi-line?** Does each word span multiple lines (e.g., word on line 1, pronunciation line 2, meaning line 3)? If so, **preprocess the file first** to normalize it into a single-line tab-separated format, save as `data/unfamiliar.txt`, then use the default regex `^(\S+)\s+(.+)$`.
- **Extraneous content**: Pronunciation, numbering, example sentences, part-of-speech tags?

Common formats:

| Format | Example |
|--------|---------|
| Tab-separated | `abolish	v. 废除，取消` |
| Space-separated | `abolish v. 废除，取消` |
| Slash-separated | `abolish / v. 废除，取消 /` |
| Vertical bar | `abolish \| v. 废除，取消` |
| Em-dash | `abolish — v. 废除，取消` |
| Numbered | `1. abolish v. 废除，取消` |
| With pronunciation | `abolish /əˈbɑlɪʃ/ v. 废除，取消` |
| Multi-line (3 lines/word) | Line1: `1 abolish`, Line2: `/əˈbɑlɪʃ/`, Line3: `v. 废除` |

### Step 3: Construct the Regex

Build a regex with `^` and `$` anchors capturing group 1 = word, group 2 = meaning:

```
# Tab-separated
^(\S+)\t(.+)$

# Space-separated
^(\S+)\s+(.+)$

# Slash-separated with pronunciation
^(\S+)\s*/\s*(?:[^/]+)\s*/\s*(.+?)\s*/?\s*$

# Vertical bar
^(\S+)\s*\|\s*(.+)$

# Numbered
^\d+\.?\s*(\S+)\s+(.+)$

# Em-dash
^(\S+)\s*[—–-]\s*(.+)$
```

### Step 4: Write the Regex

Write ONLY the regex pattern to `tools/word-triage/regex-config.txt`.

### Step 5: MANDATORY Self-Testing (Three Phases)

**You MUST complete ALL three phases. If any phase fails, fix the regex and restart from Phase A. Do NOT proceed to Step 6 until all phases pass.**

#### Phase A — Full Parse Test

Test the regex against **ALL non-empty lines** of the word list:

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
print(f'Total lines: {total}')
print(f'Passed: {passed} ({pass_rate:.1f}%)')
print(f'Failed: {total - passed}')
if failed_lines:
    print('First 10 failures:')
    for fl in failed_lines[:10]:
        print(fl)
sys.exit(0 if pass_rate >= 95 else 1)
"
```

**Requirement: ≥ 95% pass rate.** If lower, analyze the first 10 failing lines, identify why they don't match, revise the regex, and restart Phase A.

Special cases that are OK to fail:
- Lines that are clearly not word entries (headers, section titles, pure numbers)
- Lines with only a word but no meaning (these should become "无释义")
- If > 5% of lines are headers/metadata, preprocess the file to remove them before testing

#### Phase B — Capture Group Validation

Randomly sample 20 matched lines and verify the capture groups:

```bash
PYTHONIOENCODING=utf-8 python -c "
import re, random
regex = r'<YOUR_REGEX>'
with open('<WORDLIST_PATH>', 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
matches = [(l, re.match(regex, l)) for l in lines]
matches = [(l, m) for l, m in matches if m]
random.shuffle(matches)
errors = 0
for line, m in matches[:20]:
    w = m.group(1).strip()
    d = m.group(2).strip()
    # Check: word should be mostly ASCII letters (allow hyphens, apostrophes)
    has_non_ascii = any(ord(c) > 127 for c in w)
    # Check: definition should not be empty
    def_ok = len(d) >= 2
    status = 'OK'
    issues = []
    if has_non_ascii: issues.append('word has non-ASCII')
    if not def_ok: issues.append('definition too short')
    if issues: errors += 1; status = 'FAIL'
    print(f'{status}: word={w[:30]!r}, def={d[:50]!r} {issues if issues else \"\"}')
print(f'Errors: {errors}/20')
sys.exit(0 if errors == 0 else 1)
"
```

**Requirement: 0 errors in 20 samples.** If errors found:
- "word has non-ASCII" → groups might be swapped (group 1 captured the Chinese meaning). Swap group positions in regex.
- "definition too short" → regex might be cutting off the definition. Widen group 2's pattern.
- After fixing, go back to Phase A.

#### Phase C — Browser Simulation Test

Simulate exactly what `app.js` does when parsing the word list:

```bash
PYTHONIOENCODING=utf-8 python -c "
import re, json
regex = r'<YOUR_REGEX>'
with open('<WORDLIST_PATH>', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()
words = []
errors = 0
for line in lines:
    trimmed = line.strip()
    if not trimmed or trimmed.startswith('#') or trimmed.startswith('//'):
        continue
    m = re.match(regex, trimmed)
    if m and len(m.groups()) >= 2:
        words.append({'word': m.group(1).strip(), 'meaning': m.group(2).strip()})
    elif m and len(m.groups()) == 1:
        words.append({'word': m.group(1).strip(), 'meaning': '(no definition)'})
    else:
        errors += 1
print(f'Words parsed: {len(words)}')
print(f'Parse errors: {errors}')
print('First 5 results:')
for w in words[:5]:
    print(f'  {w[\"word\"]}  ->  {w[\"meaning\"][:60]}')
if len(words) < 10:
    print('ERROR: Too few words parsed! Regex likely wrong.')
    sys.exit(1)
else:
    print(f'SUCCESS: {len(words)} words ready for the web tool.')
"
```

**Requirement: ≥ 10 words parsed.** If fewer, the regex is fundamentally wrong — go back to Step 2.

### Step 6: 汇报配置结果

**不要自动启动服务器或打开浏览器。** 请用中文向用户汇报以下内容：

---

**📋 词表配置报告**

- **词表是否找到：** `<是/否>` — `<文件路径>`
- **词表名称：** `<文件名>`（例如：`考研词汇表.txt`）
- **词表排列方式：** `<字母顺序 / 按频率 / 随机 / 按章节 / 其他>`
- **检测到的格式：** `<Tab分隔 / 空格分隔 / 斜杠分隔 / 等>`
- **正则表达式已写入：** `<正则表达式>` → 已保存至 `tools/word-triage/regex-config.txt`

**测试结果：**
- 阶段A（全量解析）：通过率 `<XX.X>%`（要求 ≥95%）
- 阶段B（捕获组验证）：`<N>` 个错误 / 20 条样本（要求 0 个错误）
- 阶段C（浏览器模拟）：解析出 `<N>` 个单词（要求 ≥10）

---

**下一步你可以进行的操作：**

1. 启动本地服务器：
   ```
   python -m http.server 8080 --directory .
   ```
2. 在浏览器中打开分词工具：
   - Windows：`start http://localhost:8080/tools/word-triage/`
   - macOS：`open http://localhost:8080/tools/word-triage/`
   - Linux：`xdg-open http://localhost:8080/tools/word-triage/`
3. 在网页工具中，点击 **"选择词表文件"**，加载你的词表开始分类。
4. 使用快捷键分类单词：`←` 不熟悉，`→` 熟悉，`Space` 翻转查看释义，`↓` 跳过。


