# Analyzer Machine — Agent Guide

Этот файл — основной entry point для локальных AI-агентов, которые работают прямо в репозитории и имеют доступ к shell и файловой системе.

Совместимые обертки:

- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`

Все они должны трактоваться как ссылки на этот `AGENTS.md`, а не как отдельные источники правил.

## Что это за проект

Analyzer Machine — Python CLI для evidence-based анализа:

- источников трафика
- landing pages
- конверсий по целям
- Google Search Console
- Яндекс.Вебмастера

Основные папки:

- `app/` — код CLI, анализов и API-клиентов
- `clients/<client>/config.yaml` — конфиг отдельного клиента
- `data_cache/<client>/` — raw, normalized и workbook артефакты
- `reports/` и `docs/reports/` — отчеты
- `tests/` — автоматические проверки

## Порядок чтения

Если нужен контекст, читай в таком порядке:

1. `AGENTS.md`
2. `README.md`
3. `capabilities_registry.yaml`
4. `docs/AGENT_LOOP.md`
5. `docs/AUDIT_RULES.md`

Исторические документы:

- `CODEX_RULES.md` — полезный контекст по режимам и принципам
- `CODEX_SETUP.md` — только для старого browser-only сценария Codex

## Режимы работы

### OPERATOR

Режим по умолчанию для расследований и аналитики.

- Код и документацию без явного запроса не менять.
- Любые цифры брать только из CLI output, workbook, raw или normalized файлов.
- Метрики не считать "в голове".
- По умолчанию предпочитать `--format insights`, если пользователю не нужна таблица.

### BUILDER

Режим изменений в коде и документации.

- Разрешены правки кода, tests и docs.
- После правок обязательно дать команды проверки.
- При изменении capabilities синхронизировать docs и `capabilities_registry.yaml`.

## Жесткие правила

- Никогда не печатать токены, secrets и credentials.
- Никогда не коммитить `.env`, `.env.local` и другие секретные файлы.
- Для новых аналитических выводов всегда указывать evidence path.
- Если capability нет, говорить `CAPABILITY MISSING`, а не импровизировать.

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli --help
```

Полезные команды:

```bash
python -m app.cli clients
python -m app.cli validate <client>
python -m app.cli show <client>
python -m pytest tests -v
```

## Что проверять перед анализом

1. Есть ли `clients/<client>/config.yaml`
2. Заполнен ли `metrika.counter_id`
3. Нужны ли `goal_id`, `gsc.site_url`, `ym_webmaster.user_id`, `ym_webmaster.host_id`
4. Есть ли нужные переменные в `.env`
5. Есть ли уже реализованная capability в `capabilities_registry.yaml`

## Реально реализованные команды

### Мультиклиентность и конфиг

- `python -m app.cli clients`
- `python -m app.cli show <client>`
- `python -m app.cli validate <client>`

### Яндекс.Метрика: raw / normalized

- `python -m app.cli metrika-sources <client> <date1> <date2> [--limit N]`
- `python -m app.cli metrika-pages <client> <date1> <date2> [--limit N] [--refresh]`
- `python -m app.cli metrika-pages-by-source <client> <date1> <date2> [--source "..."] [--limit N] [--refresh]`
- `python -m app.cli metrika-goals-by-source <client> <date1> <date2> --goal-id <id> [--limit N] [--refresh]`
- `python -m app.cli metrika-goals-by-page <client> <date1> <date2> --goal-id <id> [--limit N] [--refresh]`
- `python -m app.cli metrika-goals-list <client> [--refresh]`

### Анализ Метрики

- `python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh] [--format table|insights]`
- `python -m app.cli analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh] [--format table|insights]`
- `python -m app.cli analyze-pages-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --source "<source>" [--limit N] [--refresh] [--format table|insights]`
- `python -m app.cli analyze-goals-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> [--goal-id <id>] [--limit N] [--refresh] [--format table|insights]`
- `python -m app.cli analyze-goals-by-page <client> <p1_start> <p1_end> <p2_start> <p2_end> [--goal-id <id>] [--limit N] [--refresh] [--format table|insights]`

### Полное расследование

- `python -m app.cli investigate <client> --query "<обычный запрос>" [--refresh]`
- Подробный сценарий: `docs/INVESTIGATE.md`

### Google Search Console

- `python -m app.cli gsc-queries <client> <date1> <date2> [--limit N] [--refresh]`
- `python -m app.cli gsc-pages <client> <date1> <date2> [--limit N] [--refresh]`
- `python -m app.cli gsc-query-page <client> <date1> <date2> [--limit N] [--refresh]`
- `python -m app.cli analyze-gsc-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh] [--format table|insights]`
- `python -m app.cli analyze-gsc-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh] [--format table|insights]`

### Яндекс.Вебмастер

- `python -m app.cli ym-webmaster-hosts <client> [--refresh]`
- `python -m app.cli ym-webmaster-queries <client> <date1> <date2> [--limit N] [--refresh]`
- `python -m app.cli analyze-ym-webmaster-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh] [--format table|insights]`
- `python -m app.cli ym-webmaster-indexing <client> [--status EXCLUDED] [--limit N] [--offset N] [--refresh]`

### Audit helpers

- `python -m app.cli audit-data <client> <period_start> <period_end>`
- `python -m app.cli audit-metric "metric=value" --source <path-or-file> --client <client> [--period "..."]`
- `python -m app.cli audit-report <report_path> [--strict]`

`audit-report` сейчас checklist-driven и не является полным парсером отчета.

## Переменные окружения

Минимум для Метрики:

```bash
YANDEX_METRIKA_TOKEN=...
```

Для GSC:

```bash
GSC_CLIENT_ID=...
GSC_CLIENT_SECRET=...
GSC_REFRESH_TOKEN=...
```

Для Яндекс.Вебмастера:

```bash
YM_WEBMASTER_TOKEN=...
```

## Локальный SEO skill

Для SEO-расследований установлен локальный skill:

- `~/.codex/skills/seo-investigation/SKILL.md`

Он нужен как вспомогательный слой для гипотез и выбора источников, но source of truth для поведения CLI остаётся в коде `app/orchestrator/`.

## Ожидаемый workflow агента

1. Понять, это OPERATOR или BUILDER.
2. В OPERATOR выбрать минимальный набор уже существующих команд.
3. По возможности использовать cache-first и включать `--refresh` только когда это действительно нужно.
4. Прочитать workbook из `data_cache/<client>/`.
5. Сформулировать выводы с фактами, драйверами, гипотезами и next actions.
6. Если команда или capability отсутствует, явно остановиться с `CAPABILITY MISSING`.

## Что считать устаревшим

- `CODEX_SETUP.md` не описывает локальный режим агента.
- Любые упоминания несуществующих команд вроде `analyze-professional` считать историческим мусором, а не актуальной частью проекта.
