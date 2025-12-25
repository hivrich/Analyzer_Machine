from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from app.config import list_clients, load_client_config

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


if __name__ == "__main__":
    app()
