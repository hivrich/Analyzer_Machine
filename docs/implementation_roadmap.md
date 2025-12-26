# Implementation Roadmap — поэтапная реализация агента

**Цель:** Пошаговый план реализации от текущего состояния (C1) до полноценного агента-профессионала.

**Принцип:** Маленькие вертикальные срезы (1 capability за итерацию), после каждой итерации — тестирование на реальном кейсе.

---

## Текущее состояние (Baseline)

**Реализовано:**
- ✅ C1 (Sources period compare)
- ✅ CLI infrastructure (Typer, Rich)
- ✅ Config management (clients/<client>/config.yaml)
- ✅ Data cache structure (data_cache/<client>/)
- ✅ Workbook format (meta + totals + rows)
- ✅ .env секреты (YANDEX_METRIKA_TOKEN)

**Можем делать:**
- Сравнение источников трафика между периодами
- Вывод Rich таблиц
- Сохранение workbook для анализа

**НЕ можем делать:**
- Найти конкретные страницы-драйверы
- Проверить позиции/CTR по запросам
- Проверить индексацию
- Автоматический agent loop

---

## Phase 1: MVP Tier 1 (критичные capabilities)

**Цель:** Агент может работать на профессиональном уровне для анализа падения органики.

**Критерий успеха:** Запрос "Почему упала органика?" → отчёт с конкретными страницами, запросами, причинами.

---

### Iteration 1.1: C2.1 (Landing Pages by Source)

**Приоритет:** 🔴 Критично  
**Оценка:** 4-6 часов  
**Dependencies:** Метрика API (есть), понимание фильтров

**Scope:**

1. **`app/landing_pages.py` (новый модуль)**
   - `normalize_pages(raw_data)` — аналогично `normalize_sources`
   - Тесты (unit tests для normalize)

2. **`app/metrika_client.py` (расширение)**
   - Добавить метод:
     ```python
     def landing_pages_by_source(
         self,
         date1: str,
         date2: str,
         source_filter: str,
         limit: int = 50
     ) -> Dict[str, Any]:
         """
         Landing pages с фильтром по источнику.
         
         Args:
             source_filter: "Search engine traffic" / "Direct traffic" / etc.
         
         Returns:
             Raw API response
         """
         url = "https://api-metrika.yandex.net/stat/v1/data"
         params = {
             "ids": str(self.counter_id),
             "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageDepth,ym:s:avgVisitDurationSeconds",
             "dimensions": "ym:s:startURL",
             "filters": f"ym:s:lastTrafficSource=='{source_filter}'",
             "date1": date1,
             "date2": date2,
             "accuracy": "full",
             "limit": str(limit),
             "sort": "-ym:s:visits"
         }
         return self._get(url, params)
     ```

3. **`app/analysis_pages.py` (новый модуль)**
   - `compare_pages_periods(data_p1, data_p2)` — аналогично `analysis_sources.compare_sources_periods`
   - `calculate_contributions(rows)` — переиспользовать логику
   - `load_or_fetch_pages(client, date1, date2, source_filter, limit, refresh, metrika)` — кэш + API
   - `create_pages_workbook(...)` — формат workbook

4. **`app/cli.py` (расширение)**
   - Добавить команды:
     ```python
     @app.command("metrika-pages-by-source")
     def metrika_pages_by_source_cmd(
         client: str,
         date1: str,
         date2: str,
         source: str = typer.Option("Search engine traffic", "--source"),
         limit: int = typer.Option(50, "--limit"),
     ):
         """Получить landing pages из Метрики с фильтром по источнику."""
         ...
     
     @app.command("analyze-pages-by-source")
     def analyze_pages_by_source_cmd(
         client: str,
         p1_start: str,
         p1_end: str,
         p2_start: str,
         p2_end: str,
         source: str = typer.Option("Search engine traffic", "--source"),
         limit: int = typer.Option(50, "--limit"),
         refresh: bool = typer.Option(False, "--refresh"),
     ):
         """Сравнить landing pages между периодами (с фильтром по источнику)."""
         ...
     ```

**DoD (Definition of Done):**
```bash
# Тест 1: Получить данные
python -m app.cli metrika-pages-by-source partacademy 2024-12-01 2024-12-31 --source "Search engine traffic" --limit 50

# Тест 2: Сравнить периоды
python -m app.cli analyze-pages-by-source partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --source "Search engine traffic" --limit 50

# Ожидаемый результат:
# - Rich таблица с топ-50 страниц
# - Workbook: data_cache/partacademy/analysis_pages_by_source_SearchEngine_...json
# - Totals сходятся с C1 (органика)
```

