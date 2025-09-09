import re, os, json, shutil, datetime
from pathlib import Path

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def write_text(p: str, s: str):
    ensure_dir(os.path.dirname(p))
    Path(p).write_text(s, encoding="utf-8")

def slugify(text: str) -> str:
    t = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    t = re.sub(r'\s+', '-', t.strip())
    return t.lower()

def build_stamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

def minify_html(html_str: str) -> str:
    import re
    preserved = {}
    i = 0
    def keep(tag, s):
        nonlocal i
        pat = re.compile(fr"<{tag}[\s\S]*?</{tag}>", re.IGNORECASE)
        def repl(m):
            nonlocal i
            key = f"Â§Â§KEEP{i}Â§Â§"
            preserved[key] = m.group(0)
            i += 1
            return key
        return pat.sub(repl, s)
    s = html_str
    for tag in ["pre","code","script","style"]:
        s = keep(tag, s)
    s = re.sub(r">\s+<", "><", s)
    s = re.sub(r"\s{2,}", " ", s)
    for k,v in preserved.items():
        s = s.replace(k, v)
    return s

def jsonld(data: dict) -> str:
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, default=str) + "</script>\n"

