Cursor tasking guide
====================

Goal: align this repo with the “full” Analyzer Machine you had in Cursor (API clients, analysis scripts, data cache, reports) and make it runnable in this environment with the provided credentials.

What exists now
---------------
- Minimal CLI only: `app/cli.py` (Typer commands `clients`, `show`, `validate`) and config loader `app/config.py`.
- Client configs in `clients/*` plus sample report assets in `docs/reports/partacademy/`.
- No API clients or analysis jobs are present in the repo yet.

Tasks for Cursor to implement
-----------------------------
1) Restore data collectors (paths under `app/`)
- Recreate the missing modules: `analysis_*.py`, `metrika_client.py`, `gsc_client.py`, `ym_webmaster_client.py` (names from the original Cursor workspace). Place them under `app/` to keep imports consistent.
- Each client should read tokens from environment variables that are already available here: `YANDEX_METRIKA_TOKEN`, `YM_WEBMASTER_TOKEN`, `GSC_CLIENT_ID`, `GSC_REFRESH_TOKEN`.
- Add lightweight wrappers that expose simple functions for fetching counters/metrics so the CLI can consume them later.

2) Handle proxy restrictions
- Current environment forces traffic through `http://proxy:8080` and blocks `api-metrika.yandex.net` with `403 CONNECT`.
- Add proxy configuration hooks (e.g., respecting `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`) and allow overriding them per request so domains like `api-metrika.yandex.net`/`api-metrika.yandex.ru` can be bypassed if permitted.
- Provide a retryable HTTP helper (requests.Session with timeouts) to centralize proxy/no-proxy handling for all API clients.

3) Ship a runnable workflow
- Add a `make reports` (or similar) target to orchestrate loading configs, fetching data via the clients, and generating HTML/Markdown reports in `docs/reports/<client>/`.
- Include a `.env.example` listing required variables (tokens above + optional proxy tuning such as `NO_PROXY`). Do **not** commit real secrets.
- Extend README with usage examples for the new commands and the expected report outputs.

4) Testing and CI hooks
- Add smoke tests for the HTTP helper and config parsing (Pytest preferred). Make sure they can run offline by mocking HTTP calls.
- If CI is added, include a job that runs `pytest` and `python -m app.cli validate <client>` for all clients.

Context for Cursor
- Known network symptom here: `Tunnel connection failed: 403 Forbidden` when calling Yandex Metrika via the forced proxy. The code should allow opting out of the proxy for specific hosts when possible.
- Sample client to validate against: `clients/partacademy/config.yaml`. The existing report scaffold lives in `docs/reports/partacademy/`.
