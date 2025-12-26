# Analyzer Machine — Быстрый старт для OpenAI Codex

Этот документ поможет вам начать работу с проектом Analyzer Machine в OpenAI Codex (браузерная версия).

## Что это за проект?

Analyzer Machine — это агент для анализа трафика, конверсий и SEO метрик. Он:
- Получает данные из Яндекс.Метрики, Google Search Console, Яндекс.Вебмастер
- Сравнивает периоды (дельты, вклады, топ драйверы)
- Создаёт evidence-based отчёты с гипотезами и рекомендациями

## Структура проекта

```
Analyzer Machine/
├── app/                    # Python модули
│   ├── cli.py              # CLI команды
│   ├── config.py           # Загрузка конфигов клиентов
│   ├── analysis_*.py       # Модули анализа (sources, pages, goals, gsc, ym_webmaster)
│   └── *_client.py         # Клиенты к API (metrika, gsc, ym_webmaster)
├── clients/                 # Конфиги клиентов
│   └── <client_name>/
│       └── config.yaml      # Конфигурация клиента
├── docs/                    # Документация
│   ├── samples/            # Примеры данных (workbook JSON)
│   ├── data_sources/       # Каталоги API
│   ├── hypotheses/         # Библиотека гипотез
│   └── *.md                # Документация проекта
├── capabilities_registry.yaml  # Реестр capabilities агента
├── CODEX_RULES.md          # Правила работы агента (этот файл)
└── requirements.txt        # Python зависимости
```

## Как Codex должен интерпретировать правила

### 1. Режим по умолчанию: OPERATOR

Если пользователь не указывает режим, используйте `MODE: OPERATOR`:
- **НЕ изменяйте** код или документы
- Все цифры должны быть из evidence файлов
- LLM только интерпретирует результаты кода

### 2. Когда пользователь просит анализ

Автоматически:
1. Составьте план (какие команды запустить)
2. Запустите команды CLI
3. Прочитайте workbook файлы из `data_cache/`
4. Создайте отчёт со ссылками на evidence

### 3. Структура данных

**Workbook файлы** находятся в `data_cache/<client>/analysis_*.json`

**Примеры структуры:** см. `docs/samples/workbook_*.json`

**Формат:**
- `meta` — метаданные (client, периоды, дата генерации)
- `totals` — итоги (total_visits_p1, total_visits_p2, total_delta_abs, total_delta_pct)
- `rows[]` — строки данных с дельтами и вкладами

### 4. Доступные команды

См. `CODEX_RULES.md` раздел "Доступные команды CLI" или запустите:
```bash
python -m app.cli --help
```

## Примеры запросов к агенту

### Пример 1: Анализ падения трафика

**Запрос пользователя:**
"Почему упал трафик? Сравни декабрь 2024 и декабрь 2025 для клиента partacademy"

**Что должен сделать Codex:**
1. Понять: client=partacademy, p1=2024-12-01..2024-12-31, p2=2025-12-01..2025-12-31
2. Запустить: `python -m app.cli analyze-sources partacademy 2024-12-01 2024-12-31 2025-12-01 2025-12-31 --refresh`
3. Прочитать: `data_cache/partacademy/analysis_sources_*.json`
4. Создать отчёт с фактами, драйверами, гипотезами

### Пример 2: Анализ конверсий

**Запрос пользователя:**
"Проверь конверсии по источникам для partacademy за те же периоды"

**Что должен сделать Codex:**
1. Найти goal_id в `clients/partacademy/config.yaml` (или использовать `metrika-goals-list`)
2. Запустить: `python -m app.cli analyze-goals-by-source partacademy 2024-12-01 2024-12-31 2025-12-01 2025-12-31 --goal-id <goal_id> --refresh`
3. Прочитать workbook и интерпретировать результаты

### Пример 3: Capability Missing

**Запрос пользователя:**
"Проверь позиции в Google для partacademy"

**Что должен сделать Codex:**
1. Понять, что нужны данные GSC
2. Проверить, настроен ли GSC (есть ли `gsc.site_url` в config и credentials в env)
3. Если нет — вывести "CAPABILITY MISSING" с инструкциями
4. Если да — запустить `analyze-gsc-queries` или `analyze-gsc-pages`

## Настройка окружения

### Переменные окружения

Создайте `.env` файл (не коммитить в git!):
```bash
# Яндекс.Метрика
YANDEX_METRIKA_TOKEN=your_token_here

# Google Search Console (опционально)
GSC_CLIENT_ID=your_client_id
GSC_CLIENT_SECRET=your_client_secret
GSC_REFRESH_TOKEN=your_refresh_token

# Яндекс.Вебмастер (опционально)
YM_WEBMASTER_TOKEN=your_token_here
```

### Установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows
pip install -r requirements.txt
```

### Конфигурация клиента

Создайте `clients/<client_name>/config.yaml`:
```yaml
site:
  name: "example.com"
  timezone: "Europe/Moscow"

metrika:
  counter_id: 12345678
  goal_id: 123456
  currency: "RUB"

gsc:
  site_url: "https://example.com/"  # опционально

ym_webmaster:
  user_id: 12345678  # опционально
  host_id: "https:example.com:443"  # опционально
```

## Работа в Codex (браузер)

### Ограничения

Codex работает в браузере, поэтому:
- **НЕ может** выполнять команды CLI напрямую (нет доступа к терминалу)
- **НЕ может** делать реальные API запросы
- **МОЖЕТ** читать файлы проекта
- **МОЖЕТ** анализировать структуру кода
- **МОЖЕТ** предлагать команды для выполнения пользователем

### Как Codex должен работать

1. **Читать код и документацию** для понимания структуры
2. **Предлагать команды** для выполнения пользователем
3. **Анализировать результаты** (если пользователь предоставит workbook файлы)
4. **Создавать отчёты** на основе предоставленных данных

### Пример диалога в Codex

**Пользователь:**
"Почему упал трафик для partacademy? Сравни декабрь 2024 и 2025"

**Codex должен ответить:**
```
Понял задачу: анализ падения трафика для partacademy (2024-12-01..31 vs 2025-12-01..31).

Для выполнения анализа нужно:

1. Убедиться, что настроены credentials:
   - YANDEX_METRIKA_TOKEN в .env
   - clients/partacademy/config.yaml содержит counter_id

2. Выполнить команды (в вашем терминале):
   python -m app.cli analyze-sources partacademy 2024-12-01 2024-12-31 2025-12-01 2025-12-31 --refresh
   python -m app.cli analyze-pages partacademy 2024-12-01 2024-12-31 2025-12-01 2025-12-31 --refresh

3. После выполнения команд, предоставьте мне workbook файлы:
   - data_cache/partacademy/analysis_sources_*.json
   - data_cache/partacademy/analysis_pages_*.json

Я проанализирую их и создам отчёт с фактами, драйверами и гипотезами.
```

## Полезные ссылки

- **Правила работы:** `CODEX_RULES.md`
- **Стандарт агента:** `docs/AGENT_LOOP.md`
- **Примеры данных:** `docs/samples/`
- **Реестр capabilities:** `capabilities_registry.yaml`
- **Гипотезы:** `docs/hypotheses/`

## Важные напоминания

1. **Никогда не выдумывайте данные** — только из evidence файлов
2. **Никогда не печатайте секреты** — токены, ключи, credentials
3. **Все расчёты кодом** — не считать "в голове"
4. **В режиме OPERATOR не менять код** — только читать и интерпретировать

