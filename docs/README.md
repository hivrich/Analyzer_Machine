# Docs Index

Ниже список документов, которые действительно стоит читать в первую очередь.

## Актуальные документы

- `../AGENTS.md` — главный onboarding для локального агента
- `../README.md` — обзор проекта и быстрый старт
- `AGENT_LOOP.md` — реализованный workflow анализа
- `INVESTIGATE.md` — главный путь: расследование по обычному запросу
- `AUDIT_RULES.md` — текущие правила аудита
- `api_catalog.md` — каталог API и источников
- `spec.md` — спецификация проекта
- `capability_matrix.md` — матрица capabilities
- `samples/README.md` — примеры workbook и normalized данных

## Полезные справочники

- `GSC_OAUTH_SETUP.md` — настройка GSC
- `analysis_rules.md` — правила аналитической интерпретации
- `REPORT_STANDARD.md` — структура отчетов
- `data_sources/` — справочники источников данных
- `hypotheses/` — библиотека гипотез и маппинг к данным

## Исторические или архитектурные документы

Эти файлы полезны как контекст, но не должны считаться source of truth для текущего workflow без сверки с кодом:

- `HOW_TO_WORK.md`
- `RESEARCH_SUMMARY.md`
- `implementation_roadmap.md`
- `mvp_capabilities_roadmap.md`
- `modules_architecture.md`
- `orchestrator_architecture.md`
- `agent_example_run.md`
- `AUDIT_SYSTEM_README.md`
- `AUDIT_CHECKLISTS.md`

Если документ конфликтует с `AGENTS.md`, `app/cli.py` или `capabilities_registry.yaml`, приоритет у кода и актуальных root docs.
