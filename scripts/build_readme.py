#!/usr/bin/env python3
"""
مرحله ساخت کاتالوگ: catalog.json را می‌خواند و CATALOG.md را بر اساس
دسته و زیردسته بازسازی می‌کند. catalog.json همیشه منبع حقیقت است؛
این اسکریپت فقط آن را به شکل قابل‌خواندن نمایش می‌دهد.

README.md دیگر توسط این اسکریپت بازنویسی نمی‌شود — آن فایل معرفی
دستی پروژه است. فقط یک بخش کوچک آماری داخل README.md (بین دو کامنت
CATALOG_STATS_START/END) به‌صورت خودکار به‌روزرسانی می‌شود، در صورتی
که این نشانگرها در README.md وجود داشته باشند.
"""

import os
import json
import re
from collections import defaultdict
from datetime import datetime, timezone

CATALOG_FILE = 'data/catalog.json'
CATALOG_OUTPUT_FILE = 'CATALOG.md'
README_FILE = 'README.md'

STATS_START = '<!-- CATALOG_STATS_START -->'
STATS_END = '<!-- CATALOG_STATS_END -->'


def slugify(text):
    """
    anchor سازگار با شیوه‌ی خود گیتهاب برای هدینگ‌های Markdown می‌سازد:
    حروف کوچک، فاصله به خط تیره، و حذف کاراکترهای غیرحرفی/غیرعددی
    (به‌جز خط تیره) — دقیقاً همان الگوریتمی که گیتهاب برای لینک‌های
    داخلی هدینگ‌ها استفاده می‌کند.
    """
    text = text.strip().lower()
    text = text.replace(' ', '-')
    # حذف هر کاراکتری که حرف (فارسی/انگلیسی)، عدد یا خط تیره نیست
    text = re.sub(r'[^\w\-]', '', text, flags=re.UNICODE)
    return text


def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def update_readme_stats(total, needs_review_count):
    """
    فقط بخش کوچک آماری بین دو نشانگر را در README.md به‌روزرسانی می‌کند،
    بدون دست‌زدن به بقیه‌ی محتوای دستی‌نوشته‌شده. اگر README.md وجود
    نداشته باشد یا نشانگرها در آن پیدا نشوند، هیچ تغییری اعمال نمی‌شود.
    """
    if not os.path.exists(README_FILE):
        print("ℹ️  README.md not found — skipping stats update.")
        return

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    if STATS_START not in content or STATS_END not in content:
        print("ℹ️  Stats markers not found in README.md — skipping stats update.")
        return

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    stats_block = (
        f"{STATS_START}\n"
        f"**Total repos / تعداد کل ریپوها:** {total}  \n"
        f"**Needs review / نیازمند بررسی:** {needs_review_count}  \n"
        f"**Last updated / آخرین به‌روزرسانی:** {now}  \n"
        f"See the full list in [`CATALOG.md`](./CATALOG.md).\n"
        f"{STATS_END}"
    )

    pattern = re.escape(STATS_START) + r'.*?' + re.escape(STATS_END)
    new_content = re.sub(pattern, stats_block, content, flags=re.DOTALL)

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ README.md stats block updated")


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
    lines.append("# 🌟 کاتالوگ ریپوهای استارشده / Starred Repos Catalog")
    lines.append("")
    lines.append("> این فایل به‌صورت خودکار از روی `data/catalog.json` ساخته می‌شود — دستی ویرایشش نکنید.")
    lines.append("> This file is auto-generated from `data/catalog.json` — do not edit manually.")
    lines.append("")
    lines.append(f"**آخرین به‌روزرسانی / Last updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**تعداد کل ریپوها / Total repos:** {total}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # فهرست مطالب
    lines.append("## 📑 فهرست دسته‌ها")
    lines.append("")
    for category in sorted(by_category.keys()):
        count = sum(len(v) for v in by_category[category].values())
        anchor = slugify(category)
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

    with open(CATALOG_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ {CATALOG_OUTPUT_FILE} generated ({total} repos, {len(needs_review)} needing review)")

    update_readme_stats(total, len(needs_review))


if __name__ == '__main__':
    main()
