# Google Search Console — полная карта возможностей для Analyzer Machine

**API:** Search Console API (Search Analytics)  
**Endpoint:** `https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query`  
**Документация:** [developers.google.com/webmaster-tools/search-console-api-original](https://developers.google.com/webmaster-tools/search-console-api-original)

---

## 1. Доступные dimensions (измерения)

| Dimension | Описание | Использование | Приоритет |
|-----------|----------|---------------|-----------|
| `query` | Поисковый запрос | Анализ запросов | **Критично** |
| `page` | URL страницы | Анализ страниц | **Критично** |
| `country` | Страна поиска | Гео-анализ | Средне |
| `device` | Устройство (DESKTOP/MOBILE/TABLET) | Анализ по устройствам | Важно |
| `searchAppearance` | Тип отображения (AMP, rich results) | Фичи выдачи | Низкий |
| `date` | Дата | Динамика | Важно |

**Комбинации:**
- `query` × `page` — какие запросы приводят на какие страницы
- `query` × `device` — позиции по устройствам
- `page` × `country` — гео-распределение по страницам

---

## 2. Доступные metrics (метрики)

| Metric | Описание | Тип | Использование | Приоритет |
|--------|----------|-----|---------------|-----------|
| `clicks` | Клики из поиска | int | Трафик | **Критично** |
| `impressions` | Показы в выдаче | int | Видимость | **Критично** |
| `ctr` | CTR (Click-Through Rate, %) | float | Кликабельность | **Критично** |
| `position` | Средняя позиция | float | Ранжирование | **Критично** |

**Примечание:** GSC всегда возвращает ВСЕ 4 метрики, фильтровать на стороне клиента.

---

## 3. Filters (фильтры)

### 3.1 Типы фильтров

| Operator | Описание | Пример |
|----------|----------|--------|
| `equals` | Точное совпадение | query equals "seo курсы" |
| `contains` | Содержит | query contains "seo" |
| `notEquals` | Не равно | country notEquals "usa" |
| `notContains` | Не содержит | query notContains "brand" |
| `includingRegex` | Regex (включая) | page includingRegex ".*\\/blog\\/.*" |
| `excludingRegex` | Regex (исключая) | page excludingRegex ".*\\/tag\\/.*" |

### 3.2 Примеры фильтров

#### Фильтр 1: Только запросы с "seo"
```json
{
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "query",
      "operator": "contains",
      "expression": "seo"
    }]
  }]
}
```

#### Фильтр 2: Только конкретная страница
```json
{
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "page",
      "operator": "equals",
      "expression": "https://example.com/page-url"
    }]
  }]
}
```

#### Фильтр 3: Страницы блога (regex)
```json
{
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "page",
      "operator": "includingRegex",
      "expression": ".*\\/blog\\/.*"
    }]
  }]
}
```

---

## 4. Capabilities на основе GSC

### C5: Google Search Console integration

#### C5.1: Queries analysis (анализ запросов)

**Назначение:** Найти запросы, потерявшие позиции/клики/CTR

**Dimensions:** `query`, optionally `device`  
**Metrics:** clicks, impressions, ctr, position

**Запрос:**
```json
POST /webmasters/v3/sites/https%3A%2F%2Fexample.com/searchAnalytics/query

{
  "startDate": "2024-12-01",
  "endDate": "2024-12-31",
  "dimensions": ["query"],
  "rowLimit": 1000,
  "dataState": "final"
}
```

**Артефакты:**
- `data_cache/<client>/gsc_queries_raw_2024-12-01_2024-12-31.json`
- `data_cache/<client>/gsc_queries_norm_2024-12-01_2024-12-31.json`
- `data_cache/<client>/analysis_gsc_queries_<p1><p2>.json` (workbook: дельты clicks/position/ctr)

**Гипотезы:**
- H2.2 (падение показов)
- H2.3 (падение позиций)
- H2.4 (CTR просел)

---

#### C5.2: Pages analysis (анализ страниц)

**Назначение:** Найти страницы, потерявшие позиции/клики

**Dimensions:** `page`  
**Metrics:** clicks, impressions, ctr, position

**Запрос:**
```json
{
  "startDate": "2024-12-01",
  "endDate": "2024-12-31",
  "dimensions": ["page"],
  "rowLimit": 1000,
  "dataState": "final"
}
```

**Артефакты:**
- `data_cache/<client>/gsc_pages_raw_2024-12-01_2024-12-31.json`
- `data_cache/<client>/gsc_pages_norm_2024-12-01_2024-12-31.json`
- `data_cache/<client>/analysis_gsc_pages_<p1><p2>.json` (workbook)

**Гипотезы:**
- H2.1 (кластеры страниц)
- H5.1 (страницы потеряли позиции)

---

#### C5.3: Query × Page (запросы по страницам)

**Назначение:** Какие запросы приводят на какие страницы

**Dimensions:** `query`, `page`  
**Metrics:** clicks, impressions, ctr, position

**Запрос:**
```json
{
  "startDate": "2024-12-01",
  "endDate": "2024-12-31",
  "dimensions": ["query", "page"],
  "rowLimit": 5000,
  "dataState": "final"
}
```

**Применение:**
- Детализация: какая страница по какому запросу упала
- Приоритет: **Критично** для глубокого анализа

---

#### C5.4: Queries by device (запросы по устройствам)

**Dimensions:** `query`, `device`

**Применение:**
- Проверка гипотезы "упала только мобильная выдача"
- H8.1 (технические проблемы на mobile)

---

#### C5.5: Pages by device (страницы по устройствам)

**Dimensions:** `page`, `device`

**Применение:**
- Какие страницы упали на mobile/desktop
- Техпроблемы по устройствам

---

## 5. Сравнение периодов (period compare)

### 5.1 Логика сравнения

Для каждого entity (query или page):

**Метрики периода 1 (P1):**
- `clicks_p1`
- `impressions_p1`
- `ctr_p1`
- `position_p1`

**Метрики периода 2 (P2):**
- `clicks_p2`
- `impressions_p2`
- `ctr_p2`
- `position_p2`

**Расчётные поля:**
- `delta_clicks = clicks_p2 - clicks_p1`
- `delta_impressions = impressions_p2 - impressions_p1`
- `delta_ctr = ctr_p2 - ctr_p1` (в процентных пунктах)
- `delta_position = position_p2 - position_p1` (отрицательная = улучшение)
- `contribution_pct = delta_clicks / total_delta_clicks * 100`

---

### 5.2 Формула contribution (вклад)

```python
total_delta_clicks = sum(delta_clicks for all entities)
contribution_pct = (delta_clicks / total_delta_clicks) * 100
```

**Интерпретация:**
- Положительный contribution_pct → этот entity дал рост
- Отрицательный → дал падение

---

## 6. Ограничения GSC API

| Параметр | Значение | Комментарий |
|----------|----------|-------------|
| `rowLimit` | 1-25,000 | По умолчанию 1000, максимум 25,000 |
| Данных доступно | 16 месяцев | Данные старше 16 мес удаляются |
| Обновление данных | ~2-3 дня lag | Свежие данные могут быть неполными |
| `dataState` | `all` или `final` | `final` = только финальные данные (рекомендуется) |

**Рекомендация для агента:**
- `rowLimit=1000-5000` для queries
- `dataState=final` для точности
- Не запрашивать данные за последние 3 дня (lag)

---

## 7. Интеграция с Метрикой (cross-validation)

### 7.1 Сопоставление данных

| GSC | Метрика | Совместимость |
|-----|---------|---------------|
| `clicks` | `ym:s:visits` (organic) | ⚠️ Приблизительно (атрибуция) |
| `page` | `ym:s:startURL` | ✅ Прямое соответствие |
| `position` | — | ❌ Только в GSC |
| `impressions` | — | ❌ Только в GSC |

**Использование:**
1. Метрика (C2.1): найти страницы-драйверы падения органики
2. GSC (C5.2): проверить позиции/CTR по этим страницам
3. Корреляция: если clicks (GSC) падают, а visits (Метрика) стабильны → проблема в атрибуции Метрики

---

### 7.2 Пример workflow агента

**Шаг 1:** Метрика C1 → органика упала на 36%

**Шаг 2:** Метрика C2.1 (pages by source="Search engine") → топ-10 страниц дали 80% падения

**Шаг 3:** GSC C5.2 (pages analysis) → проверить позиции по этим 10 страницам

**Шаг 4:** GSC C5.3 (query × page) → какие запросы упали по этим страницам

**Результат:** Конкретные запросы + страницы + причины (позиция/CTR/показы)

---

## 8. Примеры запросов для агента

### Запрос 1: Queries period compare

**P1:** 2024-12-01 — 2024-12-31  
**P2:** 2025-12-01 — 2025-12-31

```python
# Период 1
response_p1 = gsc_client.query({
    "startDate": "2024-12-01",
    "endDate": "2024-12-31",
    "dimensions": ["query"],
    "rowLimit": 1000,
    "dataState": "final"
})

# Период 2
response_p2 = gsc_client.query({
    "startDate": "2025-12-01",
    "endDate": "2025-12-31",
    "dimensions": ["query"],
    "rowLimit": 1000,
    "dataState": "final"
})

# Сравнение
workbook = compare_gsc_queries(response_p1, response_p2)
```

**Workbook structure:**
```json
{
  "meta": {
    "client": "partacademy",
    "site_url": "https://partacademy.ru",
    "p1_start": "2024-12-01",
    "p1_end": "2024-12-31",
    "p2_start": "2025-12-01",
    "p2_end": "2025-12-31",
    "generated_at": "2025-12-26T...",
    "source": "google_search_console"
  },
  "totals": {
    "total_clicks_p1": 15000,
    "total_clicks_p2": 9500,
    "total_delta_clicks": -5500,
    "total_delta_pct": -36.7
  },
  "rows": [
    {
      "query": "seo курсы онлайн",
      "clicks_p1": 1200,
      "clicks_p2": 400,
      "delta_clicks": -800,
      "delta_pct": -66.7,
      "impressions_p1": 5000,
      "impressions_p2": 4800,
      "delta_impressions": -200,
      "position_p1": 3.5,
      "position_p2": 8.2,
      "delta_position": 4.7,
      "ctr_p1": 24.0,
      "ctr_p2": 8.3,
      "delta_ctr": -15.7,
      "contribution_pct": 14.5
    }
  ]
}
```

---

### Запрос 2: Pages by specific query filter

**Назначение:** Найти все страницы по запросу "seo курсы"

```json
{
  "startDate": "2024-12-01",
  "endDate": "2024-12-31",
  "dimensions": ["page"],
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "query",
      "operator": "equals",
      "expression": "seo курсы"
    }]
  }],
  "rowLimit": 100,
  "dataState": "final"
}
```

---

## 9. Гипотезы и их проверки через GSC

### H2.2: Падение показов (спрос или индексация)

**Проверка через GSC:**
- C5.1 (queries): сравнить `impressions_p1` vs `impressions_p2`
- Если показы упали, а позиции стабильны → спрос упал или индексация
- Если показы упали вместе с позициями → позиции причина

**Evidence:**
- `analysis_gsc_queries_<p1><p2>.json`
- Топ запросов по вкладу `delta_impressions`

---

### H2.3: Падение позиций

**Проверка:**
- C5.1 (queries): сравнить `position_p1` vs `position_p2`
- Топ запросов с наибольшим `delta_position` (положительное = ухудшение)

**Evidence:**
- Конкретные запросы с конкретными дельтами позиций

---

### H2.4: CTR просел без позиции

**Проверка:**
- C5.1: `position` стабильна, но `ctr` упал
- Возможные причины: сниппеты конкурентов улучшились, title/description стали нерелевантны

**Evidence:**
- Запросы с `delta_ctr < -5%` и `|delta_position| < 2`

---

### H5.1: Страницы потеряли позиции

**Проверка:**
- C5.2 (pages): топ страниц по `delta_clicks`
- C5.3 (query × page): какие запросы по этим страницам упали

**Evidence:**
- Конкретные URL + конкретные запросы + дельты

---

## 10. Приоритизация для агента

### Критично (Tier 1)
1. **C5.1** Queries analysis (period compare)
2. **C5.2** Pages analysis (period compare)
3. **C5.3** Query × Page (детализация)

### Важно (Tier 2)
4. C5.4 Queries by device
5. C5.5 Pages by device

### Средне (Tier 3)
6. Country analysis
7. Date-level dynamics

---

## 11. Аутентификация

### OAuth 2.0

**Scopes:**
- `https://www.googleapis.com/auth/webmasters.readonly` — read-only (достаточно)

**Настройка:**
1. Создать проект в Google Cloud Console
2. Включить Search Console API
3. Создать OAuth 2.0 credentials (Desktop app или Web app)
4. Получить `client_id`, `client_secret`
5. Сгенерировать `refresh_token` через Authorization flow
6. Хранить `refresh_token` в `.env` (НЕ коммитить!)

**Пример хранения в `.env`:**
```
GSC_CLIENT_ID=...
GSC_CLIENT_SECRET=...
GSC_REFRESH_TOKEN=...
GSC_SITE_URL=https://partacademy.ru
```

---

## 12. Файловая структура артефактов

```
data_cache/partacademy/
  gsc_queries_raw_2024-12-01_2024-12-31.json
  gsc_queries_norm_2024-12-01_2024-12-31.json
  gsc_queries_raw_2025-12-01_2025-12-31.json
  gsc_queries_norm_2025-12-01_2025-12-31.json
  
  analysis_gsc_queries_2024120120241231__2025120120251231.json  (workbook)
  
  gsc_pages_raw_2024-12-01_2024-12-31.json
  gsc_pages_norm_2024-12-01_2024-12-31.json
  
  analysis_gsc_pages_2024120120241231__2025120120251231.json  (workbook)
  
  gsc_query_page_raw_2024-12-01_2024-12-31.json  (query × page)
  gsc_query_page_norm_2024-12-01_2024-12-31.json
```

---

## 13. Выводы для агента

**Критичность GSC:**
- **Без GSC невозможно:** определить конкретные причины падения органики (позиции/CTR/показы по запросам)
- **С GSC можно:** точно сказать "упали позиции по 10 запросам с X до Y"

**Интеграция с Метрикой:**
- Метрика → "что упало" (источники, страницы, объём)
- GSC → "почему упало" (позиции, CTR, показы, конкретные запросы)

**Приоритет реализации:** **Tier 1 (критично)**

