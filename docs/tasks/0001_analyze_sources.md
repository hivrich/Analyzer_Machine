TASK: 0001 — analyze-sources: сравнение источников трафика между двумя периодами (детерминированно, без LLM)

GOAL (что получить)
Добавить в CLI команду, которая:
— берёт данные по источникам трафика из Метрики за 2 периода,
— считает дельты/проценты/вклады программно,
— выводит понятную сводку в консоль,
— сохраняет “workbook” (агрегаты) в data_cache для последующей интерпретации LLM (но в этой задаче LLM не используем).

COMMAND (интерфейс)
python -m app.cli analyze-sources <client> <p1_start> <p1_end> <p2_start> <p2_end> [--limit N] [--refresh]

Где:
— <client> = папка в clients/<client>/config.yaml
— p1/p2 = ISO даты YYYY-MM-DD
— --limit = ограничение на число строк (по умолчанию 50)
— --refresh = принудительно перезапросить Метрику даже если кэш уже есть

CONSTRAINTS (жёсткие правила)

Все вычисления (дельты, % изменения, вклад) — только кодом.

Никаких “догадок” по цифрам: если данных нет — явно показать “нет данных”/0 и объяснить в консоли.

Никаких секретов в выводе (токен/заголовки/URL с токеном).

Повторные запросы минимизировать: по умолчанию работать из кэша, API дергать только если кэша нет или --refresh.

В этой задаче LLM не вызываем вообще (0 токенов).

DATA SOURCES (что читаем)
— Используем уже существующую команду/логику metrika-sources (raw + normalized в data_cache/<client>/).
— Если для периода нет кэша: автоматически вызываем тот же API запрос, что и metrika-sources, сохраняем raw/norm и продолжаем анализ.

ANALYSIS (что считаем)
Базовые поля на уровне “source” (строка = один источник):
— visits_p1, visits_p2
— delta_abs = visits_p2 - visits_p1
— delta_pct = (visits_p2 - visits_p1) / max(visits_p1, 1) * 100
— contribution_pct = delta_abs / total_delta_abs_sum * 100
Где total_delta_abs_sum = сумма delta_abs по всем источникам (может быть отрицательной).
Правило: если total_delta_abs_sum == 0, contribution_pct = 0 для всех.

Нормализация источников
— Источник считается ключом строкового поля source из normalized данных.
— Если источник есть в одном периоде и отсутствует в другом — считать отсутствующее значение = 0.

OUTPUT (что должно появиться)

Rich-таблица в консоль:
Колонки минимум:
source | visits_p1 | visits_p2 | delta_abs | delta_pct | contribution_pct
Сортировка:
— по убыванию abs(delta_abs), затем по source.
Округление:
— delta_pct: 1 знак
— contribution_pct: 1 знак

Workbook JSON в data_cache/<client>/:
analysis_sources_<p1_start><p1_end>__<p2_start><p2_end>.json
Содержимое workbook (минимум):
— meta: client, counter_id, dates, generated_at, limit, refresh_used
— totals: total_visits_p1, total_visits_p2, total_delta_abs, total_delta_pct
— rows: массив top-N строк (после сортировки), с полями как в таблице

ERROR HANDLING (как должно вести себя)
— Если токен не задан: понятная ошибка “YANDEX_METRIKA_TOKEN не задан”, exit code 1.
— Если Метрика вернула ошибку: вывести статус/сообщение без секретов, exit code 1.
— Если даты некорректны/перепутаны: понятная ошибка, exit code 1.

DOD (Definition of Done)

Команда работает на partacademy при наличии токена и counter_id:
python -m app.cli analyze-sources partacademy 2023-12-01 2023-12-31 2024-12-01 2024-12-31

Если кэша нет — он создаётся автоматически (raw + norm для обоих периодов).

Создаётся workbook-файл в data_cache/partacademy/ с ожидаемым именованием.

Итоги сходятся:
— total_visits_p1 = сумма visits_p1 по всем строкам (внутренне, до top-N)
— total_visits_p2 аналогично
— total_delta_abs = total_visits_p2 - total_visits_p1

Никакие секреты в stdout не попадают.

NOTES (на будущее, не делать в этой задаче)
— Подключение LLM: отдельная задача 0002 (LLM-summary по workbook).
— Расширение на цели/конверсии/ecommerce: отдельные задачи 0003+.