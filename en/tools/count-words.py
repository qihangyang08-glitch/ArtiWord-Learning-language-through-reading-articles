#!/usr/bin/env python3
"""
Word counter update and article history recording.

Increments usage counters for words used in a generated article,
and records the article in the history to avoid reusing the same source.

Usage:
    # Update counters only
    python count-words.py --words '["abolish","abrupt","yield"]'

    # Full recording with article info
    python count-words.py \
        --words '["abolish","abrupt"]' \
        --title "Climate Policy Shifts" \
        --url "https://www.economist.com/..." \
        --article-id "2026-06-16-climate-policy"

    # Read words from stdin (JSON array)
    echo '["word1","word2"]' | python count-words.py --stdin
"""

import argparse
import json
import os
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

    args = parser.parse_args()

    # Parse words
    words = []
    if args.stdin:
        words = json.loads(sys.stdin.read())
    elif args.words:
        words = json.loads(args.words)

    if not words:
        print("Error: No words provided. Use --words or --stdin.", file=sys.stderr)
        sys.exit(1)

    if not isinstance(words, list):
        print("Error: Words must be a JSON array.", file=sys.stderr)
        sys.exit(1)

    # Update counters
    counters = update_counters(args.counters, words)
    print(f"✅ Counters updated: {len(words)} words")

    # Show top counts
    sorted_counts = sorted(counters.items(), key=lambda x: x[1], reverse=True)
    top = sorted_counts[:5]
    print(f"   Top counts: {', '.join(f'{w}({c})' for w, c in top)}")
    if len(sorted_counts) > 5:
        print(f"   ... and {len(sorted_counts) - 5} more")

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
