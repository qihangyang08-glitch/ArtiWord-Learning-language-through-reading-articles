#!/usr/bin/env python3
"""
Word counter update and article history recording.

Increments usage counters for words used in a generated article,
and records the article in the history to avoid reusing the same source.

Usage:
    # Update counters only (manual word list)
    python count-words.py --words '["abolish","abrupt","yield"]'

    # Auto-detect words from article file (RECOMMENDED)
    python count-words.py --article-file articles/2026-06-16-slug.md

    # Full recording with article info (manual)
    python count-words.py \
        --words '["abolish","abrupt"]' \
        --title "Climate Policy Shifts" \
        --url "https://www.economist.com/..." \
        --article-id "2026-06-16-climate-policy"

    # Auto-detect + full recording
    python count-words.py \
        --article-file articles/2026-06-16-slug.md \
        --title "Climate Policy Shifts" \
        --url "https://www.economist.com/..." \
        --article-id "2026-06-16-climate-policy" \
        --keywords "climate,carbon,policy"

    # Read words from stdin (JSON array)
    echo '["word1","word2"]' | python count-words.py --stdin
"""

import argparse
import json
import os
import re
import sys
from datetime import date

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def resolve_path(relative_path):
    """Resolve a path relative to the project root."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, relative_path)


def load_json(path):
    """Load a JSON file. Returns empty dict/list if nonexistent or empty."""
    if not os.path.exists(path):
        return {} if 'counter' in path else {'used_urls': [], 'articles': []}

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return {} if 'counter' in path else {'used_urls': [], 'articles': []}
        return json.loads(content)


def save_json(path, data):
    """Save data to a JSON file with pretty formatting."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def load_word_list(path):
    """Load word list and return set of known words."""
    words = set()
    if not os.path.exists(path):
        return words
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Tab-separated: word\tmeaning
            parts = line.split('\t', 1)
            if parts:
                words.add(parts[0].strip())
    return words


def extract_words_from_frontmatter(content):
    """Extract words_used from YAML frontmatter."""
    # Match frontmatter block
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return []
    fm = fm_match.group(1)
    # Find words_used line
    wu_match = re.search(r'words_used:\s*\[(.*?)\]', fm)
    if wu_match:
        raw = wu_match.group(1)
        # Parse JSON array elements (quoted strings)
        words = re.findall(r'"([^"]+)"', raw)
        return words
    # Try multi-line YAML array
    wu_block = re.search(r'words_used:\s*\n((?:\s*-\s*.+\n?)*)', fm)
    if wu_block:
        words = re.findall(r'-\s*"?([^"\n]+)"?', wu_block.group(1))
        return [w.strip() for w in words]
    return []


def extract_bolded_words(content):
    """Extract words wrapped in **...** from article body."""
    # Skip frontmatter
    body = re.sub(r'^---\s*\n.*?\n---', '', content, flags=re.DOTALL)
    # Find all **word** patterns
    bolded = re.findall(r'\*\*([^*]+)\*\*', body)
    # Each bolded item might contain multiple words; extract first word
    words = []
    for b in bolded:
        b = b.strip()
        # It might be a multi-word phrase; take first word
        first_word = b.split()[0] if b.split() else b
        # Clean punctuation
        first_word = re.sub(r'[^\w\'-]', '', first_word)
        if first_word:
            words.append(first_word)
    return words


