from pathlib import Path
import yaml, markdown, datetime
from .utils import slugify

MD_EXTS = ['extra','toc','tables','fenced_code']

def parse_md(path: Path):
    raw = path.read_text(encoding='utf-8')
    fm = {}
    body = raw
    if raw.startswith('---'):
        parts = raw.split('\n', 1)[1].split('---', 1)
        if len(parts) == 2:
            fm_text, body = parts[0], parts[1]
            fm = yaml.safe_load(fm_text) or {}
    html = markdown.markdown(body, extensions=MD_EXTS)
    fm.setdefault('title', path.stem.replace('-', ' ').title())
    fm.setdefault('date', datetime.datetime.utcnow().strftime("%Y-%m-%d"))
    slug = fm.get('slug') or slugify(fm['title'])
    return {'meta': fm, 'html': html, 'slug': slug}

def load_posts(content_dir: str):
    posts = []
    pdir = Path(content_dir) / "posts"
    if not pdir.exists():
        return posts
    for p in sorted(pdir.glob("*.md")):
        d = parse_md(p)
        d['path'] = p
        posts.append(d)
    posts.sort(key=lambda x: x['meta'].get('date', ''), reverse=True)
    return posts
