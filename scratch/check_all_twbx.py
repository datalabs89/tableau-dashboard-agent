import zipfile
from lxml import etree

for p in [r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx', r'C:\Users\User\Desktop\Superstore_Ellen_Blackburn_Edition.twbx']:
    print('CHECKING:', p)
    with zipfile.ZipFile(p, 'r') as z:
        for name in z.namelist():
            if name.endswith('.twb'):
                xml = z.read(name)
                tree = etree.fromstring(xml)
                for s in ['Sparkline_Sales', 'Sparkline_Profit', 'Sparkline_Quantity', 'Sparkline_Profit_Ratio']:
                    ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
                    table = ws.find('.//table')
                    rows = table.find('rows')
                    print(f"  {s} rows text: {repr(rows.text if rows is not None else None)}")
