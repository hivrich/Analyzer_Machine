# Analyzer Machine — Правила работы для AI агента

Этот документ содержит все правила работы агента Analyzer Machine. Используйте его как контекст при работе с проектом в OpenAI Codex или других AI-инструментах.

## Основные правила (Core Rules)

### 1. Не выдумывать данные
- Не выдумывать данные/цифры/ответы API
- Если данных нет — указывать, какая команда/файл нужны
- Все цифры должны быть из evidence (workbook, кэш, вывод CLI)

### 2. Безопасность секретов
- Никаких секретов в выводе: токены/ключи/credentials не печатать
- Не записывать секреты в репозиторий
- Секреты только в переменных окружения (`.env` файлы, не в git)

### 3. Расчёты только кодом
- Все расчёты (дельты, вклады, топы) должны считаться кодом/скриптами
- Не считать "в голове" и не просить LLM считать
- LLM используется только для интерпретации результатов кода

### 4. Аккуратность правок
- Любые правки файлов — аккуратно
- Не удалять существующее без причины

## Мультиклиентность

- Каждый сайт = отдельная папка `clients/<client_name>/config.yaml`
- Секреты: только локально (`.env` или `clients/<client_name>/.env.local`)
- Эти файлы всегда в `.gitignore` и `.cursorindexingignore`
- Отчёты/артефакты складывать в `reports/` и/или `reports/<client_name>/`

## Режимы работы (MODE)

### По умолчанию: MODE: OPERATOR

Если пользователь не указывает режим явно, используется `MODE: OPERATOR`.

### MODE: OPERATOR (выполнение анализа, без изменения кода)

**Цель:** Выполнить расследование используя существующие capabilities, создать evidence-based отчёт.

**Жёсткие правила:**
1. **НЕ изменять** код или документы в режиме OPERATOR
2. Все цифры/выводы **ОБЯЗАТЕЛЬНО** должны быть из evidence файлов (raw/norm/workbook), созданных CLI
3. LLM **не должен** "считать" метрики; только интерпретировать результаты кода
4. Никогда не печатать и не логировать секреты (токены, client secrets)

**Процесс:**
1. Распарсить запрос пользователя, вывести гипотезы
2. Сопоставить гипотезы с доступными capabilities из `docs/hypotheses/hypothesis_to_data_map.md` или `capabilities_registry.yaml`
3. Запустить минимальный набор CLI команд для сбора evidence (raw/norm/workbook)
4. Если команда упала: диагностировать и повторить только операционными шагами (без изменения кода)
5. Если нужные данные/срез не поддерживаются: вывести "CAPABILITY MISSING" и создать DEV-TICKET:
   - какие данные нужны (endpoint/dimensions/metrics/filters)
   - ожидаемые CLI команды
   - ожидаемые cache/workbook артефакты
   - DoD (как проверить)
   - затем ОСТАНОВИТЬСЯ (не импровизировать выводы)
6. Вывод: выполненные команды + пути к evidence + краткий отчёт со ссылками на evidence

### MODE: BUILDER (реализация или исправление capabilities)

**Цель:** Реализовать/исправить capabilities, чтобы режим OPERATOR мог работать.

**Жёсткие правила:**
1. Изменения кода разрешены **ТОЛЬКО** в режиме BUILDER
2. Каждое изменение должно заканчиваться smoke test (команды для запуска + ожидаемые артефакты)
3. Обновлять документацию при добавлении/изменении capabilities (если эти документы есть в репозитории):
   - `docs/spec.md`
   - `docs/api_catalog.md`
   - `docs/hypotheses/hypothesis_to_data_map.md`
4. Никогда не печатать и не логировать секреты

**Процесс:**
1. Указать точный scope изменений (какие файлы изменить, почему)
2. Реализовать минимальные изменения для удовлетворения DEV-TICKET / исправления бага
3. Запустить smoke tests локально (или предоставить точные команды) и подтвердить артефакты (raw/norm/workbook)
4. Вернуть краткий changelog (изменённые файлы) + команды для проверки
5. Затем указать перезапустить в `MODE: OPERATOR` для реального расследования

## Agent Loop (стандарт работы агента)

### Обязательная процедура при запросе "проанализируй/разбери/сделай выводы"

#### Шаг 1: PLAN (сначала)

1. Переформулировать задачу в 2–4 строки: client, периоды, KPI (трафик/конверсии/ecommerce)
2. Выбрать существующие capabilities/команды CLI, которые нужны, и перечислить точные команды
3. Указать, какие артефакты будут созданы автоматически:
   - `data_cache/<client>` — у команды есть флаг `--refresh`, использовать его по умолчанию
   - Если `--refresh` не поддерживается, продолжить без него (без остановки)
