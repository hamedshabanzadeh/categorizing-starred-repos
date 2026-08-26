#!/usr/bin/env python3
"""
Categorize starred repositories based on topics, language, and description.
"""

import os
import json
import requests
from collections import defaultdict
from datetime import datetime

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_ACTOR = os.getenv('GITHUB_ACTOR')
API_BASE = 'https://api.github.com'

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# دسته‌بندی‌های اصلی و کلمات کلیدی
CATEGORY_KEYWORDS = {
    'Frontend': ['react', 'vue', 'angular', 'svelte', 'next', 'nuxt', 'ember', 'html', 'css', 'javascript', 'typescript', 'ui', 'ux', 'frontend', 'web', 'browser'],
    'Backend': ['django', 'flask', 'fastapi', 'node', 'express', 'spring', 'laravel', 'rails', 'backend', 'server', 'api', 'rest', 'graphql'],
    'DevOps & Cloud': ['docker', 'kubernetes', 'terraform', 'ansible', 'ci/cd', 'jenkins', 'devops', 'aws', 'gcp', 'azure', 'cloud', 'deployment'],
    'Data Science & ML': ['tensorflow', 'pytorch', 'scikit', 'pandas', 'numpy', 'ml', 'machine-learning', 'ai', 'data-science', 'deep-learning', 'nlp', 'computer-vision'],
    'Database': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'database', 'sql', 'nosql', 'orm'],
    'Testing': ['pytest', 'jest', 'mocha', 'testing', 'test', 'unittest', 'e2e', 'tdd'],
    'CLI & Tools': ['cli', 'command-line', 'tool', 'utilities', 'automation', 'script'],
    'Mobile': ['react-native', 'flutter', 'swift', 'kotlin', 'mobile', 'ios', 'android', 'app'],
    'Security': ['security', 'cryptography', 'authentication', 'authorization', 'ssl', 'encryption'],
    'Documentation': ['documentation', 'docs', 'guide', 'tutorial', 'learning'],
    'Other': []
}

def get_starred_repos():
    """Fetch all starred repositories."""
    repos = []
    page = 1
    per_page = 100
    
    while True:
        url = f'{API_BASE}/user/starred'
        params = {'page': page, 'per_page': per_page, 'sort': 'updated', 'direction': 'desc'}
        
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            break
        
        repos.extend(data)
        page += 1
    
    return repos

def categorize_repo(repo):
    """Categorize a repository based on topics, language, and description."""
    name = repo.get('name', '').lower()
    description = (repo.get('description') or '').lower()
    language = (repo.get('language') or '').lower()
    topics = [t.lower() for t in repo.get('topics', [])]
    
    combined_text = f"{name} {description} {language} {' '.join(topics)}"
    
    # Find matching categories
    matched_categories = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == 'Other':
            continue
        if any(keyword in combined_text for keyword in keywords):
            matched_categories.append(category)
    
    # Default to Other if no match
    if not matched_categories:
        matched_categories = ['Other']
    
    return matched_categories

def format_repo_entry(repo):
    """Format repository information."""
    return {
        'name': repo['name'],
        'url': repo['html_url'],
        'description': repo.get('description') or 'No description',
        'stars': repo.get('stargazers_count', 0),
        'language': repo.get('language') or 'Not specified',
        'topics': repo.get('topics', [])
    }

def generate_readme(categorized_repos):
    """Generate README with categorized repositories."""
    readme_content = f"""# 🌟 Categorized Starred Repositories

**Last updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This repository automatically categorizes and organizes starred repositories by topic and use case.

---

"""
    
    # Generate table of contents
    readme_content += "## 📑 Table of Contents\n\n"
    for category in sorted(categorized_repos.keys()):
        readme_content += f"- [{category}](#{category.lower().replace(' ', '-')}) ({len(categorized_repos[category])} repos)\n"
    
    readme_content += "\n---\n\n"
    
    # Generate category sections
    for category in sorted(categorized_repos.keys()):
        repos = categorized_repos[category]
        readme_content += f"## {category}\n\n"
        
        for repo in sorted(repos, key=lambda x: x['stars'], reverse=True):
            readme_content += f"### [{repo['name']}]({repo['url']})\n"
            readme_content += f"- **Description:** {repo['description']}\n"
            readme_content += f"- **Language:** {repo['language']}\n"
            readme_content += f"- **Stars:** ⭐ {repo['stars']}\n"
            if repo['topics']:
                readme_content += f"- **Topics:** {', '.join([f'`{t}`' for t in repo['topics']])}\n"
            readme_content += "\n"
    
    readme_content += f"\n---\n**Total repositories:** {sum(len(repos) for repos in categorized_repos.values())}\n"
    
    return readme_content

def generate_json(categorized_repos):
    """Generate JSON output."""
    output = {
        'last_updated': datetime.utcnow().isoformat(),
        'total_repos': sum(len(repos) for repos in categorized_repos.values()),
        'categories': categorized_repos
    }
    return json.dumps(output, indent=2, ensure_ascii=False)

def main():
    print("🚀 Fetching starred repositories...")
    repos = get_starred_repos()
    print(f"📊 Found {len(repos)} starred repositories")
    
    # Categorize repositories
    categorized = defaultdict(list)
    
    print("🧠 Categorizing repositories...")
    for repo in repos:
        categories = categorize_repo(repo)
        repo_entry = format_repo_entry(repo)
        
        for category in categories:
            categorized[category].append(repo_entry)
    
    print(f"✅ Categorized into {len(categorized)} categories")
    
    # Generate outputs
    print("📝 Generating README...")
    readme = generate_readme(categorized)
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print("✅ README.md generated")
    
    print("📄 Generating JSON output...")
    json_output = generate_json(categorized)
    
    with open('categorized_repos.json', 'w', encoding='utf-8') as f:
        f.write(json_output)
    print("✅ categorized_repos.json generated")
    
    # Print summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    for category in sorted(categorized.keys()):
        print(f"{category}: {len(categorized[category])} repositories")
    print("="*50)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
