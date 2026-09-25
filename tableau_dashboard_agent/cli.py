"""Command Line Interface for Tableau Dashboard Agent.

Usage:
  python -m tableau_dashboard_agent inspect <file>
  python -m tableau_dashboard_agent lint <file>
  python -m tableau_dashboard_agent validate <file>
  python -m tableau_dashboard_agent redesign <file> [--output OUT] [--theme THEME] [--target DB]
  python -m tableau_dashboard_agent create <file> --title TITLE [--kpis K1 K2] [--charts C1 C2]
  python -m tableau_dashboard_agent swap-conn <file> [--server S] [--dbname DB]
  python -m tableau_dashboard_agent themes
  python -m tableau_dashboard_agent templates
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tableau_dashboard_agent.agent import TableauDashboardAgent
from tableau_dashboard_agent.themes import THEMES
import cwtwb.gallery as gallery


def main():
    parser = argparse.ArgumentParser(
        prog="tableau-dashboard-agent",
        description="Tableau Dashboard Agent: Create and Redesign Tableau Dashboards with official schemas & linting.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect datasources, connections, and sheets in a workbook.")
    p_inspect.add_argument("file", help="Path to .twb or .twbx file")

    # 2. Lint
    p_lint = subparsers.add_parser("lint", help="Audit workbook using Visualization-Linting and structural rules.")
    p_lint.add_argument("file", help="Path to .twb or .twbx file")

    # 3. Validate
    p_val = subparsers.add_parser("validate", help="Validate workbook XML against official Tableau Document Schemas.")
    p_val.add_argument("file", help="Path to .twb or .twbx file")

    # 4. Redesign
    p_redesign = subparsers.add_parser("redesign", help="Redesign dashboard layouts into modern executive containers.")
    p_redesign.add_argument("file", help="Path to .twb or .twbx file")
    p_redesign.add_argument("-o", "--output", help="Output .twb / .twbx file path")
    p_redesign.add_argument("-t", "--theme", default="executive-light", choices=list(THEMES.keys()), help="Design theme")
    p_redesign.add_argument("--target", help="Specific dashboard to redesign (default: all)")
    p_redesign.add_argument("--no-actions", action="store_true", help="Disable auto filter actions")

    # 5. Create
    p_create = subparsers.add_parser("create", help="Create a new executive dashboard inside a workbook.")
    p_create.add_argument("file", help="Path to .twb or .twbx file")
    p_create.add_argument("--title", required=True, help="Dashboard Title")
    p_create.add_argument("--subtitle", default="Executive Performance Overview", help="Dashboard Subtitle")
    p_create.add_argument("--theme", default="executive-light", choices=list(THEMES.keys()), help="Design theme")
    p_create.add_argument("--kpis", nargs="*", default=[], help="Worksheet names for KPI ribbon")
    p_create.add_argument("--charts", nargs="*", default=[], help="Worksheet names for main charts")
    p_create.add_argument("--details", nargs="*", default=[], help="Worksheet names for detail tables")
    p_create.add_argument("-o", "--output", help="Output .twb / .twbx file path")

    # 6. Swap Connection
    p_swap = subparsers.add_parser("swap-conn", help="Swap datasource connection parameters using Document API.")
    p_swap.add_argument("file", help="Path to .twb or .twbx file")
    p_swap.add_argument("--server", help="New server hostname or IP")
    p_swap.add_argument("--dbname", help="New database name or path")
    p_swap.add_argument("--username", help="New username")
    p_swap.add_argument("--port", help="New port")
    p_swap.add_argument("--datasource", help="Specific datasource name to modify")
    p_swap.add_argument("-o", "--output", help="Output file path")

    # 7. Themes
    subparsers.add_parser("themes", help="List available dashboard design themes.")

    # 8. Templates
    subparsers.add_parser("templates", help="List available gallery layout templates.")

    # 9. Visual Scorecard
    p_scorecard = subparsers.add_parser("scorecard", help="Generate Visual Design Scorecard & extract thumbnails.")
    p_scorecard.add_argument("file", help="Path to .twb or .twbx file")
    p_scorecard.add_argument("--dashboard", help="Specific dashboard name")

    # 10. Theme Apply
    p_theme_apply = subparsers.add_parser("theme-apply", help="Apply executive theme to workbook (.twb/.twbx).")
    p_theme_apply.add_argument("file", help="Path to .twb or .twbx file")
    p_theme_apply.add_argument("--theme", required=True, choices=["executive-light", "executive-dark", "minimalist-slate", "periwinkle-executive", "digital-marketing"], help="Theme to apply")
    p_theme_apply.add_argument("-o", "--output", help="Output file path")

    # 11. Learn from Reference
    p_learn = subparsers.add_parser("learn", help="Autonomously learn patterns from Tableau Public URL or local .twbx.")
    p_learn.add_argument("source", help="Tableau Public URL or local file path (.twb/.twbx)")
    p_learn.add_argument("--no-skill-update", action="store_true", help="Do not update SKILL.md")

    args = parser.parse_args()
    agent = TableauDashboardAgent()

    if args.command == "inspect":
        meta = agent.inspect_workbook(args.file)
        print(f"=== Workbook Inspection: {Path(meta.file_path).name} ===")
        print(f"Packaged (.twbx): {meta.is_packaged}")
        print(f"Dashboards ({len(meta.dashboards)}): {', '.join(meta.dashboards) or 'None'}")
        print(f"Worksheets ({len(meta.worksheets)}): {', '.join(meta.worksheets) or 'None'}")
        print(f"Datasources ({len(meta.datasources)}):")
        for ds in meta.datasources:
            print(f"  * {ds.caption or ds.name} (Fields: {ds.fields_count})")
            for c in ds.connections:
                print(f"      Connection: class={c.dbclass}, server={c.server}, db={c.dbname}")

    elif args.command == "lint":
        report = agent.lint_workbook(args.file)
        print(report.summary())

    elif args.command == "validate":
        res = agent.validate_schema(args.file)
        print(res.summary())

    elif args.command == "redesign":
        res = agent.redesign_dashboard(
            file_path=args.file,
            output_path=args.output,
            target_dashboard=args.target,
            theme=args.theme,
            add_filter_actions=not args.no_actions,
        )
        print(res.summary())
        print(f"\nResult saved to: {res.output_file}")

    elif args.command == "create":
        res = agent.create_dashboard(
            file_path=args.file,
            title=args.title,
            subtitle=args.subtitle,
            kpis=args.kpis,
            charts=args.charts,
            details=args.details,
            theme=args.theme,
            output_path=args.output,
        )
        print(res.summary())
        print(f"\nResult saved to: {res.output_file}")

    elif args.command == "swap-conn":
        out = agent.swap_datasource_connection(
            file_path=args.file,
            server=args.server,
            dbname=args.dbname,
            username=args.username,
            port=args.port,
            datasource_name=args.datasource,
            output_path=args.output,
        )
        print(f"Connections updated successfully. Saved to: {out}")

    elif args.command == "themes":
        print("=== Available Dashboard Design Themes ===")
        for key, t in THEMES.items():
            print(f"* {key:<18} : {t.name} - {t.description}")

    elif args.command == "templates":
        print("=== Available Gallery Templates ===")
        for t in gallery.list_gallery_templates():
            print(f"* {t.name:<20} : {t.title} - {t.description}")

    elif args.command == "scorecard":
        from tableau_dashboard_agent.visual_evaluator import VisualEvaluator
        sc = VisualEvaluator.evaluate_dashboard(args.file, args.dashboard)
        print(sc.summary())

    elif args.command == "theme-apply":
        out = agent.apply_theme(args.file, theme_name=args.theme, output_path=args.output)
        print(f"Applied theme '{args.theme}' successfully!")
        print(f"Saved to: {out}")

    elif args.command == "learn":
        summary = agent.learn_from_reference(args.source, update_skill=not args.no_skill_update)
        print(summary.summary())


if __name__ == "__main__":
    main()
