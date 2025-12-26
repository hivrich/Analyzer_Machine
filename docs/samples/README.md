# Примеры данных (Sample Data)

Эта папка содержит примеры структуры данных, которые создаёт агент Analyzer Machine.

## Назначение

Примеры помогают:
- Понять структуру workbook JSON файлов
- Понять формат normalized данных
- Тестировать код без реальных API запросов
- Документировать контракты данных

## Файлы

### Workbook файлы (агрегированные результаты анализа)

- `workbook_sources_example.json` - анализ источников трафика
  - Структура: `meta`, `totals`, `rows[]`
  - Поля в rows: `source`, `visits_p1`, `visits_p2`, `delta_abs`, `delta_pct`, `contribution_pct`

- `workbook_pages_example.json` - анализ landing pages
  - Структура: аналогична sources, но поле `landingPage` вместо `source`

- `workbook_goals_example.json` - анализ конверсий по целям
  - Структура: `meta` (с `goal_id`, `dimension`), `totals` (с `total_goal_visits_p1/p2`, `total_cr_p1/p2`), `rows[]`
  - Поля в rows: `source`/`landingPage`, `visits_p1/p2`, `goal_visits_p1/p2`, `cr_p1/p2`, `delta_goal_visits`, `delta_cr_pp`

- `workbook_gsc_queries_example.json` - анализ запросов Google Search Console
  - Структура: `meta` (с `kind: "queries"`, `site_url`), `totals` (с `total_clicks`, `total_impressions`, `total_ctr`), `rows[]`
  - Поля в rows: `query`, `clicks_p1/p2`, `impressions_p1/p2`, `ctr_p1/p2`, `position_p1/p2`, `delta_*`

- `workbook_gsc_pages_example.json` - анализ страниц Google Search Console
  - Структура: аналогична GSC queries, но поле `page` вместо `query`

### Normalized данные (нормализованные ответы API)

- `normalized_data_example.json` - пример нормализованных данных из Яндекс.Метрики
  - Формат: массив объектов
  - Поля: `source`, `visits`, `users`, `bounceRate`, `pageDepth`, `avgVisitDurationSeconds`

## Использование

### Для разработки

```python
import json
from pathlib import Path

# Загрузить пример workbook
with open("docs/samples/workbook_sources_example.json") as f:
    workbook = json.load(f)

# Использовать для тестирования
assert workbook["totals"]["total_visits_p1"] == 50000.0
```

### Для документации

Ссылайтесь на эти файлы в документации, чтобы показать структуру данных без реальных значений клиентов.

## Важно

- Все данные в примерах **синтетические/анонимные**
- Не содержат реальных данных клиентов
- Не содержат секретов (токены, ключи)
- Структура соответствует реальным файлам из `data_cache/`

## Где используются

- `data_cache/<client>/analysis_*.json` - workbook файлы
- `data_cache/<client>/metrika_*_norm_*.json` - normalized данные
- `data_cache/<client>/gsc_*_norm_*.json` - normalized GSC данные

