with open(r'C:\Users\User\Documents\My Tableau Repository\Logs\log.txt', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

new_lines = lines[30940:]
print(f"New lines count: {len(new_lines)}")

# Check for errors or fatal messages
errors = [l for l in new_lines if '"sev":"error"' in l or '"sev":"fatal"' in l or '0xBAD' in l]
print(f"Error count: {len(errors)}")
for e in errors:
    print("ERROR:", e.strip()[:300])

# Check for successful document open
open_events = [l for l in new_lines if any(k in l for k in ['open-document', 'load-workbook', 'Executive_Overview', 'Superstore_Tableau_Visionary_Edition'])]
print(f"Open events: {len(open_events)}")
for ev in open_events[:10]:
    print("EVENT:", ev.strip()[:300])
