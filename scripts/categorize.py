#!/usr/bin/env python3
"""
مرحله ۱: شناسایی و جمع‌آوری ریپوهای تازه استار شده.
اطلاعات خام هر ریپوی جدید (که هنوز در catalog.json ثبت نشده) را در
data/inbox.json می‌نویسد. هیچ فراخوانی AI اینجا انجام نمی‌شود.
"""

import os
import json
import base64
import requests

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
API_BASE = 'https://api.github.com'

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

INBOX_FILE = 'data/inbox.json'
CATALOG_FILE = 'data/catalog.json'


def get_starred_repos():
    """تمام ریپوهای استارشده را از GitHub API می‌گیرد."""
    repos = []
    page = 1
    per_page = 100

    while True:
        url = f'{API_BASE}/user/starred'
        params = {'page': page, 'per_page': per_page, 'sort': 'created', 'direction': 'desc'}
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    return repos


def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_readme_snippet(full_name):
    """بخشی از README ریپو را می‌گیرد تا هنگام تحلیل به مدل کمک کند."""
    url = f'{API_BASE}/repos/{full_name}/readme'
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return ''
        content = response.json().get('content', '')
        decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
        return decoded[:1000]
    except Exception:
        return ''


def main():
    if not GITHUB_TOKEN:
        raise SystemExit("❌ GITHUB_TOKEN is not set (needed to read starred repos).")

    print("🚀 Fetching starred repositories...")
    all_repos = get_starred_repos()
    print(f"📊 Found {len(all_repos)} starred repositories in total")

    catalog = load_json(CATALOG_FILE, {'repos': []})
    catalog_ids = {entry['id'] for entry in catalog.get('repos', [])}

    inbox = load_json(INBOX_FILE, {'items': []})
    inbox_ids = {item['id'] for item in inbox.get('items', [])}

    new_repos = [r for r in all_repos if r['id'] not in catalog_ids and r['id'] not in inbox_ids]
    print(f"🆕 {len(new_repos)} new repositories to add to the inbox")

    if not new_repos:
        print("✅ Nothing new. Exiting.")
        return

    for repo in new_repos:
        item = {
            'id': repo['id'],
            'repo': repo['full_name'],
            'url': repo['html_url'],
            'description': repo.get('description') or '',
            'language': repo.get('language') or 'Not specified',
            'topics': repo.get('topics', []),
            'stars': repo.get('stargazers_count', 0),
            'readme_snippet': get_readme_snippet(repo['full_name'])
        }
        inbox.setdefault('items', []).append(item)
        print(f"➕ Added to inbox: {repo['full_name']}")

    save_json(INBOX_FILE, inbox)
    print(f"📝 {len(new_repos)} repos added to {INBOX_FILE}")
    print(f"⏳ Total items waiting for analysis: {len(inbox['items'])}")


if __name__ == '__main__':
    main()
