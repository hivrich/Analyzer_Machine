# Пример работы агента на реальном кейсе partacademy

**Кейс:** Падение органического трафика partacademy.ru в декабре 2025

**Цель:** Показать полный цикл работы агента от запроса пользователя до финального отчёта с конкретными рекомендациями.

---

## Вход: Запрос пользователя

**Голос → текст:**
> "Разберись, почему упала органика partacademy в декабре 2025, найди причины и что делать"

**Контекст:**
- Client: partacademy
- Counter ID: 41010869
- Goal ID: 0 (не настроен)
- Доступные capabilities: C1 (implemented), C2.1-C6.2 (planned_tier1)

---

## Agent Loop: Iteration 1

### Step 1: Intake (определение сигналов и гипотез)

**Parsing user query:**
```
Keywords extracted:
- "органика" → traffic source: organic
- "упала" → direction: drop
- "декабрь 2025" → period: 2025-12
- "причины" → root cause analysis
- "что делать" → recommendations needed
```

**Signals detected:**
- **S2** (органический трафик упал)

**Primary hypotheses:**
- **H2.1** (Просадка по кластерам страниц)
- **H2.3** (Падение позиций)

**Secondary hypotheses:**
- H2.2 (Падение показов)
- H2.4 (CTR просел)
- H2.5 (Индексация/canonical/robots)

**Periods inferred:**
- P1: 2024-12-01 to 2024-12-25 (comparison baseline)
- P2: 2025-12-01 to 2025-12-25 (current period)

**Intake Result:**
```json
{
  "signals": ["S2"],
  "hypotheses": ["H2.1", "H2.3", "H2.2", "H2.5"],
  "params": {
    "client": "partacademy",
    "p1_start": "2024-12-01",
    "p1_end": "2024-12-25",
    "p2_start": "2025-12-01",
    "p2_end": "2025-12-25",
    "limit": 50
  }
}
```

---

### Step 2: Query Planning (выбор capabilities)

**Reading Capability Registry...**

**Mapping hypotheses to capabilities:**
- H2.1 → C2.1 (Pages by source)
- H2.3 → C5.1 (GSC Queries), C6.1 (ВМ Queries)
- H2.2 → C5.1, C6.1
- H2.5 → C6.2 (ВМ Indexing)

**Dependency graph:**
```
C1 (Sources) [priority 1]
  ├─→ C2.1 (Pages by source) [priority 2]
        ├─→ C5.1 (GSC Queries) [priority 3]
        ├─→ C6.1 (ВМ Queries) [priority 3]
        └─→ C6.2 (ВМ Indexing) [priority 4]
```

**Query Plan:**
```json
{
  "queries": [
    {
      "id": "q1",
      "capability_id": "C1",
      "command": "python -m app.cli analyze-sources partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 50",
      "priority": 1,
      "depends_on": [],
      "checks_hypotheses": ["H2.1", "H2.3"],
      "status": "ready"
    },
    {
      "id": "q2",
      "capability_id": "C2.1",
      "command": "python -m app.cli analyze-pages-by-source partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --source 'Search engine traffic' --limit 50",
      "priority": 2,
      "depends_on": ["q1"],
      "checks_hypotheses": ["H2.1"],
      "status": "ready"
    },
    {
      "id": "q3",
      "capability_id": "C5.1",
      "command": "python -m app.cli analyze-gsc-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 1000",
      "priority": 3,
      "depends_on": ["q2"],
      "checks_hypotheses": ["H2.2", "H2.3"],
      "status": "ready"
    },
    {
      "id": "q4",
      "capability_id": "C6.1",
      "command": "python -m app.cli analyze-ym-webmaster-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 500",
      "priority": 3,
      "depends_on": ["q2"],
      "checks_hypotheses": ["H2.2", "H2.3"],
      "status": "ready"
    },
    {
      "id": "q5",
      "capability_id": "C6.2",
      "command": "python -m app.cli ym-webmaster-indexing partacademy --status EXCLUDED",
      "priority": 4,
      "depends_on": ["q2"],
      "checks_hypotheses": ["H2.5"],
      "status": "ready"
    }
  ]
}
```

---

### Step 3: Executor (выполнение запросов)

**[Executor] Running Query Plan (5 queries)...**

