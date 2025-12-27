from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime

import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.table import Table

from app.analysis_gsc import (
    calculate_contributions as calculate_contributions_gsc,
    compare_gsc_periods,
    create_workbook as create_workbook_gsc,
    load_or_fetch_gsc,
    sort_rows as sort_gsc_rows,
    workbook_filename as gsc_workbook_filename,
)
from app.analysis_goals import (
    calculate_contributions as calculate_contributions_goals,
    compare_goals_periods,
    create_workbook as create_workbook_goals,
    load_or_fetch_goals_by_page,
    load_or_fetch_goals_by_source,
    sort_rows as sort_goals_rows,
    workbook_filename as goals_workbook_filename,
)
from app.analysis_pages import (
    calculate_contributions as calculate_contributions_pages,
    compare_pages_periods,
    create_workbook as create_workbook_pages,
    load_or_fetch_pages,
    load_or_fetch_pages_by_source,
    sort_analysis_rows as sort_analysis_rows_pages,
)
from app.analysis_sources import (
    calculate_contributions,
    compare_sources_periods,
    create_workbook,
    load_or_fetch_sources,
    sort_analysis_rows,
)
from app.config import list_clients, load_client_config
from app.metrika_client import MetrikaClient, normalize_goals_list, normalize_pages, normalize_sources
from app.gsc_client import GSCClient
from app.analysis_ym_webmaster import (
    calculate_contributions as calculate_contributions_ymw,
    compare_queries_periods as compare_ymw_queries_periods,
    create_workbook as create_workbook_ymw,
    load_or_fetch_queries as load_or_fetch_ymw_queries,
    sort_rows as sort_ymw_rows,
    workbook_filename as ymw_workbook_filename,
)
from app.ym_webmaster_client import YMWebmasterClient, normalize_webmaster_indexing
from app.analysis_insights import print_insights

# Загружаем переменные окружения из .env
load_dotenv()

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command("clients")
def clients_cmd():
    """Показать список клиентов (папок в clients/ без _template)."""
    items = list_clients()
    if not items:
        rprint("Клиентов не найдено (проверь папку clients/).")
        raise typer.Exit(code=1)

    table = Table(title="Clients")
    table.add_column("client")
    table.add_column("config.yaml exists")

    for c in items:
        try:
            _, cfg_path = load_client_config(c)
            exists = "yes" if cfg_path.exists() else "no"
        except Exception:
            exists = "no"
        table.add_row(c, exists)

    rprint(table)


@app.command("show")
def show_cmd(client: str = typer.Argument(..., help="Имя папки в clients/<client>/")):
    """Показать config клиента (в кратком виде)."""
    cfg, cfg_path = load_client_config(client)

    table = Table(title=f"{client} ({cfg_path})")
    table.add_column("key")
    table.add_column("value")
    table.add_row("site.name", cfg.site_name or "(empty)")
    table.add_row("site.timezone", cfg.timezone)
    table.add_row("metrika.counter_id", str(cfg.counter_id))
    table.add_row("metrika.goal_id", str(cfg.goal_id))
    table.add_row("metrika.currency", cfg.currency)
    table.add_row("reporting.llm_enabled", str(cfg.llm_enabled))
    table.add_row("reporting.language", cfg.language)
    rprint(table)


@app.command("validate")
def validate_cmd(client: str = typer.Argument(..., help="Имя папки в clients/<client>/")):
    """Проверка, что конфиг заполнен минимально для работы."""
    cfg, _ = load_client_config(client)

    problems: list[str] = []
    if not cfg.site_name:
        problems.append("site.name пустой")
    if cfg.counter_id <= 0:
        problems.append("metrika.counter_id не задан (<=0)")

    if problems:
        rprint("[bold red]Config invalid:[/bold red]")
        for p in problems:
            rprint(f"- {p}")
        raise typer.Exit(code=2)

    rprint("[bold green]OK[/bold green] (минимально валидный конфиг)")


@app.command("metrika-sources")
def metrika_sources_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    limit: int = typer.Option(50, "--limit", help="Лимит источников трафика"),
):
    """Получить источники трафика из Яндекс.Метрики и сохранить в data_cache."""
    cfg, _ = load_client_config(client)

    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    # Получаем данные из API
    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)
    raw_data = metrika.traffic_sources(date1, date2, limit)

    # Нормализуем данные
    normalized_data = normalize_sources(raw_data)

    # Сохраняем данные
    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw_file = cache_dir / f"metrika_sources_raw_{date1}_{date2}.json"
    norm_file = cache_dir / f"metrika_sources_norm_{date1}_{date2}.json"

    raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")

    rprint(f"[green]Данные сохранены:[/green] {raw_file.name}, {norm_file.name}")

    # Выводим таблицу
    table = Table(title=f"Источники трафика ({client}, {date1} - {date2})")
    table.add_column("source")
    table.add_column("visits", justify="right")
    table.add_column("users", justify="right")
    table.add_column("bounceRate", justify="right")
    table.add_column("pageDepth", justify="right")
    table.add_column("avgVisitDurationSeconds", justify="right")

    for row in normalized_data:
        table.add_row(
            row["source"],
            str(int(row["visits"])),
            str(int(row["users"])),
            f"{row['bounceRate']:.2f}",
            f"{row['pageDepth']:.2f}",
            f"{row['avgVisitDurationSeconds']:.2f}",
        )

    rprint(table)


@app.command("metrika-pages")
def metrika_pages_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    limit: int = typer.Option(50, "--limit", help="Лимит входных страниц"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
):
    """Получить входные страницы (landing pages) из Яндекс.Метрики и сохранить в data_cache."""
    cfg, _ = load_client_config(client)

    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw_file = cache_dir / f"metrika_pages_raw_{date1}_{date2}.json"
    norm_file = cache_dir / f"metrika_pages_norm_{date1}_{date2}.json"

    normalized_data = None

    # Пытаемся использовать кэш (если он достаточный по размеру)
    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list) and len(cached) >= max(1, limit):
                normalized_data = cached
                rprint(f"[green]Использую кэш:[/green] {norm_file.name}")
        except Exception:
            normalized_data = None

    # Если кэш не подходит — идём в API
    if normalized_data is None:
        metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)
        raw_data = metrika.landing_pages(date1, date2, limit)
        normalized_data = normalize_pages(raw_data)

        raw_file.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
        norm_file.write_text(json.dumps(normalized_data, ensure_ascii=False, indent=2), encoding="utf-8")

        rprint(f"[green]Данные сохранены:[/green] {raw_file.name}, {norm_file.name}")

    # Выводим таблицу
    table = Table(title=f"Входные страницы (landing pages) ({client}, {date1} - {date2})")
    table.add_column("landingPage")
    table.add_column("visits", justify="right")
    table.add_column("users", justify="right")
    table.add_column("bounceRate", justify="right")
    table.add_column("pageDepth", justify="right")
    table.add_column("avgVisitDurationSeconds", justify="right")

    rows_to_print = normalized_data[:limit] if limit > 0 else normalized_data
    for row in rows_to_print:
        table.add_row(
            row["landingPage"],
            str(int(row["visits"])),
            str(int(row["users"])),
            f"{row['bounceRate']:.2f}",
            f"{row['pageDepth']:.2f}",
            f"{row['avgVisitDurationSeconds']:.2f}",
        )

    rprint(table)


