"""Build the Cardio-Pulm 1 multiple-choice page.

cards.json       the flashcard deck (lessons -> cards with q, a, more, figs, hy)
distractors.json "<lesson n>-<card index>" -> three written wrong choices (two are used)
template.html    page shell; __DATA__ is replaced with the question data

Writes body.html (page content only, for publishing as an artifact) and
index.html (the same page wrapped in a full HTML document, for GitHub Pages).
Choice order is fixed per question (seeded by its id) so it never moves between visits.
"""
import json, hashlib, os, re

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
d = json.load(open(f'{here}/cards.json'))
dis = json.load(open(f'{here}/distractors.json'))
TAG = re.compile(r'<[^>]+>')


def two_wrong(answer, wrong):
    """Keep the two wrong choices closest in length to the answer, so length gives nothing away."""
    n = len(TAG.sub('', answer))
    return sorted(wrong, key=lambda w: abs(len(TAG.sub('', w)) - n))[:2]


lessons = []
for l in d['lessons']:
    secs = []
    for j, c in enumerate(l['cards']):
        cid = f"{l['n']}-{j}"
        h = int(hashlib.sha1(cid.encode()).hexdigest(), 16)
        k = h % 3
        wrong = two_wrong(c['a'], dis[cid])
        if (h >> 8) & 1:
            wrong.reverse()
        q = {'id': cid, 'q': c['q'], 'o': wrong[:k] + [c['a']] + wrong[k:], 'k': k}
        for key in ('more', 'figs', 'hy'):
            if c.get(key):
                q[key] = c[key]
        if not secs or secs[-1]['t'] != c['topic']:
            secs.append({'t': c['topic'], 'qs': []})
        secs[-1]['qs'].append(q)
    lessons.append({'n': l['n'], 'key': l['key'], 't': l['t'], 'sub': l['sub'], 'cp2': l['cp2'], 'secs': secs})

used = {f for l in d['lessons'] for c in l['cards'] for f in c.get('figs', [])}
data = {'lessons': lessons, 'figs': {k: v for k, v in d['figs'].items() if k in used}}
js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
body = open(f'{here}/template.html').read().replace('__DATA__', js)
open(f'{here}/body.html', 'w').write(body)
head = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);'
        'padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}'
        '[hidden]{display:none!important}</style>\n')
page = head + body.replace('<div class="bar">', '</head><body>\n<div class="bar">', 1) + '\n</body></html>\n'
open(f'{root}/index.html', 'w').write(page)
print(sum(len(s['qs']) for l in lessons for s in l['secs']), 'questions,', len(used), 'pictures,', len(page.encode()), 'bytes')
