#!/usr/bin/env python3
"""
Article similarity checker for deduplication.

Compares a candidate article against all previously generated articles
using keyword Jaccard similarity + title overlap. Outputs a recommendation
for the LLM to make the final duplicate decision.

Usage:
    # Single article check
    python check-similarity.py --title "New Title" --text "Article body..."
    python check-similarity.py --title "New Title" --text "..." --threshold 0.3
    python check-similarity.py --file articles/2026-06-16-slug.md

    # Batch mode: check multiple candidates, rank by similarity
    python check-similarity.py --batch '[{"title":"A","text":"..."},{"title":"B","text":"..."}]'
    python check-similarity.py --batch-file candidates.json

Output (single):
    {
      "matches": [...],
      "recommendation": "safe" | "review_needed" | "likely_duplicate"
    }

Output (batch):
    {
      "candidates": [
        {"title": "...", "score": 0.05, "recommendation": "safe", "matches": [...]},
        ...
      ],
      "best": {...},
      "ranked_by_safety": ["title1", "title2", ...]
    }
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# English stopwords (most common words that don't carry topic meaning)
STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 'and', 'but', 'or', 'nor', 'not', 'if', 'while', 'although',
    'because', 'since', 'until', 'about', 'up', 'out', 'off', 'over',
    'just', 'now', 'also', 'its', 'it', 'itself', 'they', 'them', 'their',
    'theirs', 'he', 'him', 'his', 'she', 'her', 'hers', 'we', 'us', 'our',
    'ours', 'you', 'your', 'yours', 'me', 'my', 'mine', 'i', 'that',
    'this', 'these', 'those', 'which', 'what', 'who', 'whom', 'whose',
    'one', 'two', 'said', 'say', 'says', 'like', 'make', 'makes', 'made',
    'many', 'much', 'even', 'still', 'yet', 'well', 'back', 'way', 'new',
    'first', 'last', 'long', 'great', 'little', 'own', 'see', 'get',
    'go', 'come', 'know', 'take', 'think', 'look', 'want', 'give', 'use',
    'find', 'tell', 'ask', 'work', 'seem', 'feel', 'try', 'leave', 'call',
}


def resolve_path(relative_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, relative_path)


def extract_keywords(text, top_n=30):
    """Extract top N meaningful keywords from text."""
    # Normalize: lowercase, remove punctuation
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)

    words = text.split()
    # Filter: len > 2, not a stopword, not purely numeric
    meaningful = [
        w for w in words
        if len(w) > 2 and w not in STOPWORDS and not w.isdigit()
    ]

    # Frequency count
    counter = Counter(meaningful)
    # Return top N
    return [word for word, _ in counter.most_common(top_n)]


def jaccard_similarity(set_a, set_b):
    """Jaccard similarity: |intersection| / |union|."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def title_similarity(title_a, title_b):
    """Word-level overlap ratio for titles."""
    if not title_a or not title_b:
        return 0.0

    def tokenize(t):
        return set(re.sub(r'[^a-z\s]', ' ', t.lower()).split())

    set_a = tokenize(title_a) - STOPWORDS
    set_b = tokenize(title_b) - STOPWORDS

    if not set_a or not set_b:
        return 0.0

    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def load_history(path):
    """Load article history JSON."""
    if not os.path.exists(path):
        return {'used_urls': [], 'articles': []}

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return {'used_urls': [], 'articles': []}
        return json.loads(content)


