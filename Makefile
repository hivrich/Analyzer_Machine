.PHONY: reports test

reports:
	CLIENT?=partacademy
	@echo "Generating reports for $(CLIENT)"
	python - <<'PY'
from app.analysis_sources import fetch_sources
from app.analysis_pages import fetch_pages
from app.analysis_goals import fetch_goals
from app.analysis_gsc import fetch_gsc_sites
from app.analysis_ym_webmaster import fetch_webmaster_hosts

print("sources", fetch_sources())
print("pages", fetch_pages())
print("goals", fetch_goals())
print("gsc", fetch_gsc_sites())
print("ym webmaster", fetch_webmaster_hosts())
PY

test:
	pytest
