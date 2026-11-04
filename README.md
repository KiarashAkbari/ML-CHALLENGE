# دورهٔ ML — سه مرحله، سه پوشه

هر پوشه یک مرحله است و کد مخصوص خودش را دارد؛ هیچ فایل دیگری در ریشه نیست.
کد مرحلهٔ ۱ و ۲ از مخزن `dotin` (نسخهٔ به‌روز) آمده و مرحلهٔ ۳ اینجا نوشته شده است.

| پوشه | چه دارد | brief | آزمون |
|---|---|---|---|
| `stage-1/` | کارخانهٔ داده: دریافت، اعتبارسنجی، پاک‌سازی، جمعیت، manifest | `stage-1/files-given/00,01` | `Ran 257 OK` |
| `stage-2/` | دیتابیس و بهینگی: طرح‌ریزی، viewها، as-of، کوئری‌های اندازه‌گیری‌شده | `stage-2/files-given/02` | `Ran 46 OK (skipped=25)` |
| `stage-3/` | مدل اعتباری با معیار هزینهٔ تصمیم + نوت‌بوک + گزارش | `stage-3/files-given/03` | `Ran 243 OK` |

قاعدهٔ حاکم بر هر سه پوشه در `AGENTS.md` ریشه است (فارسی برای متن، انگلیسی برای
شناسه‌ها، پین دقیق، مسیر نسبی، یک seed ثابت، نبودِ دادهٔ خام در Git).

## ترتیب اجرا

یک محیط مجازی در `stage-1/.venv` ساخته می‌شود و هر سه مرحله با همان
`.venv/bin/python` اجرا می‌شوند. دو دلیل دارد، نه سلیقه‌ای:

- روی توزیع‌های تازهٔ دبیان/اوبونتو `pip install` بیرون از venv با
  `externally-managed-environment` رد می‌شود (PEP 668) و اغلب دستور `python`
  هم وجود ندارد؛ فقط `python3`.
- `stage-2/scripts/bootstrap_test_db.sh` دنبال `../stage-1/.venv/bin/python`
  می‌گردد و اگر نباشد به `python3` خام برمی‌گردد که پین‌ها را ندارد.

```bash
python3 -V                                   # باید >= 3.12 باشد

cd stage-1
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .          # بستهٔ data_factory
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests     # ۲۵۷ آزمون، بدون اینترنت

cd ../stage-2
../stage-1/.venv/bin/python -m pip install -r requirements.txt   # -e ../stage-1 را هم می‌گیرد
../stage-1/.venv/bin/python -m unittest discover -s tests        # ۴۶ آزمون (۲۵ skip)

cd ../stage-3
../stage-1/.venv/bin/python -m pip install -r requirements.txt   # scikit-learn + joblib
../stage-1/.venv/bin/python -m unittest discover -s tests        # ۲۴۳ آزمون آفلاین
```

اگر `python3 -m venv` از `ensurepip` شکایت کرد:
`sudo apt install python3-venv` (یا `python3.12-venv`) و بعد دوباره بسازید.
برای نوت‌بوک هم همان پایتون را هسته کنید:
`../stage-1/.venv/bin/python -m notebook solution.ipynb` — اجرای Restart & Run All
از همان مسیرِ مرحلهٔ ۳، چون همهٔ مسیرهای داخل نوت‌بوک نسبی‌اند.

## آینهٔ pip، venvِ آماده، و مسیری که اصلاً دانلود نمی‌کند

سه راه هست و ترتیبشان تصادفی نیست: اول ببینید شبکه چه چیزی را رد می‌کند، بعد نصب کنید.

**۱) بدون شبکه، فقط `PYTHONPATH` (سریع‌ترین و قابل‌اتکا‌ترین).** هیچ نصبی لازم نیست؛
`data_factory` از این متغیر می‌آید و `credit` را هم نوت‌بوک و هم تست‌ها خودشان به
`sys.path` اضافه می‌کنند (سلول اول نوت‌بوک `src/` را می‌گذارد):

