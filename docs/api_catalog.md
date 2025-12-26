# Analyzer Machine — API Catalog: Яндекс.Метрика (Reporting API)

Этот документ фиксирует **проверенный и минимально-достаточный** набор запросов к API Яндекс.Метрики, который нужен Analyzer Machine для on‑demand анализа трафика, источников и конверсий.

## 1) Базовые эндпоинты

### 1.1 Reporting API (табличные отчёты)
- Метод: `GET`
- URL: `https://api-metrika.yandex.net/stat/v1/data`
- Назначение: агрегированные отчёты по сессиям (`ym:s:*`) и просмотрам страниц (`ym:pv:*`).

### 1.2 Management API (служебно, опционально)
- Метод: `GET`
- URL: `https://api-metrika.yandex.net/management/v1/counters`
- Назначение: получить список доступных счётчиков (помогает найти `counter_id`, если его нет в конфиге).

## 2) Аутентификация

OAuth‑токен передаётся в заголовке:

`Authorization: OAuth <token>`

Токен хранится локально (например, в `.env` как `YANDEX_METRIKA_TOKEN`) и **никогда не коммитится**.

## 3) Общие правила совместимости метрик/измерений

В Reporting API есть разные «таблицы» данных:

- `ym:s:*` — сессии (визиты)
- `ym:pv:*` — просмотры страниц (хиты)

В одном запросе **нельзя** смешивать `ym:s:*` и `ym:pv:*` в `metrics`/`dimensions`.
Исключение: в `filters` можно фильтровать по другому префиксу.

## 4) Параметры запроса `/stat/v1/data`

Ниже — параметры, которые реально используем (или оставляем как «рычаги» для точности/производительности).

### 4.1 Идентификатор счётчика
- `ids` (предпочтительно): список ID счётчиков через запятую  
  Пример: `ids=44147844`
- `id` (встречается в примерах документации): одиночный ID  
  Пример: `id=44147844`

В Analyzer Machine используем **один счётчик**, поэтому на практике это всегда «одно число».

### 4.2 Период
- `date1`, `date2`: `YYYY-MM-DD`

### 4.3 Метрики и измерения
- `metrics` (обязательный): список метрик через запятую (лимит: 20 метрик на запрос)
- `dimensions` (опционально): список измерений через запятую

### 4.4 Сегментация/фильтры
- `filters` (опционально): выражение сегментации (строка)

### 4.5 Сортировка и пагинация
- `sort` (опционально): список метрик/измерений для сортировки (по умолчанию по убыванию, `-` перед именем)
- `limit` (опционально): число строк на странице (обычно 100; максимум в API — до 100000)
- `offset` (опционально): индекс первой строки (начиная с 1)

### 4.6 Точность / семплирование
- `accuracy` (опционально): размер выборки / семплирование. Допустимые значения:
  - `low`, `medium`, `high`, `full`
  - либо число `0 < accuracy ≤ 1` (доля выборки)

Рекомендация для Analyzer Machine:
- по умолчанию: `accuracy=medium`
- при спорных/пограничных выводах: повышать до `high` или `full`

### 4.7 Прочее (полезно при отладке)
- `lang` (опционально): язык значений (например `ru`)
- `pretty` (опционально): `true/false` — «красивый» ответ (в логах и дебаге)

### 4.8 Часовой пояс
- `timezone` (опционально): смещение вида `+03:00`, `+01:00` и т.п.

Важно: это **не** IANA‑таймзона (не `Europe/Zurich`).  
Если `timezone` не задан — Метрика использует таймзону счётчика.

## 5) Проверенный набор метрик для Analyzer Machine

### 5.1 Базовые метрики сессий (используются сейчас)
- `ym:s:visits` — визиты
- `ym:s:users` — пользователи
- `ym:s:bounceRate` — отказность (в процентах)
- `ym:s:pageDepth` — глубина просмотра
- `ym:s:avgVisitDurationSeconds` — средняя длительность визита (сек)

### 5.2 Цели (goal_id берём из `clients/<client>/config.yaml`)
Параметризация метрик цели (официально поддерживается Reporting API):

- `ym:s:goal<goal_id>visits` — число **конверсионных визитов** по цели
- `ym:s:goal<goal_id>conversionRate` — конверсия по цели (в процентах)

Пример: если `goal_id=123456`, то:
- `ym:s:goal123456visits`
- `ym:s:goal123456conversionRate`

## 6) Запросы, которые использует/будет использовать Analyzer Machine

Ниже — «контракты» для методов клиента `MetrikaClient` и CLI‑команд.

