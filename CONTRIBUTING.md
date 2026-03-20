# Contributing

## Базовый принцип

Analyzer Machine держится на простом контракте:

- данные собирает и считает код
- модель только интерпретирует результат
- любые выводы должны быть привязаны к evidence

## Перед началом

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli --help
```

## Структура работы

### Если задача аналитическая

1. Не меняй код без явного запроса.
2. Используй существующие CLI команды.
3. Ссылайся на `data_cache/<client>/` и workbook-файлы.

### Если задача инженерная

1. Меняй только нужный scope.
2. Синхронизируй docs, если меняется capability или workflow.
3. После правок прогоняй:

```bash
python3 -m pytest tests -q
python3 -m app.cli --help
```

## Source of truth для AI-слоя

- `AGENTS.md` — основной onboarding
- `capabilities_registry.yaml` — capability registry
- `docs/AGENT_LOOP.md` — фактический агентный workflow
- `docs/AUDIT_RULES.md` — audit contract

## Что не делать

- не коммитить `.env`, credentials и локальные кэши
- не выдумывать capabilities, если их нет в CLI
- не оставлять docs в состоянии, противоречащем коду

