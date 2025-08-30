# build.py — generate blog posts from keywords using OpenAI and write HTML files
from pathlib import Path
import os, json, re, argparse, datetime, html
from slugify import slugify  # pip install python-slugify
try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("pip install openai python-slugify")

ROOT = Path(__file__).parent
SITE = ROOT / "site"
POSTS = SITE / "posts"

BASE_STYLE = """
:root{--brand:#ef4444;--bg:#0b0b0d;--fg:#e8e8ea;--card:#131319;--ring:#27283a}
*{box-sizing:border-box}html,body{margin:0;padding:0}
body{font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif;background:var(--bg);color:var(--fg)}
.container{max-width:940px;margin:0 auto;padding:24px}
.card{background:var(--card);border:1px solid var(--ring);border-radius:16px;padding:20px;margin:16px 0}
.btn{display:inline-block;padding:10px 16px;border-radius:12px;background:var(--brand);color:#fff;font-weight:600;text-decoration:none}
.small{opacity:.8;font-size:.9em}
.disclosure{opacity:.9}
.product-box{border:1px dashed var(--ring);padding:16px;border-radius:12px;margin-top:8px}
"""

INDEX_SHELL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{brand} — Blog</title>
<meta name="description" content="{desc}"/>
<style>{style}</style>
</head><body><div class="container">
<h1>🔥 {brand}</h1>
<p class="card">Fresh posts generated automatically.</p>
<div class="card"><strong>Affiliate Disclosure</strong><br/>
<p class="disclosure small">This site contains affiliate links. We may earn a commission at no extra cost to you.</p></div>
<h2>Latest Posts</h2>
{post_list}
<footer class="small">© {year} {brand}</footer>
</div></body></html>
"""

POST_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — {brand}</title>
<meta name="description" content="{meta_desc}"/>
<link rel="canonical" href="{site_url}/posts/{slug}/"/>
<style>{style}</style>
</head><body><div class="container">
<p><a class="small" href="{base_prefix}/">← Back to Home</a></p>
<article class="card">
<h1>{title}</h1>
<p class="small">Published {date}</p>
{body_html}
<h2>Top Pick</h2>
<div class="product-box">
  <strong>{product_name}</strong>
  <p>{product_blurb} <a href="{aff_url}" rel="sponsored nofollow noopener" target="_blank" class="btn">Check price →</a></p>
</div>
</article>
<footer class="small">© {year} {brand}</footer>
</div>
<script type="application/ld+json">{schema}</script>
</body></html>
"""

def load_keywords(path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [k.strip() for k in data.get("keywords", []) if k.strip()]

def call_openai(keyword, model=None):
    # Uses env vars: OPENAI_API_KEY and optional OPENAI_MODEL
    client = OpenAI()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    prompt = f"""
You are a helpful blogger. Write a concise, useful article.

Keyword: "{keyword}"

Return strict JSON with fields:
- title (<=65 chars)
- meta_description (<=155 chars)
- sections: array of {{heading, paragraphs:[string,...]}}
- faq: array of {{q,a}}
- product_name (non-brand-generic ok)
- product_blurb (one sentence)
"""
    # chat.completions for broad compatibility
    res = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":"Write helpful, factual, concise blog content."},
                  {"role":"user","content":prompt}],
        temperature=0.7
    )
    text = res.choices[0].message.content.strip()
    # try to extract JSON
    m = re.search(r"\{.*\}\s*$", text, re.S)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        # fallback minimal content
        return {
            "title": keyword.title(),
            "meta_description": f"Guide about {keyword}.",
            "sections":[{"heading":"Overview","paragraphs":[f"Quick guide to {keyword}."]}],
            "faq":[],
            "product_name":"Sample Product",
            "product_blurb":"A reliable pick for most people."
        }