#### Query 1: C1 (Sources)

```bash
$ python -m app.cli analyze-sources partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 50
```

**Output:**
```
Workbook сохранён: analysis_sources_2024120120241225__2025120120251225.json
      Сравнение источников трафика (partacademy, 2024-12-01-2024-12-25 vs 2025-12-01-2025-12-25)      
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ source       ┃ visits_p1 ┃ visits_p2 ┃ delta_abs ┃ delta_pct ┃ contribution… ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Search       │     42117 │     26692 │    -15425 │     -36.6 │         112.1 │
│ engine       │           │           │           │           │               │
│ traffic      │           │           │           │           │               │
...

Итоги:
  Всего визитов P1: 50,515
  Всего визитов P2: 36,760
  Изменение (абс.): -13,755
  Изменение (%): -27.2%
```

**✅ q1 completed:** `data_cache/partacademy/analysis_sources_2024120120241225__2025120120251225.json`

---

#### Query 2: C2.1 (Pages by source = "Search engine traffic")

```bash
$ python -m app.cli analyze-pages-by-source partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --source 'Search engine traffic' --limit 50
```

**Output:**
```
Workbook сохранён: analysis_pages_by_source_SearchEngine_2024120120241225__2025120120251225.json
      Сравнение входных страниц (Search engine traffic, partacademy, 2024-12-01-2024-12-25 vs 2025-12-01-2025-12-25)
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ page                    ┃ visits_p1 ┃ visits_p2 ┃ delta_abs ┃ delta_pct ┃ contribution… ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ /course/marketing-ba... │      6200 │      1000 │     -5200 │     -83.9 │          33.7 │
│ /course/seo-fundamen... │      5100 │      1000 │     -4100 │     -80.4 │          26.6 │
│ /blog/seo-trends-2024   │      4000 │       200 │     -3800 │     -95.0 │          24.6 │
...

Итоги:
  Всего визитов P1 (органика): 42,117
  Всего визитов P2 (органика): 26,692
  Изменение (абс.): -15,425
  Изменение (%): -36.6%
```

**✅ q2 completed:** `data_cache/partacademy/analysis_pages_by_source_SearchEngine_2024120120241225__2025120120251225.json`

---

#### Query 3 & 4: C5.1 (GSC Queries) & C6.1 (ВМ Queries) — параллельно

**Query 3:**
```bash
$ python -m app.cli analyze-gsc-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 1000
```

**Output:**
```
Workbook сохранён: analysis_gsc_queries_2024120120241225__2025120120251225.json
Топ-10 запросов по вкладу (Google):
1. "маркетинг курсы": clicks 1200→300, position 3.0→12.0
2. "основы маркетинга онлайн": clicks 800→150, position 4.0→18.0
3. "seo курсы": clicks 1500→400, position 7.0→20.0
...
```

**✅ q3 completed:** `data_cache/partacademy/analysis_gsc_queries_2024120120241225__2025120120251225.json`

**Query 4:**
```bash
$ python -m app.cli analyze-ym-webmaster-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 500
```

**Output:**
```
Workbook сохранён: analysis_ym_webmaster_queries_2024120120241225__2025120120251225.json
Топ-10 запросов по вкладу (Яндекс):
1. "seo курсы москва": clicks 800→250, position 4.2→12.5
2. "маркетинг обучение": clicks 650→180, position 5.1→15.2
...
```

**✅ q4 completed:** `data_cache/partacademy/analysis_ym_webmaster_queries_2024120120241225__2025120120251225.json`

---

#### Query 5: C6.2 (ВМ Indexing)

```bash
$ python -m app.cli ym-webmaster-indexing partacademy --status EXCLUDED
```

**Output:**
```
Найдено EXCLUDED URLs: 15
Сохранено: data_cache/partacademy/ym_webmaster_indexing_excluded_20251226.json

Топ EXCLUDED (релевантные для анализа):
1. /blog/seo-trends-2024 — DUPLICATE (canonical на другую страницу)
2. /old-category/page — HTTP_404
3. /duplicate-page — DUPLICATE
...
```

**✅ q5 completed:** `data_cache/partacademy/ym_webmaster_indexing_excluded_20251226.json`

---

