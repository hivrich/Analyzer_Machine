# Analyzer Machine

On-demand агент для анализа трафика, конверсий и SEO метрик.

## Описание

Analyzer Machine — это инструмент для профессионального анализа веб-метрик:
- Сравнение периодов (дельты, вклады, топ драйверы)
- Анализ источников трафика, landing pages, конверсий
- Интеграция с Яндекс.Метрикой, Google Search Console, Яндекс.Вебмастер
- Evidence-based отчёты с гипотезами и рекомендациями

## Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd "Analyzer Machine"

# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows

# Установить зависимости
pip install -r requirements.txt
```

### Настройка

1. **Создать `.env` файл** (не коммитить в git!):
```bash
# Яндекс.Метрика (обязательно)
YANDEX_METRIKA_TOKEN=your_token_here

# Google Search Console (опционально)
GSC_CLIENT_ID=your_client_id
GSC_CLIENT_SECRET=your_client_secret
GSC_REFRESH_TOKEN=your_refresh_token

# Яндекс.Вебмастер (опционально)
YM_WEBMASTER_TOKEN=your_token_here
```

2. **Создать конфиг клиента** `clients/<client_name>/config.yaml`:
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

### Использование

```bash
# Список доступных команд
python -m app.cli --help

# Сравнение источников трафика
python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]

# Пример
python -m app.cli analyze-sources partacademy 2024-12-01 2024-12-31 2025-12-01 2025-12-31 --refresh
```

## Структура проекта

```
Analyzer Machine/
├── app/                          # Python модули
│   ├── cli.py                    # CLI команды
│   ├── config.py                 # Загрузка конфигов
│   ├── analysis_*.py            # Модули анализа
│   └── *_client.py               # Клиенты к API
├── clients/                       # Конфиги клиентов
│   └── <client_name>/
│       └── config.yaml
├── docs/                          # Документация
│   ├── samples/                  # Примеры данных
│   ├── data_sources/             # Каталоги API
│   └── *.md                      # Документация
├── data_cache/                    # Кэш данных (не в git)
├── reports/                       # Отчёты (не в git)
├── capabilities_registry.yaml     # Реестр capabilities
├── CODEX_RULES.md                 # Правила для AI агента
├── CODEX_SETUP.md                 # Настройка для Codex
└── requirements.txt               # Python зависимости
```

## Работа с AI агентами

### Для OpenAI Codex (браузер)

См. `CODEX_SETUP.md` — подробные инструкции по работе в Codex.

**Кратко:**
- Codex может читать код и документацию
- Codex может предлагать команды для выполнения
- Codex может анализировать workbook файлы (если вы их предоставите)
- Codex **не может** выполнять команды напрямую (нет доступа к терминалу)

### Для Cursor IDE

Проект настроен для работы в Cursor:
- Правила в `.cursor/rules/*.mdc`
- Автоматическая загрузка `.env` через `python-dotenv`
- Интеграция с терминалом Cursor

## Основные команды

### Анализ источников трафика
```bash
python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

### Анализ landing pages
```bash
python -m app.cli analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

### Анализ конверсий
```bash
python -m app.cli analyze-goals-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --goal-id <goal_id> [--limit N] [--refresh]
python -m app.cli analyze-goals-by-page <client> <p1_start> <p1_end> <p2_start> <p2_end> --goal-id <goal_id> [--limit N] [--refresh]
```

### Google Search Console
```bash
python -m app.cli analyze-gsc-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
python -m app.cli analyze-gsc-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]
```

Полный список команд: `python -m app.cli --help`

## Документация

- **Правила работы агента:** `CODEX_RULES.md`
- **Настройка для Codex:** `CODEX_SETUP.md`
- **Стандарт агента:** `docs/AGENT_LOOP.md`
- **Спецификация:** `docs/spec.md`
- **Каталог API:** `docs/api_catalog.md`
- **Примеры данных:** `docs/samples/`
- **Реестр capabilities:** `capabilities_registry.yaml`

## Примеры данных

Примеры структуры workbook и normalized данных находятся в `docs/samples/`:
- `workbook_sources_example.json` — пример workbook для источников
- `workbook_pages_example.json` — пример workbook для страниц
- `workbook_goals_example.json` — пример workbook для конверсий
- `workbook_gsc_queries_example.json` — пример workbook для GSC запросов
- `workbook_gsc_pages_example.json` — пример workbook для GSC страниц
- `normalized_data_example.json` — пример normalized данных

См. `docs/samples/README.md` для подробного описания.

## Мультиклиентность

- Каждый сайт = отдельная папка `clients/<client_name>/config.yaml`
- Секреты только локально (`.env` или `clients/<client_name>/.env.local`)
- Эти файлы всегда в `.gitignore`
- Отчёты/артефакты в `reports/` и/или `reports/<client_name>/`

## Безопасность

- **Никаких секретов в репозитории** — токены, ключи, credentials только в `.env`
- `.env` файлы в `.gitignore` и `.cursorindexingignore`
- Секреты не печатаются в выводе CLI
- Все расчёты делаются кодом, не "в голове"

## Режимы работы

### MODE: OPERATOR (по умолчанию)
- Выполнение анализа без изменения кода
- Все цифры из evidence файлов
- LLM только интерпретирует результаты

### MODE: BUILDER
- Реализация/исправление capabilities
- Изменения кода разрешены
- Обязателен smoke test после изменений

Подробнее: `CODEX_RULES.md` раздел "Режимы работы"

## Лицензия

[Указать лицензию, если есть]

## Контакты

[Указать контакты, если нужно]
