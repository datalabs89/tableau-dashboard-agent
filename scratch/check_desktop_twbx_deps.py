import zipfile
from lxml import etree

with zipfile.ZipFile(r'C:\Users\User\Desktop\Superstore_Ellen_Blackburn_Edition.twbx', 'r') as z:
    for name in z.namelist():
        if name.endswith('.twb'):
            xml = z.read(name)
            tree = etree.fromstring(xml)
            for s in ['Sparkline_Sales', 'Sparkline_Profit', 'Sparkline_Quantity', 'Sparkline_Profit_Ratio']:
                ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
                print(f"=== {s} ===")
                for dep in ws.findall('.//datasource-dependencies'):
                    print(f" DS: {dep.get('datasource')}")
                    for col in dep.findall('column'):
                        print(f"   col: {col.get('name')}")
                    for ci in dep.findall('column-instance'):
                        print(f"   ci: {ci.get('name')} (col={ci.get('column')}, deriv={ci.get('derivation')})")
