#!/usr/bin/env python3
"""
Random word extraction with priority weighting.

Reads the unfamiliar word list and counter file, then selects N words
via weighted random sampling. Words with higher usage counts get lower
priority (weight = 1/(count+1)^2).

Usage:
    python extract-words.py                    # Default: 200 words, JSON
    python extract-words.py --count 50         # Extract 50 words
    python extract-words.py --format text      # Plain text output
    python extract-words.py --exclude abolish,abrupt  # Exclude specific words
    python extract-words.py --seed 42          # Fixed seed for reproducibility

Output (JSON):
    {
      "words": [{"word": "abolish", "meaning": "v. 废除，取消"}, ...],
      "count": 200,
      "excluded": ["already_used_word"]
    }
"""

import argparse
import json
import os
import random
import re
import sys

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# Default regex for parsing word list lines (same as regex-config.txt default)
DEFAULT_WORD_REGEX = re.compile(r'^(\S+)\s+(.+)$')


def resolve_path(relative_path):
    """Resolve a path relative to the project root (parent of tools/)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, relative_path)


def load_word_list(path):
    """Load unfamiliar word list. Returns list of {word, meaning, line}."""
    words = []
    if not os.path.exists(path):
        print(f"Error: Word list not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = DEFAULT_WORD_REGEX.match(line)
            if match:
                words.append({
                    'word': match.group(1).strip(),
                    'meaning': match.group(2).strip(),
                    'line': line,
                })
    return words


def load_counters(path):
    """Load counters JSON. Returns dict {word: count}."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)


def compute_weights(words, counters, exclude_set):
    """
    Compute sampling weights for each word.
    weight = 1 / (count + 1)^2
    Words in exclude_set get weight 0.
    """
    weights = []
    for w in words:
        if w['word'] in exclude_set:
            weights.append(0.0)
        else:
            cnt = counters.get(w['word'], 0)
            weights.append(1.0 / ((cnt + 1) ** 2))
    return weights


def weighted_sample(words, weights, n):
    """
    Weighted random sampling without replacement.
    Uses numpy-style cumulative weight approach.
    If n >= available words, returns all available words in random order.
    """
    available = [(w, wt) for w, wt in zip(words, weights) if wt > 0]
    if len(available) == 0:
        return []

    if n >= len(available):
        result = [w for w, _ in available]
        random.shuffle(result)
        return result

    # Weighted sampling without replacement
    selected = []
    remaining = list(available)  # [(word, weight), ...]

    for _ in range(n):
        total_weight = sum(wt for _, wt in remaining)
        if total_weight <= 0:
            break
        r = random.random() * total_weight
        cumulative = 0.0
        chosen_idx = 0
        for i, (_, wt) in enumerate(remaining):
            cumulative += wt
            if cumulative >= r:
                chosen_idx = i
                break
        selected.append(remaining.pop(chosen_idx)[0])

    return selected


def main():
    parser = argparse.ArgumentParser(
        description='Random word extraction with priority weighting'
    )
    parser.add_argument(
        '--count', '-n', type=int, default=200,
        help='Number of words to extract (default: 200)'
    )
    parser.add_argument(
        '--format', '-f', choices=['json', 'text'], default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--exclude', '-x', type=str, default='',
        help='Comma-separated list of words to exclude'
    )
    parser.add_argument(
        '--seed', '-s', type=int, default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--wordlist', '-w', type=str,
        default=resolve_path('data/unfamiliar.txt'),
        help='Path to unfamiliar word list'
    )
    parser.add_argument(
        '--counters', '-c', type=str,
        default=resolve_path('data/counters.json'),
        help='Path to counters JSON file'
    )

    args = parser.parse_args()

    # Set seed
    if args.seed is not None:
        random.seed(args.seed)

    # Parse exclude list
    exclude_set = set()
    if args.exclude:
        exclude_set = {w.strip() for w in args.exclude.split(',') if w.strip()}

    # Load data
    words = load_word_list(args.wordlist)
    counters = load_counters(args.counters)

    if not words:
        print("Error: No words found in word list.", file=sys.stderr)
        sys.exit(1)

    # Compute weights and sample
    weights = compute_weights(words, counters, exclude_set)
    selected = weighted_sample(words, weights, min(args.count, len(words)))

    # Format output
    if args.format == 'text':
        for w in selected:
            print(w['line'])
    else:
        output = {
            'words': [{'word': w['word'], 'meaning': w['meaning']} for w in selected],
            'count': len(selected),
        }
        if exclude_set:
            output['excluded'] = sorted(exclude_set)
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
