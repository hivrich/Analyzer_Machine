# Analyzer Machine — Implemented Agent Loop

Этот документ описывает фактический workflow агента в текущем репозитории.

Он отражает реально существующие команды из `app/cli.py`, а не будущие или экспериментальные идеи.

## Базовые принципы

1. Сначала evidence, потом интерпретация.
2. Любые цифры должны ссылаться на workbook, raw/norm JSON или CLI output.
3. Метрики считаются кодом, а не моделью.
4. По умолчанию использовать `--format insights`, если пользователю не нужна таблица.
5. Если capability отсутствует, говорить `CAPABILITY MISSING`.

## Шаг 1. Классифицировать задачу

Перед запуском понять:

- клиент
- периоды
- KPI
- источник данных: Метрика, GSC, Яндекс.Вебмастер
- нужен ли только анализ или также правки кода

Если пользователь не просит менять код, это `MODE: OPERATOR`.
Если пользователь просит допилить capability, документацию или инфраструктуру, это `MODE: BUILDER`.

## Шаг 2. Проверить готовность окружения

Минимум перед run:

1. существует `clients/<client>/config.yaml`
2. задан `metrika.counter_id`
3. для goals есть `goal_id` в конфиге или будет передан `--goal-id`
4. для GSC настроены `gsc.site_url`, `GSC_CLIENT_ID`, `GSC_CLIENT_SECRET`, `GSC_REFRESH_TOKEN`
5. для Яндекс.Вебмастера настроены `ym_webmaster.user_id`, `ym_webmaster.host_id`, `YM_WEBMASTER_TOKEN`

Полезные команды:

```bash
python -m app.cli clients
python -m app.cli show <client>
python -m app.cli validate <client>
```

## Шаг 3. Выбрать минимальную capability

### Предпочтительный путь для обычного запроса

Если пользователь пишет задачу обычным языком, главный путь теперь такой:

```bash
python -m app.cli investigate <client> --query "<обычный запрос>" [--refresh]
```

`investigate` работает итеративно:

1. сначала делает общий срез
2. строит первые гипотезы
3. сам решает, каких данных не хватает
4. запускает следующий раунд только по нужным источникам
5. останавливается, когда причина уже достаточно понятна или когда новых полезных шагов нет

Низкоуровневые compare-команды ниже нужны либо для ручной проверки, либо как строительные блоки для `investigate`.

### Реально реализованные compare-команды

```bash
python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> --format insights
python -m app.cli analyze-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> --format insights
python -m app.cli analyze-pages-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --source "<source>" --format insights
python -m app.cli analyze-goals-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --goal-id <goal_id> --format insights
python -m app.cli analyze-goals-by-page <client> <p1_start> <p1_end> <p2_start> <p2_end> --goal-id <goal_id> --format insights
python -m app.cli analyze-gsc-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> --format insights
python -m app.cli analyze-gsc-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> --format insights
python -m app.cli analyze-ym-webmaster-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> --format insights
```

### Вспомогательные fetch-команды

```bash
python -m app.cli metrika-sources <client> <date1> <date2>
python -m app.cli metrika-pages <client> <date1> <date2>
python -m app.cli metrika-pages-by-source <client> <date1> <date2> --source "<source>"
python -m app.cli metrika-goals-by-source <client> <date1> <date2> --goal-id <goal_id>
python -m app.cli metrika-goals-by-page <client> <date1> <date2> --goal-id <goal_id>
python -m app.cli gsc-queries <client> <date1> <date2>
python -m app.cli gsc-pages <client> <date1> <date2>
python -m app.cli ym-webmaster-queries <client> <date1> <date2>
python -m app.cli ym-webmaster-indexing <client> --status EXCLUDED
```

## Шаг 4. Собрать и прочитать evidence

После compare-команд ожидаем workbook в `data_cache/<client>/`.

Типовые паттерны:

- `analysis_sources_*.json`
- `analysis_pages_*.json`
- `analysis_pages_by_source_*.json`
- `analysis_goals_by_source_*.json`
- `analysis_goals_by_page_*.json`
- `analysis_gsc_queries_*.json`
- `analysis_gsc_pages_*.json`
- `analysis_ym_webmaster_queries_*.json`

Также рядом лежат raw и normalized файлы по каждому источнику.

## Шаг 5. Проверить результат

Доступные audit helpers:

```bash
python -m app.cli audit-data <client> <period_start> <period_end>
python -m app.cli audit-metric "metric=value" --source <path-or-file> --client <client>
python -m app.cli audit-report <report_path> [--strict]
```

Замечание:

- `audit-report` сейчас делает базовый checklist, а не полный машинный разбор отчета.
- Поэтому при важных выводах нужен и автоматический, и ручной sanity-check.

## Шаг 6. Сформировать ответ

Ответ по анализу должен содержать:

- краткий executive summary
- факты с evidence path
- драйверы роста или падения
- гипотезы и что нужно для проверки
- next actions

## CAPABILITY MISSING

Если команда или нужный срез реально отсутствуют:

1. Явно написать `CAPABILITY MISSING: <name>`
2. Указать, каких данных не хватает
3. Указать ожидаемую CLI команду
4. Указать ожидаемые артефакты в `data_cache/<client>/`
5. Остановиться, не выдумывая промежуточный ответ
