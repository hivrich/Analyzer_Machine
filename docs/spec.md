# Analyzer Machine — Spec (MVP)

## 1) Цель

Сделать on-demand инструмент (CLI + библиотека), который по запросу в “человеческой” форме (в перспективе — голос → текст):
- подтягивает внешние данные (в MVP: Яндекс.Метрика),
- считает сравнения и вклады строго кодом (без “арифметики в голове” и без выдуманных чисел),
- сохраняет доказательные артефакты (evidence pack): raw → norm → workbook,
- позволяет агенту (в Cursor) итеративно формулировать и проверять SEO-гипотезы через capabilities.

Важно: архитектура должна оставаться **расширяемой**. Добавление новых срезов/источников данных допускается как новые capabilities без переписывания ядра.

---

## 2) Не-цели (в MVP)

- Постоянный фоновый сбор данных (cron/etl).
- Обязательная БД (достаточно файлового кэша).
- BI/дашборды.
- Автоматическая рассылка отчётов (Telegram/email).
- Полноценный “голосовой интерфейс” как отдельный продукт (в MVP достаточно текстового входа; голос = внешний слой транскрибации).

---

## 3) Пользовательские сценарии (MVP)

### 3.1 Быстрый снимок
Пользователь запускает команду и получает:
- таблицу (в терминале) по выбранному срезу за период,
- сохранённый кэш (raw + norm).

### 3.2 Диагностика “что просело и почему”
Пользователь запускает сравнение двух периодов и получает:
- totals (P1 vs P2),
- дельты (abs и %),
- вклады (contribution) и top-drivers,
- workbook JSON как доказательную базу для интерпретации/отчёта.

---

## 4) Источники данных (MVP)

Обязательно:
- Яндекс.Метрика Reporting API `/stat/v1/data` (сессии `ym:s:*`)

Опционально позже:
- Яндекс.Вебмастер API
- Google Search Console API
- CRM/платёжка (ground truth по продажам)

---

## 5) Архитектура (MVP)

Компоненты:

1) **Config**
- читает `clients/<client>/config.yaml`
- хранит counter_id и базовые настройки клиента

2) **Collector**
- вызывает API Метрики
- сохраняет raw ответы в `data_cache/<client>/...raw...json`

3) **Normalizer**
- преобразует raw в нормализованные таблицы (list[dict])
- сохраняет norm в `data_cache/<client>/...norm...json`

4) **Analyzer**
- рассчитывает totals/deltas/contributions/top-N строго кодом
- сохраняет результат в “workbook” JSON (компактный артефакт для отчёта/LLM)

5) **CLI**
- entrypoint: `python -m app.cli ...`
- команды для:
  - сборов (metrika-*)
  - анализа (analyze-*)
  - диагностики (clients/show/validate)

6) **Agent layer (позже, поверх MVP)**
- принимает задачу естественным языком (в перспективе голос → текст),
- выбирает capabilities, запускает CLI, собирает evidence pack,
- формирует отчёт по workbook (LLM — только на уровне текста, не расчётов),
- если capability отсутствует — фиксирует “Capability missing” и предлагает расширение.

---

## 6) Capabilities (реализовано сейчас)

Фактический набор доступных capabilities фиксируется также в:
- `docs/hypotheses/hypothesis_to_data_map.md`

### Реализовано сейчас

C1. Sources period compare
- Сбор: `python -m app.cli metrika-sources <client> <date1> <date2>`
- Анализ: `python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]`
- Артефакты:
  - `data_cache/<client>/metrika_sources_raw_<date1>_<date2>.json`
  - `data_cache/<client>/metrika_sources_norm_<date1>_<date2>.json`
  - `data_cache/<client>/analysis_sources_<p1><p1>__<p2><p2>.json`

C2. Landing pages period compare (overall)
- Сбор: `python -m app.cli metrika-pages <client> <date1> <date2> [--limit N] [--refresh]`
- Анализ: `python -m app.cli analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]`
- Артефакты:
  - `data_cache/<client>/metrika_pages_raw_<date1>_<date2>.json`
  - `data_cache/<client>/metrika_pages_norm_<date1>_<date2>.json`
  - `data_cache/<client>/analysis_pages_<p1><p1>__<p2><p2>.json`

---

## 7) Структура репозитория

- `clients/` — конфиги клиентов (без секретов)
- `app/` — код
- `data_cache/` — локальный кэш данных (gitignored)
- `reports/` — отчёты (gitignored, позже)
- `.env` — локальные секреты (gitignored)
- `docs/` — спецификации и правила
- `docs/hypotheses/` — библиотека гипотез и маппинг на data/capabilities

---

## 8) Форматы артефактов

### 8.1 Кэш (файлы)
- raw: `data_cache/<client>/*_raw_<date1>_<date2>.json`
- norm: `data_cache/<client>/*_norm_<date1>_<date2>.json`

### 8.2 Workbook (результат анализа)
- `data_cache/<client>/analysis_sources_<p1_start><p1_end>__<p2_start><p2_end>.json`
- `data_cache/<client>/analysis_pages_<p1_start><p1_end>__<p2_start><p2_end>.json`

Workbook обязан содержать:
- `meta` (client, counter_id, периоды, generated_at, limit, refresh_used)
- `totals` (агрегаты по всем строкам)
- `rows` (top-N по драйверам изменения)

---

## 9) Требования к точности и воспроизводимости

1) Любые цифры — только из raw/norm/workbook.
2) Все расчёты (дельты/вклады/топы) делает Python-код.
3) Во время аналитического Run запрещено менять базовый код, кроме случая “Capability missing”.
4) Секреты не логировать и не коммитить.

---

## 10) Мультиклиентность

- Каждый клиент: `clients/<client>/config.yaml`
- CLI в командах анализа принимает `client` первым аргументом

---

## 11) Версии и окружение

Рекомендуемая версия Python: **3.12.x**.

---

## 12) Definition of Done (текущий инкремент)

Инкремент считается выполненным, когда:

1) Работают команды:
- `metrika-sources <client> <date1> <date2>`
- `analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end>`
- `metrika-pages <client> <date1> <date2> [--refresh]`
- `analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--refresh]`

2) После выполнения команд появляются файлы evidence pack в `data_cache/<client>/` в ожидаемых форматах.

3) Документация синхронизирована:
- `docs/spec.md`
- `docs/api_catalog.md` (каталог запросов)
- `docs/hypotheses/hypothesis_to_data_map.md` (capabilities registry)

---

## 13) Ссылки

- `docs/api_catalog.md`
- `docs/analysis_rules.md`
- `docs/AGENT_LOOP.md`
- `docs/hypotheses/hypothesis_to_data_map.md`
- `docs/hypotheses/seo_hypothesis_library.md`
