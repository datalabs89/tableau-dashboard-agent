import zipfile
from lxml import etree

with zipfile.ZipFile(r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx', 'r') as z:
    xml = z.read('Superstore_Ellen_Blackburn_Edition.twb')
    tree = etree.fromstring(xml)
    for s in ['Sparkline_Sales', 'Sparkline_Profit', 'Sparkline_Quantity', 'Sparkline_Profit_Ratio']:
        ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
        table = ws.find('.//table')
        rows = table.find('rows')
        print(f"=== {s} ===")
        print(etree.tostring(rows, pretty_print=True).decode('utf-8'))