---

### 6.1 Источники трафика (команда `metrika-sources`)
Цель: получить сводку по источникам за период.

- Endpoint: `/stat/v1/data`
- Префикс: `ym:s:*` (сессии)
- Dimensions:
  - `ym:s:lastTrafficSource`
- Metrics:
  - `ym:s:visits, ym:s:users, ym:s:bounceRate, ym:s:pageDepth, ym:s:avgVisitDurationSeconds`
- Sort: `-ym:s:visits`
- Limit: как правило 20–100 (по `--limit`)

Пример (query string):
`ids=<counter_id>&dimensions=ym:s:lastTrafficSource&metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds&date1=<date1>&date2=<date2>&sort=-ym:s:visits&limit=<limit>&accuracy=medium&lang=ru`

---

### 6.2 Входные страницы (landing pages) (команда `metrika-pages`, планируется)
Цель: найти страницы входа с максимальными потерями/ростом.

Вариант A (предпочтительный для читабельности; больше данных):
- Dimensions: `ym:s:startURL`
- Metrics: `ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds`
- Sort: `-ym:s:visits`

Вариант B (preset, быстрый старт; использует hash‑измерения):
- `preset=content_entrance`
- Metrics/Dimensions фиксированы пресетом (см. оф. документацию пресета Contents → Landing pages).

Пример (вариант A):
`ids=<counter_id>&dimensions=ym:s:startURL&metrics=ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds&date1=<date1>&date2=<date2>&sort=-ym:s:visits&limit=<limit>&accuracy=medium&lang=ru`

---

### 6.3 «Все страницы» по просмотрам (команда `metrika-pages`, доп.режим; планируется)
Цель: понять структуру потребления контента (pageviews) по URL.

- Префикс: `ym:pv:*` (просмотры страниц)
- Dimensions:
  - `ym:pv:URL` (или hash‑варианты из пресета `popular`)
- Metrics:
  - `ym:pv:pageviews, ym:pv:users`
- Sort: `-ym:pv:pageviews`

Пример:
`ids=<counter_id>&dimensions=ym:pv:URL&metrics=ym:pv:pageviews,ym:pv:users&date1=<date1>&date2=<date2>&sort=-ym:pv:pageviews&limit=<limit>&accuracy=medium&lang=ru`

---

### 6.4 Конверсии по источникам (команда `metrika-goals`, планируется)
Цель: разложить конверсию по источникам.

- Dimensions: `ym:s:lastTrafficSource`
- Metrics (пример для одной цели):
  - `ym:s:visits`
  - `ym:s:goal<goal_id>visits`
  - `ym:s:goal<goal_id>conversionRate`
- Sort: обычно по `-ym:s:goal<goal_id>visits` или `-ym:s:visits`

Пример:
`ids=<counter_id>&dimensions=ym:s:lastTrafficSource&metrics=ym:s:visits,ym:s:goal<goal_id>visits,ym:s:goal<goal_id>conversionRate&date1=<date1>&date2=<date2>&sort=-ym:s:goal<goal_id>visits&limit=<limit>&accuracy=medium&lang=ru`

---

### 6.5 Конверсии по входным страницам (команда `metrika-goals`, доп.режим; планируется)
Цель: найти страницы входа, которые «просели» по конверсиям.

- Dimensions: `ym:s:startURL`
- Metrics:
  - `ym:s:visits`
  - `ym:s:goal<goal_id>visits`
  - `ym:s:goal<goal_id>conversionRate`

---

### 6.6 Ecommerce (позже; требует отдельной валидации метрик)
В проекте предусмотрена интеграция ecommerce‑метрик, но **перед использованием** нужно:
1) зафиксировать конкретные метрики/измерения, которые доступны в счётчике,
2) договориться о том, что именно считаем «покупкой» (ecommerce vs цель),
3) покрыть тестами/сэмплингом расхождения «интерфейс vs API».

До этого момента в MVP опираемся на **цели** (goal_id).

## 7) Где в проекте это используется

- `MetrikaClient`: `/app/metrika_client.py`
- CLI: `/app/cli.py`
- Конфиги клиентов: `/clients/<client>/config.yaml`

## 8) Официальные справочники

- Reporting API: Table `/stat/v1/data` (OpenAPI reference)
- Sampling / accuracy (семплирование)
- Parametrization (goal<goal_id>…)
- Presets (content_entrance, popular, sources_summary)

(Ссылки держим в репозитории в README/Docs, чтобы не «протухали» в тексте.)
