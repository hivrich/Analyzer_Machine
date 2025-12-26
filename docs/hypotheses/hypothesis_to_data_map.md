# Hypothesis → Data Map (Analyzer Machine)

Назначение: маппинг сигналов/гипотез на конкретные данные и capabilities проекта.
Агент использует этот файл, чтобы сам выбирать какие команды выполнять, не требуя от пользователя “технического языка”.

Важно:
- Capabilities — расширяемые. Агент может предлагать новые capabilities/срезы/сегменты и (при необходимости) дописывать код под новую гипотезу.
- Любой вывод в отчёте обязан ссылаться на конкретный evidence (workbook/кэш-файлы).

---

## Capabilities registry (текущее состояние проекта)

### Реализовано сейчас

C1. sources_period_compare:
- Команда: `python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]`
- Артефакты:
  - `data_cache/<client>/metrika_sources_raw_*.json`
  - `data_cache/<client>/metrika_sources_norm_*.json`
  - `data_cache/<client>/analysis_sources_*.json` (workbook)
- Назначение: дельты/вклады по источникам трафика.

C2. landing_pages_period_compare (overall, без сегментации):
- Команды:
  - `python -m app.cli metrika-pages <client> <date1> <date2> [--limit N] [--refresh]`
  - `python -m app.cli analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]`
- Артефакты:
  - `data_cache/<client>/metrika_pages_raw_*.json`
  - `data_cache/<client>/metrika_pages_norm_*.json`
  - `data_cache/<client>/analysis_pages_*.json` (workbook)
- Назначение: дельты/вклады по входным страницам (landing pages) по визитам между периодами (в целом по сайту).
- Ограничение: нет разреза/фильтра “только органика / только referral / только Direct”. Для этого нужен отдельный capability (см. ниже).

### Не реализовано (планируемые capabilities)

C2.1 landing_pages_period_compare_by_source (landing pages × source/channel, сегментация):
- Цель: строить landing pages внутри выбранного источника/канала (например, только Search engine traffic / только Link traffic).
- Статус: не реализовано.

C3. goals_period_compare (конверсии по goal_id, по источникам/страницам)
C4. ecommerce_period_compare (transactions, revenue, AOV, CR; по источникам/страницам)
C5. search_console_pages_queries_compare (GSC: clicks/impr/ctr/pos по страницам/запросам)
C6. webmaster_pages_queries_compare (Яндекс.Вебмастер: аналогично + индексация)
C7. crm_sales_compare (заказы/выручка из CRM/платёжки как ground truth)

---

## Map: Signals → checks → capabilities

Формат:
- Signal: что видим
- Primary checks: минимальный набор проверок (сначала)
- Secondary checks: если primary не объяснил кейс
- Capability: чем это делаем (C1..C7)
- Evidence: какие файлы должны появиться

---

### S1: Общий трафик упал (YoY/WoW)

Primary checks:
- Декомпозиция по источникам: кто дал вклад в падение/рост.
Capability: C1
Evidence:
- `analysis_sources_*.json` + `metrika_sources_norm/raw` по обоим периодам

Secondary checks:
- Драйверы падения/роста по входным страницам (в целом по сайту).
Capability: C2
Evidence:
- `analysis_pages_*.json` + `metrika_pages_norm/raw` по обоим периодам

---

### S2: Упал органический трафик (Search engine traffic)

Primary checks:
- Вклад органики в общее изменение (из C1).
Capability: C1
Evidence:
- `analysis_sources_*.json`

Secondary checks:
- Landing pages, которые дали наибольший вклад в изменение трафика (в целом).
Capability: C2
Evidence:
- `analysis_pages_*.json`

Secondary checks (требуют новых capabilities):
- Landing pages внутри органики (нужна сегментация по источнику/каналу): C2.1
- GSC/Вебмастер по страницам/запросам: клики/показы/CTR/позиции (C5, C6)
- Индексация/исключения (C6)

---

### S3: Яндекс упал сильнее Google (или наоборот)

Primary checks:
- Подтвердить различие в поисковых источниках (частично через C1, но это “общая органика” без разделения по системам).
Capability: C1 (частично)

Secondary checks:
- GSC vs Вебмастер по страницам/запросам (C5, C6)
- Индексация/ошибки по конкретным URL (C6)
- Сопоставить драйверы падения по страницам (C2) и затем подтвердить через C5/C6

---

### S4: Трафик стабилен, но упали продажи/конверсия

Primary checks:
- Ecommerce: transactions/revenue/AOV/CR по периодам (C4)
- Валидация трекинга: CRM/платёжка vs Метрика (C7)
Evidence:
- ecommerce workbook + crm workbook

Secondary checks:
- Микс источников/landing pages изменился? (C1 + C2)
- Поведение на коммерческих страницах: bounceRate/pageDepth/duration по сегментам (требует расширения C2/C2.1 или новых срезов)

---

### S5: Падение концентрировано в нескольких landing pages

Primary checks:
- Landing pages × period compare (в целом по сайту).
Capability: C2
Evidence:
- `analysis_pages_*.json` + `metrika_pages_norm/raw`

Secondary checks:
- Поисковые метрики по этим URL (C5/C6)
- Индексация/исключения по этим URL (C6)
- Если нужно доказать “это именно органика” — сегментация landing pages внутри органики (C2.1)

---

### S6: Резко упал referral/link traffic

Primary checks:
- C1: вклад “Link traffic” по источникам.
- C2: какие landing pages дали вклад в общее падение/рост (как “быстрый скрининг”).
Capability:
- C1 + C2
Evidence:
- `analysis_sources_*.json` + `analysis_pages_*.json`

Secondary checks (требуют новых capabilities):
- Landing pages внутри referral/link (сегментация): C2.1
- Если Direct растёт синхронно: гипотеза про атрибуцию/редиректы (в рамках инструмента — через срезы C2.1 и/или CRM-валидацию C7)

---

### S7: Аномалии Direct

Primary checks:
- C1: доля и динамика Direct vs других каналов.
Evidence:
- `analysis_sources_*.json`

Secondary checks:
- Брендовый спрос (C5/C6 по брендовым запросам)
- Проверка UTM/редиректов: в рамках инструмента — через срезы landing pages и сегменты (C2 + C2.1)

---

### S8: Рост отказов/падение вовлеченности

Primary checks:
- Поведение по источникам (частично в metrika sources norm).
Capability:
- C1 (частично)

Secondary checks:
- Поведение по landing pages и сегментам (нужны расширения вокруг C2/C2.1 или отдельные отчёты)
- Техническая гипотеза: нужна внешняя диагностика (не Метрика), фиксируется как “Next actions”

---

## Правило принятия решений (как агент выбирает следующий шаг)

1) Если речь о трафике — начинать с C1 (sources compare).
2) Затем выполнять C2 (landing pages overall), чтобы быстро найти страницы-драйверы изменения.
3) Если нужна причинность “внутри источника/канала” (например, “только органика”) — требуется C2.1. Если C2.1 отсутствует, агент должен явно пометить “Capability missing” и предложить:
   - реализовать C2.1 (код + команда),
   - или переключиться на C5/C6 (если доступно) для доказательств по поиску,
   - или уточнить постановку задачи.
4) Если пользователь говорит “конверсия/ecommerce/продажи” — приоритет C4 и C7. Если C4/C7 отсутствуют — “Capability missing”.
5) Любой вывод в отчёте должен ссылаться на конкретный evidence (workbook/кэш) и быть проверяемым.
