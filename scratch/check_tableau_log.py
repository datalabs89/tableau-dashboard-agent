with open(r'C:\Users\User\Documents\My Tableau Repository\Logs\log.txt', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
for line in lines[-100:]:
    if any(k in line.lower() for k in ['error', 'fail', 'bad', 'exception', 'warn', 'invalid', 'load', 'sparkline']):
        print(line.strip())