```bash
cd "$(git rev-parse --show-toplevel)"
P=/path/to/your-existing-venv/bin/python      # یا .venv/bin/python اگر تازه می‌سازید
export PYTHONPATH="$PWD/stage-1/src"          # برای data_factory
cd stage-1 && $P -m unittest discover -s tests
cd ../stage-2 && $P -m unittest discover -s tests
cd ../stage-3 && export PYTHONPATH="$PWD/src:$PYTHONPATH" && $P -m unittest discover -s tests
```

همین روشی است که هر سه مجموعه آزمون با آن سبز شده‌اند، پس «راه حل موقت» نیست. تنها
چیزی که با آن فعال نمی‌شود فرمان `data-factory` (console script) است.

**۲) نصب محلی، آفلاین:** اگر اصرار بر install دارید، `-e` با دو فلگ کار می‌کند:

```bash
cd stage-1
$P -m pip install --no-index --no-deps --no-build-isolation -e .
```

`--no-deps` لازم است چون وابستگی‌های `pyproject.toml` ریشه‌ای (requests، sqlalchemy،
psycopg) قبلاً در venv هستند؛ و `--no-build-isolation` بدون بستهٔ `wheel` در venv با
`error: invalid command 'bdist_wheel'` می‌شکند — آن‌وقت یا `wheel` را نصب کنید یا روش ۱.

**۳) با ایندکس:** فقط **محل دانلود** عوض می‌شود؛ پین‌ها دست‌نخورده‌اند و `-e ../stage-1`
که داخل `requirements.txt` مرحلهٔ ۲ و ۳ است اصلاً دانلود نمی‌کند (مسیر محلی است). نام
آینه را در این فایل پیدا نمی‌کنید و دلیلش همان است که دادهٔ خام در Git نمی‌آید: هر
آینه‌ای که من از اینجا نمی‌توانم بسنجم، نباید به شکل حقیقت در مستندات بنشیند. یک
متغیر محیطی کافی است تا همه‌چیز از آن بخواند:

```bash
# آینهٔ Runflare (دانشجوی تحویل‌دهنده؛ از جعبهٔ کاریِ من قابل تست نبود)
export PIP_INDEX_URL="https://mirror-pypi.runflare.com/simple"
export PIP_TIMEOUT=60 PIP_RETRIES=5                # پیش‌فرض ۱۵s است؛ روی مسیر ناپایدار کم است
cd stage-3 && $P -m pip install -r requirements.txt
```

اگر همان اول خطا داد، شکلِ درستِ مسیر را با یک حلقه پیدا کنید (بعضی آینه‌ها `/simple`
هستند، بعضی `/pypi/simple`، بعضی ریشهٔ دامنه):

```bash
for u in /simple /pypi/simple /; do
  b="${u%/}"      # اسلش انتهایی را حذف کن، وگرنه //six/ می‌شود
  printf "%-14s %s\n" "$b" "$(curl -sSL -m 8 -o /dev/null -w '%{http_code}' \
      "https://mirror-pypi.runflare.com$b/six/" 2>/dev/null || echo down)"
done   # 200 یعنی همین؛ آن‌وقت PIP_INDEX_URL = https://…<مسیری که 200 داد>
```

`-L` لازم است، نه سلیقه: روی `pypi.org` خودِ همین دو مسیر را آزمودم و
`/pypi/simple/six/` اول `301` می‌دهد و با دنبال‌کردنِ ریدایرکت `200` — یعنی بدون
`-L` یک آینهٔ سالم را «مرده» گزارش می‌کنید. منطق حلقه هم آزموده‌شده است:
`/simple/six/` جواب `200` می‌دهد و شکلِ خراب (`/simple-six/`) جواب `404`.

نکته‌ای که بدون آن تشخیص اشتباه می‌شود: **pip به دو میزبان وصل می‌شود**، نه یکی.
فهرست نسخه‌ها از `pypi.org` (یا ایندکس آینه) می‌آید و خودِ فایل از میزبانی که آن
فهرست معرفی می‌کند. پس می‌تواند `200` گرفتن از ایندکس با `curl` درست باشد و دانلود با
`Temporary failure in name resolution` برای `files.pythonhosted.org` بشکند؛ در آن
حالت آینه‌ای لازم است که **خودِ wheel‌ها را میزبانی کند** و URL فایل را به خودش
بازنویسی کند، نه فقط صفحهٔ ایندکس را پروکسی کند. ببینید pip از کجا برمی‌دارد:

