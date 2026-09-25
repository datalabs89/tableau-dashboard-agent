"""Example: Creating a new executive dashboard from worksheets in a workbook."""

from pathlib import Path
from tableau_dashboard_agent import TableauDashboardAgent

def main():
    agent = TableauDashboardAgent(default_theme="executive-dark")
    
    sample_wb = Path(r"C:\Users\User\Downloads\Superstore.twbx")
    if not sample_wb.exists():
        print(f"Sample file not found at {sample_wb}")
        return

    print("Creating new Executive Command Center dashboard...")
    result = agent.create_dashboard(
        file_path=sample_wb,
        title="Executive Command Center",
        subtitle="Global Sales Performance & Shipping Operations",
        kpis=["Total Sales"],
        charts=["SalesbySegment", "ShippingTrend"],
        theme="executive-dark",
        output_path=Path("Superstore_Command_Center.twbx"),
    )
    print(result.summary())

if __name__ == "__main__":
    main()
