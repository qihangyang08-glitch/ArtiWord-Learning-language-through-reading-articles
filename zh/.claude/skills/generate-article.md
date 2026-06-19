---
name: generate-article
description: >
  Generate an English reading article that embeds CET-6 vocabulary words
  for memorization and translation practice via authentic article rewriting.
---

# Generate Memory Article

Generate an English reading article that embeds vocabulary words for memorization and translation practice.

---

## ⚠️ Encoding Notice (READ FIRST)

On Windows, Claude Code's terminal often uses GBK encoding, causing `UnicodeEncodeError` with emoji/Chinese output. **ALWAYS** prefix Python commands with:

```bash
PYTHONIOENCODING=utf-8 python ...
```

All project scripts handle this internally, but always use the env var for inline `python -c "..."` tests. Every Bash code block below includes this prefix.

---

## Article Purpose

Generate ONE article that serves ALL of:
1. Vocabulary acquisition (target words used naturally in context)
2. Long-sentence analysis practice (complex sentence structures)
3. Translation training (Chinese↔English)
4. Reading comprehension (inference, vocabulary-in-context, main idea)

The article must read like authentic published writing — never like a vocabulary exercise.

---

## Full Workflow

### Phase 0: Environment Check

Ensure the local server is running (needed for some operations):

```bash
(python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close()" 2>/dev/null && echo "Server OK") || (echo "Starting server..." && start "WordLerning-Server" python -m http.server 8080 --directory .)
```

(On macOS use `open`, on Linux use `xdg-open` instead of `start`)

### Phase 1: Extract Target Words

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py --count 200
```

Output: JSON array of ~200 words with meanings, weighted by usage count (lower count = higher priority).

**If coverage is low** (extracted words don't overlap well with the article's natural vocabulary), re-run to get fresh batches:

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py --count 200 --exclude word1,word2,word3,...
```

Pass previously extracted words to `--exclude`. Call 2-3 times max — the script's purpose is to avoid context overflow, not to exhaust the word list.

### Phase 2: Search for Source Article

Use WebSearch to find an authentic English article.

**Source quality requirements:**
- Outlets: The Economist, The Guardian, BBC Future, Scientific American, Aeon, Nautilus, MIT Technology Review, Nature News, NYT (science/ideas sections)
- Type: Opinion/analysis/feature essays — NOT straight news reports
- Length: 400-800 words

**Topic selection — choose ONLY from these categories:**

| Category | Sub-topics |
|----------|------------|
| Technology & Society | AI, social media, privacy, data economy, platform governance, automation, digital labor |
| Science & Human Behavior | psychology, neuroscience, education, language learning, human attention, memory |
| Economics & Public Policy | labor markets, consumer behavior, urban development, inequality, globalization |
| Environment & Sustainability | climate change, renewable energy, food systems, biodiversity |
| Culture & Modern Life | work-life balance, remote work, digital culture, generational differences |

**AVOID:** fiction, fantasy, military, celebrity gossip, sports news, entertainment reporting.

### Phase 3: Dedup Check (MANDATORY)

**You MUST run the dedup check before proceeding with any article.** This prevents wasting effort on duplicate content.

After finding a candidate article via WebSearch and fetching its full text with WebFetch:

```bash
PYTHONIOENCODING=utf-8 python tools/check-similarity.py \
  --title "CANDIDATE_ARTICLE_TITLE" \
  --text "CANDIDATE_ARTICLE_FULL_TEXT"
```

The script outputs a JSON with `recommendation` field:

| Recommendation | Action |
|----------------|--------|
| `safe` | Proceed to Phase 4 |
| `review_needed` | Read the `matches` array. Each match has `overlap_keywords` and `score`. **You (the LLM) judge**: do these articles cover the same story/argument? If yes → skip this article, search again. If merely same broad topic but different angle → you may proceed. |
| `likely_duplicate` | **Skip this article immediately.** Search for a different one, then re-run Phase 3. |

If you skip an article, search for a different one and re-run Phase 3. You must not use an article that is `likely_duplicate`.

### Phase 4: Assess Vocabulary Overlap

From the candidate article, assess:
1. How many target words naturally appear in or fit the article's topic
2. Whether the article has complex sentence structures
3. Whether it argues a position (not just reports facts)

If overlap is poor (< 10 potential words), re-run Phase 1 with `--exclude` and search again.

### Phase 5: Rewrite the Article

IMPORTANT: Read the source article fully via WebFetch before rewriting.

#### Authenticity Principle (OVERRIDES ALL)

```
Authenticity > Logic > Difficulty > Vocabulary Coverage
```

If maximizing vocabulary coverage reduces authenticity, authenticity wins. Drop words that don't fit naturally.

#### Vocabulary Integration Rules

1. **Prioritize uncommon meanings** — e.g., `yield` → "屈服/让步" not "产生"; `address` → "处理/演说" not "地址"; `capital` → "首都/资本" not "大写字母"; `deliberate` → "故意的/深思熟虑的" not just the verb form
2. **Prefer idiomatic collocations** — use words in their natural word partnerships (e.g., "yield to pressure", "address the issue", "capital offense")
3. **Prefer phrasal verbs and fixed expressions** — e.g., "bear out" (confirm), "fall through" (fail), "take to" (begin liking)
4. **NEVER force a word** — if it doesn't fit naturally, omit it. A missing word is better than an awkward sentence.
5. **Bold all target words** with `**word**` so they're visually marked in the final article.
6. **Write like a native speaker** — no Chinglish. Verify collocations mentally against native usage patterns (think COCA/Ludwig).

#### Difficulty Requirements