```bash
$P -m pip install -v --no-deps scikit-learn==1.9.1 2>&1 | grep -E "Looking in indexes|Downloading|Download URL"
```

اگر در خروجی `files.pythonhosted.org` دیدید، آن آینه برای این مشکل کاری نمی‌کند. اگر
هیچ‌کدام کار نکرد، wheelhouse تمیزترین راه است: روی هر ماشینِ وصل‌شده
`pip download -r requirements.txt -d /tmp/wheels` و روی این ماشین
`$P -m pip install --no-index --find-links /tmp/wheels -r requirements.txt` — همان
پین‌ها، بدون هیچ ایندکسی.

`--index-url` را در خودِ `requirements.txt` ننویسید: همان فایل را کسی که به این
میزبان دسترسی ندارد می‌خواند و به‌جای یک نصب کند، با خطای DNS می‌بندد؛ و
`--extra-index-url` هم بدتر است، چون نام بسته می‌تواند از هر دو میزبان حل شود و
«کدام میزبان این نسخه را داد» دیگر قابل گفتن نیست. پس آینه یک تنظیمِ محیطی است، نه
بخشی از قفل.

`pip config --site set global.index-url ...` هم کار می‌کند ولی در venv نوشته می‌شود و
روی هر نصبِ بعدیِ همان venv اثر می‌گذارد؛ با آینه‌ای که بعداً می‌میرد، خودِ venv
بی‌مصرف می‌شود. اگر نوشتید، با `pip config --site unset global.index-url` پاکش کنید
(`ERROR: No such key` یعنی پاک شده).

دو امضای خطا که اگر دیدید، مشکل از شبکه یا مسیر نیست، از خودِ فرمان است:

- `../stage-1 is not a valid editable requirement` → `requirements.txt` مرحلهٔ ۲ و ۳ را
  از بیرون پوشهٔ آن مرحله اجرا کرده‌اید؛ pip مسیر نسبی را با **pwd** حل می‌کند، نه با
  جای فایل. `cd stage-2` بعد `pip install -r requirements.txt`.
- `Read timed out ... - skipping` روی هر میزبان → ایندکسِ داخل venv مسموم شده؛ روش
  unset بالا را بزنید و دوباره تست کنید.
- `Temporary failure in name resolution` روی میزبانِ فایل، در حالی که `curl` از
  ایندکس `200` گرفته → آینه فقط صفحهٔ ایندکس را پروکسی می‌کند و wheel را از همان
  میزبان اصلی نشان می‌دهد؛ با `-v` و خط `Download URL` ببینید از کجا برمی‌دارد.
- `ImportError: Failed to import test module: …` و `Ran 206` به‌جای `Ran 228` → یک
  بستهٔ نصب‌نشده بیست‌ودو آزمون را با خودش می‌برد، چون unittest خرابیِ import را برای
  کل ماژول یک خطا گزارش می‌کند. قبل از هر قضاوتی: `$P -c "import joblib, sklearn"`.

اگر venvِ کارکردی از قبل دارید، ساختنِ جدید لازم نیست؛ فقط یک‌بار چک کنید بستهٔ
مرحلهٔ ۱ از **همین** درخت می‌آید:

```bash
$P -c "from data_factory import config; print(config.__file__)"
```

دلیلش تکرارپذیری است، نه سلیقه: `requirements.txt` مرحلهٔ ۲ و ۳ با `-e ../stage-1`
نوشته شده، پس اگر venv قدیمی `data_factory` را به clone دیگری وصل کرده باشد، آزمون‌ها
کدِ آن مخزن را اجرا می‌کنند و «چیزی که تست شد» با چیزی که تحویل می‌شود فرق می‌کند.
خروجی باید مسیر همین مخزن باشد؛ اگر clone دیگری چاپ شد، یا روش ۱ را با `PYTHONPATH`
همین مخزن انتخاب کنید، یا روش ۲ را از داخل `stage-1` اجرا کنید.

دادهٔ خام هیچ‌جا در Git نیست؛ `config/credit.example.toml` و
`stage-1/config/default.toml` محل گذاشتن مسیرها روی ماشین شماست.
