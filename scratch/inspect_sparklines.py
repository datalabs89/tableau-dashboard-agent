from lxml import etree
import os

for path in [
    r'C:\Users\User\Documents\Superstore_Modern_Executive_Dashboard.twb',
    r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twb'
]:
    if not os.path.exists(path):
        continue
    tree = etree.parse(path)
    print('FILE:', path)
    for s in ['Sparkline_Sales', 'Sparkline_Profit', 'Sparkline_Quantity', 'Sparkline_Profit_Ratio']:
        ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
        if ws is not None:
            r = ws.find('.//table/rows')
            print(s, 'rows:', r.text if r is not None else 'NO ROWS EL')
            c = ws.find('.//table/cols')
            print(s, 'cols:', c.text if c is not None else 'NO COLS EL')
            p = ws.find('.//panes/pane')
            m = p.find('mark') if p is not None else None
            print(s, 'mark:', m.get('class') if m is not None else 'NO MARK')
