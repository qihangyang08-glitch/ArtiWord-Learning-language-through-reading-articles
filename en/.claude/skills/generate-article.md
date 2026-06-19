---
name: generate-article
description: >
  Generate a reading article in French that embeds vocabulary words
  for memorization and translation practice (French ↔ English).
---

# Generate Memory Article

Generate a reading article in French that embeds vocabulary words for memorization and translation practice.

---

## ⚠️ Encoding Notice (READ FIRST)

On Windows, always prefix Python commands with:

```bash
PYTHONIOENCODING=utf-8 python ...
```

All project scripts handle this internally.

---

## Article Purpose

Generate ONE article that serves ALL of:
1. Vocabulary acquisition (target words in natural context)
2. Long-sentence analysis practice
3. Translation training (French ↔ English)
4. Reading comprehension

The article must read like authentic published writing — never like a vocabulary exercise.

---

## Full Workflow

### Phase 0: Confirm Language Configuration

The user has configured: **Native = English, Target = French**.

Confirm this with the user: *"I'll generate an article in **French** with translations to **English**. Is that correct?"*

If the user wants to change languages, tell them to re-run `python configure.py`.

Adjust all subsequent steps accordingly:
- Source article language = French
- Translation direction = French ↔ English
- Vocabulary table headings = in English
- Question language = English

### Phase 1: Environment Check

```bash
(python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); s.close()" 2>/dev/null && echo "Server OK") || (echo "Starting..." && start "WordLerning-Server" python -m http.server 8080 --directory .)
```

### Phase 2: Extract Target Words

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py --count 200
```

Re-run with `--exclude` if coverage is poor (2-3 times max).

### Phase 3: Multi-Search for Source Articles

Use WebSearch to find **3-5 candidate articles** in French. Bias towards **recently published** articles (current year preferred). Search with diverse keywords to get different angles.

**Source quality requirements:**
- Reputable publications in French
- Opinion/analysis/feature essays — NOT straight news
- Appropriate difficulty for an intermediate-advanced learner

**Topic reference (for guidance only — NOT a filter):**

The categories below are **suggestions for search direction**. An article does NOT need to fit any category perfectly. Do NOT reject an article just because its topic is outside this list. As long as the article is substantial and analytical, it's eligible.

| Category | Sub-topics |
|----------|------------|
| Technology & Society | AI, social media, privacy, data economy, automation |
| Science & Human Behavior | psychology, neuroscience, education, memory |
| Economics & Public Policy | labor markets, urban development, inequality |
| Environment & Sustainability | climate change, renewable energy, biodiversity |
| Culture & Modern Life | work-life balance, remote work, digital culture |

**No word-count filter:** Do not filter by article length. Quality is the only criterion. You will trim, excerpt, or expand the article to the target length during rewriting.

Fetch full text of all candidates with WebFetch.

### Phase 4: Batch Dedup Check (MANDATORY)

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
3. If all candidates are `likely_duplicate`, search for a fresh batch and re-run Phase 4

| Best Candidate Recommendation | Action |
|-------------------------------|--------|
| `safe` (top_score < 0.2) | Proceed to Phase 5 |
| `review_needed` (0.2 ≤ top_score < 0.5) | Read the `matches` — LLM judges if same story/argument. If yes → pick next candidate. If merely same broad topic → you may proceed. |
| `likely_duplicate` (top_score ≥ 0.5) | Skip this candidate, try the next one in the ranking |

### Phase 5: Assess Vocabulary Overlap

From the selected candidate article, estimate how many target words naturally fit the article's topic and context.

If overlap is poor (< 10 potential fitting words), **simply re-run Phase 2 with `--exclude`** to get fresh words, then return to Phase 5 with the same article. Do NOT search for a new article — a quality article with fresh words is better than a mediocre article with high overlap.

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py --count 200 --exclude word1,word2,word3,...
```

Call 2-3 times max.

### Phase 6: Rewrite the Article

**Authenticity Principle (OVERRIDES ALL):**
```
Authenticity > Logic > Difficulty > Vocabulary Coverage
```

**Vocabulary Integration:**
1. Prioritize uncommon/idiomatic meanings
2. Prefer natural collocations and phrasal verbs
3. NEVER force a word — omit if it doesn't fit
4. **Bold** all target words with `**word**`
5. Write like a native speaker of the target language

**Difficulty:** Intermediate-advanced learner level. Abstract reasoning, multi-perspective analysis.

**Structure (4 paragraphs):**
- P1: Introduce the problem/phenomenon
- P2: Evidence, examples, research
- P3: Counterargument, limitations
- P4: Synthesis, implications

