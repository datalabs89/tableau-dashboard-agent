from lxml import etree
import zipfile

with zipfile.ZipFile(r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx', 'r') as zf:
    twb_raw = zf.read('Superstore_Ellen_Blackburn_Edition.twb')
    root = etree.fromstring(twb_raw)
    for s in ['Dynamic_Trend', 'Regional_Breakdown', 'Category_Breakdown', 'Segment_Sales']:
        ws = root.find(f'.//worksheets/worksheet[@name="{s}"]')
        print(f"=== SHEET: {s}")
        for dep in ws.findall('.//datasource-dependencies'):
            print('  dep ds:', dep.get('datasource'))
            for ci in dep.findall('column-instance'):
                print('    ci:', ci.get('name'))