**Risks:**
- Slugify source для имени файла (пробелы → "_")
- Валидация source_filter (неправильное имя → пустой результат)

---

### Iteration 1.2: C5 (Google Search Console Integration)

**Приоритет:** 🔴 Критично  
**Оценка:** 8-10 часов (OAuth сложнее)  
**Dependencies:** GSC OAuth credentials

**Scope:**

1. **OAuth 2.0 Setup**
   - Создать проект в Google Cloud Console
   - Включить Search Console API
   - Создать OAuth credentials (Desktop app)
   - Сгенерировать refresh_token (один раз, вручную)
   - Добавить в `.env`:
     ```
     GSC_CLIENT_ID=...
     GSC_CLIENT_SECRET=...
     GSC_REFRESH_TOKEN=...
     ```

2. **`app/gsc_client.py` (новый модуль)**
   - Класс `GSCClient`:
     ```python
     @dataclass(frozen=True)
     class GSCClient:
         client_id: str
         client_secret: str
         refresh_token: str
         site_url: str
         
         def _get_access_token(self) -> str:
             """Обменять refresh_token на access_token."""
             ...
         
         def queries(
             self,
             date1: str,
             date2: str,
             dimensions: List[str],
             row_limit: int = 1000
         ) -> Dict[str, Any]:
             """
             Запросы из GSC.
             
             Args:
                 dimensions: ["query"] или ["query", "device"]
                 row_limit: 1-25000
             
             Returns:
                 GSC API response
             """
             ...
         
         def pages(
             self,
             date1: str,
             date2: str,
             row_limit: int = 1000
         ) -> Dict[str, Any]:
             """Страницы из GSC."""
             ...
     ```

3. **`app/gsc_normalize.py` (новый модуль)**
   - `normalize_gsc_queries(raw_data)` → список словарей с query/clicks/impressions/ctr/position
   - `normalize_gsc_pages(raw_data)` → аналогично

4. **`app/analysis_gsc.py` (новый модуль)**
   - `compare_gsc_queries(data_p1, data_p2)` — дельты clicks/impressions/position/ctr, вклады
   - `compare_gsc_pages(data_p1, data_p2)` — аналогично
   - `create_gsc_workbook(...)`

5. **`app/cli.py` (расширение)**
   - Команды:
     ```python
     @app.command("gsc-queries")
     def gsc_queries_cmd(...)
     
     @app.command("analyze-gsc-queries")
     def analyze_gsc_queries_cmd(...)
     
     @app.command("gsc-pages")
     def gsc_pages_cmd(...)
     
     @app.command("analyze-gsc-pages")
     def analyze_gsc_pages_cmd(...)
     ```

6. **`clients/<client>/config.yaml` (расширение)**
   ```yaml
   gsc:
     site_url: "https://partacademy.ru"
   ```

**DoD:**
```bash
# Тест 1: Queries
python -m app.cli analyze-gsc-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 1000

# Тест 2: Pages
python -m app.cli analyze-gsc-pages partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --limit 1000

# Ожидаемый результат:
# - Workbook с топ-1000 запросов/страниц
# - Дельты clicks/impressions/position/ctr
# - Вклады
```

**Risks:**
- OAuth сложность (первая настройка вручную)
- Rate limits GSC API (~300 requests/day)
- Lag данных (2-3 дня)

---

### Iteration 1.3: C6 (Яндекс.Вебмастер Integration)

**Приоритет:** 🔴 Критично для РФ  
**Оценка:** 8-10 часов  
**Dependencies:** ВМ OAuth credentials

**Scope:** Аналогично C5, но для Яндекс.Вебмастер API

1. OAuth setup (oauth.yandex.ru)
2. `app/ym_webmaster_client.py`
3. `app/ym_webmaster_normalize.py`
4. `app/analysis_ym_webmaster.py`
5. CLI команды
6. Config расширение

**DoD:** Аналогично C5

---

**Phase 1 Summary:**
- ✅ C1 (есть)
- ✅ C2.1 (Iteration 1.1)
- ✅ C5.1, C5.2 (Iteration 1.2)
- ✅ C6.1, C6.2 (Iteration 1.3)