def check_similarity(new_title, new_text, history_path, threshold=0.15):
    """
    Compare new article against all articles in history.
    Returns matches and a recommendation.
    """
    history = load_history(history_path)
    articles = history.get('articles', [])

    if not articles:
        return {
            'matches': [],
            'recommendation': 'safe',
            'note': 'No previous articles in history',
            'top_score': 0.0,
        }

    new_keywords = set(extract_keywords(new_text))

    matches = []
    for article in articles:
        # Use stored keywords if available, otherwise extract from title only
        stored_keywords = set(article.get('keywords', []))
        if not stored_keywords:
            # Fallback: just use title
            stored_keywords = set(extract_keywords(article.get('title', '')))

        kw_sim = jaccard_similarity(new_keywords, stored_keywords)
        t_sim = title_similarity(new_title, article.get('title', ''))

        # Weighted score
        score = 0.6 * kw_sim + 0.4 * t_sim

        if score >= threshold:
            overlap_kw = sorted(new_keywords & stored_keywords)
            matches.append({
                'id': article.get('id', ''),
                'title': article.get('title', ''),
                'score': round(score, 3),
                'keyword_jaccard': round(kw_sim, 3),
                'title_similarity': round(t_sim, 3),
                'overlap_keywords': overlap_kw[:15],  # Top 15 overlapping
                'date': article.get('date', ''),
            })

    # Sort by score descending
    matches.sort(key=lambda x: x['score'], reverse=True)

    # Determine recommendation
    if not matches:
        recommendation = 'safe'
    else:
        top_score = matches[0]['score']
        if top_score >= 0.5:
            recommendation = 'likely_duplicate'
        elif top_score >= 0.2:
            recommendation = 'review_needed'
        else:
            recommendation = 'safe'

    result = {
        'matches': matches[:5],  # Top 5 matches
        'recommendation': recommendation,
        'total_articles_checked': len(articles),
    }

    if matches:
        result['top_score'] = round(matches[0]['score'], 3)
    else:
        result['top_score'] = 0.0

    return result


def check_batch(candidates, history_path, threshold=0.15):
    """
    Check multiple candidates against history.
    candidates: list of {"title": str, "text": str}
    Returns ranked results with best (lowest similarity) first.
    """
    results = []
    for c in candidates:
        title = c.get('title', 'Untitled')
        text = c.get('text', '')
        if not text.strip():
            results.append({
                'title': title,
                'error': 'No text provided',
                'score': 1.0,
                'recommendation': 'error',
                'matches': [],
            })
            continue

        r = check_similarity(title, text, history_path, threshold)
        results.append({
            'title': title,
            'score': r['top_score'],
            'recommendation': r['recommendation'],
            'matches': r['matches'],
            'total_checked': r['total_articles_checked'],
        })

    # Sort by score ascending (lowest similarity = safest = best)
    ranked = sorted(results, key=lambda x: x['score'])

    output = {
        'candidates': results,
        'best': ranked[0] if ranked else None,
        'ranked_by_safety': [r['title'] for r in ranked],
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Article similarity checker for deduplication'
    )
    parser.add_argument(
        '--title', '-t', type=str, default='',
        help='Title of the candidate article'
    )
    parser.add_argument(
        '--text', type=str, default='',
        help='Full text of the candidate article (or use --file)'
    )
    parser.add_argument(
        '--file', '-f', type=str, default='',
        help='Path to candidate article .md file (reads title + body)'
    )
    parser.add_argument(
        '--threshold', type=float, default=0.15,
        help='Minimum similarity score to report (default: 0.15)'
    )
    parser.add_argument(
        '--history', type=str,
        default=resolve_path('data/article-history.json'),
        help='Path to article history JSON'
    )
    parser.add_argument(
        '--batch', '-b', type=str, default='',
        help='JSON string of candidate array: [{"title":"...","text":"..."},...]'
    )
    parser.add_argument(
        '--batch-file', type=str, default='',
        help='Path to JSON file with candidate array'
    )

    args = parser.parse_args()

    # Batch mode
    if args.batch or args.batch_file:
        if args.batch_file:
            if not os.path.exists(args.batch_file):
                print(f"Error: Batch file not found: {args.batch_file}", file=sys.stderr)
                sys.exit(1)
            with open(args.batch_file, 'r', encoding='utf-8') as f:
                candidates = json.loads(f.read())
        else:
            candidates = json.loads(args.batch)

        if not isinstance(candidates, list):
            print("Error: --batch must be a JSON array.", file=sys.stderr)
            sys.exit(1)

        result = check_batch(candidates, args.history, args.threshold)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Single mode
    title = args.title
    text = args.text

    # Read from file if specified
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Try to extract title from frontmatter or first heading
            fm_match = re.search(r'title:\s*"?(.+?)"?\n', content)
            if fm_match and not args.title:
                title = fm_match.group(1).strip()
            # Use full content as text
            text = content
        else:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

    if not text.strip():
        print("Error: No text provided. Use --text, --file, --batch, or --batch-file.", file=sys.stderr)
        sys.exit(1)

    result = check_similarity(title, text, args.history, args.threshold)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