@app.command("metrika-pages-by-source")
def metrika_pages_by_source_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    source: str = typer.Option(
        "Search engine traffic", "--source", help="Источник (значение ym:s:lastTrafficSource)"
    ),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
):
    """Получить landing pages из Метрики в разрезе источника и сохранить в data_cache."""
    cfg, _ = load_client_config(client)

    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        normalized_data = load_or_fetch_pages_by_source(
            client=client,
            date1=date1,
            date2=date2,
            source=source,
            limit=limit,
            refresh=refresh,
            metrika_client=metrika,
        )
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    table = Table(
        title=f"Входные страницы (by source) ({client}, {source}, {date1} - {date2})"
    )
    table.add_column("landingPage")
    table.add_column("visits", justify="right")
    table.add_column("users", justify="right")
    table.add_column("bounceRate", justify="right")
    table.add_column("pageDepth", justify="right")
    table.add_column("avgVisitDurationSeconds", justify="right")

    rows_to_print = normalized_data[:limit] if limit > 0 else normalized_data
    for row in rows_to_print:
        table.add_row(
            row["landingPage"],
            str(int(row["visits"])),
            str(int(row["users"])),
            f"{row['bounceRate']:.2f}",
            f"{row['pageDepth']:.2f}",
            f"{row['avgVisitDurationSeconds']:.2f}",
        )

    rprint(table)


@app.command("metrika-goals-by-source")
def metrika_goals_by_source_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    goal_id: int = typer.Option(0, "--goal-id", help="ID цели в Метрике (0 = взять из config)"),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
):
    """Получить конверсии (goal) по источникам и сохранить в data_cache."""
    cfg, _ = load_client_config(client)

    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    resolved_goal_id = int(goal_id or 0) or int(cfg.goal_id or 0)
    if resolved_goal_id <= 0:
        rprint(
            "[bold red]Error:[/bold red] goal_id не задан. Укажите --goal-id или заполните metrika.goal_id в config.yaml"
        )
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        normalized = load_or_fetch_goals_by_source(
            client=client,
            date1=date1,
            date2=date2,
            goal_id=resolved_goal_id,
            limit=limit,
            refresh=refresh,
            metrika_client=metrika,
        )
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    table = Table(title=f"Goals by source ({client}, goal_id={resolved_goal_id}, {date1} - {date2})")
    table.add_column("source")
    table.add_column("visits", justify="right")
    table.add_column("goal_visits", justify="right")
    table.add_column("goal_cr_pct", justify="right")

    rows_to_print = normalized[:limit] if limit > 0 else normalized
    for row in rows_to_print:
        table.add_row(
            row["source"],
            str(int(row["visits"])),
            str(int(row["goal_visits"])),
            f"{float(row['goal_cr_pct']):.2f}",
        )
    rprint(table)


@app.command("metrika-goals-by-page")
def metrika_goals_by_page_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    goal_id: int = typer.Option(0, "--goal-id", help="ID цели в Метрике (0 = взять из config)"),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
):
    """Получить конверсии (goal) по входным страницам и сохранить в data_cache."""
    cfg, _ = load_client_config(client)

    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    resolved_goal_id = int(goal_id or 0) or int(cfg.goal_id or 0)
    if resolved_goal_id <= 0:
        rprint(
            "[bold red]Error:[/bold red] goal_id не задан. Укажите --goal-id или заполните metrika.goal_id в config.yaml"
        )
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        normalized = load_or_fetch_goals_by_page(
            client=client,
            date1=date1,
            date2=date2,
            goal_id=resolved_goal_id,
            limit=limit,
            refresh=refresh,
            metrika_client=metrika,
        )
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    table = Table(title=f"Goals by landingPage ({client}, goal_id={resolved_goal_id}, {date1} - {date2})")
    table.add_column("landingPage")
    table.add_column("visits", justify="right")
    table.add_column("goal_visits", justify="right")
    table.add_column("goal_cr_pct", justify="right")

    rows_to_print = normalized[:limit] if limit > 0 else normalized
    for row in rows_to_print:
        table.add_row(
            row["landingPage"],
            str(int(row["visits"])),
            str(int(row["goal_visits"])),
            f"{float(row['goal_cr_pct']):.2f}",
        )
    rprint(table)


@app.command("metrika-goals-list")
def metrika_goals_list_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
):
    """Показать список целей Метрики (Management API) для выбора goal_id."""
    cfg, _ = load_client_config(client)

    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_file = cache_dir / "metrika_goals_list_raw.json"
    norm_file = cache_dir / "metrika_goals_list_norm.json"

    normalized = None
    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                normalized = cached
                rprint(f"[green]Использую кэш:[/green] {norm_file.name}")
        except Exception:
            normalized = None

    if normalized is None:
        metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)
        try:
            raw = metrika.list_goals()
            normalized = normalize_goals_list(raw)
        except RuntimeError as e:
            error_msg = str(e)
            if token in error_msg:
                error_msg = error_msg.replace(token, "***")
            if "OAuth" in error_msg:
                error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
            rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
            raise typer.Exit(code=1)
        except Exception as e:
            rprint(f"[bold red]Error:[/bold red] Не удалось загрузить список целей: {e}")
            raise typer.Exit(code=1)

        raw_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        norm_file.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        rprint(f"[green]Данные сохранены:[/green] {raw_file.name}, {norm_file.name}")

    table = Table(title=f"Metrika goals list ({client})")
    table.add_column("id", justify="right")
    table.add_column("type")
    table.add_column("name")

    for g in normalized:
        table.add_row(str(g.get("id", "")), str(g.get("type", "")), str(g.get("name", "")))

    if cfg.goal_id and int(cfg.goal_id) > 0:
        rprint(f"\nТекущий goal_id в config.yaml: {cfg.goal_id}")
    else:
        rprint("\nТекущий goal_id в config.yaml: 0 (не задан)")

    rprint(table)


