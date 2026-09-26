"""One-click rollback script to restore the exact pre-visionary working state."""
import shutil
from pathlib import Path

backup_dir = Path("backup_pre_visionary")
targets = [
    (backup_dir / "Superstore_Ellen_Blackburn_Edition_WORKING.twbx", Path(r"C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx")),
    (backup_dir / "Superstore_Ellen_Blackburn_Edition_WORKING.twbx", Path(r"C:\Users\User\Desktop\Superstore_Ellen_Blackburn_Edition.twbx")),
    (backup_dir / "Superstore_Ellen_Blackburn_Edition_WORKING.twb", Path(r"C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twb")),
    (backup_dir / "Superstore_Ellen_Blackburn_Edition_WORKING.twbx", Path(r"C:\Users\User\Documents\Superstore_Tableau_Visionary_Edition.twbx")),
    (backup_dir / "Superstore_Ellen_Blackburn_Edition_WORKING.twbx", Path(r"C:\Users\User\Desktop\Superstore_Tableau_Visionary_Edition.twbx")),
    (backup_dir / "refine_ellen_blackburn_exact_WORKING.py", Path("refine_ellen_blackburn_exact.py")),
]

for src, dst in targets:
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Restored: {src.name} -> {dst}")
    else:
        print(f"Warning: Backup source not found: {src}")

print("\n>>> Rollback complete! System restored to pre-visionary working state. <<<")
