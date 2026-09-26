import zipfile
from lxml import etree

with zipfile.ZipFile(r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx', 'r') as z:
    xml = z.read('Superstore_Ellen_Blackburn_Edition.twb')
    tree = etree.fromstring(xml)
    for s in ['Sparkline_Sales', 'Sparkline_Profit', 'Sparkline_Quantity', 'Sparkline_Profit_Ratio']:
        ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
        table = ws.find('.//table')
        rows = table.find('rows')
        print(s, 'rows text:', repr(rows.text if rows is not None else None))
        cols = table.find('cols')
        print(s, 'cols text:', repr(cols.text if cols is not None else None))
