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

The article must read like authentic published writing — never just like a vocabulary exercise.

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

### Phase 2: Multi-Search for Source Articles

Use WebSearch to find **3-5 candidate articles**. Bias towards **recently published** articles (current year preferred). Search with diverse keywords to get different angles.

**Source quality requirements:**
- Outlets: The Economist, The Guardian, BBC Future, Scientific American, Aeon, Nautilus, MIT Technology Review, Nature News, NYT (science/ideas sections)
- Type: Opinion/analysis/feature essays — NOT straight news reports

**Topic reference (for guidance only — NOT a filter):**

The categories below are **suggestions for search direction**. An article does NOT need to fit any category perfectly. Do NOT reject an article just because its topic is outside this list. As long as the article is substantial and analytical, it's eligible.

| Category | Sub-topics |
|----------|------------|
| Technology & Society | AI, social media, privacy, data economy, platform governance, automation, digital labor |
| Science & Human Behavior | psychology, neuroscience, education, language learning, human attention, memory |
| Economics & Public Policy | labor markets, consumer behavior, urban development, inequality, globalization |
| Environment & Sustainability | climate change, renewable energy, food systems, biodiversity |
| Culture & Modern Life | work-life balance, remote work, digital culture, generational differences |

**AVOID:** fiction, fantasy, military, celebrity gossip, sports news, entertainment reporting.

**No word-count filter:** Do not filter by article length. Quality is the only criterion. You will trim, excerpt, or expand the article to the target length during rewriting.

Fetch full text of all candidates with WebFetch.

### Phase 3: Batch Dedup Check (MANDATORY)

**Check ALL candidates at once** against article history using the batch mode:

```bash
PYTHONIOENCODING=utf-8 python tools/check-similarity.py --batch '[
  {"title": "Title 1", "text": "Full text of article 1..."},
  {"title": "Title 2", "text": "Full text of article 2..."},
  {"title": "Title 3", "text": "Full text of article 3..."}
]'
```

The script returns a `ranked_by_safety` list (lowest similarity score = safest = best candidate).

**Select the best candidate:**
1. Pick the highest-ranked article from `ranked_by_safety`
2. If the best article is `likely_duplicate` (top_score ≥ 0.5), skip it and check the next
3. If all candidates are `likely_duplicate`, search for a fresh batch and re-run Phase 3

| Best Candidate Recommendation | Action |
|-------------------------------|--------|
| `safe` (top_score < 0.2) | Proceed to Phase 4 |
| `review_needed` (0.2 ≤ top_score < 0.5) | Read the `matches` — LLM judges if same story/argument. If yes → pick next candidate. If merely same broad topic → you may proceed. |
| `likely_duplicate` (top_score ≥ 0.5) | Skip this candidate, try the next one in the ranking |

### Phase 4: Assess Vocabulary Overlap

From the selected candidate article, estimate how many target words naturally fit the article's topic and context.

If overlap is poor (< 10 potential fitting words), **simply re-run Phase 1 with `--exclude`** to get fresh words, then return to Phase 4 with the same article. Do NOT search for a new article — a quality article with fresh words is better than a mediocre article with high overlap.

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py --count 200 --exclude word1,word2,word3,...
```

Call 2-3 times max.

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

Include **3-5 long sentences** suitable for translation practice. These are the core of the translation training section.

**Finding and marking long sentences:**

1. **Look for naturally complex sentences** in the rewritten article — sentences with multiple clause types, layered modifiers, or sophisticated logic.
2. **Mark each long sentence** in the article body using markdown underline syntax:
   ```
   ___This is a long, complex sentence suitable for translation practice.___
   ```
   Alternatively, wrap them in `[square brackets]` if the article style prefers.
3. **If the article lacks sufficiently difficult sentences** (most naturally written articles won't reach CET-6 / postgraduate exam translation difficulty), **manually rewrite or insert** complex sentences. The article's natural flow must still be maintained — rewritten sentences must read as if an editor polished them, not as grammar exercises.

**Each long sentence must combine multiple of:**
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

The script **automatically detects target words** from the article's frontmatter `words_used` field (which you wrote in 10a) and cross-references them with the word list. You do NOT need to manually list words.

```bash
PYTHONIOENCODING=utf-8 python tools/count-words.py \
  --article-file "articles/YYYY-MM-DD-descriptive-slug.md" \
  --title "Article Title" \
  --url "https://original-source-url" \
  --article-id "YYYY-MM-DD-descriptive-slug" \
  --keywords "keyword1,keyword2,keyword3,..."
```

This automatically:
1. Reads the article file and extracts `words_used` from frontmatter
2. Increments usage counters for each detected word (lowering priority for future extraction)
3. Records the source URL and keywords in article history for future dedup checks

---

## Final Checklist

Before finishing, verify:

- [ ] Phase 3 batch dedup check passed (not a duplicate — best candidate selected)
- [ ] Article reads like authentic published English (not a vocab exercise)
- [ ] Uncommon meanings are prioritized where natural
- [ ] 3-5 long sentences marked with `___...___` or rewritten to add difficulty
- [ ] Translation section has structural analysis for 2 hardest sentences
- [ ] Vocabulary table covers all used target words with collocations
- [ ] Reading questions are inference/vocab-in-context style (not fact recall)
- [ ] Article saved to `articles/` with correct frontmatter (including `words_used`)
- [ ] Keywords extracted and passed to `count-words.py --keywords`
- [ ] `count-words.py --article-file` ran successfully (auto-detected words)