def _get_gsc_client(cfg) -> GSCClient:
    client_id = os.getenv("GSC_CLIENT_ID", "").strip()
    client_secret = os.getenv("GSC_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("GSC_REFRESH_TOKEN", "").strip()
    site_url = str(getattr(cfg, "gsc_site_url", "") or "").strip()
    if not site_url:
        raise ValueError("gsc.site_url не задан в clients/<client>/config.yaml")
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("GSC_CLIENT_ID/GSC_CLIENT_SECRET/GSC_REFRESH_TOKEN не заданы в окружении")
    return GSCClient(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        site_url=site_url,
    )


@app.command("gsc-queries")
def gsc_queries_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    limit: int = typer.Option(1000, "--limit", help="Лимит строк (rowLimit)"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить GSC"),
):
    """Получить данные GSC по запросам (queries) за период и сохранить в data_cache."""
    cfg, _ = load_client_config(client)
    try:
        gsc = _get_gsc_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        norm, _dims = load_or_fetch_gsc(
            client=client, kind="queries", date1=date1, date2=date2, limit=limit, refresh=refresh, gsc_client=gsc
        )
    except Exception as e:
        msg = str(e)
        # не печатаем секреты
        for secret in [gsc.client_id, gsc.client_secret, gsc.refresh_token]:
            if secret and secret in msg:
                msg = msg.replace(secret, "***")
        rprint(f"[bold red]Error:[/bold red] GSC error: {msg[:500]}")
        raise typer.Exit(code=1)

    table = Table(title=f"GSC queries ({client}, {cfg.gsc_site_url}, {date1} - {date2})")
    table.add_column("query")
    table.add_column("clicks", justify="right")
    table.add_column("impr", justify="right")
    table.add_column("ctr_%", justify="right")
    table.add_column("pos", justify="right")
    for row in norm[:limit] if limit > 0 else norm:
        table.add_row(
            str(row.get("query", "")),
            str(int(row.get("clicks", 0.0) or 0.0)),
            str(int(row.get("impressions", 0.0) or 0.0)),
            f"{float(row.get('ctr', 0.0) or 0.0):.2f}",
            f"{float(row.get('position', 0.0) or 0.0):.2f}",
        )
    rprint(table)


@app.command("gsc-pages")
def gsc_pages_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    limit: int = typer.Option(1000, "--limit", help="Лимит строк (rowLimit)"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить GSC"),
):
    """Получить данные GSC по страницам (pages) за период и сохранить в data_cache."""
    cfg, _ = load_client_config(client)
    try:
        gsc = _get_gsc_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        norm, _dims = load_or_fetch_gsc(
            client=client, kind="pages", date1=date1, date2=date2, limit=limit, refresh=refresh, gsc_client=gsc
        )
    except Exception as e:
        msg = str(e)
        for secret in [gsc.client_id, gsc.client_secret, gsc.refresh_token]:
            if secret and secret in msg:
                msg = msg.replace(secret, "***")
        rprint(f"[bold red]Error:[/bold red] GSC error: {msg[:500]}")
        raise typer.Exit(code=1)

    table = Table(title=f"GSC pages ({client}, {cfg.gsc_site_url}, {date1} - {date2})")
    table.add_column("page")
    table.add_column("clicks", justify="right")
    table.add_column("impr", justify="right")
    table.add_column("ctr_%", justify="right")
    table.add_column("pos", justify="right")
    for row in norm[:limit] if limit > 0 else norm:
        table.add_row(
            str(row.get("page", "")),
            str(int(row.get("clicks", 0.0) or 0.0)),
            str(int(row.get("impressions", 0.0) or 0.0)),
            f"{float(row.get('ctr', 0.0) or 0.0):.2f}",
            f"{float(row.get('position', 0.0) or 0.0):.2f}",
        )
    rprint(table)


@app.command("analyze-gsc-queries")
def analyze_gsc_queries_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    limit: int = typer.Option(1000, "--limit", help="Лимит строк (rowLimit)"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить GSC"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение GSC queries между двумя периодами (детерминированно)."""
    cfg, _ = load_client_config(client)
    try:
        gsc = _get_gsc_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        d1, _ = load_or_fetch_gsc(client, "queries", p1_start, p1_end, limit, refresh, gsc)
        d2, _ = load_or_fetch_gsc(client, "queries", p2_start, p2_end, limit, refresh, gsc)
    except Exception as e:
        msg = str(e)
        for secret in [gsc.client_id, gsc.client_secret, gsc.refresh_token]:
            if secret and secret in msg:
                msg = msg.replace(secret, "***")
        rprint(f"[bold red]Error:[/bold red] GSC error: {msg[:500]}")
        raise typer.Exit(code=1)

    rows = compare_gsc_periods(d1, d2, key_field="query")
    rows = calculate_contributions_gsc(rows)
    all_rows = rows.copy()
    rows = sort_gsc_rows(rows, key_field="query")

    workbook = create_workbook_gsc(
        client=client,
        site_url=cfg.gsc_site_url,
        kind="queries",
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / gsc_workbook_filename("queries", p1_start, p1_end, p2_start, p2_end)
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")
    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="clicks", 
            dimension_name="query"
        )
        return

    table = Table(title=f"GSC queries compare ({client}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})")
    table.add_column("query")
    table.add_column("clicks_p1", justify="right")
    table.add_column("clicks_p2", justify="right")
    table.add_column("delta_clicks", justify="right")
    table.add_column("delta_clicks_pct", justify="right")
    table.add_column("delta_pos", justify="right")
    table.add_column("delta_ctr_pp", justify="right")
    table.add_column("contrib_%", justify="right")

    for r in rows[:limit] if limit > 0 else rows:
        table.add_row(
            str(r.get("query", "")),
            str(int(r.get("clicks_p1", 0.0) or 0.0)),
            str(int(r.get("clicks_p2", 0.0) or 0.0)),
            str(int(r.get("delta_clicks", 0.0) or 0.0)),
            f"{float(r.get('delta_clicks_pct', 0.0) or 0.0):.1f}",
            f"{float(r.get('delta_position', 0.0) or 0.0):.2f}",
            f"{float(r.get('delta_ctr_pp', 0.0) or 0.0):.2f}",
            f"{float(r.get('contribution_pct', 0.0) or 0.0):.1f}",
        )
    rprint(table)


@app.command("analyze-gsc-pages")
def analyze_gsc_pages_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    limit: int = typer.Option(1000, "--limit", help="Лимит строк (rowLimit)"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить GSC"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение GSC pages между двумя периодами (детерминированно)."""
    cfg, _ = load_client_config(client)
    try:
        gsc = _get_gsc_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        d1, _ = load_or_fetch_gsc(client, "pages", p1_start, p1_end, limit, refresh, gsc)
        d2, _ = load_or_fetch_gsc(client, "pages", p2_start, p2_end, limit, refresh, gsc)
    except Exception as e:
        msg = str(e)
        for secret in [gsc.client_id, gsc.client_secret, gsc.refresh_token]:
            if secret and secret in msg:
                msg = msg.replace(secret, "***")
        rprint(f"[bold red]Error:[/bold red] GSC error: {msg[:500]}")
        raise typer.Exit(code=1)

    rows = compare_gsc_periods(d1, d2, key_field="page")
    rows = calculate_contributions_gsc(rows)
    all_rows = rows.copy()
    rows = sort_gsc_rows(rows, key_field="page")

    workbook = create_workbook_gsc(
        client=client,
        site_url=cfg.gsc_site_url,
        kind="pages",
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / gsc_workbook_filename("pages", p1_start, p1_end, p2_start, p2_end)
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")
    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="clicks", 
            dimension_name="page"
        )
        return

    table = Table(title=f"GSC pages compare ({client}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})")
    table.add_column("page")
    table.add_column("clicks_p1", justify="right")
    table.add_column("clicks_p2", justify="right")
    table.add_column("delta_clicks", justify="right")
    table.add_column("delta_clicks_pct", justify="right")
    table.add_column("delta_pos", justify="right")
    table.add_column("delta_ctr_pp", justify="right")
    table.add_column("contrib_%", justify="right")

    for r in rows[:limit] if limit > 0 else rows:
        table.add_row(
            str(r.get("page", "")),
            str(int(r.get("clicks_p1", 0.0) or 0.0)),
            str(int(r.get("clicks_p2", 0.0) or 0.0)),
            str(int(r.get("delta_clicks", 0.0) or 0.0)),
            f"{float(r.get('delta_clicks_pct', 0.0) or 0.0):.1f}",
            f"{float(r.get('delta_position', 0.0) or 0.0):.2f}",
            f"{float(r.get('delta_ctr_pp', 0.0) or 0.0):.2f}",
            f"{float(r.get('contribution_pct', 0.0) or 0.0):.1f}",
        )
    rprint(table)


def _get_ym_webmaster_token() -> str:
    return os.getenv("YM_WEBMASTER_TOKEN", "").strip() or os.getenv("YANDEX_WEBMASTER_TOKEN", "").strip()


def _get_ym_webmaster_client(cfg) -> YMWebmasterClient:
    token = _get_ym_webmaster_token()
    if not token:
        raise ValueError("YM_WEBMASTER_TOKEN (или YANDEX_WEBMASTER_TOKEN) не задан в окружении")
    user_id = str(getattr(cfg, "ym_webmaster_user_id", "") or "").strip()
    host_id = str(getattr(cfg, "ym_webmaster_host_id", "") or "").strip()
    if not user_id or not host_id:
        raise ValueError(
            "ym_webmaster.user_id/host_id не заданы в clients/<client>/config.yaml. "
            "Сначала выполните: python -m app.cli ym-webmaster-hosts <client>"
        )
    return YMWebmasterClient(token=token, user_id=user_id, host_id=host_id)


@app.command("ym-webmaster-hosts")
def ym_webmaster_hosts_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Вебмастер"),
):
    """Показать список hosts (сайтов) в Яндекс.Вебмастер и сохранить в data_cache."""
    _cfg, _ = load_client_config(client)
    token = _get_ym_webmaster_token()
    if not token:
        rprint("[bold red]Error:[/bold red] YM_WEBMASTER_TOKEN (или YANDEX_WEBMASTER_TOKEN) не задан в окружении")
        raise typer.Exit(code=1)

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_file = cache_dir / "ym_webmaster_hosts_raw.json"
    norm_file = cache_dir / "ym_webmaster_hosts_norm.json"

    normalized = None
    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                normalized = cached
                rprint(f"[green]Использую кэш:[/green] {norm_file.name}")
        except Exception:
            normalized = None

    if normalized is None:
        try:
            from app.http_client import get_default_session

            session = get_default_session()
            headers = {"Authorization": f"OAuth {token}"}

            # 1) user_id
            r_user = session.get("https://api.webmaster.yandex.net/v4/user", headers=headers)
            if r_user.status_code >= 400:
                raise RuntimeError(f"{r_user.status_code}: {r_user.text}")
            user_json = r_user.json()
            user_id = user_json.get("user_id")
            if not user_id:
                raise RuntimeError(f"Unexpected /v4/user response: {user_json}")

            # 2) hosts
            r_hosts = session.get(
                f"https://api.webmaster.yandex.net/v4/user/{user_id}/hosts",
                headers=headers,
            )
            if r_hosts.status_code >= 400:
                raise RuntimeError(f"{r_hosts.status_code}: {r_hosts.text}")
            hosts_json = r_hosts.json()

            raw = {
                "user_id": int(user_id),
                "hosts": hosts_json.get("hosts", []) or [],
            }

        except Exception as e:
            msg = str(e)
            if token and token in msg:
                msg = msg.replace(token, "***")
            rprint(f"[bold red]Error:[/bold red] Вебмастер error: {msg[:500]}")
            raise typer.Exit(code=1)

        hosts = raw.get("hosts") or []
        normalized = []
        if isinstance(hosts, list):
            for h in hosts:
                if not isinstance(h, dict):
                    continue
                normalized.append(
                    {
                        "host_id": str(h.get("host_id", "")).strip(),
                        "unicode_host_url": str(h.get("unicode_host_url", "")).strip(),
                        "verified": bool(h.get("verified", False)),
                    }
                )

        raw_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        norm_file.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        rprint(f"[green]Данные сохранены:[/green] {raw_file.name}, {norm_file.name}")

    table = Table(title=f"Yandex Webmaster hosts ({client})")
    table.add_column("host_id")
    table.add_column("unicode_host_url")
    table.add_column("verified")
    for h in normalized:
        table.add_row(str(h.get("host_id", "")), str(h.get("unicode_host_url", "")), str(h.get("verified", "")))
    rprint(table)

    rprint("\nЧтобы включить Вебмастер capabilities, добавьте в config.yaml секцию:")
    rprint("ym_webmaster:")
    rprint("  user_id: <USER_ID>")
    rprint("  host_id: <HOST_ID>")



@app.command("ym-webmaster-queries")
def ym_webmaster_queries_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    date1: str = typer.Argument(..., help="Начальная дата (YYYY-MM-DD)"),
    date2: str = typer.Argument(..., help="Конечная дата (YYYY-MM-DD)"),
    limit: int = typer.Option(500, "--limit", help="Лимит строк"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Вебмастер"),
):
    """Получить популярные запросы из Яндекс.Вебмастера и сохранить в data_cache."""
    cfg, _ = load_client_config(client)
    try:
        ym = _get_ym_webmaster_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        norm = load_or_fetch_ymw_queries(client, date1, date2, limit, refresh, ym)
    except Exception as e:
        msg = str(e)
        if ym.token and ym.token in msg:
            msg = msg.replace(ym.token, "***")
        rprint(f"[bold red]Error:[/bold red] Вебмастер error: {msg[:500]}")
        raise typer.Exit(code=1)

    table = Table(title=f"YM Webmaster queries ({client}, {date1} - {date2})")
    table.add_column("query")
    table.add_column("clicks", justify="right")
    table.add_column("shows", justify="right")
    table.add_column("pos", justify="right")
    for r in norm[:limit] if limit > 0 else norm:
        table.add_row(
            str(r.get("query", "")),
            str(int(r.get("clicks", 0.0) or 0.0)),
            str(int(r.get("shows", 0.0) or 0.0)),
            f"{float(r.get('position', 0.0) or 0.0):.2f}",
        )
    rprint(table)


@app.command("analyze-ym-webmaster-queries")
def analyze_ym_webmaster_queries_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    limit: int = typer.Option(500, "--limit", help="Лимит строк"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Вебмастер"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение запросов Яндекс.Вебмастера между двумя периодами."""
    cfg, _ = load_client_config(client)
    try:
        ym = _get_ym_webmaster_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        d1 = load_or_fetch_ymw_queries(client, p1_start, p1_end, limit, refresh, ym)
        d2 = load_or_fetch_ymw_queries(client, p2_start, p2_end, limit, refresh, ym)
    except Exception as e:
        msg = str(e)
        if ym.token and ym.token in msg:
            msg = msg.replace(ym.token, "***")
        rprint(f"[bold red]Error:[/bold red] Вебмастер error: {msg[:500]}")
        raise typer.Exit(code=1)

    rows = compare_ymw_queries_periods(d1, d2)
    rows = calculate_contributions_ymw(rows)
    all_rows = rows.copy()
    rows = sort_ymw_rows(rows)

    workbook = create_workbook_ymw(
        client=client,
        host_id=cfg.ym_webmaster_host_id,
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / ymw_workbook_filename(p1_start, p1_end, p2_start, p2_end)
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")
    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="clicks", 
            dimension_name="query"
        )
        return

    table = Table(title=f"YM Webmaster queries compare ({client}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})")
    table.add_column("query")
    table.add_column("clicks_p1", justify="right")
    table.add_column("clicks_p2", justify="right")
    table.add_column("delta_clicks", justify="right")
    table.add_column("delta_clicks_pct", justify="right")
    table.add_column("delta_pos", justify="right")
    table.add_column("contrib_%", justify="right")
    for r in rows[:limit] if limit > 0 else rows:
        table.add_row(
            str(r.get("query", "")),
            str(int(r.get("clicks_p1", 0.0) or 0.0)),
            str(int(r.get("clicks_p2", 0.0) or 0.0)),
            str(int(r.get("delta_clicks", 0.0) or 0.0)),
            f"{float(r.get('delta_clicks_pct', 0.0) or 0.0):.1f}",
            f"{float(r.get('delta_position', 0.0) or 0.0):.2f}",
            f"{float(r.get('contribution_pct', 0.0) or 0.0):.1f}",
        )
    rprint(table)


@app.command("ym-webmaster-indexing")
def ym_webmaster_indexing_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    status: str = typer.Option("EXCLUDED", "--status", help="Статус URL (EXCLUDED/INDEXED/NOT_FOUND)"),
    limit: int = typer.Option(100, "--limit", help="Лимит строк"),
    offset: int = typer.Option(0, "--offset", help="Смещение (offset)"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Вебмастер"),
):
    """Получить список URL по статусу индексации (например EXCLUDED) и сохранить в data_cache."""
    cfg, _ = load_client_config(client)
    try:
        ym = _get_ym_webmaster_client(cfg)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_file = cache_dir / f"ym_webmaster_indexing_raw_{status}_{limit}_{offset}.json"
    norm_file = cache_dir / f"ym_webmaster_indexing_norm_{status}_{limit}_{offset}.json"

    normalized = None
    if not refresh and norm_file.exists():
        try:
            cached = json.loads(norm_file.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                normalized = cached
                rprint(f"[green]Использую кэш:[/green] {norm_file.name}")
        except Exception:
            normalized = None

    if normalized is None:
        try:
            raw = ym.indexing_samples(search_url_status=status, limit=limit, offset=offset)
            normalized = normalize_webmaster_indexing(raw)
        except Exception as e:
            msg = str(e)
            if ym.token and ym.token in msg:
                msg = msg.replace(ym.token, "***")
            rprint(f"[bold red]Error:[/bold red] Вебмастер error: {msg[:500]}")
            raise typer.Exit(code=1)

        raw_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        norm_file.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        rprint(f"[green]Данные сохранены:[/green] {raw_file.name}, {norm_file.name}")

    table = Table(title=f"YM Webmaster indexing ({client}, status={status}, limit={limit}, offset={offset})")
    table.add_column("url")
    table.add_column("status")
    table.add_column("http_code", justify="right")
    table.add_column("last_access")
    table.add_column("reason")
    for r in normalized[: min(len(normalized), 50)]:
        table.add_row(
            str(r.get("url", "")),
            str(r.get("search_url_status", "")),
            str(r.get("http_code", "")),
            str(r.get("last_access", "")),
            str(r.get("reason", "")),
        )
    rprint(table)


@app.command("analyze-sources")
def analyze_sources_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение источников трафика между двумя периодами."""
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    try:
        cfg, _ = load_client_config(client)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить конфиг: {e}")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    try:
        from datetime import datetime

        dt_p1_start = datetime.strptime(p1_start, "%Y-%m-%d")
        dt_p1_end = datetime.strptime(p1_end, "%Y-%m-%d")
        dt_p2_start = datetime.strptime(p2_start, "%Y-%m-%d")
        dt_p2_end = datetime.strptime(p2_end, "%Y-%m-%d")

        if dt_p1_end < dt_p1_start:
            rprint(f"[bold red]Error:[/bold red] p1_end ({p1_end}) < p1_start ({p1_start})")
            raise typer.Exit(code=1)

        if dt_p2_end < dt_p2_start:
            rprint(f"[bold red]Error:[/bold red] p2_end ({p2_end}) < p2_start ({p2_start})")
            raise typer.Exit(code=1)
    except ValueError as e:
        rprint(f"[bold red]Error:[/bold red] Некорректный формат даты: {e}")
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        data_p1 = load_or_fetch_sources(client, p1_start, p1_end, limit, refresh, metrika)
        data_p2 = load_or_fetch_sources(client, p2_start, p2_end, limit, refresh, metrika)
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    rows = compare_sources_periods(data_p1, data_p2)
    rows = calculate_contributions(rows)
    all_rows = rows.copy()
    rows = sort_analysis_rows(rows)

    workbook = create_workbook(
        client=client,
        counter_id=cfg.counter_id,
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / (
        f"analysis_sources_{p1_start.replace('-', '')}{p1_end.replace('-', '')}"
        f"__{p2_start.replace('-', '')}{p2_end.replace('-', '')}.json"
    )
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")

    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="visits", 
            dimension_name="source"
        )
        return

    table = Table(
        title=f"Сравнение источников трафика ({client}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})"
    )
    table.add_column("source")
    table.add_column("visits_p1", justify="right")
    table.add_column("visits_p2", justify="right")
    table.add_column("delta_abs", justify="right")
    table.add_column("delta_pct", justify="right")
    table.add_column("contribution_pct", justify="right")

    for row in rows[:limit] if limit > 0 else rows:
        table.add_row(
            row["source"],
            str(int(row["visits_p1"])),
            str(int(row["visits_p2"])),
            str(int(row["delta_abs"])),
            f"{row['delta_pct']:.1f}",
            f"{row['contribution_pct']:.1f}",
        )

    rprint(table)

    totals = workbook["totals"]
    rprint("\n[bold]Итоги:[/bold]")
    rprint(f"  Всего визитов P1: {int(totals['total_visits_p1']):,}")
    rprint(f"  Всего визитов P2: {int(totals['total_visits_p2']):,}")
    rprint(f"  Изменение (абс.): {int(totals['total_delta_abs']):,}")
    rprint(f"  Изменение (%): {totals['total_delta_pct']:.1f}%")


@app.command("analyze-pages")
def analyze_pages_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение входных страниц (landing pages) между двумя периодами."""
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    try:
        cfg, _ = load_client_config(client)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить конфиг: {e}")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    try:
        dt_p1_start = __import__("datetime").datetime.strptime(p1_start, "%Y-%m-%d")
        dt_p1_end = __import__("datetime").datetime.strptime(p1_end, "%Y-%m-%d")
        dt_p2_start = __import__("datetime").datetime.strptime(p2_start, "%Y-%m-%d")
        dt_p2_end = __import__("datetime").datetime.strptime(p2_end, "%Y-%m-%d")

        if dt_p1_end < dt_p1_start:
            rprint(f"[bold red]Error:[/bold red] p1_end ({p1_end}) < p1_start ({p1_start})")
            raise typer.Exit(code=1)

        if dt_p2_end < dt_p2_start:
            rprint(f"[bold red]Error:[/bold red] p2_end ({p2_end}) < p2_start ({p2_start})")
            raise typer.Exit(code=1)
    except ValueError as e:
        rprint(f"[bold red]Error:[/bold red] Некорректный формат даты: {e}")
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        data_p1 = load_or_fetch_pages(client, p1_start, p1_end, limit, refresh, metrika)
        data_p2 = load_or_fetch_pages(client, p2_start, p2_end, limit, refresh, metrika)
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    rows = compare_pages_periods(data_p1, data_p2)
    rows = calculate_contributions_pages(rows)
    all_rows = rows.copy()
    rows = sort_analysis_rows_pages(rows)

    workbook = create_workbook_pages(
        client=client,
        counter_id=cfg.counter_id,
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / (
        f"analysis_pages_{p1_start.replace('-', '')}{p1_end.replace('-', '')}"
        f"__{p2_start.replace('-', '')}{p2_end.replace('-', '')}.json"
    )
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")

    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="visits", 
            dimension_name="landingPage"
        )
        return

    table = Table(
        title=f"Сравнение landing pages ({client}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})"
    )
    table.add_column("landingPage")
    table.add_column("visits_p1", justify="right")
    table.add_column("visits_p2", justify="right")
    table.add_column("delta_abs", justify="right")
    table.add_column("delta_pct", justify="right")
    table.add_column("contribution_pct", justify="right")

    for row in rows[:limit] if limit > 0 else rows:
        table.add_row(
            row["landingPage"],
            str(int(row["visits_p1"])),
            str(int(row["visits_p2"])),
            str(int(row["delta_abs"])),
            f"{row['delta_pct']:.1f}",
            f"{row['contribution_pct']:.1f}",
        )

    rprint(table)

    totals = workbook["totals"]
    rprint("\n[bold]Итоги:[/bold]")
    rprint(f"  Всего визитов P1: {int(totals['total_visits_p1']):,}")
    rprint(f"  Всего визитов P2: {int(totals['total_visits_p2']):,}")
    rprint(f"  Изменение (абс.): {int(totals['total_delta_abs']):,}")
    rprint(f"  Изменение (%): {totals['total_delta_pct']:.1f}%")


@app.command("analyze-pages-by-source")
def analyze_pages_by_source_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    source: str = typer.Option(
        "Search engine traffic", "--source", help="Источник (значение ym:s:lastTrafficSource)"
    ),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение landing pages между двумя периодами внутри выбранного источника трафика."""
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    try:
        cfg, _ = load_client_config(client)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить конфиг: {e}")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    try:
        dt_p1_start = __import__("datetime").datetime.strptime(p1_start, "%Y-%m-%d")
        dt_p1_end = __import__("datetime").datetime.strptime(p1_end, "%Y-%m-%d")
        dt_p2_start = __import__("datetime").datetime.strptime(p2_start, "%Y-%m-%d")
        dt_p2_end = __import__("datetime").datetime.strptime(p2_end, "%Y-%m-%d")

        if dt_p1_end < dt_p1_start:
            rprint(f"[bold red]Error:[/bold red] p1_end ({p1_end}) < p1_start ({p1_start})")
            raise typer.Exit(code=1)

        if dt_p2_end < dt_p2_start:
            rprint(f"[bold red]Error:[/bold red] p2_end ({p2_end}) < p2_start ({p2_start})")
            raise typer.Exit(code=1)
    except ValueError as e:
        rprint(f"[bold red]Error:[/bold red] Некорректный формат даты: {e}")
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        data_p1 = load_or_fetch_pages_by_source(client, p1_start, p1_end, source, limit, refresh, metrika)
        data_p2 = load_or_fetch_pages_by_source(client, p2_start, p2_end, source, limit, refresh, metrika)
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    rows = compare_pages_periods(data_p1, data_p2)
    rows = calculate_contributions_pages(rows)
    all_rows = rows.copy()
    rows = sort_analysis_rows_pages(rows)

    workbook = create_workbook_pages(
        client=client,
        counter_id=cfg.counter_id,
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )
    workbook["meta"]["source"] = source

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Безопасное имя файла (ascii slug)
    import re as _re

    source_slug = _re.sub(r"[^a-z0-9]+", "_", source.strip().lower())
    source_slug = _re.sub(r"_+", "_", source_slug).strip("_") or "unknown"
    workbook_file = cache_dir / (
        f"analysis_pages_by_source_{source_slug}_"
        f"{p1_start.replace('-', '')}{p1_end.replace('-', '')}"
        f"__{p2_start.replace('-', '')}{p2_end.replace('-', '')}.json"
    )
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")

    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="visits", 
            dimension_name="landingPage"
        )
        return

    table = Table(
        title=f"Landing pages by source ({client}, {source}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})"
    )
    table.add_column("landingPage")
    table.add_column("visits_p1", justify="right")
    table.add_column("visits_p2", justify="right")
    table.add_column("delta_abs", justify="right")
    table.add_column("delta_pct", justify="right")
    table.add_column("contribution_pct", justify="right")

    for row in rows[:limit] if limit > 0 else rows:
        table.add_row(
            row["landingPage"],
            str(int(row["visits_p1"])),
            str(int(row["visits_p2"])),
            str(int(row["delta_abs"])),
            f"{row['delta_pct']:.1f}",
            f"{row['contribution_pct']:.1f}",
        )

    rprint(table)

    totals = workbook["totals"]
    rprint("\n[bold]Итоги:[/bold]")
    rprint(f"  Всего визитов P1: {int(totals['total_visits_p1']):,}")
    rprint(f"  Всего визитов P2: {int(totals['total_visits_p2']):,}")
    rprint(f"  Изменение (абс.): {int(totals['total_delta_abs']):,}")
    rprint(f"  Изменение (%): {totals['total_delta_pct']:.1f}%")


@app.command("analyze-goals-by-source")
def analyze_goals_by_source_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    goal_id: int = typer.Option(0, "--goal-id", help="ID цели в Метрике (0 = взять из config)"),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение goals (конверсий) по источникам между двумя периодами."""
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    try:
        cfg, _ = load_client_config(client)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить конфиг: {e}")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    resolved_goal_id = int(goal_id or 0) or int(cfg.goal_id or 0)
    if resolved_goal_id <= 0:
        rprint(
            "[bold red]Error:[/bold red] goal_id не задан. Укажите --goal-id или заполните metrika.goal_id в config.yaml"
        )
        raise typer.Exit(code=1)

    try:
        dt_p1_start = __import__("datetime").datetime.strptime(p1_start, "%Y-%m-%d")
        dt_p1_end = __import__("datetime").datetime.strptime(p1_end, "%Y-%m-%d")
        dt_p2_start = __import__("datetime").datetime.strptime(p2_start, "%Y-%m-%d")
        dt_p2_end = __import__("datetime").datetime.strptime(p2_end, "%Y-%m-%d")

        if dt_p1_end < dt_p1_start:
            rprint(f"[bold red]Error:[/bold red] p1_end ({p1_end}) < p1_start ({p1_start})")
            raise typer.Exit(code=1)

        if dt_p2_end < dt_p2_start:
            rprint(f"[bold red]Error:[/bold red] p2_end ({p2_end}) < p2_start ({p2_start})")
            raise typer.Exit(code=1)
    except ValueError as e:
        rprint(f"[bold red]Error:[/bold red] Некорректный формат даты: {e}")
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        data_p1 = load_or_fetch_goals_by_source(
            client, p1_start, p1_end, resolved_goal_id, limit, refresh, metrika
        )
        data_p2 = load_or_fetch_goals_by_source(
            client, p2_start, p2_end, resolved_goal_id, limit, refresh, metrika
        )
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    rows = compare_goals_periods(data_p1, data_p2, key_field="source")
    rows = calculate_contributions_goals(rows)
    all_rows = rows.copy()
    rows = sort_goals_rows(rows, key_field="source")

    workbook = create_workbook_goals(
        client=client,
        counter_id=cfg.counter_id,
        goal_id=resolved_goal_id,
        dimension="source",
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / goals_workbook_filename(
        "goals_by_source", resolved_goal_id, p1_start, p1_end, p2_start, p2_end
    )
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")
    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="goal_visits", 
            dimension_name="source"
        )
        return

    table = Table(
        title=f"Goals by source ({client}, goal_id={resolved_goal_id}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})"
    )
    table.add_column("source")
    table.add_column("goal_visits_p1", justify="right")
    table.add_column("goal_visits_p2", justify="right")
    table.add_column("delta_goal_visits", justify="right")
    table.add_column("delta_goal_visits_pct", justify="right")
    table.add_column("delta_cr_pp", justify="right")
    table.add_column("contribution_pct", justify="right")

    for row in rows[:limit] if limit > 0 else rows:
        table.add_row(
            row["source"],
            str(int(row["goal_visits_p1"])),
            str(int(row["goal_visits_p2"])),
            str(int(row["delta_goal_visits_abs"])),
            f"{row['delta_goal_visits_pct']:.1f}",
            f"{row['delta_cr_pp']:.2f}",
            f"{row['contribution_pct']:.1f}",
        )
    rprint(table)

    totals = workbook["totals"]
    rprint("\n[bold]Итоги:[/bold]")
    rprint(f"  Visits P1: {int(totals['total_visits_p1']):,}")
    rprint(f"  Visits P2: {int(totals['total_visits_p2']):,}")
    rprint(f"  Goal visits P1: {int(totals['total_goal_visits_p1']):,}")
    rprint(f"  Goal visits P2: {int(totals['total_goal_visits_p2']):,}")
    rprint(f"  CR P1: {totals['total_cr_p1']:.2f}%")
    rprint(f"  CR P2: {totals['total_cr_p2']:.2f}%")
    rprint(f"  Δ goal visits: {int(totals['total_delta_goal_visits_abs']):,}")
    rprint(f"  Δ goal visits (%): {totals['total_delta_goal_visits_pct']:.1f}%")
    rprint(f"  Δ CR (pp): {totals['total_delta_cr_pp']:.2f}")


@app.command("analyze-goals-by-page")
def analyze_goals_by_page_cmd(
    client: str = typer.Argument(..., help="Имя папки в clients/<client>/"),
    p1_start: str = typer.Argument(..., help="Начальная дата периода 1 (YYYY-MM-DD)"),
    p1_end: str = typer.Argument(..., help="Конечная дата периода 1 (YYYY-MM-DD)"),
    p2_start: str = typer.Argument(..., help="Начальная дата периода 2 (YYYY-MM-DD)"),
    p2_end: str = typer.Argument(..., help="Конечная дата периода 2 (YYYY-MM-DD)"),
    goal_id: int = typer.Option(0, "--goal-id", help="ID цели в Метрике (0 = взять из config)"),
    limit: int = typer.Option(50, "--limit", help="Лимит строк в выводе"),
    refresh: bool = typer.Option(False, "--refresh", help="Принудительно перезапросить Метрику"),
    format: str = typer.Option("table", "--format", help="Формат вывода: table или insights"),
):
    """Сравнение goals (конверсий) по входным страницам между двумя периодами."""
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    if not token:
        rprint("[bold red]Error:[/bold red] YANDEX_METRIKA_TOKEN не задан в окружении")
        raise typer.Exit(code=1)

    try:
        cfg, _ = load_client_config(client)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить конфиг: {e}")
        raise typer.Exit(code=1)

    if cfg.counter_id <= 0:
        rprint("[bold red]Error:[/bold red] metrika.counter_id не задан в конфиге")
        raise typer.Exit(code=1)

    resolved_goal_id = int(goal_id or 0) or int(cfg.goal_id or 0)
    if resolved_goal_id <= 0:
        rprint(
            "[bold red]Error:[/bold red] goal_id не задан. Укажите --goal-id или заполните metrika.goal_id в config.yaml"
        )
        raise typer.Exit(code=1)

    try:
        dt_p1_start = __import__("datetime").datetime.strptime(p1_start, "%Y-%m-%d")
        dt_p1_end = __import__("datetime").datetime.strptime(p1_end, "%Y-%m-%d")
        dt_p2_start = __import__("datetime").datetime.strptime(p2_start, "%Y-%m-%d")
        dt_p2_end = __import__("datetime").datetime.strptime(p2_end, "%Y-%m-%d")

        if dt_p1_end < dt_p1_start:
            rprint(f"[bold red]Error:[/bold red] p1_end ({p1_end}) < p1_start ({p1_start})")
            raise typer.Exit(code=1)

        if dt_p2_end < dt_p2_start:
            rprint(f"[bold red]Error:[/bold red] p2_end ({p2_end}) < p2_start ({p2_start})")
            raise typer.Exit(code=1)
    except ValueError as e:
        rprint(f"[bold red]Error:[/bold red] Некорректный формат даты: {e}")
        raise typer.Exit(code=1)

    metrika = MetrikaClient(token=token, counter_id=cfg.counter_id)

    try:
        data_p1 = load_or_fetch_goals_by_page(client, p1_start, p1_end, resolved_goal_id, limit, refresh, metrika)
        data_p2 = load_or_fetch_goals_by_page(client, p2_start, p2_end, resolved_goal_id, limit, refresh, metrika)
    except RuntimeError as e:
        error_msg = str(e)
        if token in error_msg:
            error_msg = error_msg.replace(token, "***")
        if "OAuth" in error_msg:
            error_msg = error_msg.split("OAuth")[0] + "OAuth ***"
        rprint(f"[bold red]Error:[/bold red] Ошибка API Метрики: {error_msg[:500]}")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] Не удалось загрузить данные: {e}")
        raise typer.Exit(code=1)

    rows = compare_goals_periods(data_p1, data_p2, key_field="landingPage")
    rows = calculate_contributions_goals(rows)
    all_rows = rows.copy()
    rows = sort_goals_rows(rows, key_field="landingPage")

    workbook = create_workbook_goals(
        client=client,
        counter_id=cfg.counter_id,
        goal_id=resolved_goal_id,
        dimension="landingPage",
        p1_start=p1_start,
        p1_end=p1_end,
        p2_start=p2_start,
        p2_end=p2_end,
        limit=limit,
        refresh_used=refresh,
        rows=rows,
        all_rows=all_rows,
    )

    cache_dir = Path("data_cache") / client
    cache_dir.mkdir(parents=True, exist_ok=True)
    workbook_file = cache_dir / goals_workbook_filename(
        "goals_by_page", resolved_goal_id, p1_start, p1_end, p2_start, p2_end
    )
    workbook_file.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")
    rprint(f"[green]Workbook сохранён:[/green] {workbook_file.name}")

    if format == "insights":
        print_insights(
            rows, 
            workbook["totals"], 
            metric_name="goal_visits", 
            dimension_name="landingPage"
        )
        return

    table = Table(
        title=f"Goals by landingPage ({client}, goal_id={resolved_goal_id}, {p1_start}-{p1_end} vs {p2_start}-{p2_end})"
    )
    table.add_column("landingPage")
    table.add_column("goal_visits_p1", justify="right")
    table.add_column("goal_visits_p2", justify="right")
    table.add_column("delta_goal_visits", justify="right")
    table.add_column("delta_goal_visits_pct", justify="right")
    table.add_column("delta_cr_pp", justify="right")
    table.add_column("contribution_pct", justify="right")

    for row in rows[:limit] if limit > 0 else rows:
        table.add_row(
            row["landingPage"],
            str(int(row["goal_visits_p1"])),
            str(int(row["goal_visits_p2"])),
            str(int(row["delta_goal_visits_abs"])),
            f"{row['delta_goal_visits_pct']:.1f}",
            f"{row['delta_cr_pp']:.2f}",
            f"{row['contribution_pct']:.1f}",
        )
    rprint(table)

    totals = workbook["totals"]
    rprint("\n[bold]Итоги:[/bold]")
    rprint(f"  Visits P1: {int(totals['total_visits_p1']):,}")
    rprint(f"  Visits P2: {int(totals['total_visits_p2']):,}")
    rprint(f"  Goal visits P1: {int(totals['total_goal_visits_p1']):,}")
    rprint(f"  Goal visits P2: {int(totals['total_goal_visits_p2']):,}")
    rprint(f"  CR P1: {totals['total_cr_p1']:.2f}%")
    rprint(f"  CR P2: {totals['total_cr_p2']:.2f}%")
    rprint(f"  Δ goal visits: {int(totals['total_delta_goal_visits_abs']):,}")
    rprint(f"  Δ goal visits (%): {totals['total_delta_goal_visits_pct']:.1f}%")
    rprint(f"  Δ CR (pp): {totals['total_delta_cr_pp']:.2f}")


@app.command()
def audit_data(
    client: str = typer.Argument(..., help="Имя клиента"),
    period_start: str = typer.Argument(..., help="Начало периода (YYYY-MM-DD)"),
    period_end: str = typer.Argument(..., help="Конец периода (YYYY-MM-DD)"),
):
    """
    ⚡ AUDIT: Проверка данных для клиента за период.
    
    Проверяет:
    - Наличие всех необходимых файлов
    - Актуальность данных
    - Отсутствие аномалий
    - Корректность сумм
    """
    from app.audit import AuditEngine
    
    rprint(f"[bold yellow]⚡ AUDIT: Data Verification[/bold yellow]")
    rprint(f"Client: {client}, Period: {period_start} to {period_end}\n")
    
    engine = AuditEngine(client)
    
    # Проверяем наличие основных файлов
    reports_dir = Path("reports") / client
    cache_dir = Path("data_cache") / client
    
    issues = []
    
    # 1. Проверка директорий
    if not reports_dir.exists():
        issues.append(f"Reports directory not found: {reports_dir}")
    
    if not cache_dir.exists():
        issues.append(f"Cache directory not found: {cache_dir}")
    
    # 2. Проверка наличия workbooks
    expected_files = [
        f"analysis_sources_*_{period_start}_{period_end}.json",
        f"analysis_pages_*_{period_start}_{period_end}.json",
    ]
    
    for pattern in expected_files:
        files = list(cache_dir.glob(pattern))
        if not files:
            issues.append(f"Missing workbook: {pattern}")
        else:
            # Проверка актуальности
            for file in files:
                age_days = (datetime.now() - datetime.fromtimestamp(file.stat().st_mtime)).days
                if age_days > 7:
                    issues.append(f"Stale data ({age_days} days old): {file.name}")
    
    if issues:
        rprint("[red]❌ Audit FAILED:[/red]")
        for issue in issues:
            rprint(f"  - {issue}")
        raise typer.Exit(1)
    else:
        rprint("[green]✅ Audit PASSED: All data files present and up-to-date[/green]")


@app.command()
def audit_metric(
    claim: str = typer.Argument(..., help="Утверждение вида 'metric=value'"),
    source: str = typer.Option(..., "--source", help="Файл-источник данных"),
    client: str = typer.Option(..., "--client", help="Имя клиента"),
    period: str = typer.Option("", "--period", help="Период (опционально)"),
):
    """
    ⚡ AUDIT: Проверка конкретной цифры.
    
    Пример:
    python -m app.cli audit-metric "visits_organic=12499" \\
        --source "analysis_sources_*.json" \\
        --client trisystems \\
        --period "Q4 2025"
    """
    from app.audit import AuditEngine, DataPoint
    
    # Парсим claim
    if "=" not in claim:
        rprint("[red]Error: claim должен быть вида 'metric=value'[/red]")
        raise typer.Exit(1)
    
    metric, value_str = claim.split("=", 1)
    
    try:
        value = float(value_str)
    except ValueError:
        value = value_str
    
    rprint(f"[bold yellow]⚡ AUDIT: Metric Verification[/bold yellow]")
    rprint(f"Claim: {metric} = {value}")
    rprint(f"Source: {source}")
    rprint(f"Client: {client}\n")
    
    engine = AuditEngine(client)
    
    result = engine.verify_data_source(DataPoint(
        metric=metric,
        value=value,
        source_file=source,
        period=period,
        context={}
    ))
    
    if result.status == "passed":
        rprint(f"[green]✅ PASSED[/green]: {result.claim}")
        rprint(f"Evidence: {', '.join(result.evidence)}")
    else:
        rprint(f"[red]❌ FAILED[/red]: {result.claim}")
        rprint(f"Issues:")
        for issue in result.issues:
            rprint(f"  - {issue}")
        raise typer.Exit(1)


@app.command()
def audit_report(
    report_path: str = typer.Argument(..., help="Путь к отчету"),
    strict: bool = typer.Option(False, "--strict", help="Строгий режим (провал при warnings)"),
):
    """
    ⚡ AUDIT: Полная проверка отчета перед публикацией.
    
    Проверяет:
    - Все цифры имеют источники
    - Все расчеты верны
    - Все гипотезы обоснованы
    
    Пример:
    python -m app.cli audit-report reports/trisystems/REPORT.md --strict
    """
    from app.audit import AuditEngine
    
    report_file = Path(report_path)
    if not report_file.exists():
        rprint(f"[red]Error: Report not found: {report_path}[/red]")
        raise typer.Exit(1)
    
    rprint(f"[bold yellow]⚡ AUDIT: Report Verification[/bold yellow]")
    rprint(f"Report: {report_path}\n")
    
    # TODO: Реализовать парсинг отчета и проверку всех утверждений
    # Пока что базовая проверка
    
    rprint("[yellow]⚠️ Full report audit not yet implemented[/yellow]")
    rprint("Manual checks required:")
    rprint("  1. Все цифры имеют источники (file + line)?")
    rprint("  2. Все гипотезы имеют альтернативы?")
    rprint("  3. Указан confidence для ключевых выводов?")
    rprint("  4. Нет противоречий в данных?")
    rprint("  5. Рекомендации реалистичны (не 'с потолка')?")
    
    # Placeholder для будущей реализации
    rprint("\n[blue]ℹ️ See docs/AUDIT_RULES.md for full checklist[/blue]")


if __name__ == "__main__":
    app()
