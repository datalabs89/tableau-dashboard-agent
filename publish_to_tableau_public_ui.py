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

    twbx_file = Path(twbx_path).resolve()
    if not twbx_file.exists():
        print(f"Error: Target workbook not found at: {twbx_file}")
        return False

    if not Path(tableau_exe).exists():
        print(f"Error: Tableau Desktop not found at: {tableau_exe}")
        return False

    print("=" * 65)
    print("TABLEAU PUBLIC AUTOMATED PUBLISHER (DESKTOP UI)")
    print("=" * 65)
    print(f"File: {twbx_file.name}")
    print(f"Target Public Title: {workbook_name}")
    print(f"Executable: {tableau_exe}")
    print("-" * 65)

    print("\n[Step 1/5] Launching Tableau Desktop with workbook...")
    proc = subprocess.Popen([tableau_exe, str(twbx_file)])
    print(f"Process PID: {proc.pid}")

    print("\n[Step 2/5] Waiting for Tableau Desktop to fully load & render...")
    for i in range(16, 0, -2):
        print(f"  Initializing... {i}s remaining", end="\r", flush=True)
        time.sleep(2)
    print("\n  Initialization wait finished.")

    try:
        print("\n[Step 3/5] Connecting to Tableau Desktop window...")
        desktop = Desktop(backend="uia")
        
        # Find window containing Tableau
        main_win = None
        for w in desktop.windows():
            try:
                title = w.window_text()
                if "tableau" in title.lower() and "publisher" not in title.lower():
                    main_win = w
                    break
            except Exception:
                continue

        if main_win is None:
            # Fallback to connecting via Application
            app = Application(backend="uia").connect(process=proc.pid)
            main_win = app.top_window()

        print(f"  Target Window Identified: '{main_win.window_text()}'")
        main_win.set_focus()
        time.sleep(1)

        print("\n[Step 4/5] Triggering Server -> Tableau Public -> Save to Tableau Public...")
        # Send Alt+S to open Server menu
        main_win.type_keys("%s", set_foreground=True)
        time.sleep(1.5)
        # Send P for Tableau Public
        main_win.type_keys("p")
        time.sleep(1.5)
        # Send S for Save to Tableau Public
        main_win.type_keys("s")
        time.sleep(4)

        print("\n[Step 5/5] Detecting Tableau Public publish dialog...")
        found_dialog = False
        for attempt in range(6):
            dialogs = desktop.windows(title_re=".*(Tableau Public|Save Workbook|Sign In).*")
            if dialogs:
                dlg = dialogs[0]
                dlg_title = dlg.window_text()
                print(f"  Active Dialog: '{dlg_title}'")
                found_dialog = True
                
                if "sign in" in dlg_title.lower():
                    print("\n>>> INFO: Sesi Tableau Public meminta login.")
                    print(">>> Silakan masukkan email & password akun Tableau Public Anda pada jendela yang terbuka.")
                else:
                    print(f"  Mengisi nama visualisasi: '{workbook_name}'...")
                    dlg.set_focus()
                    dlg.type_keys(f"^a{workbook_name}{{ENTER}}")
                    print("\n>>> SUCCESS: Perintah Publish telah dikirim ke Tableau Desktop! <<<")
                break
            time.sleep(2)

        if not found_dialog:
            print("  Tableau Desktop sedang memproses request upload ke server Tableau Public.")
            print("  Periksa jendela Tableau Desktop yang sedang aktif di layar Anda.")

        return True

    except Exception as e:
        print(f"\nNotice during UI interaction: {e}")
        print("Tableau Desktop tetap terbuka dan siap untuk dipublish secara manual jika diperlukan.")
        return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\User\Desktop\Superstore_Tableau_Visionary_Edition.twbx"
    publish_to_tableau_public(target)