4. Прочитать созданный workbook(и) из `data_cache/<client>/`
5. Во время Run **НЕ менять** код и документы

#### Шаг 2: AGENT (выполнение)

1. Выполнять команды через встроенный терминал
2. Собирать артефакты в `data_cache/` и `reports/`
3. Любые цифры/выводы допускаются только если есть "evidence": путь к workbook/кэшу/выводу CLI
4. Запрещено читать "в голове" и не просить LLM считать
5. Секреты никогда не печатать и не записывать в репозиторий

#### Шаг 3: REPORT (интерпретация)

Отчёт должен содержать:
- **Executive summary** — главные выводы (2–3 предложения)
- **Facts** — факты (цифры) с путями к evidence
- **Drivers** — топ вкладов (что больше всего повлияло)
- **Hypotheses** — 5–8 гипотез + какие данные нужны для проверки
- **Next actions** — приоритетные действия

**Evidence pack:**
- Создать `reports/<client>/<investigation_name>_evidence.txt` со списком путей к workbook и кэшам

### Natural Language (естественный язык)

Если пользователь просит анализ (падение/рост/аномалия/разобраться/почему), считать это запросом на Run.

Пользователь **НЕ обязан** упоминать: runbook, AGENT_LOOP, workbook, data_cache, evidence, команды CLI.

Агент сам подбирает команды и сам управляет файлами/путями/папками по правилам выше.

## Структура данных

### Workbook файлы

Workbook — это агрегированные результаты анализа, сохранённые в JSON.

**Структура:**
```json
{
  "meta": {
    "client": "...",
    "counter_id": 12345678,
    "p1_start": "2024-01-01",
    "p1_end": "2024-01-31",
    "p2_start": "2025-01-01",
    "p2_end": "2025-01-31",
    "generated_at": "2025-12-26T12:00:00.000000Z",
    "limit": 50,
    "refresh_used": false
  },
  "totals": {
    "total_visits_p1": 50000.0,
    "total_visits_p2": 40000.0,
    "total_delta_abs": -10000.0,
    "total_delta_pct": -20.0
  },
  "rows": [
    {
      "source": "Search engine traffic",
      "visits_p1": 40000.0,
      "visits_p2": 30000.0,
      "delta_abs": -10000.0,
      "delta_pct": -25.0,
      "contribution_pct": 100.0
    }
  ]
}
```

**Примеры:** см. `docs/samples/workbook_*.json`

### Normalized данные

Normalized данные — это нормализованные ответы API, сохранённые в JSON.

**Формат:** массив объектов

**Пример:** см. `docs/samples/normalized_data_example.json`

## Доступные команды CLI

### Анализ источников трафика
```bash
python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

### Анализ landing pages
```bash
python -m app.cli analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

### Анализ landing pages по источнику
```bash
python -m app.cli analyze-pages-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --source "<source>" [--limit N] [--refresh]
```

### Анализ конверсий по источникам
```bash
python -m app.cli analyze-goals-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --goal-id <goal_id> [--limit N] [--refresh]
```

### Анализ конверсий по страницам
```bash
python -m app.cli analyze-goals-by-page <client> <p1_start> <p1_end> <p2_start> <p2_end> --goal-id <goal_id> [--limit N] [--refresh]
```

### Анализ Google Search Console (запросы)
```bash
python -m app.cli analyze-gsc-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

### Анализ Google Search Console (страницы)
```bash
python -m app.cli analyze-gsc-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

### Список целей Яндекс.Метрики
```bash
python -m app.cli metrika-goals-list <client> [--refresh]
```

## Capabilities Registry

Реестр всех capabilities агента находится в `capabilities_registry.yaml`.

Каждая capability содержит:
- `id` — уникальный идентификатор
- `name` — человеко-читаемое имя
- `status` — implemented / planned_tier1 / planned_tier2 / planned_tier3
- `command_template` — шаблон CLI команды
- `artifacts` — список артефактов (workbook, cache)
- `checks_hypotheses` — список ID гипотез, которые можно проверить
- `priority` — числовой приоритет

## Гипотезы и данные

Маппинг гипотез к данным находится в:
- `docs/hypotheses/hypothesis_to_data_map.md`
- `docs/hypotheses/seo_hypothesis_library.md`

## Документация

Полная документация проекта:
- `docs/AGENT_LOOP.md` — стандарт работы агента
- `docs/spec.md` — спецификация проекта
- `docs/api_catalog.md` — каталог API запросов
- `docs/analysis_rules.md` — правила анализа
- `docs/capability_matrix.md` — матрица capabilities
- `docs/data_sources/` — каталоги источников данных

## Ориентиры

- Стандарт процесса: `docs/AGENT_LOOP.md`
- Принципы работы: `docs/AGENT_LOOP.md`
- Пример работы агента: `docs/agent_example_run.md`