- **Vocabulary**: ~CET-6 level (≈6000 word families), avoid excessive academic jargon
- **Reasoning**: Abstract reasoning, multi-perspective analysis, cause-effect chains, contrast & concession
- **Information density**: Moderate — enough substance to reward close reading, not so dense it's impenetrable
- **Avoid**: Pure description, simple narration, list-like presentation

#### Article Structure (4 paragraphs)

| Paragraph | Purpose |
|-----------|---------|
| **P1 (Opening)** | Introduce the problem or phenomenon — hook the reader |
| **P2 (Evidence)** | Provide evidence, examples, or research findings |
| **P3 (Counterargument)** | Present an opposing view, limitation, or nuance |
| **P4 (Synthesis)** | Provide synthesis, implications, or a qualified conclusion |

Follow real journalistic argumentation patterns — don't make it formulaic.

#### Long Sentence Design

Include **3-5 long sentences** suitable for translation practice.

Each long sentence must combine **multiple** of:
- Relative clauses (defining + non-defining)
- Appositive phrases
- Parenthetical structures (dashes, brackets)
- Non-finite clauses (participles, gerunds, infinitives)
- Prepositional phrase stacking
- Contrast/concession logic (while, whereas, although, despite)

Target length: **30-60 words per sentence**.

Sentences must remain grammatical and publishable — not grammatical puzzles. A real editor would accept them.

### Phase 6: Write Translation Training Section

Select the **two hardest long sentences** for detailed analysis.

For EACH sentence, provide:

1. **原文** — the full sentence
2. **句子结构分析** — overall structure description (e.g., "复合句：主句 + 非限定性定语从句 + 分词状语")
3. **主句提取** — strip to the main clause only (subject + predicate + object/complement)
4. **逐层句法分析** — break down layer by layer:
   ```
   第1层：[主句] Subject + Verb + Object
   第2层：  ├── [定语从句] which/that ... (修饰 Object)
   第3层：  │   └── [介词短语] in which ...
   第2层：  └── [分词状语] Given that ...
   ```
5. **参考翻译** — idiomatic Chinese translation

### Phase 7: Write Full Translation

Provide a complete **段落对应翻译** (paragraph-by-paragraph) of the entire article in natural Chinese.

### Phase 8: Write Vocabulary Training Section

List ALL target words actually used in the article.

For EACH word, provide this table:

| 单词 | 文中含义 | 核心含义 | 常用搭配 | 用法常见度 |
|------|---------|---------|---------|-----------|
| yield | 屈服、让步 | 产生；屈服；产出 | yield to pressure, high-yield bonds | ✅ / ⚠ 较冷门 |

If a word is used in an uncommon sense, mark it as ⚠ and add a brief note.

### Phase 9: Write Reading Comprehension Questions

Create questions that mirror CET-6 / postgraduate entrance exam style:

1. **2 语境词汇题** (Vocabulary in Context) — 4 options each
2. **2 推理题** (Inference Questions) — 4 options each
3. **1 中心思想题** (Main Idea Question) — 4 options

Provide answer keys. **Avoid** factual recall, true/false, fill-in-the-blank.

### Phase 10: Save and Record

#### 10a: Save the Article

Save to `articles/YYYY-MM-DD-<descriptive-slug>.md` using this exact format:

```markdown
---
title: "Article Title"
source_url: "https://..."
date: "YYYY-MM-DD"
words_used: ["word1", "word2", ...]
difficulty: "CET-6"
topic: "Technology & Society"
---

# Article Title

[Full article body with **bolded** target words]

---

## 长难句翻译练习

### 句子 1
**原文：** > ...
**句子结构分析：** ...
**主句提取：** ...
**逐层句法分析：** ...
**参考翻译：** ...

### 句子 2
(same structure)

---

## 全文翻译

[Paragraph-by-paragraph Chinese translation]

---

## 词汇训练

| 单词 | 文中含义 | 核心含义 | 常用搭配 | 用法常见度 |
|------|---------|---------|---------|-----------|
| ... | ... | ... | ... | ... |

---

## 阅读理解题

### 语境词汇题
**1.** ...
**2.** ...

### 推理题
**3.** ...
**4.** ...

### 中心思想题
**5.** ...

### 答案
1. X  2. X  3. X  4. X  5. X
```

#### 10b: Extract Keywords for Dedup

Before calling count-words.py, identify **10-20 keywords** from the rewritten article that represent its core topic. These will be stored for future dedup checks.

Keywords should be: lowercase, singular form, topic-significant nouns and verbs. For example, an article about carbon pricing → `climate, carbon, emission, trading, policy, renewable, greenhouse, taxation, energy, subsidy`.

#### 10c: Update Counters and History

```bash
PYTHONIOENCODING=utf-8 python tools/count-words.py \
  --words '["word1","word2","word3",...]' \
  --title "Article Title" \
  --url "https://original-source-url" \
  --article-id "YYYY-MM-DD-descriptive-slug" \
  --keywords "keyword1,keyword2,keyword3,..."
```

This increments usage counters (lowering priority for next extraction), records the source URL, and stores keywords for future similarity checks.

---

## Final Checklist

Before finishing, verify:

- [ ] Phase 3 dedup check passed (not a duplicate)
- [ ] Article reads like authentic published English (not a vocab exercise)
- [ ] Uncommon meanings are prioritized where natural
- [ ] 3-5 long sentences (30-60 words) with multiple clause types
- [ ] Translation section has structural analysis for 2 sentences
- [ ] Vocabulary table covers all used target words with collocations
- [ ] Reading questions are inference/vocab-in-context style (not fact recall)
- [ ] Article saved to `articles/` with correct frontmatter
- [ ] Keywords extracted and passed to `count-words.py --keywords`
- [ ] `count-words.py` ran successfully
