"""Preserve source formula identity and typeset it locally with KaTeX/MathML."""
from pathlib import Path
import html
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MATH = re.compile(r'(?<!\\)\$\$(.+?)\$\$|(?<!\\)\$([^$]+?)\$|\\\[(.+?)\\\]|\\\((.+?)\\\)', re.S)


def key(value):
    return re.sub(r'\s+', '', value).casefold()


def tex(match):
    return next(x for x in match.groups() if x is not None).strip()


def plausible(value, registry):
    if value.startswith('defs"') or '"properties"' in value:
        return False
    return key(value) in registry or bool(re.search(r'\\[A-Za-z]+|[_^=<>]|^[A-Za-z]$', value))


def build_cache():
    if not (ROOT / '.cache/reader-tools/node_modules/katex/package.json').exists():
        raise RuntimeError('Missing local KaTeX. Run: npm install --prefix .cache/reader-tools --no-audit --no-fund katex@0.19.1')
    formulas = set()
    for path in (ROOT / 'translations/fulltext').glob('*/bilingual.json'):
        visual_path = path.parent / 'visuals.json'
        visual = json.loads(visual_path.read_text()) if visual_path.exists() else {}
        formulas.update(item['tex'] for item in visual.get('math', {}).values())
        for unit in json.loads(path.read_text())['units']:
            for field in ['en', 'zh']:
                formulas.update(tex(m) for m in MATH.finditer(unit.get(field, '')) if plausible(tex(m), visual.get('math', {})))
    proc = subprocess.run(['node', str(ROOT / 'scripts/render_reader_math.cjs')], input=json.dumps(sorted(formulas)), text=True, capture_output=True, check=True)
    cache = json.loads(proc.stdout)
    dist = ROOT / '.cache/reader-tools/node_modules/katex/dist'
    target = ROOT / 'translations/fulltext/assets/katex'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dist / 'katex.min.css', target / 'katex.min.css')
    shutil.copytree(dist / 'fonts', target / 'fonts', dirs_exist_ok=True)
    shutil.copy2(dist.parent / 'LICENSE', target / 'LICENSE')
    (target / 'SOURCE.txt').write_text('KaTeX, MIT license.\nhttps://github.com/KaTeX/KaTeX\nInstalled version: ' + json.loads((dist.parent / 'package.json').read_text())['version'] + '\n')
    return cache


class MathRenderer:
    def __init__(self, visual, cache):
        self.registry = visual.get('math', {})
        self.cache = cache
        self.restored = []
        self.appended = []
        self.errors = []

    def render_tex(self, value):
        original = self.registry.get(key(value))
        value = original['tex'] if original else value
        result = self.cache.get(value, {})
        if result.get('html'):
            return result['html']
        if original:
            # Preserve the publisher's MathML for constructs KaTeX lacks.
            return re.sub(r'\s+id="[^"]*"', '', original['html'])
        self.errors.append(value)
        return '<span class="math-unresolved">公式待核对；请查看本页原文</span>'

    def restore(self, unit, value):
        source = [tex(m) for m in MATH.finditer(unit['en']) if key(tex(m)) in self.registry]
        matches = [m for m in MATH.finditer(value) if plausible(tex(m), self.registry)]
        if source and len(source) == len(matches):
            for match, canonical in reversed(list(zip(matches, source))):
                value = value[:match.start()] + '$' + canonical + '$' + value[match.end():]
            self.restored.append(unit['id'])
            return value, ''
        seen = {key(tex(m)) for m in matches}
        missing = list(dict.fromkeys(s for s in source if key(s) not in seen))
        if not missing:
            return value, ''
        self.appended.append(dict(id=unit['id'], formulas=missing))
        return value, '<details class="restored-math"><summary>译文遗漏的变量或原式（按原文补充）</summary><p>' + '； '.join(self.render_tex(s) for s in missing) + '</p></details>'

    def inline(self, value):
        protected = {}
        for original in self.registry.values():
            if '$' not in original['tex']:
                continue
            literal = '$' + original['tex'] + '$'
            if literal in value:
                token = 'READERMATHPROTECTED' + str(len(protected)) + 'TOKEN'
                protected[token] = self.render_tex(original['tex'])
                value = value.replace(literal, token)
        parts = []
        offset = 0
        for match in MATH.finditer(value):
            formula = tex(match)
            if not plausible(formula, self.registry):
                continue
            parts.append(html.escape(value[offset:match.start()]))
            parts.append('<span class="math-inline">' + self.render_tex(formula) + '</span>')
            offset = match.end()
        parts.append(html.escape(value[offset:]))
        rendered = ''.join(parts)
        for token, content in protected.items():
            rendered = rendered.replace(token, content)
        return rendered