**Итого:** ~20-26 часов, 3 iterations

**Критерий успеха Phase 1:**
```bash
# Full test case
python -m app.cli analyze-sources partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25
python -m app.cli analyze-pages-by-source partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25 --source "Search engine traffic"
python -m app.cli analyze-gsc-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25
python -m app.cli analyze-gsc-pages partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25
python -m app.cli analyze-ym-webmaster-queries partacademy 2024-12-01 2024-12-25 2025-12-01 2025-12-25
python -m app.cli ym-webmaster-indexing partacademy --status EXCLUDED
```

→ 6 workbooks → можно вручную проанализировать и написать отчёт профессионального уровня

---

## Phase 2: Orchestrator (автоматизация agent loop)

**Цель:** Пользователь пишет одну фразу → агент сам планирует и выполняет

**Оценка:** 12-16 часов

---

### Iteration 2.1: Intake + Query Planner

**Scope:**

1. **`app/orchestrator/intake.py`**
   - `intake(user_query, context)` → IntakeResult(signals, hypotheses, params)
   - Keyword extraction
   - Signal detection (простые правила)
   - Period inference (из текста или по умолчанию)

2. **`app/orchestrator/query_planner.py`**
   - `plan_queries(hypotheses, registry, params)` → QueryPlan
   - Чтение `capabilities_registry.yaml`
   - Mapping hypotheses → capabilities
   - Топологическая сортировка по зависимостям

3. **`app/orchestrator/registry.py`**
   - Класс `CapabilityRegistry`
   - `load(yaml_path)` → реестр capabilities
   - `get_capabilities_for_hypothesis(hypothesis_id)` → список capabilities

**DoD:**
```python
# Unit test
intake_result = intake("Разберись, почему упала органика partacademy в декабре 2025", {})
assert intake_result.signals == ["S2"]
assert "H2.1" in intake_result.hypotheses

query_plan = plan_queries(intake_result.hypotheses, registry, intake_result.params)
assert query_plan.queries[0].capability_id == "C1"
assert query_plan.queries[1].capability_id == "C2.1"
```

---

### Iteration 2.2: Executor + Analyzer

**Scope:**

1. **`app/orchestrator/executor.py`**
   - `execute_plan(plan, use_cache)` → ExecutionResult
   - Subprocess для CLI команд
   - Сбор workbooks

2. **`app/orchestrator/analyzer.py`**
   - `analyze_workbooks(execution_result, hypotheses, rules)` → AnalysisResult
   - Hypothesis checkers (H2.1, H2.3, etc.)
   - `AnalysisRules.load()` — чтение правил из `docs/analysis_rules.md`

3. **`app/orchestrator/analysis_rules.py`**
   - Правила проверки гипотез (пороги, формулы)

**DoD:**
```python
# Integration test
execution_result = execute_plan(query_plan, use_cache=True)
assert len(execution_result.results) == 5  # 5 queries
assert execution_result.errors == []

analysis_result = analyze_workbooks(execution_result, hypotheses, AnalysisRules.load())
assert analysis_result.verdicts[0].hypothesis_id == "H2.1"
assert analysis_result.verdicts[0].status == "confirmed"
```

---

### Iteration 2.3: Decision Engine + Report Generator

**Scope:**

1. **`app/orchestrator/decision_engine.py`**
   - `decide_next_step(analysis_result, query_plan)` → Decision
   - Правила: done / continue / capability_missing

2. **`app/orchestrator/report_generator.py`**
   - `generate_report(analysis_result, context, run_id)` → Report
   - Markdown отчёт (Executive Summary + Facts + Hypotheses + Recommendations)
   - Evidence list (пути к workbooks)

3. **`app/orchestrator/agent_loop.py`**
   - `agent_loop(user_query, client, max_iterations)` → Report
   - Интеграция всех модулей

**DoD:**
```python
# Full agent loop test
report = agent_loop("Разберись, почему упала органика partacademy в декабре 2025", "partacademy")
assert report.run_id
assert Path(f"reports/partacademy/{report.run_id}/report.md").exists()
assert Path(f"reports/partacademy/{report.run_id}/evidence.txt").exists()
```

---

### Iteration 2.4: CLI команда для агента

**Scope:**