**Execution Result:**
```json
{
  "results": [
    {"query_id": "q1", "capability_id": "C1", "workbook_path": "data_cache/partacademy/analysis_sources_...json", "status": "success"},
    {"query_id": "q2", "capability_id": "C2.1", "workbook_path": "data_cache/partacademy/analysis_pages_by_source_...json", "status": "success"},
    {"query_id": "q3", "capability_id": "C5.1", "workbook_path": "data_cache/partacademy/analysis_gsc_queries_...json", "status": "success"},
    {"query_id": "q4", "capability_id": "C6.1", "workbook_path": "data_cache/partacademy/analysis_ym_webmaster_queries_...json", "status": "success"},
    {"query_id": "q5", "capability_id": "C6.2", "workbook_path": "data_cache/partacademy/ym_webmaster_indexing_excluded_...json", "status": "success"}
  ],
  "errors": [],
  "duration": 45.2
}
```

---

### Step 4: Analyzer (проверка гипотез)

**[Analyzer] Checking hypotheses against workbooks...**

#### Hypothesis H2.1 (Кластеры страниц)

**Rule:** Если топ-3 страницы дают >70% вклада → confirmed

**Workbook:** `analysis_pages_by_source_SearchEngine_...json`

**Calculation:**
```python
top3 = workbook["rows"][:3]
top3_contribution = 33.7 + 26.6 + 24.6 = 84.9%
```

**Verdict:**
```json
{
  "hypothesis_id": "H2.1",
  "status": "confirmed",
  "confidence": 0.95,
  "facts": [
    "Топ-3 страницы дали 84.9% вклада (> 70% threshold)",
    "/course/marketing-basics: -5,200 визитов (33.7% вклада)",
    "/course/seo-fundamentals: -4,100 визитов (26.6% вклада)",
    "/blog/seo-trends-2024: -3,800 визитов (24.6% вклада)"
  ],
  "evidence": ["data_cache/partacademy/analysis_pages_by_source_SearchEngine_...json"]
}
```

---

#### Hypothesis H2.3 (Падение позиций)

**Rule:** Если позиции упали на >5 мест по ключевым запросам → confirmed

**Workbooks:** `analysis_gsc_queries_...json`, `analysis_ym_webmaster_queries_...json`

**Calculation:**
```python
# Google
top_queries_gsc = [
    {"query": "маркетинг курсы", "delta_position": +9.0},
    {"query": "основы маркетинга онлайн", "delta_position": +14.0},
    {"query": "seo курсы", "delta_position": +13.0}
]

# Яндекс
top_queries_ym = [
    {"query": "seo курсы москва", "delta_position": +8.3},
    {"query": "маркетинг обучение", "delta_position": +10.1}
]

# Среднее падение позиций: +11.1 мест (> 5 threshold)
```

**Verdict:**
```json
{
  "hypothesis_id": "H2.3",
  "status": "confirmed",
  "confidence": 0.92,
  "facts": [
    "Позиции по ключевым запросам упали на 9-14 мест (Google) и 8-10 мест (Яндекс)",
    "Google: 'маркетинг курсы' (3→12), 'основы маркетинга онлайн' (4→18), 'seo курсы' (7→20)",
    "Яндекс: 'seo курсы москва' (4.2→12.5), 'маркетинг обучение' (5.1→15.2)",
    "Показы стабильны, клики упали → причина = позиции, не спрос"
  ],
  "evidence": [
    "data_cache/partacademy/analysis_gsc_queries_...json",
    "data_cache/partacademy/analysis_ym_webmaster_queries_...json"
  ]
}
```

---

#### Hypothesis H2.5 (Индексация)

**Rule:** Если страницы-драйверы есть в EXCLUDED → confirmed

**Workbooks:** `analysis_pages_by_source_...json` + `ym_webmaster_indexing_excluded_...json`

**Correlation:**
```python
top_pages = ["/course/marketing-basics", "/course/seo-fundamentals", "/blog/seo-trends-2024"]
excluded_urls = ["/blog/seo-trends-2024", "/old-category/page", ...]

# Пересечение: 1 из 3 (33%)
intersection = ["/blog/seo-trends-2024"]
```

