import json, re, sys
specs = json.load(open(sys.argv[1])); html = sys.argv[2]
t = open(html, encoding='utf8').read()
m = re.search(r'const DATA = (\{.*?\});\n', t); data = json.loads(m.group(1))
sr = {s['id']: s['sr'] for s in specs}
n = 0
for books in data.values():
    for b in books:
        if b['id'] in sr and not (b.get('spine') or '').startswith('books/') or (b['id'] in sr and b.get('spine','').endswith(b['id'] + '-spine.jpg')):
            if b['id'] in sr:
                b['spine'] = 'books/%s-spine.jpg' % b['id']; b['sr'] = sr[b['id']]; n += 1
t = t[:m.start(1)] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + t[m.end(1):]
open(html, 'w', encoding='utf8').write(t); print('spines set', n)
