#!/usr/bin/env python3
"""
Language configuration for Word-Lerning (English version).

Sets your native language and target language, then generates
the skill files with the correct language pair embedded.

Usage:
    python configure.py          # Interactive mode
    python configure.py --native English --target German   # Non-interactive
"""

import argparse
import json
import os
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def resolve_path(relative_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, relative_path)


def load_config():
    path = resolve_path('config.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'native': 'English', 'target': 'French'}


def save_config(config):
    path = resolve_path('config.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f'\nConfig saved: {path}')


def generate_skills(native, target):
    skills_dir = resolve_path('.claude/skills')
    generated = []

    for filename in sorted(os.listdir(skills_dir)):
        if not filename.endswith('.md.template'):
            continue

        template_path = os.path.join(skills_dir, filename)
        output_name = filename.replace('.template', '')
        output_path = os.path.join(skills_dir, output_name)

        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace('{{NATIVE}}', native)
        content = content.replace('{{TARGET}}', target)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        generated.append(f'  {filename} -> {output_name}')

    return generated


def main():
    parser = argparse.ArgumentParser(
        description='Configure language pair for Word-Lerning (English)'
    )
    parser.add_argument('--native', type=str, help='Your native language')
    parser.add_argument('--target', type=str, help='Language you are learning')
    args = parser.parse_args()

    config = load_config()

    print('Word-Lerning (English) — Language Configuration')
    print('=' * 50)

    # Determine languages
    if args.native and args.target:
        native = args.native.strip()
        target = args.target.strip()
        print(f'  Native: {native}')
        print(f'  Target: {target}')
    else:
        native = input(f'Your native language [{config.get("native", "English")}]: ').strip()
        target = input(f'Language you\'re learning [{config.get("target", "French")}]: ').strip()
        if not native:
            native = config.get('native', 'English')
        if not target:
            target = config.get('target', 'French')

    if not native or not target:
        print('Error: Both languages are required.', file=sys.stderr)
        sys.exit(1)

    # Save config
    save_config({'native': native, 'target': target})

    # Generate skills
    print('\nGenerating skill files...')
    generated = generate_skills(native, target)
    for line in generated:
        print(line)

    print(f'\nDone! Skills configured for: {native} -> {target}')
    print('Now run install.bat (or bash install.sh) to install the skills.')


if __name__ == '__main__':
    main()
