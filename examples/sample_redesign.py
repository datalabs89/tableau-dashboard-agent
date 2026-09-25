"""Example: Redesigning an existing Tableau Workbook."""

from pathlib import Path
from tableau_dashboard_agent import TableauDashboardAgent

def main():
    agent = TableauDashboardAgent(default_theme="executive-light")
    
    # Path to sample workbook
    sample_wb = Path(r"C:\Users\User\Downloads\Superstore.twbx")
    if not sample_wb.exists():
        print(f"Sample file not found at {sample_wb}")
        return

    print("Step 1: Inspecting workbook...")
    meta = agent.inspect_workbook(sample_wb)
    print(f"Found {len(meta.dashboards)} dashboards and {len(meta.worksheets)} worksheets.")

    print("\nStep 2: Running visual & structural audit...")
    lint = agent.lint_workbook(sample_wb)
    print(f"Initial Health Score: {lint.score}/100 with {len(lint.findings)} findings.")

    print("\nStep 3: Redesigning dashboard 'Overview' into Executive Light layout...")
    result = agent.redesign_dashboard(
        file_path=sample_wb,
        target_dashboard="Overview",
        theme="executive-light",
        output_path=Path("Superstore_Overview_Executive.twbx"),
    )
    print(result.summary())

if __name__ == "__main__":
    main()
