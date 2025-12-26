# MVP Capabilities Roadmap — минимум для профессионального уровня

**Цель:** Определить минимальный набор capabilities, при котором агент работает на уровне профессионального SEO-аналитика.

**Критерий успеха:** Агент может расследовать реальный кейс partacademy (падение органики -36.6%) и выдать конкретные страницы, запросы, причины и рекомендации.

---

## 1. Определение "профессионального уровня"

### Что НЕ профессионально

**Вывод уровня "обычный отчёт Метрики":**
> "Органический трафик упал на 36.6% (-15,425 визитов)"

**Проблема:** Это можно увидеть и без агента. Нет actionable insights.

---

### Что ЯВЛЯЕТСЯ профессиональным

**Вывод уровня "SEO-специалист":**
> "Органический трафик упал на 36.6% из-за потери позиций 3 ключевых страниц:
> 
> 1. `/course/marketing-basics` — позиция 5→15 (-5,200 визитов)
>    - Запросы: "маркетинг курсы" (поз. 3→12), "основы маркетинга онлайн" (поз. 4→18)
>    - Причина: позиции упали, показы стабильны → контент/конкуренты
>    - Рекомендация: аудит контента, проверка конкурентов по этим запросам
> 
> 2. `/course/seo-fundamentals` — позиция 8→22 (-4,100 визитов)
>    - Запросы: "seo курсы" (поз. 7→20), "основы seo" (поз. 6→25)
>    - Причина: позиции упали в Яндексе (Google стабилен)
>    - Рекомендация: проверить индексацию Яндекс, технические требования
> 
> 3. `/blog/seo-trends-2024` — выпала из топ-30 (-3,800 визитов)
>    - Причина: страница исключена из индекса Яндекса (DUPLICATE, canonical на другую страницу)
>    - Рекомендация: исправить canonical, повторная индексация
> 
> Итого: 3 страницы дали 94% вклада в падение органики."

**Ключевые отличия:**
- Конкретные страницы (не "органика вообще")
- Конкретные запросы (не "позиции упали")
- Конкретные причины (позиции / индексация / дубли)
- Actionable рекомендации (что делать)
- Всё подтверждено evidence (workbook, GSC, Вебмастер)

---

## 2. Минимальный набор capabilities для профессионального уровня

### MVP Capabilities (Tier 1)

| ID | Capability | Зачем | Данные | Приоритет |
|----|------------|-------|--------|-----------|
| **C1** | Sources compare | Подтвердить падение органики, найти вклад источника | Метрика: sources × visits | **✅ Есть** |
| **C2.1** | Pages by source | Найти страницы-драйверы в органике | Метрика: startURL × visits (filter: Search engine) | **1 (критично)** |
| **C5.1** | GSC Queries | Найти запросы, потерявшие позиции/CTR/показы (Google) | GSC: query × clicks/impressions/ctr/position | **2 (критично)** |
| **C5.2** | GSC Pages | Позиции/CTR по страницам (Google) | GSC: page × clicks/impressions/ctr/position | **2 (критично)** |
| **C6.1** | ВМ Queries | Найти запросы, потерявшие позиции (Яндекс) | ВМ: query × clicks/shows/position | **3 (критично для РФ)** |
| **C6.2** | ВМ Indexing | Проверить индексацию, найти EXCLUDED URLs | ВМ: search_url_status, причины исключения | **3 (критично для РФ)** |

**Итого:** 6 capabilities (1 есть + 5 новых)

---

### Почему именно эти 6?

**C1 (Sources):**
- Отвечает на вопрос: "Какой источник упал?"
- Подтверждает сигнал S2 (органика упала)
- ✅ Уже реализовано

**C2.1 (Pages by source):**
- Отвечает на вопрос: "Какие страницы упали в органике?"
- **Без этого:** невозможно найти страницы-драйверы
- **С этим:** "3 страницы дали 94% вклада"

**C5.1 (GSC Queries):**
- Отвечает на вопрос: "Какие запросы упали и почему?" (Google)
- **Без этого:** непонятно, позиции упали или показы
- **С этим:** "Запрос X: позиция 5→15, показы стабильны → позиции причина"

**C5.2 (GSC Pages):**
- Отвечает на вопрос: "Позиции по конкретным страницам" (Google)
- Дополняет C2.1 (Метрика показывает объём, GSC — почему)

**C6.1 (ВМ Queries):**
- Аналогично C5.1, но для Яндекса
- **Критично для РФ:** если Яндекс упал, а Google стабилен → Яндекс-специфичная причина

