"""Tableau Cloud CI/CD Publisher using Tableau Server Client (TSC).

Automates publishing of .twbx dashboards to Tableau Cloud or Tableau Server
using Personal Access Tokens (PAT).
"""

import os
import sys
from pathlib import Path


def load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()


def publish_to_cloud(
    twbx_path: str,
    workbook_name: str = "Superstore_Tableau_Visionary_Edition",
    project_name: str = "default",
):
    load_env()
    try:
        import tableauserverclient as TSC
    except ImportError:
        print("Error: tableauserverclient is not installed.")
        print("Run: pip install tableauserverclient")
        sys.exit(1)

    server_url = os.getenv("TABLEAU_SERVER", "https://prod-ap-northeast-1a.online.tableau.com")
    site_id = os.getenv("TABLEAU_SITE", "")
    token_name = os.getenv("TABLEAU_TOKEN_NAME", "")
    token_value = os.getenv("TABLEAU_TOKEN_VALUE", "")

    if not all([token_name, token_value]):
        print("Missing environment variables: TABLEAU_TOKEN_NAME or TABLEAU_TOKEN_VALUE.")
        print("Please set them or pass them via GitHub Secrets.")
        sys.exit(1)

    print(f"Connecting to Tableau Cloud at {server_url} (Site: '{site_id}')...")
    tableau_auth = TSC.PersonalAccessTokenAuth(
        token_name=token_name,
        personal_access_token=token_value,
        site_id=site_id,
    )
    server = TSC.Server(server_url, use_server_version=True)

    with server.auth.sign_in(tableau_auth):
        print(f"Authenticated successfully! Querying projects...")
        all_projects, _ = server.projects.get()
        target_project = next((p for p in all_projects if p.name.lower() == project_name.lower()), None)
        project_id = target_project.id if target_project else None

        print(f"Publishing workbook: {twbx_path} -> Name: '{workbook_name}'...")
        wb_item = TSC.WorkbookItem(name=workbook_name, project_id=project_id)
        wb_item = server.workbooks.publish(
            wb_item,
            twbx_path,
            mode=TSC.Server.PublishMode.Overwrite,
        )
        print(f"SUCCESS: Workbook '{wb_item.name}' published successfully!")
        print(f"Webpage URL: {wb_item.webpage_url}")


if __name__ == "__main__":
    target_twbx = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\User\Desktop\Superstore_Tableau_Visionary_Edition.twbx"
    publish_to_cloud(target_twbx)
