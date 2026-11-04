# ML-CHALLENGE — تحویل سه‌مرحله‌ای

این مخزن تحویل سه مرحلهٔ چالش ML (ترم ۳) است: کارخانهٔ داده، کارایی پایگاه‌داده، و یادگیری ماشین. هر مرحله در پوشهٔ مستقل خودش با نوت‌بوک، گزارش، تست‌ها و شواهد اجرا قرار دارد.

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

- **بنچمارک تأییدشده:** هر ۵ کوئری زیر 200ms (میانه: Q1=11.99، Q2=127.68، Q3=1.22، Q4=4.52، Q5=3.53 ms).
- **وضعیت:** شواهد PostgreSQL واقعی موجود است؛ برخی موارد تکمیلی (ممیزی FK، هزینهٔ درج ایندکس، مقایسهٔ کامل view/snapshot، بازسازی از صفر) هنوز شواهد تکمیلی لازم دارند.
- **جزئیات:** `stage-2-kiarash-akbari/readme.md` و `stage-2-kiarash-akbari/report.md`.

## مرحلهٔ ۳ — یادگیری ماشین

- **مسئله:** پیش‌بینی هزینه‌محور نکول اعتباری (Give Me Some Credit) با انتخاب آستانه از روی ماتریس هزینهٔ ۱۲:۱ (FN:FP).
- **وضعیت:** فونداسیون کامل است (قرارداد داده، منبع فایل، ریاضیات هزینه/آستانه، ویژگی‌ها، DDL نسخه‌دار، ۱۳۷ تست آفلاین OK). اجرای DDL روی PostgreSQL واقعی، بارگذاری `cs-training.csv`، آموزش مدل، و نوت‌بوک/گزارش نهایی هنوز انجام نشده‌اند.
- **اجرا (تست آفلاین):**

```bash
cd stage-3-kiarash-akbari
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v   # 137 tests, OK
```

- **جزئیات:** `stage-3-kiarash-akbari/readme.md`.

## وضعیت کلی

| مرحله | وضعیت |
|---|---|
| ۱ — کارخانهٔ داده | تحویل‌شده و ادغام‌شده |
| ۲ — کارایی پایگاه‌داده | شواهد اصلی موجود؛ موارد تکمیلی باقی‌مانده |
| ۳ — یادگیری ماشین | فونداسیون کامل؛ مدل‌سازی و نوت‌بوک نهایی باقی‌مانده |

## نکته برای داور

این مخزن آینهٔ مستقل کار است؛ توسعهٔ فعال در مخزن `dotin` انجام می‌شود. برای جزئیات تصمیم‌ها، شواهد عددی و روش اجرا، `report.md` و `readme.md` هر مرحله را ببینید.