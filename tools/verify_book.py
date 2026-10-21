from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import posixpath, json, re
book=Path('src/book.md').read_text()
assert len(re.findall(r'^# 第 \d+ 章',book,re.M))==14
sources=json.loads(Path('research/sources.json').read_text())
assert all(not s.get('error') and s['bytes']>1000 for s in sources)
with ZipFile('dist/从零开始学Kubernetes.epub') as z:
 assert z.infolist()[0].filename=='mimetype'
 assert z.infolist()[0].compress_type==0
 assert z.read('mimetype')==b'application/epub+zip'
 files=set(z.namelist())
 container=ET.fromstring(z.read('META-INF/container.xml'))
 opf=next(e.attrib['full-path'] for e in container.iter() if e.tag.endswith('rootfile'))
 root=ET.fromstring(z.read(opf));base=posixpath.dirname(opf)
 items={e.attrib['id']:e.attrib for e in root.iter() if e.tag.endswith('}item')}
 for item in items.values():assert posixpath.join(base,item['href']) in files,item
 spine=[e.attrib['idref'] for e in root.iter() if e.tag.endswith('}itemref')]
 assert len(spine)>=19,len(spine)
 xhtml=[p for p in files if p.endswith('.xhtml')]
 for p in xhtml:
  node=ET.fromstring(z.read(p))
  for e in node.iter():
   for attr in ('href','src'):
    href=e.get(attr,'')
    if not href or re.match(r'^[a-z]+:',href):continue
    target=href.split('#')[0]
    if target:assert posixpath.normpath(posixpath.join(posixpath.dirname(p),target)) in files,(p,href)
 text=''.join(''.join(ET.fromstring(z.read(p)).itertext()) for p in xhtml)
 for title in re.findall(r'^# (.+)$',book,re.M):assert title in text,title
 assert '你好，Kubernetes！' in text
 assert 'livenessProbe:' in text
 print(f'PASS: {len(xhtml)} XHTML files; {len(spine)} spine entries; 14 chapters; all chapter titles, local links, XML and required content checked.')
print(f'PASS: {len(sources)} retrieved official source records; no failed retrievals.')
