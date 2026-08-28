#!/usr/bin/env python3
"""
مرحله ساخت README: catalog.json را می‌خواند و README.md را بر اساس
دسته و زیردسته بازسازی می‌کند. catalog.json همیشه منبع حقیقت است؛
این اسکریپت فقط آن را به شکل قابل‌خواندن نمایش می‌دهد.
"""

import os
import json
from collections import defaultdict
from datetime import datetime, timezone

CATALOG_FILE = 'data/catalog.json'
README_FILE = 'README.md'


def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def main():
    catalog = load_json(CATALOG_FILE, {'repos': []})
    repos = catalog.get('repos', [])

    total = len(repos)
    needs_review = [r for r in repos if r.get('needs_review') or r.get('confidence') == 'low']

    by_category = defaultdict(lambda: defaultdict(list))
    for repo in repos:
        if repo.get('needs_review') or repo.get('confidence') == 'low':
            continue
        by_category[repo.get('category', 'نامشخص')][repo.get('subcategory', '')].append(repo)

    lines = []
    lines.append("# 🌟 کاتالوگ ریپوهای استارشده")
    lines.append("")
    lines.append(f"**آخرین به‌روزرسانی:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**تعداد کل ریپوها:** {total}")
    lines.append("")
    lines.append("این فهرست به‌صورت خودکار از روی `data/catalog.json` ساخته می‌شود.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # فهرست مطالب
    lines.append("## 📑 فهرست دسته‌ها")
    lines.append("")
    for category in sorted(by_category.keys()):
        count = sum(len(v) for v in by_category[category].values())
        anchor = category.lower().replace(' ', '-')
        lines.append(f"- [{category}](#{anchor}) ({count} ریپو)")
    if needs_review:
        lines.append(f"- [نیازمند بررسی](#نیازمند-بررسی) ({len(needs_review)} ریپو)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # بخش‌های دسته‌بندی‌شده
    for category in sorted(by_category.keys()):
        lines.append(f"## {category}")
        lines.append("")
        for subcategory in sorted(by_category[category].keys()):
            repos_in_sub = by_category[category][subcategory]
            if subcategory:
                lines.append(f"### {subcategory}")
                lines.append("")
            for repo in sorted(repos_in_sub, key=lambda x: x.get('stars', 0), reverse=True):
                lines.append(f"#### [{repo['repo']}]({repo['url']})")
                lines.append(f"{repo.get('description_fa', '')}")
                lines.append("")
                lines.append(f"- **کاربرد:** {repo.get('purpose', '')}")
                lines.append(f"- **زبان:** {repo.get('language', 'Not specified')}")
                lines.append(f"- **استار:** ⭐ {repo.get('stars', 0)}")
                if repo.get('tags'):
                    lines.append(f"- **برچسب‌ها:** {', '.join(f'`{t}`' for t in repo['tags'])}")
                lines.append("")

    # بخش نیازمند بررسی
    if needs_review:
        lines.append("---")
        lines.append("")
        lines.append("## نیازمند بررسی")
        lines.append("")
        lines.append("این ریپوها با اطمینان پایین دسته‌بندی شده‌اند و بهتر است دستی بررسی شوند.")
        lines.append("")
        for repo in needs_review:
            lines.append(f"#### [{repo['repo']}]({repo['url']})")
            lines.append(f"{repo.get('description_fa', '') or repo.get('purpose', '') or '(بدون توضیح)'}")
            lines.append("")
            lines.append(f"- **دسته پیشنهادی:** {repo.get('category', '?')}")
            lines.append(f"- **اطمینان:** {repo.get('confidence', '?')}")
            lines.append("")

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ README.md generated ({total} repos, {len(needs_review)} needing review)")


if __name__ == '__main__':
    main()