**C6.2 (ВМ Indexing):**
- Отвечает на вопрос: "Страницы выпали из индекса?"
- **Единственный способ** проверить гипотезу H2.5, H5.2 (индексация)
- Показывает **причины** исключения (404, noindex, duplicate, canonical)

---

## 3. Что можно делать с MVP

### Кейс 1: Падение органики (S2)

**Гипотезы, которые можно проверить:**
- ✅ H2.1 (кластеры страниц) — через C2.1
- ✅ H2.2 (падение показов) — через C5.1, C6.1
- ✅ H2.3 (падение позиций) — через C5.1, C6.1
- ✅ H2.4 (CTR просел) — через C5.1
- ✅ H2.5 (индексация) — через C6.2

**Результат:** Полное расследование падения органики с конкретными страницами, запросами и причинами.

---

### Кейс 2: Яндекс упал, Google стабилен (S3)

**Гипотезы, которые можно проверить:**
- ✅ H3.1 (алгоритмические изменения) — через C5.1 vs C6.1
- ✅ H3.3 (индексация отличается) — через C6.2

**Результат:** Понимание, почему Яндекс упал, а Google нет.

---

### Кейс 3: Падение в нескольких страницах (S5)

**Гипотезы, которые можно проверить:**
- ✅ H5.1 (страницы потеряли позиции) — через C5.2
- ✅ H5.2 (выпали из индекса) — через C6.2

---

### Что НЕ можем делать с MVP

**Кейс 4: Конверсия упала (S4)**
- ❌ H4.* (конверсии) — нужен C3 (Goals)
- **Tier 2**

**Кейс 5: Техпроблемы на mobile (H8.1)**
- ❌ Device analysis — нужны фильтры по device
- **Tier 3**

**Кейс 6: Ecommerce (H4.1)**
- ❌ Транзакции/доход — нужен C4 (Ecommerce)
- **Tier 3**

---

## 4. Roadmap реализации MVP

### Фаза 1: Landing pages by source (C2.1)

**Приоритет:** 1 (критично)

**Scope:**
1. Модуль `app/metrika_client.py`:
   - Добавить метод `landing_pages_by_source(date1, date2, source_filter, limit)`
   - Использовать `filters=ym:s:lastTrafficSource=='{source_filter}'`

2. Модуль `app/landing_pages.py` (новый):
   - `normalize_pages(raw_data)` — аналогично `normalize_sources`

3. Модуль `app/analysis_pages.py` (новый):
   - `compare_pages_periods(data_p1, data_p2)` — аналогично `analysis_sources`
   - `load_or_fetch_pages(client, date1, date2, source_filter, limit, refresh, metrika)`

4. CLI команда `app/cli.py`:
   - `metrika-pages-by-source <client> <date1> <date2> --source <source> [--limit N] [--refresh]`
   - `analyze-pages-by-source <client> <p1_start> <p1_end> <p2_start> <p2_end> --source <source> [--limit N] [--refresh]`

**Артефакты:**
- `data_cache/<client>/metrika_pages_by_source_raw_<source_slug>_<date1>_<date2>.json`
- `data_cache/<client>/metrika_pages_by_source_norm_<source_slug>_<date1>_<date2>.json`
- `data_cache/<client>/analysis_pages_by_source_<source_slug>_<p1><p2>.json` (workbook)

**DoD:**
```bash
python -m app.cli analyze-pages-by-source partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --source "Search engine traffic" --limit 50
```

Результат: Rich таблица + workbook с топ-50 страниц в органике, дельты, вклады.

---

### Фаза 2: Google Search Console integration (C5.1, C5.2)

**Приоритет:** 2 (критично)

**Scope:**
1. Модуль `app/gsc_client.py` (новый):
   - Класс `GSCClient`
   - OAuth 2.0 authentication
   - Метод `queries(date1, date2, dimensions, filters, row_limit)`
   - Метод `pages(date1, date2, dimensions, filters, row_limit)`

2. Модуль `app/analysis_gsc.py` (новый):
   - `compare_gsc_queries(data_p1, data_p2)` — дельты clicks/impressions/ctr/position
   - `compare_gsc_pages(data_p1, data_p2)` — аналогично

3. CLI команды:
   - `gsc-queries <client> <date1> <date2> [--limit N] [--refresh]`
   - `analyze-gsc-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N]`
   - `gsc-pages <client> <date1> <date2> [--limit N] [--refresh]`
   - `analyze-gsc-pages <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N]`

**Конфигурация (`clients/<client>/config.yaml`):**
```yaml
gsc:
  site_url: "https://partacademy.ru"
  # OAuth credentials в .env
```

**Артефакты:**
- `data_cache/<client>/gsc_queries_raw_<date1>_<date2>.json`
- `data_cache/<client>/gsc_queries_norm_<date1>_<date2>.json`
- `data_cache/<client>/analysis_gsc_queries_<p1><p2>.json` (workbook)