def detect_words_from_article(article_path, wordlist_path):
    """
    Auto-detect target words from article file.
    1. Try frontmatter words_used first (most reliable)
    2. Fall back to **bolded** words cross-referenced with word list
    """
    if not os.path.exists(article_path):
        print(f"Error: Article file not found: {article_path}", file=sys.stderr)
        sys.exit(1)

    with open(article_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Method 1: Frontmatter words_used
    frontmatter_words = extract_words_from_frontmatter(content)
    if frontmatter_words:
        print(f"   Auto-detected {len(frontmatter_words)} words from frontmatter")
        return frontmatter_words

    # Method 2: Bolded words + word list cross-reference
    wordlist = load_word_list(wordlist_path)
    bolded_words = extract_bolded_words(content)
    if bolded_words and wordlist:
        matched = [w for w in bolded_words if w in wordlist]
        unique_matched = list(dict.fromkeys(matched))  # dedup preserving order
        print(f"   Auto-detected {len(unique_matched)} words from bold markers (cross-referenced with word list)")
        return unique_matched

    if bolded_words:
        unique = list(dict.fromkeys(bolded_words))
        print(f"   Auto-detected {len(unique)} words from bold markers (no word list to cross-reference)")
        return unique

    print("Error: Could not auto-detect words from article. Provide --words manually.", file=sys.stderr)
    sys.exit(1)


def update_counters(counters_path, words):
    """Increment counter for each word by 1."""
    counters = load_json(counters_path)
    if not isinstance(counters, dict):
        counters = {}

    for word in words:
        counters[word] = counters.get(word, 0) + 1

    save_json(counters_path, counters)
    return counters


def record_article(history_path, words, title, url, article_id, keywords=None):
    """Record article in history and add URL to used_urls."""
    history = load_json(history_path)
    if not isinstance(history, dict):
        history = {'used_urls': [], 'articles': []}

    # Ensure keys exist
    history.setdefault('used_urls', [])
    history.setdefault('articles', [])

    # Add URL if not already present
    if url and url not in history['used_urls']:
        history['used_urls'].append(url)

    # Add article record
    article = {
        'id': article_id or f"{date.today().isoformat()}-untitled",
        'title': title or 'Untitled',
        'source_url': url or '',
        'date': date.today().isoformat(),
        'words_used': sorted(words),
    }

    # Store keywords for similarity checking
    if keywords:
        article['keywords'] = sorted(keywords)

    history['articles'].append(article)

    save_json(history_path, history)
    return history


def main():
    parser = argparse.ArgumentParser(
        description='Update word counters and article history'
    )
    parser.add_argument(
        '--words', '-w', type=str, default='',
        help='JSON array of words used, e.g. \'["word1","word2"]\''
    )
    parser.add_argument(
        '--article-file', '-f', type=str, default='',
        help='Path to article .md file — auto-detect words from frontmatter or **bold** markers'
    )
    parser.add_argument(
        '--stdin', action='store_true',
        help='Read words JSON array from stdin'
    )
    parser.add_argument(
        '--title', '-t', type=str, default='',
        help='Article title for history recording'
    )
    parser.add_argument(
        '--url', '-u', type=str, default='',
        help='Source article URL for dedup tracking'
    )
    parser.add_argument(
        '--article-id', '-i', type=str, default='',
        help='Article ID/slug (e.g. 2026-06-16-climate-policy)'
    )
    parser.add_argument(
        '--keywords', '-k', type=str, default='',
        help='Comma-separated keywords for dedup similarity checking'
    )
    parser.add_argument(
        '--counters', '-c', type=str,
        default=resolve_path('data/counters.json'),
        help='Path to counters JSON file'
    )
    parser.add_argument(
        '--history', type=str,
        default=resolve_path('data/article-history.json'),
        help='Path to article history JSON file'
    )
    parser.add_argument(
        '--wordlist', type=str,
        default=resolve_path('data/unfamiliar.txt'),
        help='Path to unfamiliar word list (for auto-detection cross-reference)'
    )

    args = parser.parse_args()

    # Determine words source
    words = []

    if args.article_file:
        # Auto-detect from article file
        print(f"📄 Scanning article: {args.article_file}")
        words = detect_words_from_article(args.article_file, args.wordlist)
        if not words:
            print("Error: No words detected from article file.", file=sys.stderr)
            sys.exit(1)
        # If --words also provided, merge (manual override)
        if args.words:
            manual_words = json.loads(args.words)
            merged = list(dict.fromkeys(words + manual_words))
            print(f"   Merged with {len(manual_words)} manual words → {len(merged)} total")
            words = merged
    elif args.stdin:
        words = json.loads(sys.stdin.read())
    elif args.words:
        words = json.loads(args.words)

    if not words:
        print("Error: No words provided. Use --article-file, --words, or --stdin.", file=sys.stderr)
        sys.exit(1)

    if not isinstance(words, list):
        print("Error: Words must be a JSON array.", file=sys.stderr)
        sys.exit(1)

    # Update counters
    counters = update_counters(args.counters, words)
    print(f"✅ Counters updated: {len(words)} words")

    # Show updated counts for the affected words
    affected = {w: counters.get(w, 0) for w in words}
    sorted_affected = sorted(affected.items(), key=lambda x: x[1], reverse=True)
    print(f"   Updated: {', '.join(f'{w}({c})' for w, c in sorted_affected[:10])}")
    if len(sorted_affected) > 10:
        print(f"   ... and {len(sorted_affected) - 10} more")

    # Record article if title/url provided
    if args.title or args.url:
        kw_list = []
        if args.keywords:
            kw_list = [kw.strip() for kw in args.keywords.split(',') if kw.strip()]
        history = record_article(
            args.history, words, args.title, args.url, args.article_id, kw_list
        )
        print(f"✅ Article recorded: {args.title or args.article_id}")
        print(f"   Total articles in history: {len(history['articles'])}")
        print(f"   Total URLs tracked: {len(history['used_urls'])}")


if __name__ == '__main__':
    main()
