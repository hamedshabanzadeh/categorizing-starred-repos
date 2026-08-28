#!/usr/bin/env python3
"""
مرحله ادغام: خروجی تحلیل هوش مصنوعی (data/ai_output.json) را می‌خواند،
با آیتم‌های موجود در data/inbox.json (بر اساس id عددی گیتهاب) تطبیق می‌دهد،
و نتیجه را در data/catalog.json (بانک اطلاعاتی دائمی) ثبت می‌کند.
آیتم‌های merge شده از inbox حذف می‌شوند و ai_output.json در پایان پاک می‌شود.
"""

import os
import json
from datetime import datetime, timezone

INBOX_FILE = 'data/inbox.json'
AI_OUTPUT_FILE = 'data/ai_output.json'
CATALOG_FILE = 'data/catalog.json'

REQUIRED_FIELDS = ['id', 'category', 'purpose', 'description_fa']


def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    if not os.path.exists(AI_OUTPUT_FILE):
        print("ℹ️  No data/ai_output.json found. Nothing to merge.")
        return

    results = load_json(AI_OUTPUT_FILE, [])
    if not results:
        print("ℹ️  data/ai_output.json is empty. Nothing to merge.")
        return

    inbox = load_json(INBOX_FILE, {'items': []})
    inbox_by_id = {item['id']: item for item in inbox.get('items', [])}

    catalog = load_json(CATALOG_FILE, {'repos': []})
    catalog_by_id = {entry['id']: entry for entry in catalog.get('repos', [])}

    merged_ids = []
    skipped = []
    needs_review = []
    suggested_categories = []

    for result in results:
        missing = [f for f in REQUIRED_FIELDS if not result.get(f)]
        rid = result.get('id')

        if missing:
            skipped.append((rid, f"missing fields: {', '.join(missing)}"))
            continue

        if rid not in inbox_by_id:
            skipped.append((rid, "not found in inbox (already merged or invalid id)"))
            continue

        item = inbox_by_id[rid]

        entry = {
            'id': rid,
            'repo': item['repo'],
            'url': item['url'],
            'category': result.get('category'),
            'subcategory': result.get('subcategory') or '',
            'purpose': result.get('purpose'),
            'description_fa': result.get('description_fa'),
            'tags': result.get('tags', []),
            'confidence': result.get('confidence', 'medium'),
            'needs_review': bool(result.get('needs_review', False)),
            'stars': item['stars'],
            'language': item['language'],
            'topics': item['topics'],
            'added_at': datetime.now(timezone.utc).isoformat()
        }

        catalog_by_id[rid] = entry  # اضافه یا به‌روزرسانی
        merged_ids.append(rid)

        if entry['needs_review'] or entry['confidence'] == 'low':
            needs_review.append(item['repo'])

        if result.get('suggested_new_category'):
            suggested_categories.append(
                f"{item['repo']} → {result.get('suggested_category', '?')}"
            )

    if not merged_ids:
        print("ℹ️  No matching items were merged.")
        if skipped:
            print("⚠️  Skipped entries:")
            for rid, reason in skipped:
                print(f"   - id {rid}: {reason}")
        return

    # ذخیره‌ی catalog به‌روزشده
    catalog['repos'] = list(catalog_by_id.values())
    save_json(CATALOG_FILE, catalog)

    # حذف آیتم‌های merge‌شده از inbox
    remaining_inbox_items = [item for item in inbox.get('items', []) if item['id'] not in merged_ids]
    save_json(INBOX_FILE, {'items': remaining_inbox_items})

    # پاک‌کردن فایل خروجی AI که پردازش شد
    os.remove(AI_OUTPUT_FILE)

    print(f"✅ Merged {len(merged_ids)} repos into catalog.json")
    print(f"⏳ {len(remaining_inbox_items)} items still remaining in inbox")

    if skipped:
        print("\n⚠️  Skipped entries:")
        for rid, reason in skipped:
            print(f"   - id {rid}: {reason}")

    if needs_review:
        print("\n🔍 Needs manual review (low confidence):")
        for repo in needs_review:
            print(f"   - {repo}")

    if suggested_categories:
        print("\n💡 Suggested new categories (review categories.yaml manually):")
        for suggestion in suggested_categories:
            print(f"   - {suggestion}")


if __name__ == '__main__':
    main()
