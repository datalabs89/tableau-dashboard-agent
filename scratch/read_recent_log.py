with open(r'C:\Users\User\Documents\My Tableau Repository\Logs\log.txt', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
recent_lines = [l for l in lines if '2026-09-26T09:4' in l or '2026-09-26T09:5' in l]
print(f"Recent lines around 9:4x-9:5x: {len(recent_lines)}")
for l in recent_lines[-40:]:
    print(l.strip())
