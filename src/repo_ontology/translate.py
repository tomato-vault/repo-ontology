"""Translate requirement / page queries to ontology views and code bindings."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repo_ontology.loader import OntologyRegistry
from repo_ontology.models import ViewSpec

console = Console()
error_console = Console(stderr=True)


def normalize_text(text: str) -> str:
    """Normalize text for resilient matching (lowercase, strip whitespace and punctuation)."""
    return re.sub(r"[\s\-_>/]+", " ", text.strip().lower())


def match_views(registry: OntologyRegistry, query: str) -> List[Tuple[ViewSpec, float, str]]:
    """Match query against registry.views by page_code, menu hierarchy, or view name.
    
    Returns list of (ViewSpec, score, match_reason) sorted by score desc.
    """
    q_raw = query.strip()
    q_norm = normalize_text(q_raw)
    results = []

    for view in registry.views.values():
        score = 0.0
        reason = ""

        # 1. Exact page_code match (e.g. S-COM-001, P-TOOL-001)
        if view.page_code and view.page_code.strip().upper() == q_raw.upper():
            score = 100.0
            reason = f"Exact page_code: {view.page_code}"
        # 2. Exact menu match
        elif normalize_text(view.menu) == q_norm:
            score = 90.0
            reason = "Exact menu path match"
        # 3. Substring in menu (e.g. '출석체크' inside '데이터관리 > 수업데이터관리 > 출석체크')
        elif q_norm in normalize_text(view.menu):
            score = 70.0
            reason = f"Menu keyword match in '{view.menu}'"
        # 4. Inverted check (menu parts in query)
        elif any(part in q_norm for part in normalize_text(view.menu).split() if len(part) >= 2):
            matched_words = [part for part in normalize_text(view.menu).split() if len(part) >= 2 and part in q_norm]
            score = 40.0 + len(matched_words) * 5.0
            reason = f"Partial menu match ({', '.join(matched_words)})"
        # 5. Exact view name match
        elif normalize_text(view.view) == q_norm:
            score = 80.0
            reason = f"View name: {view.view}"
        # 6. Substring in view name
        elif q_norm in normalize_text(view.view):
            score = 60.0
            reason = f"Partial view name match in '{view.view}'"

        if score > 0:
            results.append((view, score, reason))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def render_view_spec(registry: OntologyRegistry, view: ViewSpec) -> None:
    """Render full full-stack specification of a matched view."""
    header = f"[bold cyan]{view.view}[/bold cyan]"
    if view.page_code:
        header += f" ({view.page_code})"
    
    table = Table(title=header, border_style="cyan")
    table.add_column("Category", style="bold", width=22)
    table.add_column("Details")

    table.add_row("Menu Path", f"[bold yellow]{view.menu}[/bold yellow]")
    if view.roles:
        table.add_row("Roles / Permissions", ", ".join(view.roles))
    if view.description:
        table.add_row("Description", view.description)

    b = view.binding
    if b:
        # Frontend
        if b.frontend:
            fe_lines = []
            if b.frontend.route:
                fe_lines.append(f"Route: [bold green]{b.frontend.route}[/bold green]")
            if b.frontend.slice:
                fe_lines.append(f"FSD Slice: [bold]{b.frontend.slice}[/bold]")
            if b.frontend.component:
                fe_lines.append(f"Component: {b.frontend.component}")
            if b.frontend.components:
                fe_lines.append(f"Components: {', '.join(b.frontend.components)}")
            table.add_row("Frontend (Web)", "\n".join(fe_lines) if fe_lines else "-")

        # Mobile
        if b.mobile:
            mob_lines = [f"{k}: {v}" for k, v in b.mobile.items()]
            table.add_row("Mobile (App)", "\n".join(mob_lines))

        # Backend
        if b.backend:
            be_lines = []
            if b.backend.router:
                be_lines.append(f"Router: [bold]{b.backend.router}[/bold]")
            if b.backend.endpoints:
                be_lines.append(f"Endpoints:\n  " + "\n  ".join(b.backend.endpoints))
            if b.backend.services:
                be_lines.append(f"Services: {', '.join(b.backend.services)}")
            table.add_row("Backend (API)", "\n".join(be_lines) if be_lines else "-")

        # Ontology
        if b.ontology:
            ont_lines = []
            if b.ontology.objects:
                ont_lines.append(f"Objects: [bold magenta]{', '.join(b.ontology.objects)}[/bold magenta]")
            if b.ontology.actions:
                ont_lines.append(f"Actions: [bold]{', '.join(b.ontology.actions)}[/bold]")
            if b.ontology.functions:
                ont_lines.append(f"Functions: [bold]{', '.join(b.ontology.functions)}[/bold]")
            if b.ontology.rules:
                ont_lines.append(f"Rules: [bold yellow]{', '.join(b.ontology.rules)}[/bold yellow]")
            table.add_row("Ontology Primitives", "\n".join(ont_lines) if ont_lines else "-")

    console.print(table)

    # Show code bindings from matched ontology objects/actions/functions if available
    if b and b.ontology:
        code_table = Table(title="[dim]Bound Code Implementations (Ontology Level)[/dim]", border_style="dim")
        code_table.add_column("Primitive", style="bold", width=22)
        code_table.add_column("Type", width=12)
        code_table.add_column("Key Code Path")

        # Objects
        for obj_name in b.ontology.objects or []:
            if obj_name in registry.objects:
                obj = registry.objects[obj_name]
                cb = obj.code_binding
                if cb and cb.backend and cb.backend.model:
                    code_table.add_row(obj_name, "Object", cb.backend.model)
        # Actions
        for act_name in b.ontology.actions or []:
            if act_name in registry.actions:
                act = registry.actions[act_name]
                cb = act.code_binding
                if cb and cb.backend and cb.backend.service:
                    code_table.add_row(act_name, "Action", cb.backend.service)
        # Functions
        for fn_name in b.ontology.functions or []:
            if fn_name in registry.functions:
                fn = registry.functions[fn_name]
                cb = fn.code_binding
                if cb and cb.backend and cb.backend.pure_function:
                    code_table.add_row(fn_name, "Function", cb.backend.pure_function)

        if code_table.rows:
            console.print(code_table)
