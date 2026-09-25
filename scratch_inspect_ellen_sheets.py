from lxml import etree

tree = etree.parse(r'C:\Users\User\Documents\Superstore_Modern_Executive_Dashboard.twb')
for p in tree.findall('.//encoding[@attr="color"]'):
    print(p.attrib)
    for m in p.findall('./map'):
        print("  ", m.attrib)
