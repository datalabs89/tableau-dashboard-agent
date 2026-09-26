import zipfile
from lxml import etree

with zipfile.ZipFile(r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx', 'r') as z:
    xml = z.read('Superstore_Ellen_Blackburn_Edition.twb')
    tree = etree.fromstring(xml)
    for s in ['Sparkline_Sales', 'Sparkline_Profit', 'Sparkline_Quantity', 'Sparkline_Profit_Ratio']:
        ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
        print(f"================ {s} PANE ================")
        pane = ws.find('.//panes/pane')
        print(etree.tostring(pane, pretty_print=True).decode('utf-8'))
