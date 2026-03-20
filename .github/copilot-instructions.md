# Analyzer Machine — Copilot Instructions

Root onboarding for this repository lives in `AGENTS.md`.

Follow these rules:

- Do not invent metrics or API responses.
- Do not expose secrets from `.env` or client configs.
- Treat `capabilities_registry.yaml` as the capability source of truth.
- Prefer existing CLI commands over ad hoc scripts.
- For analysis tasks, rely on evidence from `data_cache/<client>/` and CLI output.
- For code changes, sync docs when capability behavior changes.