**Verdict:**
```json
{
  "hypothesis_id": "H2.5",
  "status": "partially_confirmed",
  "confidence": 0.70,
  "facts": [
    "1 из 3 страниц-драйверов выпала из индекса Яндекса",
    "/blog/seo-trends-2024: статус EXCLUDED, причина DUPLICATE (canonical на другую страницу)",
    "Остальные 2 страницы: в индексе, причина падения = позиции (не индексация)"
  ],
  "evidence": [
    "data_cache/partacademy/analysis_pages_by_source_SearchEngine_...json",
    "data_cache/partacademy/ym_webmaster_indexing_excluded_20251226.json"
  ]
}
```

---

**Analysis Result:**
```json
{
  "verdicts": [
    {"hypothesis_id": "H2.1", "status": "confirmed", "confidence": 0.95},
    {"hypothesis_id": "H2.3", "status": "confirmed", "confidence": 0.92},
    {"hypothesis_id": "H2.5", "status": "partially_confirmed", "confidence": 0.70}
  ]
}
```

---

### Step 5: Decision Engine (loop или done?)

**[Decision Engine] Evaluating verdicts...**

**Primary hypotheses:** H2.1, H2.3  
**Status:** Both confirmed ✅

**Decision:**
```json
{
  "action": "done",
  "reason": "Primary hypotheses (H2.1, H2.3) confirmed with high confidence. Root causes identified: 3 pages lost positions.",
  "root_causes": [
    "3 pages (/course/marketing-basics, /course/seo-fundamentals, /blog/seo-trends-2024) gave 84.9% contribution",
    "Positions dropped 9-14 places",
    "1 page excluded from Yandex index (DUPLICATE)"
  ],
  "next_actions": "Proceed to report generation"
}
```

**→ No loop needed, proceed to final report**

---

### Step 6: Report Generation

**[Report Generator] Creating report...**

**Run ID:** `2025-12-26-143022`

**Files created:**
1. `reports/partacademy/2025-12-26-143022/report.md` (Executive Summary + Facts + Recommendations)
2. `reports/partacademy/2025-12-26-143022/evidence.txt` (список workbooks)

**Report preview:** См. `docs/orchestrator_architecture.md` (секция 2.6) для полного примера

---

## Выход: Финальный отчёт

**Summary для пользователя:**

> **Анализ завершён!**
> 
> **Причина падения органики на 36.6%:**
> 
> 3 страницы потеряли позиции (дали 85% вклада):
> 1. `/course/marketing-basics` — позиция 3→12 по "маркетинг курсы" (-5,200 визитов)
> 2. `/course/seo-fundamentals` — позиция 7→20 по "seo курсы" (-4,100 визитов)
> 3. `/blog/seo-trends-2024` — выпала из индекса Яндекса (DUPLICATE) (-3,800 визитов)
> 
> **Рекомендации:**
> - Страницы 1-2: аудит контента, сравнение с конкурентами, обновление
> - Страница 3: исправить canonical, повторная индексация
> 
> **Отчёт:** `reports/partacademy/2025-12-26-143022/report.md`

---

## Сравнение: без агента vs с агентом

### Без агента (ручной анализ)

**Действия пользователя:**
1. Открыть Метрику → посмотреть отчёт "Источники" → "Органика упала"
2. Открыть отчёт "Страницы входа" → вручную найти топ падений
3. Открыть GSC → вручную найти запросы
4. Открыть Вебмастер → проверить индексацию
5. Сопоставить всё вручную → сделать выводы
6. Написать отчёт

**Время:** ~2-3 часа работы SEO-специалиста

---

### С агентом

**Действия пользователя:**
1. Сказать/написать: "Разберись, почему упала органика partacademy в декабре 2025"
2. Подождать ~1 минуту
3. Получить отчёт с конкретными страницами, запросами, причинами и рекомендациями

**Время:** 1 минута

**Качество:** Профессиональный уровень, все выводы подтверждены evidence

---

## Вывод

**Агент работает как SEO-профессионал:**
- Сам определяет гипотезы
- Сам планирует проверки
- Сам запускает команды
- Сам анализирует данные
- Сам пишет отчёт

**Пользователь получает:**
- Конкретные страницы
- Конкретные запросы
- Конкретные причины
- Actionable рекомендации
- Всё за 1 минуту вместо 2-3 часов