**Long Sentences:** 3-5 sentences (30-60 words each) combining multiple clause types.

**Finding and marking long sentences:**

1. **Look for naturally complex sentences** in the rewritten article — sentences with multiple clause types, layered modifiers, or sophisticated logic.
2. **Mark each long sentence** in the article body using markdown underline syntax (`___...___`). Alternatively, wrap them in `[square brackets]` if the article style prefers.
3. **If the article lacks sufficiently difficult sentences** for translation practice, **manually rewrite or insert** complex sentences. Maintain the article's natural flow — rewritten sentences must read as if an editor polished them, not as grammar exercises.

Each long sentence must combine **multiple** of:
- Relative clauses (defining + non-defining)
- Appositive phrases
- Parenthetical structures (dashes, brackets)
- Non-finite clauses (participles, gerunds, infinitives)
- Prepositional phrase stacking
- Contrast/concession logic (while, whereas, although, despite)

### Phase 7: Translation Training Section

Select the 2 hardest sentences. For each, provide:
1. Original text
2. Sentence structure analysis
3. Main clause extraction
4. Layered syntactic breakdown
5. Reference English translation

### Phase 8: Full Translation

Paragraph-by-paragraph English translation of the entire article.

### Phase 9: Vocabulary Training Section

Table for ALL target words used:

| Word | Meaning in Context | Core Meaning(s) | Common Collocations | Usage Frequency |
|------|-------------------|-----------------|---------------------|-----------------|
| ... | ... | ... | ... | Common / Uncommon |

### Phase 10: Reading Comprehension Questions

1. **2 Vocabulary-in-Context questions** (4 options each)
2. **2 Inference questions** (4 options each)
3. **1 Main Idea question** (4 options)

Provide answer keys. Avoid fact-recall and true/false.

### Phase 11: Save and Record

#### 11a: Save the Article

Save to `articles/YYYY-MM-DD-<descriptive-slug>.md`:

```markdown
---
title: "Article Title"
source_url: "https://..."
date: "YYYY-MM-DD"
words_used: ["word1", "word2", ...]
difficulty: "Intermediate-Advanced"
topic: "Technology & Society"
target_language: "French"
---

# Article Title

[Full article body with **bolded** target words]

---

## Translation Training

### Sentence 1
**Original:** > ...
**Structure Analysis:** ...
**Main Clause:** ...
**Layered Breakdown:** ...
**Reference Translation:** ...

### Sentence 2
(same structure)

---

## Full Translation (English)

[Paragraph-by-paragraph English translation]

---

## Vocabulary Training

| Word | Meaning in Context | Core Meaning(s) | Common Collocations | Usage |
|------|-------------------|-----------------|---------------------|-------|
| ... | ... | ... | ... | ... |

---

## Reading Comprehension

### Vocabulary in Context
**1.** ...
**2.** ...

### Inference
**3.** ...
**4.** ...

### Main Idea
**5.** ...

### Answers
1. X  2. X  3. X  4. X  5. X
```

#### 11b: Extract Keywords

Identify 10-20 topic-significant keywords from the rewritten article for future dedup.

#### 11c: Update Counters and History

The script **automatically detects target words** from the article's frontmatter `words_used` field (which you wrote in 11a) and cross-references them with the word list. You do NOT need to manually list words.

```bash
PYTHONIOENCODING=utf-8 python tools/count-words.py \
  --article-file "articles/YYYY-MM-DD-slug.md" \
  --title "Article Title" \
  --url "https://original-source-url" \
  --article-id "YYYY-MM-DD-slug" \
  --keywords "keyword1,keyword2,..."
```

This automatically:
1. Reads the article file and extracts `words_used` from frontmatter
2. Increments usage counters for each detected word (lowering priority for future extraction)
3. Records the source URL and keywords in article history for future dedup checks

---

## Final Checklist

Before finishing, verify:

- [ ] Phase 4 batch dedup check passed (not a duplicate — best candidate selected)
- [ ] Article reads authentically (not a vocab exercise)
- [ ] 3-5 long sentences with multiple clause types, marked with `___...___` or rewritten
- [ ] Translation section with structural analysis for 2 hardest sentences
- [ ] Vocabulary table covers all used words
- [ ] Reading questions are inference/vocab-in-context
- [ ] Article saved to `articles/` with correct frontmatter (including `words_used`)
- [ ] Keywords extracted and passed to `count-words.py --keywords`
- [ ] `count-words.py --article-file` ran successfully (auto-detected words)
