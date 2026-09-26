from lxml import etree

tree = etree.parse(r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twb')
for s in ['Sparkline_Sales', 'Sparkline_Profit']:
    ws = tree.find(f'.//worksheets/worksheet[@name="{s}"]')
    print(f"================ {s} ================")
    print(etree.tostring(ws, pretty_print=True).decode('utf-8'))