**DoD:**
```bash
python -m app.cli analyze-gsc-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 1000
```

Результат: workbook с топ-1000 запросов, дельты clicks/impressions/position/ctr, вклады.

---

### Фаза 3: Яндекс.Вебмастер integration (C6.1, C6.2)

**Приоритет:** 3 (критично для РФ)

**Scope:**
1. Модуль `app/ym_webmaster_client.py` (новый):
   - Класс `YMWebmasterClient`
   - OAuth authentication
   - Метод `popular_queries(date1, date2, device_type, query_indicators)`
   - Метод `indexing_samples(search_url_status, limit, offset)`

2. Модуль `app/analysis_ym_webmaster.py` (новый):
   - `compare_ym_queries(data_p1, data_p2)` — дельты clicks/shows/position
   - `analyze_indexing(excluded_urls, traffic_pages)` — корреляция с падением

3. CLI команды:
   - `ym-webmaster-queries <client> <date1> <date2> [--limit N] [--refresh]`
   - `analyze-ym-webmaster-queries <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N]`
   - `ym-webmaster-indexing <client> [--status EXCLUDED]`

**Конфигурация:**
```yaml
ym_webmaster:
  host_id: "https:partacademy.ru:443"
  user_id: "..."  # из /user endpoint
```

**Артефакты:**
- `data_cache/<client>/ym_webmaster_queries_raw_<date1>_<date2>.json`
- `data_cache/<client>/ym_webmaster_indexing_excluded_<snapshot_date>.json`
- `data_cache/<client>/analysis_ym_webmaster_queries_<p1><p2>.json`

**DoD:**
```bash
python -m app.cli analyze-ym-webmaster-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 500
python -m app.cli ym-webmaster-indexing partacademy --status EXCLUDED
```

Результат: workbook с топ-500 запросов (Яндекс) + список EXCLUDED URLs с причинами.

---

## 5. Timeline (оценка)

| Фаза | Complexity | Estimate | Dependencies |
|------|------------|----------|--------------|
| **Фаза 1** (C2.1) | Low | 4-6 часов | Метрика API (есть) |
| **Фаза 2** (C5.*) | Medium | 8-10 часов | GSC OAuth, API |
| **Фаза 3** (C6.*) | Medium | 8-10 часов | ВМ OAuth, API |
| **Итого MVP** | | **20-26 часов** | |

**Критический путь:** Фаза 1 → Фаза 2 / Фаза 3 (параллельно)

---

## 6. После MVP: Tier 2 (Goals)

### Зачем нужен Tier 2

**Кейс:** "Трафик стабилен, но продажи/конверсии упали"

**Tier 2 capabilities:**
- C3 (Goals by source)
- C3.1 (Goals by page)

**Оценка:** +8-12 часов

**Приоритет:** После стабилизации MVP и тестирования на реальных кейсах.

---

## 7. Критерий готовности MVP

### Тест на реальном кейсе

**Запрос:**
> "Разберись, почему упала органика partacademy в декабре 2025"

**Агент должен выдать:**
1. Подтверждение падения (C1): "Органика упала на 36.6%"
2. Страницы-драйверы (C2.1): "Топ-3 страницы дали 94% вклада"
3. Запросы Google (C5.1, C5.2): "Запросы X, Y упали по позициям с N до M"
4. Запросы Яндекс (C6.1): "Запросы A, B упали в Яндексе"
5. Индексация (C6.2): "Страница Z выпала из индекса (причина: DUPLICATE)"
6. Рекомендации: конкретные действия по каждой странице/запросу

**Если всё это есть:** MVP готов ✅

---

## 8. Next Steps после MVP

1. **Orchestrator** (intake → plan → execute → analyze → report)
   - Автоматический выбор capabilities по гипотезам
   - Agent loop с принятием решений
   - Генерация отчётов

2. **Tier 2** (Goals)
   - Анализ конверсий по источникам/страницам

3. **Tier 3** (Ecommerce, CRM, Device, Geo)
   - Расширение для специфичных кейсов

---

## 9. Вывод

**MVP = 6 capabilities (C1, C2.1, C5.1, C5.2, C6.1, C6.2)**

**С MVP агент работает на профессиональном уровне:**
- Конкретные страницы
- Конкретные запросы
- Конкретные причины
- Actionable рекомендации

**Без MVP:**
- Агент = "обычный отчёт Метрики"
- Нет профессионального уровня

**Roadmap:** Фаза 1 → Фаза 2 → Фаза 3 → MVP ready → Orchestrator → Tier 2

