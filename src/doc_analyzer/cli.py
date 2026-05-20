"""Command-line interface for the migration readiness tool."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from doc_analyzer.output.dashboard_writer import write_dashboard
from doc_analyzer.output.json_writer import write_json_report
from doc_analyzer.output.report_writer import write_markdown_report
from doc_analyzer.pipeline import run_pipeline

console = Console()


@click.command()
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default="input",
    help="Directory containing .docx and .pdf files.",
)
@click.option(
    "--output",
    "-o",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default="output",
    help="Directory for JSON and Markdown reports.",
)
@click.option(
    "--no-recursive",
    is_flag=True,
    help="Do not scan subdirectories.",
)
@click.option(
    "--json-only",
    is_flag=True,
    help="Write JSON reports only (skip Markdown and dashboard).",
)
@click.option(
    "--md-only",
    is_flag=True,
    help="Write Markdown report only (skip JSON and dashboard).",
)
@click.option(
    "--open-dashboard",
    is_flag=True,
    help="Open dashboard.html in the default browser after analysis.",
)
def main(
    input_dir: Path,
    output_dir: Path,
    no_recursive: bool,
    json_only: bool,
    md_only: bool,
    open_dashboard: bool,
) -> None:
    """Analyze Word and PDF documents; output JSON, summary report, and dashboard."""
    console.print("[bold blue]Document Analysis & Migration Readiness Tool[/bold blue]")
    console.print(f"Input:  [cyan]{input_dir.resolve()}[/cyan]")
    console.print(f"Output: [cyan]{output_dir.resolve()}[/cyan]")

    try:
        report = run_pipeline(input_dir, recursive=not no_recursive)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = output_dir / "dashboard.html"

    if not md_only:
        paths = write_json_report(report, output_dir)
        console.print(f"[green]OK[/green] JSON report        -> {paths['master']}")
        console.print(f"[green]OK[/green] Executive summary  -> {paths['executive']}")
        console.print(f"[green]OK[/green] Per-document JSON  -> {output_dir / 'documents'}")

    if not json_only:
        md_path = output_dir / "analysis_report.md"
        write_markdown_report(report, md_path)
        console.print(f"[green]OK[/green] Summary report     -> {md_path}")

    if not md_only and not json_only:
        write_dashboard(report, dashboard_path)
        console.print(f"[green]OK[/green] Dashboard UI       -> {dashboard_path}")
        if open_dashboard:
            webbrowser.open(dashboard_path.resolve().as_uri())

    _print_summary_table(report)
    if report.summary.get("parse_errors"):
        console.print("\n[yellow]Parse warnings:[/yellow]")
        for err in report.summary["parse_errors"]:
            console.print(f"  - {err}")

    console.print("\n[bold]Outputs:[/bold]")
    console.print("  - JSON:      analysis_report.json + documents/*.json")
    console.print("  - Report:    analysis_report.md")
    if not md_only and not json_only:
        console.print("  - Dashboard: dashboard.html  [open in any browser]")
    console.print("\n[bold green]Done.[/bold green]")


def _print_summary_table(report) -> None:
    table = Table(title="Migration Readiness Summary")
    table.add_column("File", style="cyan", max_width=36)
    table.add_column("Type")
    table.add_column("Words", justify="right")
    table.add_column("Ready?", justify="center")
    table.add_column("Readiness")
    table.add_column("Score", justify="right")

    for row in report.summary.get("rows", []):
        readiness = row["readiness"]
        style = "green" if readiness == "Ready" else "yellow" if readiness == "Partially Ready" else "red"
        ready = "Yes" if row.get("ready_for_migration") else "No"
        table.add_row(
            row["file_name"][:36],
            row["file_type"],
            str(row["word_count"]),
            ready,
            f"[{style}]{readiness}[/{style}]",
            str(row["score"]),
        )

    console.print()
    console.print(table)


if __name__ == "__main__":
    main()
