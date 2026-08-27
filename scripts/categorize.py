#!/usr/bin/env python3
"""
Categorize starred repositories using GitHub Models (AI) based on their actual
purpose, topic, and language. Only processes repos not seen in previous runs
(incremental), and accumulates results into README.md and categorized_repos.json.
"""

import os
import json
import base64
import time
import requests
from collections import defaultdict
from datetime import datetime, timezone

# توکن با دسترسی به starred repos (همون STARRED_REPOS_TOKEN قبلی)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
# توکن با دسترسی "models: read" برای فراخوانی GitHub Models (می‌تونه همون GITHUB_TOKEN پیش‌فرض اکشن باشه)
MODELS_TOKEN = os.getenv('MODELS_TOKEN', GITHUB_TOKEN)

API_BASE = 'https://api.github.com'
MODELS_API_URL = 'https://models.github.ai/inference/chat/completions'
MODEL_NAME = 'openai/gpt-4o-mini'

STATE_FILE = 'data/processed_repos.json'
JSON_OUTPUT_FILE = 'categorized_repos.json'
README_FILE = 'README.md'

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

MODELS_HEADERS = {
    'Authorization': f'Bearer {MODELS_TOKEN}',
    'Content-Type': 'application/json'
}


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


def load_state():
    """لیست ریپوهایی که قبلاً پردازش شده‌اند را می‌خواند."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed_ids': []}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_existing_output():
    """خروجی دسته‌بندی‌شده‌ی قبلی را می‌خواند تا روی آن اضافه کنیم، نه بازنویسی کامل."""
    if os.path.exists(JSON_OUTPUT_FILE):
        with open(JSON_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('categories', {})
    return {}


def get_readme_snippet(full_name):
    """بخشی از فایل README ریپو را می‌گیرد (در صورت وجود) تا به مدل کمک کند کارکرد واقعی را بفهمد."""
    url = f'{API_BASE}/repos/{full_name}/readme'
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return ''
        content = response.json().get('content', '')
        decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
        return decoded[:1500]
    except Exception:
        return ''


def classify_with_ai(repo, readme_snippet):
    """با استفاده از GitHub Models، ریپو را بر اساس کارکرد واقعی دسته‌بندی و توضیح کوتاه تولید می‌کند."""
    name = repo.get('name', '')
    description = repo.get('description') or ''
    language = repo.get('language') or ''
    topics = repo.get('topics', [])

    prompt = f"""You are analyzing a GitHub repository to categorize it and summarize it.

Repository name: {name}
Description: {description}
Primary language: {language}
Topics: {', '.join(topics)}
README excerpt:
{readme_snippet}

Respond ONLY with a valid JSON object, no markdown formatting, no extra text, in exactly this format:
{{
  "category": "<one short category, e.g. Frontend, Backend, DevOps & Cloud, Data Science & ML, Database, Testing, CLI & Tools, Mobile, Security, Documentation, Game Development, Other>",
  "summary": "<one or two sentence summary of what this project actually does, based on its real purpose>"
}}
"""

    payload = {
        'model': MODEL_NAME,
        'messages': [
            {'role': 'system', 'content': 'You are a precise assistant that only outputs valid JSON, nothing else.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.2,
        'max_tokens': 220
    }

    try:
        response = requests.post(MODELS_API_URL, headers=MODELS_HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()

        # حذف بلاک‌های احتمالی مارک‌داون دور JSON (مدل بعضی وقت‌ها ```json می‌ذاره)
        if content.startswith('```'):
            content = content.strip('`')
            if content.startswith('json'):
                content = content[4:]

        result = json.loads(content)
        category = (result.get('category') or 'Other').strip() or 'Other'
        summary = (result.get('summary') or description or 'No description').strip()
        return category, summary
    except Exception as e:
        print(f"⚠️  AI classification failed for {name}: {e}")
        return 'Other', description or 'No description'


def format_repo_entry(repo, category, summary):
    return {
        'name': repo['name'],
        'full_name': repo['full_name'],
        'url': repo['html_url'],
        'summary': summary,
        'stars': repo.get('stargazers_count', 0),
        'language': repo.get('language') or 'Not specified',
        'topics': repo.get('topics', []),
        'category': category
    }


def generate_readme(categorized_repos):
    total = sum(len(repos) for repos in categorized_repos.values())
    readme_content = f"""# 🌟 Categorized Starred Repositories

**Last updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
**Total repositories:** {total}

Automatically categorized by AI based on each project's actual purpose, topics, and language.

---

## 📑 Table of Contents

"""
    for category in sorted(categorized_repos.keys()):
        anchor = category.lower().replace(' ', '-').replace('&', '')
        readme_content += f"- [{category}](#{anchor}) ({len(categorized_repos[category])} repos)\n"

    readme_content += "\n---\n\n"

    for category in sorted(categorized_repos.keys()):
        repos = categorized_repos[category]
        readme_content += f"## {category}\n\n"

        for repo in sorted(repos, key=lambda x: x['stars'], reverse=True):
            readme_content += f"### [{repo['name']}]({repo['url']})\n"
            readme_content += f"{repo['summary']}\n\n"
            readme_content += f"- **Language:** {repo['language']}\n"
            readme_content += f"- **Stars:** ⭐ {repo['stars']}\n"
            if repo['topics']:
                readme_content += f"- **Topics:** {', '.join(f'`{t}`' for t in repo['topics'])}\n"
            readme_content += "\n"

    return readme_content


def generate_json(categorized_repos):
    output = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'total_repos': sum(len(repos) for repos in categorized_repos.values()),
        'categories': categorized_repos
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


def main():
    if not GITHUB_TOKEN:
        raise SystemExit("❌ GITHUB_TOKEN is not set (needed to read starred repos).")

    print("🚀 Fetching starred repositories...")
    all_repos = get_starred_repos()
    print(f"📊 Found {len(all_repos)} starred repositories in total")

    state = load_state()
    processed_ids = set(state.get('processed_ids', []))

    new_repos = [r for r in all_repos if r['id'] not in processed_ids]
    print(f"🆕 {len(new_repos)} new repositories to process")

    categorized = defaultdict(list, {k: v for k, v in load_existing_output().items()})

    if not new_repos:
        print("✅ Nothing new to process. Exiting.")
        return

    for repo in new_repos:
        print(f"🧠 Classifying: {repo['full_name']}")
        readme_snippet = get_readme_snippet(repo['full_name'])
        category, summary = classify_with_ai(repo, readme_snippet)
        entry = format_repo_entry(repo, category, summary)
        categorized[category].append(entry)
        processed_ids.add(repo['id'])
        time.sleep(1)  # جلوگیری از فشار زیاد به rate limit مدل

    print("📝 Generating README...")
    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(generate_readme(categorized))

    print("📄 Generating JSON output...")
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(generate_json(categorized))

    state['processed_ids'] = list(processed_ids)
    save_state(state)

    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    for category in sorted(categorized.keys()):
        print(f"{category}: {len(categorized[category])} repositories")
    print("=" * 50)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
