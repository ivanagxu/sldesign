#!/usr/bin/env python3
"""
Build script: Convert markdown news sources into HTML articles + index JSON.

Usage: python3 build_news.py
  - Reads *.md from news/sources/
  - Extracts YAML frontmatter (title, date, category)
  - Converts markdown body to HTML
  - Outputs individual HTML files + news-index.json to news/
"""

import os
import re
import json
import markdown
from datetime import datetime

SOURCES_DIR = os.path.join(os.path.dirname(__file__), 'news', 'sources')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'news')

def parse_frontmatter(text):
    """Parse YAML-like frontmatter from markdown."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    if not match:
        return {}, text
    
    meta = {}
    for line in match.group(1).strip().split('\n'):
        key, _, value = line.partition(':')
        meta[key.strip()] = value.strip().strip('"')
    
    return meta, match.group(2).strip()


def simple_md_to_html(md_text):
    """Convert markdown to HTML using the markdown library."""
    extensions = ['tables', 'fenced_code', 'codehilite', 'toc', 'meta']
    html = markdown.markdown(md_text, extensions=extensions)
    return html


def main():
    if not os.path.isdir(SOURCES_DIR):
        print(f"Sources directory not found: {SOURCES_DIR}")
        return

    articles = []

    for filename in sorted(os.listdir(SOURCES_DIR)):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(SOURCES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        meta, body = parse_frontmatter(content)
        html_body = simple_md_to_html(body)

        # Extract article ID from filename (e.g. 2025-05-04-nvidia-blackwell)
        article_id = filename.replace('.md', '')
        out_filename = f"{article_id}.html"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        # Write individual HTML article
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_body)

        # Collect metadata for index
        articles.append({
            'id': article_id,
            'title': meta.get('title', 'Untitled'),
            'date': meta.get('date', ''),
            'category': meta.get('category', '综合'),
            'filename': out_filename,
        })
        print(f"  ✓ {out_filename} — {meta.get('title', 'Untitled')}")

    # Sort articles by date descending (newest first)
    articles.sort(key=lambda x: x['date'], reverse=True)

    # Write news-index.json
    index_path = os.path.join(OUTPUT_DIR, 'news-index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Built {len(articles)} articles → {OUTPUT_DIR}/")
    print(f"   Index: {index_path}")


if __name__ == '__main__':
    main()
