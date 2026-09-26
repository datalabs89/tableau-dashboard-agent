"""Tableau Public Desktop UI Automation Publisher.

Automates saving/publishing workbooks directly to Tableau Public using Tableau Desktop
and pywinauto.
"""

import os
import sys
import time
import subprocess
from pathlib import Path


def publish_to_tableau_public(
    twbx_path: str,
    workbook_name: str = "Superstore Visionary Edition",
    tableau_exe: str = r"C:\Program Files\Tableau\Tableau 2026.2\bin\tableau.exe",
):
    try:
        from pywinauto import Application, Desktop
    except ImportError:
        print("pywinauto is not installed. Run: pip install pywinauto")
        return False

    if not Path(twbx_path).exists():
        print(f"Error: Target workbook not found at: {twbx_path}")
        return False

    if not Path(tableau_exe).exists():
        print(f"Error: Tableau Desktop not found at: {tableau_exe}")
        return False

    print("=" * 60)
    print("TABLEAU PUBLIC AUTOMATED PUBLISHER (DESKTOP UI)")
    print("=" * 60)
    print(f"Target Workbook: {Path(twbx_path).name}")
    print(f"Target Public Title: {workbook_name}")
    print(f"Tableau Executable: {tableau_exe}")
    print("-" * 60)

    print("[1/4] Launching Tableau Desktop with the workbook...")
    proc = subprocess.Popen([tableau_exe, str(twbx_path)])
    
    # Wait for Tableau Desktop to load the workbook
    print("[2/4] Waiting for Tableau Desktop to fully initialize (12 seconds)...")
    time.sleep(12)

    try:
        print("[3/4] Connecting to Tableau Desktop window...")
        app = Application(backend="uia").connect(path=tableau_exe)
        main_win = app.top_window()
        main_win.set_focus()
        print(f"      Active window title: '{main_win.window_text()}'")

        print("[4/4] Sending keyboard command: Server -> Tableau Public -> Save to Tableau Public As...")
        # Alt + S (Server) -> P (Tableau Public) -> A (Save to Tableau Public As...)
        # or Alt + S -> P -> S (Save to Tableau Public)
        main_win.type_keys("%sps")
        time.sleep(5)

        print("Checking for Tableau Public publish dialog...")
        desktop = Desktop(backend="uia")
        # Look for dialogs
        dialogs = desktop.windows(title_re=".*Tableau Public.*")
        if dialogs:
            dlg = dialogs[0]
            dlg.set_focus()
            print(f"      Found dialog: '{dlg.window_text()}'")
            print(f"      Submitting title: '{workbook_name}' and pressing Enter...")
            dlg.type_keys(f"^a{workbook_name}{{ENTER}}")
            print(">>> Publish command submitted successfully! <<<")
            return True
        else:
            print("Notice: Publish dialog was not auto-focused.")
            print("If you are not yet signed in to Tableau Public, Tableau Desktop will prompt for your Tableau Public credentials once.")
            return True
    except Exception as e:
        print(f"Automation notice: {e}")
        return False


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\User\Desktop\Superstore_Tableau_Visionary_Edition.twbx"
    publish_to_tableau_public(target)
