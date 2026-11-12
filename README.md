# ML-CHALLENGE — تحویل سه‌مرحله‌ای

این مخزن تحویل سه مرحلهٔ چالش ML (ترم ۳) است: کارخانهٔ داده، کارایی پایگاه‌داده، و یادگیری ماشین. هر مرحله در پوشهٔ مستقل خودش با نوت‌بوک، گزارش، تست‌ها و شواهد اجرا قرار دارد.

> **نکتهٔ مهم دربارهٔ اعداد:** تعداد تست‌ها، وضعیت OK و اعداد بنچمارک در این README از اجرای واقعی روی ماشین نویسنده آمده‌اند و شواهدشان در `report.md`/`docs/evidence/` هر مرحله موجود است. بازتولید دقیق روی ماشین داور به نسخهٔ Python، وابستگی‌های قفل‌شده و در دسترس‌بودن PostgreSQL وابسته است.

## ساختار مخزن

```
ML-CHALLENGE/
├── stage-1-kiarash-akbari/   # مرحلهٔ ۱ — کارخانهٔ داده (NYC 311)
├── stage-2-kiarash-akbari/   # مرحلهٔ ۲ — کارایی پایگاه‌داده (Olist)
├── stage-3-kiarash-akbari/   # مرحلهٔ ۳ — یادگیری ماشین (نکول اعتباری)
└── README.md                 # همین فایل
```

## مرحلهٔ ۱ — کارخانهٔ داده

- **مسئله:** دریافت، اعتبارسنجی، پاک‌سازی و ترکیب شکایت‌های 311 نیویورک (NYPD، شش نوع noise، ژانویه 2025 تا ژوئن 2026) با جمعیت هر محله.
- **اجرا:**

```bash
cd stage-1-kiarash-akbari
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m unittest discover -s tests      # تست‌ها، بدون اینترنت
python -m data_factory run                # کل کارخانه با یک فرمان
```

- **تست‌ها:** `257 tests, OK` روی ماشین نویسنده؛ شواهد و جزئیات در `report.md` و README مرحلهٔ ۱.
- **خروجی‌ها:** `data/curated/cases.csv`، `data/curated/complaints_by_area_month.csv`، `data/curated/data_quality_report.json`، `data/quarantine/quarantine.jsonl`، `data/run_manifest.json`.
- **وضعیت:** تحویل‌شده و ادغام‌شده (PR #19 در مخزن اصلی `dotin`).
- **جزئیات:** `stage-1-kiarash-akbari/README.md` و `stage-1-kiarash-akbari/report.md`.

## مرحلهٔ ۲ — کارایی پایگاه‌داده

- **مسئله:** طراحی schema برای Olist، بارگذاری خروجی مرحلهٔ ۱ در schema جدا، و بهینه‌سازی ۵ کوئری تحلیلی زیر بودجهٔ 200ms با شاهد پلن قبل/بعد.
- **اجرا:**

```bash
cd stage-2-kiarash-akbari
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
# بارگذاری از پوشهٔ مرحلهٔ ۱:
cd ../stage-1-kiarash-akbari
../stage-2-kiarash-akbari/.venv/bin/python -m data_factory load-database \
  --config config/default.toml --reset
cd ../stage-2-kiarash-akbari
```

- **بنچمارک:** اعداد میانه/بیشینهٔ هر ۵ کوئری (همه زیر 200ms) از اجرای واقعی روی ماشین نویسنده‌اند؛ شاهد: `data/curated/benchmark-final-*.json` و خروجی نوتبوک.
- **تست‌ها:** `257 tests OK` (مرحلهٔ ۱) و `46 tests OK (skipped=25)` (مرحلهٔ ۲ بدون DB) از اجرای روی ماشین نویسنده؛ شواهد PostgreSQL واقعی در `docs/evidence/`.
- **وضعیت:** شواهد PostgreSQL واقعی موجود است؛ برخی موارد تکمیلی (ممیزی FK، هزینهٔ درج ایندکس، مقایسهٔ کامل view/snapshot، بازسازی از صفر) هنوز شواهد تکمیلی لازم دارند.
- **جزئیات:** `stage-2-kiarash-akbari/readme.md` و `stage-2-kiarash-akbari/report.md`.

## مرحلهٔ ۳ — یادگیری ماشین

- **مسئله:** پیش‌بینی هزینه‌محور نکول اعتباری (Give Me Some Credit) با انتخاب آستانه از روی ماتریس هزینهٔ ۱۲:۱ (FN:FP).
- **اجرای واقعی:** نوت‌بوک روی `cs-training.csv` واقعی Kaggle و PostgreSQL واقعی اجرا شد: ۱۵۰٬۰۰۰ ردیف بارگذاری شد و هیچ ردیفی رد نشد؛ ۲۴ سلول کد بدون خطا در ۵۹۳٫۳ ثانیه (سقف ۲۰ دقیقه).
- **نتیجه:** هزینهٔ مجموعهٔ holdout برابر ۳۶۸٫۰۷ در هر ۱۰۰۰ متقاضی است؛ خط مبنای «هیچ‌کس را علامت نزن» ۸۰۲ است، یعنی کاهش ۵۴٫۱۱٪. همهٔ این اعداد از `docs/evidence/real/credit_evidence.json` آمده‌اند و در `report.md` با آزمون ردیابی سنجیده شده‌اند.
- **تست‌ها:** `282 tests, OK (skipped=1)` روی ماشین نویسنده (Python 3.12.3).
- **اجرا:** مرحلهٔ ۳ به پکیج `data_factory` مرحلهٔ ۱، PostgreSQL و فایل `cs-training.csv` (از رقابت Kaggle) نیاز دارد؛ دستورهای دقیق نصب، بارگذاری و Run All در `stage-3-kiarash-akbari/README.md` آمده است.
- **جزئیات:** `stage-3-kiarash-akbari/README.md` و `stage-3-kiarash-akbari/report.md`.

## وضعیت کلی

| مرحله | وضعیت |
|---|---|
| ۱ — کارخانهٔ داده | تحویل‌شده و ادغام‌شده |
| ۲ — کارایی پایگاه‌داده | شواهد اصلی موجود؛ موارد تکمیلی باقی‌مانده |
| ۳ — یادگیری ماشین | تحویل‌شده با اجرای واقعی روی دادهٔ Kaggle؛ بازتولید روی ماشین دیگر بررسی‌نشده |

## نکته برای داور

این مخزن آینهٔ مستقل کار است؛ توسعهٔ فعال در مخزن `dotin` انجام می‌شود. برای جزئیات تصمیم‌ها، شواهد عددی و روش اجرا، `report.md` و `readme.md` هر مرحله را ببینید. اعداد تست/بنچمارک ادعای تضمین روی هر ماشین نیستند؛ شواهد اجرا ضمیمه‌اند و داور می‌تواند با دستورهای بالا بازتولیدشان کند.