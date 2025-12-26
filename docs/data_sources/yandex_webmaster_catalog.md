# Яндекс.Вебмастер — полная карта возможностей для Analyzer Machine

**API:** Yandex Webmaster API v4  
**Base URL:** `https://api.webmaster.yandex.net/v4/`  
**Документация:** [yandex.ru/dev/webmaster](https://yandex.ru/dev/webmaster/)

---

## 1. Основные эндпоинты

### 1.1 User info (информация о пользователе)

**Endpoint:** `GET /user`

**Описание:** Список доступных хостов (сайтов)

**Ответ:**
```json
{
  "hosts": [
    {
      "host_id": "https:partacademy.ru:443",
      "unicode_host_url": "https://partacademy.ru/",
      "verified": true
    }
  ]
}
```

---

### 1.2 Site summary (сводка по сайту)

**Endpoint:** `GET /user/{userId}/hosts/{hostId}/summary`

**Описание:** Общая информация: индексация, ошибки, главное зеркало

**Ключевые поля:**
- `indexing_events` — события индексации
- `site_problems` — проблемы сайта
- `viruses` — вирусы (если есть)

---

## 2. Search Queries API (запросы)

### 2.1 Популярные запросы

**Endpoint:** `POST /user/{userId}/hosts/{hostId}/search-queries/popular`

**Body:**
```json
{
  "date_from": "2024-12-01",
  "date_to": "2024-12-31",
  "query_indicator": ["TOTAL_SHOWS", "TOTAL_CLICKS", "AVG_SHOW_POSITION", "AVG_CLICK_POSITION"],
  "device_type_indicator": ["ALL", "MOBILE", "MOBILE_AND_TABLET", "DESKTOP", "TABLET"],
  "text_indicator": ["URL", "TITLE"],
  "query_text": ""
}
```

**Ответ:**
```json
{
  "count": 1000,
  "text_indicator": "URL",
  "queries": [
    {
      "query_id": "123456",
      "query_text": "seo курсы",
      "indicators": {
        "TOTAL_SHOWS": 5000,
        "TOTAL_CLICKS": 1200,
        "AVG_SHOW_POSITION": 3.5,
        "AVG_CLICK_POSITION": 3.2
      }
    }
  ]
}
```

---

### 2.2 History (история по запросу)

**Endpoint:** `POST /user/{userId}/hosts/{hostId}/search-queries/popular/history`

**Body:**
```json
{
  "query_ids": ["123456", "789012"],
  "date_from": "2024-12-01",
  "date_to": "2024-12-31",
  "device_type_indicator": "ALL"
}
```

**Ответ:** Динамика по дням для каждого запроса

---

## 3. Sitemaps API (карты сайта)

### 3.1 List sitemaps

**Endpoint:** `GET /user/{userId}/hosts/{hostId}/sitemaps`

**Описание:** Список добавленных sitemap

---

### 3.2 Sitemap info

**Endpoint:** `GET /user/{userId}/hosts/{hostId}/sitemaps/{sitemapId}`

**Описание:** Статистика по sitemap:
- URLs submitted
- URLs indexed
- URLs with errors

---

## 4. Indexing API (индексация)

### 4.1 Site stats (статистика индексации)

**Endpoint:** `GET /user/{userId}/hosts/{hostId}/search-urls/samples`

**Query params:**
- `limit` (1-100)
- `offset`
- `search_url_status` — фильтр по статусу

**Статусы индексации:**
- `INDEXED` — в индексе
- `EXCLUDED` — исключены
- `NOT_FOUND` — не найдены роботом

**Ответ:**
```json
{
  "count": 5000,
  "samples": [
    {
      "url": "https://partacademy.ru/course/seo",
      "search_url_status": "INDEXED",
      "http_code": 200,
      "last_access": "2025-12-25T10:00:00Z"
    },
    {
      "url": "https://partacademy.ru/old-page",
      "search_url_status": "EXCLUDED",
      "http_code": 404,
      "last_access": "2025-12-20T15:30:00Z"
    }
  ]
}
```

---

### 4.2 Indexing stats (сводка)

**Endpoint:** `GET /user/{userId}/hosts/{hostId}/indexing/search-statistics`

**Описание:** Агрегированные данные:
- Total URLs submitted
- Total URLs indexed
- Total URLs excluded

---

## 5. Capabilities для Analyzer Machine

### C6: Яндекс.Вебмастер integration

---

#### C6.1: Queries analysis (анализ запросов)

**Назначение:** Аналогично GSC C5.1, но для Яндекса

**Dimensions:** query_text  
**Metrics:** TOTAL_SHOWS, TOTAL_CLICKS, AVG_SHOW_POSITION

**Workflow:**
1. Запросить популярные запросы за P1 (2024-12-01 — 2024-12-31)
2. Запросить популярные запросы за P2 (2025-12-01 — 2025-12-31)
3. Сравнить: дельты clicks, shows, position

**Артефакты:**
- `data_cache/<client>/ym_webmaster_queries_raw_2024-12-01_2024-12-31.json`
- `data_cache/<client>/ym_webmaster_queries_norm_2024-12-01_2024-12-31.json`
- `data_cache/<client>/analysis_ym_webmaster_queries_<p1><p2>.json` (workbook)

**Гипотезы:**
- H2.2, H2.3, H2.4 (для Яндекса)
- H3.* (сравнение Яндекс vs Google)

---

#### C6.2: Indexing analysis (анализ индексации)

**Назначение:** Найти страницы, выпавшие из индекса

**Endpoint:** `/search-urls/samples` с фильтром `search_url_status=EXCLUDED`

**Workflow:**
1. Запросить все EXCLUDED URLs
2. Сопоставить с Метрикой C2.1 (какие страницы потеряли трафик)
3. Корреляция: если страница потеряла трафик И она excluded → индексация причина

**Артефакты:**
- `data_cache/<client>/ym_webmaster_indexing_raw_<date>.json`
- `data_cache/<client>/ym_webmaster_indexing_excluded_<date>.json` (только EXCLUDED)

**Гипотезы:**
- H2.5 (индексация/robots/canonical)
- H5.2 (страницы выпали из индекса)

**Примечание:** Вебмастер показывает **причины исключения** (404, noindex, robots.txt, canonical, duplicate), что критично для диагностики.

---

#### C6.3: Sitemaps validation

**Назначение:** Проверить, что sitemap актуальна и обрабатывается

**Workflow:**
1. Получить список sitemaps
2. Для каждой sitemap: проверить URLs submitted vs indexed
3. Найти расхождения (если много submitted, но мало indexed → проблема)

**Артефакты:**
- `data_cache/<client>/ym_webmaster_sitemaps_<date>.json`

**Гипотезы:**
- H2.5 (индексация)
- Техническая гипотеза: robots.txt блокирует sitemap

---

## 6. Сравнение с GSC

| Метрика | GSC | Вебмастер | Совместимость |
|---------|-----|-----------|---------------|
| Запросы | ✅ query | ✅ query_text | ✅ Аналогично |
| Клики | ✅ clicks | ✅ TOTAL_CLICKS | ✅ Аналогично |
| Показы | ✅ impressions | ✅ TOTAL_SHOWS | ✅ Аналогично |
| Позиция | ✅ position | ✅ AVG_SHOW_POSITION | ✅ Аналогично |
| CTR | ✅ ctr (расчётный) | ⚠️ Нет (расчётный) | ⚠️ Рассчитать |
| Страницы | ✅ page | ⚠️ Через text_indicator=URL | ⚠️ Частично |
| Индексация | ❌ Нет | ✅ search_url_status | ✅ Преимущество ВМ |
| Причины исключения | ❌ Нет | ✅ Да | ✅ Преимущество ВМ |

---

## 7. Гипотезы и проверки через Вебмастер

### H2.5: Индексация / robots / canonical

**Проверка:**
- C6.2: получить EXCLUDED URLs
- Если страницы из Метрики C2.1 (топ падений) есть в EXCLUDED → индексация причина
- Проверить причины исключения: 404, noindex, robots.txt, canonical

**Evidence:**
- Список EXCLUDED URLs с причинами
- Корреляция с падением трафика

---

### H3.1-H3.4: Яндекс vs Google

**Проверка:**
- C5.1 (GSC queries) vs C6.1 (ВМ queries)
- Сравнить дельты clicks/position по одинаковым запросам
- Если Яндекс упал сильнее → Яндекс-специфичная проблема

**Evidence:**
- Side-by-side таблица GSC vs ВМ по топ запросам
- Разница в дельтах

---

### H5.2: Страницы выпали из индекса

**Проверка:**
- C6.2: найти страницы, которые были INDEXED в P1, а стали EXCLUDED в P2
- Сопоставить с падением трафика

**Evidence:**
- Список переходов INDEXED → EXCLUDED
- Даты изменений

---

## 8. Device types (устройства)

**Доступные фильтры:**
- `ALL` — все устройства
- `MOBILE` — только мобильные (не планшеты)
- `MOBILE_AND_TABLET` — мобильные + планшеты
- `DESKTOP` — десктоп
- `TABLET` — только планшеты

**Применение:**
- Анализ падения на конкретных устройствах
- H8.1 (технические проблемы на mobile)

---

## 9. Ограничения API

| Параметр | Значение | Комментарий |
|----------|----------|-------------|
| Запросов в минуту | ~60 | Rate limit |
| Max queries в ответе | 500 | Для популярных запросов |
| История | ~6 месяцев | Данные старше удаляются |
| Обновление данных | ~1-2 дня lag | Аналогично GSC |

**Рекомендация:**
- Лимит ~500 запросов на период — достаточно для топов
- Не запрашивать данные за последние 2 дня

---

## 10. Аутентификация

### OAuth 2.0

**Scopes:**
- `webmaster:read` — read-only (достаточно)

**Настройка:**
1. Создать приложение на [oauth.yandex.ru](https://oauth.yandex.ru/)
2. Получить `client_id`, `client_secret`
3. Сгенерировать `refresh_token` через Authorization flow
4. Хранить в `.env` (НЕ коммитить!)

**Пример `.env`:**
```
YM_WEBMASTER_TOKEN=...
YM_WEBMASTER_HOST_ID=https:partacademy.ru:443
YM_WEBMASTER_USER_ID=...
```

---

## 11. Workbook structure (формат для агента)

### C6.1: Queries workbook

```json
{
  "meta": {
    "client": "partacademy",
    "host_id": "https:partacademy.ru:443",
    "p1_start": "2024-12-01",
    "p1_end": "2024-12-31",
    "p2_start": "2025-12-01",
    "p2_end": "2025-12-31",
    "generated_at": "2025-12-26T...",
    "source": "yandex_webmaster"
  },
  "totals": {
    "total_clicks_p1": 12000,
    "total_clicks_p2": 7500,
    "total_delta_clicks": -4500,
    "total_delta_pct": -37.5
  },
  "rows": [
    {
      "query": "seo курсы москва",
      "clicks_p1": 800,
      "clicks_p2": 250,
      "delta_clicks": -550,
      "delta_pct": -68.75,
      "shows_p1": 3000,
      "shows_p2": 2900,
      "delta_shows": -100,
      "position_p1": 4.2,
      "position_p2": 12.5,
      "delta_position": 8.3,
      "contribution_pct": 12.2
    }
  ]
}
```

---

### C6.2: Indexing workbook

```json
{
  "meta": {
    "client": "partacademy",
    "host_id": "https:partacademy.ru:443",
    "snapshot_date": "2025-12-26",
    "generated_at": "2025-12-26T...",
    "source": "yandex_webmaster_indexing"
  },
  "summary": {
    "total_urls": 5000,
    "indexed": 4200,
    "excluded": 700,
    "not_found": 100
  },
  "excluded_urls": [
    {
      "url": "https://partacademy.ru/old-page",
      "status": "EXCLUDED",
      "reason": "HTTP_404",
      "http_code": 404,
      "last_access": "2025-12-20T15:30:00Z"
    },
    {
      "url": "https://partacademy.ru/duplicate",
      "status": "EXCLUDED",
      "reason": "DUPLICATE",
      "http_code": 200,
      "last_access": "2025-12-25T10:00:00Z",
      "canonical_url": "https://partacademy.ru/original"
    }
  ]
}
```

---

## 12. Интеграция с Метрикой и GSC

### 12.1 Workflow для агента

**Шаг 1:** Метрика C1 → органика упала на 36%

**Шаг 2:** Метрика C2.1 (pages by source) → топ-10 страниц упали

**Шаг 3 (параллельно):**
- GSC C5.2 (pages) → позиции/клики/CTR (Google)
- ВМ C6.1 (queries) → позиции/клики (Яндекс)

**Шаг 4:** Сравнить GSC vs ВМ:
- Если обе ПС упали синхронно → общая причина (контент, техпроблемы)
- Если только Яндекс упал → Яндекс-специфичная проблема (алгоритм, индексация)

**Шаг 5 (если Яндекс упал):**
- ВМ C6.2 (indexing) → проверить EXCLUDED URLs по топ-10 страницам

---

### 12.2 Корреляция данных

| Источник | Что проверяет | Зона ответственности |
|----------|---------------|----------------------|
| Метрика | Объём трафика | "Сколько упало" |
| GSC | Позиции/CTR (Google) | "Почему упало в Google" |
| Вебмастер | Позиции/CTR (Яндекс) + индексация | "Почему упало в Яндексе" |

**Правило:** Все три источника дополняют друг друга, НЕ заменяют.

---

## 13. Приоритизация для агента

### Критично (Tier 1)
1. **C6.1** Queries analysis (period compare)
2. **C6.2** Indexing analysis (EXCLUDED URLs)

### Важно (Tier 2)
3. C6.3 Sitemaps validation
4. Device-level analysis (MOBILE vs DESKTOP)

### Средне (Tier 3)
5. Query history (динамика по дням)

---

## 14. Пример запросов для агента

### Запрос 1: Popular queries (P1)

```python
POST https://api.webmaster.yandex.net/v4/user/{userId}/hosts/{hostId}/search-queries/popular

Headers:
  Authorization: OAuth {token}
  Content-Type: application/json

Body:
{
  "date_from": "2024-12-01",
  "date_to": "2024-12-31",
  "query_indicator": ["TOTAL_SHOWS", "TOTAL_CLICKS", "AVG_SHOW_POSITION"],
  "device_type_indicator": "ALL",
  "text_indicator": "URL",
  "query_text": ""
}
```

---

### Запрос 2: Indexing samples (EXCLUDED)

```python
GET https://api.webmaster.yandex.net/v4/user/{userId}/hosts/{hostId}/search-urls/samples?search_url_status=EXCLUDED&limit=100&offset=0

Headers:
  Authorization: OAuth {token}
```

---

## 15. Выводы для агента

**Уникальность Вебмастера:**
- **Индексация:** единственный источник данных об исключённых URL и причинах
- **Яндекс-специфика:** критично для российского рынка

**Интеграция с GSC:**
- GSC + Вебмастер = полная картина по обеим ПС
- Обязательно для гипотез H3.* (Яндекс vs Google)

**Приоритет реализации:** **Tier 1 (критично для российского рынка)**

**Блокеры без Вебмастера:**
- Невозможно диагностировать падение именно в Яндексе
- Невозможно найти проблемы индексации (404, noindex, canonical)