**`app/cli.py` (расширение)**
```python
@app.command("agent-run")
def agent_run_cmd(
    client: str,
    query: str = typer.Argument(..., help="Запрос в натуральной форме"),
    max_iterations: int = typer.Option(3, "--max-iter"),
):
    """
    Запустить агента для анализа (полный agent loop).
    
    Пример:
        python -m app.cli agent-run partacademy "Разберись, почему упала органика в декабре 2025"
    """
    from app.orchestrator.agent_loop import agent_loop
    
    report = agent_loop(query, client, max_iterations)
    
    rprint(f"[green]✅ Анализ завершён![/green]")
    rprint(f"Отчёт: {report.report_path}")
    rprint(f"Evidence: {report.evidence_path}")
```

**DoD:**
```bash
python -m app.cli agent-run partacademy "Разберись, почему упала органика в декабре 2025"

# Результат: отчёт в reports/partacademy/<run_id>/report.md
```

---

**Phase 2 Summary:**
- ✅ Intake + Planner (Iteration 2.1)
- ✅ Executor + Analyzer (Iteration 2.2)
- ✅ Decision + Report (Iteration 2.3)
- ✅ CLI команда (Iteration 2.4)

**Итого:** ~12-16 часов, 4 iterations

**Критерий успеха Phase 2:**
```bash
python -m app.cli agent-run partacademy "Почему упала органика?"
# → отчёт профессионального уровня за 1 минуту
```

---

## Phase 3: Tier 2 (Goals)

**Цель:** Анализ конверсий

**Оценка:** 8-12 часов

**Scope:**
- C2 (Pages overall)
- C3 (Goals by source)
- C3.1 (Goals by page)

**Аналогично Phase 1**, но с goals метриками Метрики.

---

## Phase 4: Голосовой ввод (опционально)

**Цель:** Говорить вместо писать

**Scope:**
1. Внешний STT (Whisper / системный)
2. Транскрипт → agent_loop (без изменений ядра)

**Оценка:** 4-6 часов

---

## Phase 5: Tier 3 (расширения)

**Scope:**
- C4 (Ecommerce)
- C7 (CRM integration)
- Device/Geo analysis

**По необходимости**, низкий приоритет.

---

## Timeline (общий)

| Phase | Duration | Cumulative | Status |
|-------|----------|------------|--------|
| Phase 1 (MVP Tier 1) | 20-26 часов | 20-26 часов | ⏳ Planned |
| Phase 2 (Orchestrator) | 12-16 часов | 32-42 часа | ⏳ Planned |
| Phase 3 (Tier 2 Goals) | 8-12 часов | 40-54 часа | ⏳ Planned |
| Phase 4 (Voice) | 4-6 часов | 44-60 часов | 🟢 Optional |
| Phase 5 (Tier 3) | TBD | TBD | 🟢 Optional |

**MVP Deliverable (Phase 1 + Phase 2):** ~32-42 часа (4-5 рабочих дней)

---

## Next Steps (немедленные действия)

1. **[Сейчас]** Начать Iteration 1.1 (C2.1)
   - Создать `app/landing_pages.py`
   - Расширить `app/metrika_client.py`
   - Добавить CLI команды

2. **[После 1.1]** OAuth setup для GSC
   - Google Cloud Console
   - Получить credentials
   - Сгенерировать refresh_token

3. **[После Phase 1]** Тестирование на реальном кейсе partacademy
   - Убедиться, что все 6 capabilities работают
   - Вручную написать отчёт (как референс для Phase 2)

4. **[После Phase 2]** Публичный релиз агента

---

## Критерий готовности для production

**MVP (Phase 1 + Phase 2) готов, если:**

1. ✅ Все 6 capabilities Tier 1 работают без ошибок
2. ✅ Agent loop выполняется < 2 минут на реальном кейсе
3. ✅ Отчёт содержит конкретные страницы, запросы, причины, рекомендации
4. ✅ Все выводы подтверждены evidence (workbooks)
5. ✅ Нет секретов в stdout/отчётах
6. ✅ Документация актуальна (README + docs/)

**Тогда:** Можно использовать в production для анализа падений органики.

---

## Вывод

**Roadmap = 4-5 рабочих дней до MVP**

**Приоритет:** Phase 1 (критично) → Phase 2 (orchestrator) → Phase 3 (goals)

**Принцип:** Маленькие вертикальные срезы, тестирование после каждой итерации, никаких "больших взмахов".

**Следующее действие:** Начать Iteration 1.1 (C2.1) прямо сейчас.