def render_sections(sections):
    out = []
    for s in sections:
        h = html.escape(s.get("heading",""))
        out.append(f"<h2>{h}</h2>")
        for p in s.get("paragraphs",[]):
            out.append(f"<p>{html.escape(p)}</p>")
    return "\n".join(out)

def render_faq(faq):
    if not faq: return ""
    out = ["<h2>FAQ</h2>"]
    for item in faq:
        out.append(f"<h3>{html.escape(item.get('q',''))}</h3>")
        out.append(f"<p>{html.escape(item.get('a',''))}</p>")
    return "\n".join(out)

def write_post(brand, site_url, base_prefix, keyword, data, amazon_tag):
    slug = slugify(keyword)
    folder = POSTS / slug
    folder.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    body = render_sections(data.get("sections",[])) + render_faq(data.get("faq",[]))
    schema = json.dumps({
        "@context":"https://schema.org",
        "@type":"Article",
        "headline": data.get("title", keyword.title()),
        "datePublished": today,
        "mainEntityOfPage": f"{site_url}/posts/{slug}/"
    })

    aff_url = f"https://www.amazon.com/dp/B000000000?tag={amazon_tag}"
    html_out = POST_TPL.format(
        title=data.get("title", keyword.title()),
        brand=brand,
        meta_desc=data.get("meta_description",""),
        site_url=site_url.rstrip("/"),
        slug=slug,
        base_prefix=base_prefix,
        style=BASE_STYLE,
        date=today,
        body_html=body,
        product_name=data.get("product_name","Our Pick"),
        product_blurb=data.get("product_blurb","Solid choice for most."),
        aff_url=aff_url,
        schema=schema,
        year=datetime.date.today().year
    )
    (folder / "index.html").write_text(html_out, encoding="utf-8")
    return slug, data.get("title", keyword.title())

def rebuild_index(brand, desc, site_url, base_prefix):
    # list posts
    links = []
    if POSTS.exists():
        for p in sorted(POSTS.iterdir()):
            if (p / "index.html").exists():
                slug = p.name
                title = (p / "index.html").read_text(encoding="utf-8")
                m = re.search(r"<h1>(.*?)</h1>", title)
                title = m.group(1) if m else slug.replace("-", " ").title()
                links.append(f'<p>• <a href="{base_prefix}/posts/{slug}/">{title}</a></p>')
    post_list = "\n".join(links) if links else "<p>No posts yet.</p>"
    html_out = INDEX_SHELL.format(
            brand=brand, desc=desc, style=BASE_STYLE,
            post_list=post_list, year=datetime.date.today().year)
    (SITE / "index.html").write_text(html_out, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", default="My Test Blog")
    ap.add_argument("--site_url", required=True, help="https://USERNAME.github.io/REPO")
    ap.add_argument("--amazon_tag", default="yourtag-20")
    ap.add_argument("--keywords_file", default="datakeywords.json")
    ap.add_argument("--limit", type=int, default=3, help="how many keywords to process")
    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Missing OPENAI_API_KEY env var.")

    # base prefix for project pages
    base_prefix = "/" + args.site_url.rstrip("/").split("github.io/")[-1]
    if base_prefix == "/": base_prefix = ""

    # ensure folders
    (SITE).mkdir(exist_ok=True)
    (POSTS).mkdir(parents=True, exist_ok=True)
    (SITE / ".nojekyll").write_text("\n", encoding="utf-8")

    keywords = load_keywords(ROOT / args.keywords_file)[:args.limit]
    if not keywords:
        print("No keywords found; add some to datakeywords.json")
        return

    for kw in keywords:
        data = call_openai(kw)
        slug, title = write_post(args.brand, args.site_url, base_prefix, kw, data, args.amazon_tag)
        print("✔ Wrote post:", slug, "-", title)

    rebuild_index(args.brand, f"Articles about {', '.join(keywords)}", args.site_url, base_prefix)
    print("✅ Homepage rebuilt.")

if __name__ == "__main__":
    main()
