# 🌟 Categorizing Starred Repos

A semi-automated, AI-assisted system for organizing GitHub starred repositories into a categorized, searchable catalog — without requiring an AI API key.

سیستمی نیمه خودکار و مبتنی بر هوش مصنوعی برای دسته‌بندی ریپوهای استارشده‌ی گیتهاب در قالب یک کاتالوگ منظم و قابل‌جست‌وجو — بدون نیاز به AI API key.

---

## 📊 Catalog Stats / آمار کاتالوگ

<!-- CATALOG_STATS_START -->
**Total repos / تعداد کل ریپوها:** 29  
**Needs review / نیازمند بررسی:** 0  
**Last updated / آخرین به‌روزرسانی:** 2026-08-29 22:10:25 UTC  

**🌟My full categorized list in [`CATALOG.md`](./CATALOG.md).**
<!-- CATALOG_STATS_END -->

---

## 🧭 About / درباره‌ی پروژه

As the number of starred repositories grows, finding a specific project or remembering what it does becomes harder over time. This project automatically tracks newly starred repos, uses an AI model (Claude or ChatGPT — whichever you have access to, no API key needed) to classify and describe them and maintains a permanent, structured catalog that scales to hundreds or thousands of repos.

با افزایش تعداد ریپوهای استارشده، پیدا کردن پروژه‌ی موردنظر و به‌خاطر سپردن کاربرد هرکدام به‌مرور دشوار می‌شود. این پروژه به‌صورت خودکار ریپوهای تازه استارشده را شناسایی می‌کند، با کمک یک مدل هوش مصنوعی (کلاد یا چت‌جی‌پی‌تی — هرکدام که در دسترس داشته باشید، بدون نیاز به API key) آن‌ها را دسته‌بندی و توصیف می‌کند و یک کاتالوگ دائمی و ساختاریافته نگه می‌دارد که با رشد تعداد ریپوها همچنان قابل‌مدیریت باقی می‌ماند.

---

## ⚙️ How It Works / نحوه‌ی کار

```
GitHub Stars
     ↓
Fetch new starred repos
     ↓
AI-assisted categorization
  (manual: you + docs/prompt-template.txt → Claude / ChatGPT)
     ↓
Merge into catalog
     ↓
Generate CATALOG.md
```

**Why no AI API key is needed?**
The AI analysis step is done manually — you paste `inbox.json` + `categories.yaml`, along with the fixed instructions in [`docs/prompt-template.txt`](./docs/prompt-template.txt), into Claude or ChatGPT's normal chat interface, then save the model's JSON response as `data/ai_output.json` and upload it to the repo. The prompt template tells the model exactly what fields to return and how to handle uncertain cases. All the repetitive, mechanical work (fetching, merging, building) is fully automated via GitHub Actions.

**چرا نیازی به API key هوش مصنوعی نیست؟**
مرحله‌ی تحلیل هوش مصنوعی به‌صورت دستی انجام می‌شود — محتوای `inbox.json` و `categories.yaml` را به‌همراه دستورالعمل ثابت موجود در [`docs/prompt-template.txt`](./docs/prompt-template.txt) در پنجره‌ی چت عادی کلاد یا چت‌جی‌پی‌تی پیست می‌کنید، سپس پاسخ JSON مدل را با نام `ai_output.json` ذخیره و در پوشه‌ی `data` آپلود می‌کنید. این پرامپت دقیقاً مشخص می‌کند مدل چه فیلدهایی برگرداند و با موارد نامطمئن چطور رفتار کند. تمام کارهای تکراری و ماشینی (جمع‌آوری، ادغام، ساخت خروجی) کاملاً خودکار و توسط GitHub Actions انجام می‌شود.

---

## 📁 Project Structure / ساختار پروژه

```
.
├── .github/workflows/
│   ├── categorize-starred-repos.yml   # fetch new stars daily
│   └── process-ai-results.yml         # merge AI output on upload
│
├── scripts/
│   ├── categorize.py      # fetches new starred repos → inbox.json
│   ├── merge_catalog.py   # merges ai_output.json → catalog.json
│   └── build_readme.py    # generates CATALOG.md + README stats
│
├── data/
│   ├── inbox.json         # repos waiting for AI analysis
│   ├── categories.yaml    # controlled taxonomy of categories
│   ├── catalog.json       # permanent source of truth
│   └── ai_output.json     # (temporary — created by you, deleted after merge)
│
├── docs/
│   └── prompt-template.txt   # fixed instructions you paste into Claude/ChatGPT
│
├── CATALOG.md              # auto-generated, human-readable catalog
├── README.md                # this file — project introduction
└── LICENSE                  # MIT License
```

---

## 🚀 Using This For Your Own Stars / استفاده برای ریپوهای خودتان

1. Fork this repository.
2. Create a GitHub Personal Access Token with access to your starred repos, and add it as a repository secret named `STARRED_REPOS_TOKEN`.
3. Enable "Read and write permissions" for GitHub Actions under Settings → Actions → General.
4. Let the daily workflow collect new stars into `data/inbox.json`.
5. Whenever you like, paste `data/inbox.json` + `data/categories.yaml` into Claude or ChatGPT along with the prompt template ([`docs/prompt-template.txt`](./docs/prompt-template.txt)), and upload the JSON response as `data/ai_output.json`.
6. Everything else — merging and rebuilding the catalog — happens automatically.

**Note:** If you have a large number of existing starred repos (e.g. 1000+), the first run may take a few minutes due to GitHub's rate limits — this is expected and safe.

۱. این ریپو را Fork کنید.
۲. یک GitHub Personal Access Token با دسترسی به ریپوهای استارشده بسازید و آن را به‌عنوان Secret با نام `STARRED_REPOS_TOKEN` اضافه کنید.
۳. از مسیر Settings → Actions → General، گزینه‌ی "Read and write permissions" را فعال کنید.
۴. اجازه دهید workflow روزانه، ریپوهای جدید را در `data/inbox.json` جمع‌آوری کند.
۵. هر زمان که خواستید، محتوای `data/inbox.json` و `data/categories.yaml` را همراه با متن [`docs/prompt-template.txt`](./docs/prompt-template.txt) به کلاد یا چت‌جی‌پی‌تی بدهید، و پاسخ JSON را در `data/ai_output.json` آپلود کنید.
۶. بقیه‌ی کار (ادغام و بازسازی کاتالوگ) به‌صورت خودکار انجام می‌شود.

**نکته:** اگه تعداد زیادی ریپوی استارشده از قبل دارید (مثلاً بیش از ۱۰۰۰ تا)، اولین اجرا ممکنه چند دقیقه طول بکشه — این طبیعی و بی‌خطره.

---

## 📜 License / مجوز

This project is licensed under the [MIT License](./LICENSE) — free to use, modify, and distribute, with attribution.

این پروژه تحت [مجوز MIT](./LICENSE) منتشر شده است — استفاده، تغییر و توزیع آزاد، با ذکر منبع.
