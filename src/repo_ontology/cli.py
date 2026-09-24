"""CLI interface for repo-ontology."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repo_ontology import __version__
from repo_ontology.init import init_project
from repo_ontology.lint import lint_ontology
from repo_ontology.loader import find_ontology_dir, load_ontology
from repo_ontology.scaffold import scaffold_element
from repo_ontology.trace import trace_ontology

console = Console()
error_console = Console(stderr=True)


def _report_load_errors(registry) -> bool:
    """Prevent partial registries from appearing as successful info or trace results."""
    if not registry.has_errors:
        return False
    for error in registry.errors:
        error_console.print(f"[bold red]Ontology load error:[/bold red] {error}")
    return True


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path) if args.path else Path.cwd()
    try:
        dest = init_project(target, force=args.force)
        console.print(f"[bold green]✓[/bold green] Initialized repo-ontology template at: [bold]{dest}[/bold]")
        console.print("Run '[cyan]otlg info[/cyan]' or '[cyan]otlg lint[/cyan]' to inspect the ontology.")
        return 0
    except Exception as e:
        error_console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    target = Path(args.path) if args.path else None
    try:
        registry = load_ontology(target)
    except Exception as e:
        error_console.print(f"[bold red]Error loading ontology:[/bold red] {e}")
        return 1
    if _report_load_errors(registry):
        return 1

    project_name = "Project"
    if registry.config:
        if hasattr(registry.config.project, "name"):
            project_name = registry.config.project.name
        elif isinstance(registry.config.project, dict):
            project_name = registry.config.project.get("name", "Project")
        elif registry.config.name:
            project_name = registry.config.name
    
    table = Table(title=f"Ontology Overview: {project_name}", border_style="cyan")
    table.add_column("Primitive", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Items")

    table.add_row("Objects (Entities)", str(len(registry.objects)), ", ".join(sorted(registry.objects.keys())))
    table.add_row("Links (Relations)", str(len(registry.links)), f"{len(registry.links)} defined")
    table.add_row("Actions (Mutations)", str(len(registry.actions)), ", ".join(sorted(registry.actions.keys())))
    table.add_row("Functions (Computations)", str(len(registry.functions)), ", ".join(sorted(registry.functions.keys())))
    table.add_row("Rules (Invariants)", str(len(registry.rules)), ", ".join(r.id for r in registry.rules))
    if registry.views:
        table.add_row("Views (UI / Screens)", str(len(registry.views)), f"{len(registry.views)} mapped")

    console.print(table)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    target = Path(args.path) if args.path else None
    try:
        registry = load_ontology(target)
    except Exception as e:
        error_console.print(f"[bold red]Critical Error:[/bold red] {e}")
        return 1

    issues = lint_ontology(
        registry,
        check_code=not args.skip_code,
        strict_code=args.strict,
    )

    if not issues:
        console.print("[bold green]✓ All ontology checks passed cleanly! (0 violations)[/bold green]")
        return 0

    error_count = sum(1 for i in issues if i.severity == "ERROR")
    warning_count = sum(1 for i in issues if i.severity == "WARNING")

    table = Table(title=f"Ontology Lint: {error_count} Errors, {warning_count} Warnings")
    table.add_column("Severity", justify="center")
    table.add_column("Location", style="cyan")
    table.add_column("Message")

    for issue in issues:
        sev_style = "[bold red]ERROR[/bold red]" if issue.severity == "ERROR" else "[yellow]WARN[/yellow]"
        table.add_row(sev_style, issue.location, issue.message)

    console.print(table)
    return 1 if error_count > 0 else 0


def cmd_trace(args: argparse.Namespace) -> int:
    target = Path(args.path) if args.path else None
    try:
        registry = load_ontology(target)
    except Exception as e:
        error_console.print(f"[bold red]Error loading ontology:[/bold red] {e}")
        return 1
    if _report_load_errors(registry):
        return 1

    result = trace_ontology(registry, args.query)

    if args.json:
        print(result.to_json())
    else:
        # Markdown / formatted display
        console.print(Panel(result.to_markdown(), title=f"Ontology Trace: {args.query}", border_style="green"))

    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    try:
        out_file = scaffold_element(
            element_type=args.element_type,
            name=args.name,
            domain=args.domain,
        )
        console.print(f"[bold green]✓[/bold green] Created new {args.element_type} specification: [bold]{out_file}[/bold]")
        return 0
    except Exception as e:
        error_console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def cmd_translate(args: argparse.Namespace) -> int:
    from repo_ontology.translate import match_views, render_view_spec

    target = Path(args.path) if args.path else None
    try:
        registry = load_ontology(target)
    except Exception as e:
        error_console.print(f"[bold red]Error loading ontology:[/bold red] {e}")
        return 1
    if _report_load_errors(registry):
        return 1

    if not registry.views:
        console.print("[yellow]No views defined in .ontology/sitemap.yml or .ontology/views/[/yellow]")
        console.print("Add view definitions to map UI page hierarchies to ontology primitives.")
        return 0

    results = match_views(registry, args.query)
    if not results:
        console.print(f"[bold yellow]No matching view found for:[/bold yellow] '{args.query}'")
        console.print(f"Registered views ({len(registry.views)}): {', '.join(sorted(registry.views.keys()))}")
        return 1

    console.print(f"Found [bold green]{len(results)}[/bold green] view match(es) for '[bold]{args.query}[/bold]':\n")
    for view, score, reason in results[:args.limit]:
        console.print(f"[dim]Match Confidence: {score:.1f}% ({reason})[/dim]")
        render_view_spec(registry, view)
        console.print("")

    return 0


def cmd_intake(args: argparse.Namespace) -> int:
    from repo_ontology.intake import analyze_requirements, generate_markdown_report, parse_excel_file

    input_path = Path(args.file).resolve()
    if not input_path.is_file():
        error_console.print(f"[bold red]File not found:[/bold red] {input_path}")
        return 1

    target = Path(args.path) if args.path else None
    try:
        registry = load_ontology(target)
    except Exception as e:
        error_console.print(f"[bold red]Error loading ontology:[/bold red] {e}")
        return 1
    if _report_load_errors(registry):
        return 1

    console.print(f"Reading requirements from: [bold cyan]{input_path.name}[/bold cyan]...")
    try:
        items = parse_excel_file(input_path)
    except Exception as e:
        error_console.print(f"[bold red]Error parsing requirements file:[/bold red] {e}")
        return 1

    if not items:
        console.print("[yellow]No requirements rows found in file.[/yellow]")
        return 0

    matched, unmatched = analyze_requirements(registry, items)

    # Console summary
    table = Table(title=f"Requirements Intake Summary ({input_path.name})", border_style="cyan")
    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Description")

    table.add_row("Total Requirements", str(len(items)), "Total rows extracted from sheets")
    table.add_row("Matched (Modifications)", f"[bold green]{len(matched)}[/bold green]", "Existing views in sitemap (ready for impact trace & TDD)")
    table.add_row("Unmatched (New Specs)", f"[bold yellow]{len(unmatched)}[/bold yellow]", "New screens/menus requiring scaffolding")

    console.print(table)

    # Generate Markdown Report
    report_content = generate_markdown_report(registry, matched, unmatched, input_path.name)

    out_path = Path(args.output).resolve() if args.output else registry.ontology_dir / "intake_report.md"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_content, encoding="utf-8")
        console.print(f"[bold green]✓[/bold green] Generated detailed impact report: [bold]{out_path}[/bold]")
    except Exception as e:
        error_console.print(f"[bold red]Failed to save report:[/bold red] {e}")

    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="otlg",
        description="Palantir-grade domain ontology CLI for code repositories",
    )
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize .ontology template in project")
    p_init.add_argument("path", nargs="?", default=".", help="Target directory (default: current directory)")
    p_init.add_argument("--force", "-f", action="store_true", help="Overwrite existing .ontology")
    p_init.set_defaults(func=cmd_init)

    # info
    p_info = subparsers.add_parser("info", help="Show overview of ontology objects, actions, and rules")
    p_info.add_argument("path", nargs="?", default=None, help="Project path")
    p_info.set_defaults(func=cmd_info)

    # lint
    p_lint = subparsers.add_parser("lint", help="Verify schema, referential integrity, and code bindings")
    p_lint.add_argument("path", nargs="?", default=None, help="Project path")
    p_lint.add_argument("--strict", "-s", action="store_true", help="Treat missing code files as errors")
    p_lint.add_argument("--skip-code", action="store_true", help="Skip checking actual code file existence")
    p_lint.set_defaults(func=cmd_lint)

    # trace
    p_trace = subparsers.add_parser("trace", help="Reverse-trace domain context and code paths from query")
    p_trace.add_argument("query", help="Keyword, domain ID, or entity name (e.g. attendance, grade)")
    p_trace.add_argument("path", nargs="?", default=None, help="Project path")
    p_trace.add_argument("--json", action="store_true", help="Output result as JSON")
    p_trace.set_defaults(func=cmd_trace)

    # scaffold
    p_scaffold = subparsers.add_parser("scaffold", help="Generate a new object, action, or function spec")
    p_scaffold.add_argument("element_type", choices=["object", "action", "function"], help="Type of element")
    p_scaffold.add_argument("name", help="Name of element in PascalCase (e.g., AttendanceRecord)")
    p_scaffold.add_argument("--domain", "-d", default="core", help="Domain category")
    p_scaffold.set_defaults(func=cmd_scaffold)

    # translate
    p_translate = subparsers.add_parser("translate", help="Translate page code or menu hierarchy to ontology views & full-stack bindings")
    p_translate.add_argument("query", help="Page code, menu path keyword, or screen name (e.g. '출석체크', 'S-COM-001')")
    p_translate.add_argument("path", nargs="?", default=None, help="Project path")
    p_translate.add_argument("--limit", "-n", type=int, default=3, help="Max results to display")
    p_translate.set_defaults(func=cmd_translate)

    # intake
    p_intake = subparsers.add_parser("intake", help="Intake PRD / requirements Excel file and translate to ontology impact report")
    p_intake.add_argument("file", help="Path to requirements file (.xlsx, .csv)")
    p_intake.add_argument("path", nargs="?", default=None, help="Project path")
    p_intake.add_argument("--output", "-o", default=None, help="Output markdown report path (default: .ontology/intake_report.md)")
    p_intake.set_defaults(func=cmd_intake)

    args = parser.parse_args(argv)
    return args.func(args)
