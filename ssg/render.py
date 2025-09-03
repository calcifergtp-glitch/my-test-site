import os, re, json, html, datetime
from pathlib import Path
from typing import List, Dict

from .themes import THEMES
from .templates import INDEX_SHELL, POST_TPL, PAGE_TPL

# ---------------------------
# Utilities
# ---------------------------

def escape(s: str) -> str:
    return html.escape(s or "")

# Exported slugify (build.py imports this from here)
try:
    from slugify import slugify as slugify_lib
    def slugify(s: str) -> str:
        return slugify_lib(s or "")
except Exception:
    def slugify(s: str) -> str:
        s = (s or "").lower()
        s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
        return s or "post"

def prepare_dirs(ROOT: Path):
    """Ensure site/ posts/ data/ exist and .nojekyll is present."""
    SITE = ROOT / "site"
    POSTS = SITE / "posts"
    DATA = ROOT / "data"
    SITE.mkdir(exist_ok=True)
    POSTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(exist_ok=True)
    (SITE / ".nojekyll").write_text("\n", encoding="utf-8")
    return SITE, POSTS, DATA

def hero_url(slug: str, w=1200, h=630) -> str:
    return f"https://picsum.photos/seed/{slug}/{w}/{h}"

def card_url(slug: str, w=600, h=338) -> str:
    return f"https://picsum.photos/seed/{slug}-card/{w}/{h}"

# ---------------------------
# Analytics
# ---------------------------

def analytics_snippet(analytics: str) -> str:
    if not analytics:
        return ""
    if analytics.startswith("plausible:"):
        domain = analytics.split(":", 1)[1].strip()
        return f'<script defer data-domain="{escape(domain)}" src="https://plausible.io/js/script.js"></script>'
    if analytics.startswith("ga4:"):
        mid = analytics.split(":", 1)[1].strip()
        return (
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={escape(mid)}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js', new Date());gtag('config','{escape(mid)}');</script>"
        )
    return ""

# ---------------------------
# Render helpers
# ---------------------------

def render_sections(sections: list) -> str:
    out = []
    for s in sections or []:
        h = escape(s.get("heading", ""))
        if h:
            out.append(f'<h2 class="title is-4">{h}</h2>')
        for p in s.get("paragraphs", []) or []:
            out.append(f"<p>{escape(p)}</p>")
    return "\n".join(out)

def render_faq(faq: list) -> str:
    if not faq:
        return ""
    out = ['<h2 class="title is-4">FAQ</h2>']
    for item in faq:
        q = escape(item.get("q", ""))
        a = escape(item.get("a", ""))
        if q:
            out.append(f"<h3 class='title is-6'>{q}</h3>")
            out.append(f"<p>{a}</p>")
    return "\n".join(out)

def render_tags(base_prefix: str, tags: List[str]) -> str:
    tags = [t for t in (tags or []) if t]
    if not tags:
        return '<span class="tag is-light">none</span>'
    return " ".join(
        f'<a class="tag is-link is-light" href="{base_prefix}/tag/{slugify(t)}/">{escape(t)}</a>'
        for t in tags
    )

def render_related(base_prefix: str, related: List[Dict]) -> str:
    if not related:
        return ""
    items = "\n".join(
        f'<li><a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></li>'
        for m in related
    )
    return f'<div class="box"><h2 class="title is-5">Related posts</h2><ul>{items}</ul></div>'

def render_comparison_table(base_prefix: str, items: list, amazon_tag: str) -> str:
    if not items:
        return ""
    rows = []
    for it in items[:5]:
        name = escape(it.get("name", "Product"))
        blurb = escape(it.get("blurb", ""))
        pros = ", ".join(escape(p) for p in (it.get("pros") or []))
        cons = ", ".join(escape(c) for c in (it.get("cons") or []))
        asin = (it.get("asin") or "B000000000").strip()
        url = f"https://www.amazon.com/dp/{asin}?tag={amazon_tag}"
        rows.append(
            f"""
<tr>
  <td><strong>{name}</strong><br/><small>{blurb}</small></td>
  <td>{pros or '-'}</td>
  <td>{cons or '-'}</td>
  <td><a class="button is-link is-light is-small" href="{url}" target="_blank" rel="sponsored nofollow noopener">Check price →</a></td>
</tr>"""
        )
    return f"""
<h2 class="title is-5">Comparison Table</h2>
<div class="table-container">
<table class="table is-striped is-fullwidth">
  <thead><tr><th>Product</th><th>Pros</th><th>Cons</th><th></th></tr></thead>
  <tbody>
  {''.join(rows)}
  </tbody>
</table>
</div>
"""

# ---------------------------
# Writers
# ---------------------------

def write_post(
    brand: str,
    site_url: str,
    base_prefix: str,
    payload: Dict,
    amazon_tag: str,
    theme: Dict,
    related_list: List[Dict],
    analytics_html: str,
) -> str:
    slug = payload["slug"]
    data = payload["data"]
    category = payload["category"]
    tags = payload["tags"]
    title = payload["title"]

    today = datetime.date.today().isoformat()
    body = render_sections(data.get("sections", [])) + render_faq(data.get("faq", []))
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "datePublished": today,
        "mainEntityOfPage": f"{site_url.rstrip('/')}/posts/{slug}/",
    }

    # Simple affiliate CTA + comparison table
    aff_url = f"https://www.amazon.com/dp/B000000000?tag={amazon_tag}"
    comparison_table = render_comparison_table(base_prefix, data.get("comparison", []), amazon_tag)

    html_out = POST_TPL.format(
        title=escape(title),
        brand=escape(brand),
        meta_desc=escape(data.get("meta_description", "")),
        site_url=site_url.rstrip("/"),
        slug=slug,
        base_prefix=base_prefix,
        theme_css=THEMES["bulma"]["css"],  # Post pages use Bulma for consistency
        analytics=analytics_html,
        date=today,
        hero_img=hero_url(slug),
        body_html=body,
        product_name=escape(data.get("product_name", "Our Pick")),
        product_blurb=escape(data.get("product_blurb", "Solid choice for most.")),
        aff_url=aff_url,
        comparison_table=comparison_table,
        schema=json.dumps(schema),
        year=datetime.date.today().year,
        container_open=THEMES["bulma"]["container_open"],
        container_close=THEMES["bulma"]["container_close"],
        category=escape(category),
        cat_slug=slugify(category),
        tags_html=render_tags(base_prefix, tags),
        related_html=render_related(base_prefix, related_list),
    )

    ROOT = Path(__file__).resolve().parents[1]
    POSTS = ROOT / "site" / "posts"
    folder = POSTS / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(html_out, encoding="utf-8")
    return slug

def write_standard_pages(
    brand: str,
    site_url: str,
    base_prefix: str,
    theme: Dict,
    analytics_html: str,
    audience: str = "readers",
    domain: str = "example.com",
):
    PAGES = {
        "about": {
            "title": "About",
            "body": f"<p><strong>{escape(brand)}</strong> provides practical guides, reviews, and tips. Our mission is to help {escape(audience)} make informed decisions.</p>",
        },
        "contact": {
            "title": "Contact Us",
            "body": f"<p>Email: contact@{escape(domain)}</p><p>We value transparency. Reach out with any questions.</p>",
        },
        "privacy": {
            "title": "Privacy Notice",
            "body": "<p>This site may use cookies for analytics. By continuing, you accept our use of cookies.</p>",
        },
        "disclosure": {
            "title": "Affiliate Disclosure",
            "body": "<p>Disclosure: As an Amazon Associate we earn from qualifying purchases.</p>",
        },
    }
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    for slug_name, meta in PAGES.items():
        html_out = PAGE_TPL.format(
            title=meta["title"],
            brand=escape(brand),
            site_url=site_url.rstrip("/"),
            slug=slug_name,
            theme_css=THEMES["bulma"]["css"],
            analytics=analytics_html,
            base_prefix=base_prefix,
            body_html=meta["body"],
            year=datetime.date.today().year,
            container_open=THEMES["bulma"]["container_open"],
            container_close=THEMES["bulma"]["container_close"],
        )
        (SITE / f"{slug_name}.html").write_text(html_out, encoding="utf-8")

def rebuild_index(
    brand: str,
    desc: str,
    site_url: str,
    base_prefix: str,
    theme: Dict,
    posts_meta: List[Dict],
    analytics_html: str,
):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"

    cards = []
    for m in posts_meta:
        slug = m["slug"]
        title = escape(m["title"])
        cat = escape(m["category"])
        cat_slug = slugify(m["category"])
        img = card_url(slug)
        cards.append(
            f"""
<div class="column is-half">
  <div class="card">
    <div class="card-image">
      <figure class="image">
        <img src="{img}" alt="{title}" loading="lazy">
      </figure>
    </div>
    <div class="card-content">
      <p class="tags">
        <span class="tag is-info is-light">Category</span>
        <a class="tag is-link is-light" href="{base_prefix}/category/{cat_slug}/">{cat}</a>
      </p>
      <p class="title is-5"><a href="{base_prefix}/posts/{slug}/">{title}</a></p>
      <p><a class="button is-link is-light is-small" href="{base_prefix}/posts/{slug}/">Read →</a></p>
    </div>
  </div>
</div>
"""
        )
    post_cards = "\n".join(cards) if cards else "<p>No posts yet.</p>"

    # Sidebar: categories + tag cloud
    cat_counts: Dict[str, int] = {}
    tag_counts: Dict[str, int] = {}
    for m in posts_meta:
        cat_counts[m["category"]] = cat_counts.get(m["category"], 0) + 1
        for t in m["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    category_list = (
        "\n".join(
            f'<p>• <a href="{base_prefix}/category/{slugify(c)}/">{escape(c)}</a> <span class="tag is-light">{n}</span></p>'
            for c, n in sorted(cat_counts.items(), key=lambda x: (-x[1], x[0].lower()))
        )
        or "<p><em>None yet</em></p>"
    )

    tag_cloud = (
        "\n".join(
            f'<a class="tag is-link is-light" href="{base_prefix}/tag/{slugify(t)}/">{escape(t)} ({n})</a>'
            for t, n in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0].lower()))
        )
        or '<span class="tag is-light">none</span>'
    )

    html_out = INDEX_SHELL.format(
        brand=escape(brand),
        desc=escape(desc),
        site_url=site_url.rstrip("/"),
        theme_css=theme["css"],
        analytics=analytics_html,
        container_open=theme["container_open"],
        container_close=theme["container_close"],
        post_cards=post_cards,
        category_list=category_list,
        tag_cloud=tag_cloud,
        year=datetime.date.today().year,
        base_prefix=base_prefix,
        search_bar=_search_bar_html(base_prefix),
    )
    (SITE / "index.html").write_text(html_out, encoding="utf-8")

def _search_bar_html(base_prefix: str) -> str:
    return f"""
<div class="field has-addons" style="margin:1rem 0">
  <div class="control is-expanded">
    <input id="q" class="input" type="search" placeholder="Search posts…" aria-label="Search" />
  </div>
  <div class="control">
    <button id="qbtn" class="button is-link">Search</button>
  </div>
</div>
<div id="qresults" class="content"></div>
<script>
(function() {{
  const q = document.getElementById('q');
  const btn = document.getElementById('qbtn');
  const out = document.getElementById('qresults');
  let idx = [];
  fetch('{base_prefix}/search.json').then(r => r.json()).then(d => idx = d);

  function run() {{
    const term = (q.value||'').toLowerCase().trim();
    if (!term) {{ out.innerHTML = ''; return; }}
    const parts = term.split(/\\s+/);
    const res = idx.map(it => {{
      let score = 0;
      const hay = (it.title + ' ' + it.category + ' ' + it.tags.join(' ') + ' ' + it.text).toLowerCase();
      for (const p of parts) if (hay.includes(p)) score += 1;
      return [score, it];
    }}).filter(x => x[0] > 0).sort((a,b) => b[0]-a[0]).slice(0,20).map(x => x[1]);
    out.innerHTML = res.length
      ? '<ul>' + res.map(it => `<li><a href="{base_prefix}/posts/${{it.slug}}/">${{it.title}}</a> <span class="tag is-light">${{it.category}}</span></li>`).join('') + '</ul>'
      : '<p><em>No results</em></p>';
  }}
  btn.addEventListener('click', run);
  q.addEventListener('keydown', e => {{ if (e.key === 'Enter') run(); }});
}})();
</script>
"""

def write_sitemap_and_robots(site_url: str, posts_meta: List[Dict]):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    site_url = site_url.rstrip("/")

    urls = [f"{site_url}/"]
    # Posts
    for m in posts_meta:
        urls.append(f"{site_url}/posts/{m['slug']}/")
    # Categories
    cats = sorted({m["category"] for m in posts_meta})
    for c in cats:
        urls.append(f"{site_url}/category/{slugify(c)}/")
    # Tags
    tags = sorted({t for m in posts_meta for t in m["tags"]})
    for t in tags:
        urls.append(f"{site_url}/tag/{slugify(t)}/")

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    out += [f"  <url><loc>{u}</loc></url>" for u in urls]
    out.append("</urlset>\n")
    (SITE / "sitemap.xml").write_text("\n".join(out), encoding="utf-8")

    robots = f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n"
    (SITE / "robots.txt").write_text(robots, encoding="utf-8")

def build_category_pages(
    brand: str,
    site_url: str,
    base_prefix: str,
    theme: Dict,
    posts_meta: List[Dict],
    analytics_html: str,
):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    root = SITE / "category"

    by_cat: Dict[str, List[Dict]] = {}
    for m in posts_meta:
        by_cat.setdefault(m["category"], []).append(m)

    for cat, items in by_cat.items():
        folder = root / slugify(cat)
        folder.mkdir(parents=True, exist_ok=True)

        links = "\n".join(
            f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>'
            for m in sorted(items, key=lambda x: x["title"].lower())
        )
        body = f"<h2 class='title is-4'>{escape(cat)}</h2>{links}"

        html_out = PAGE_TPL.format(
            title=f"{cat} — Category",
            brand=escape(brand),
            site_url=site_url.rstrip("/"),
            slug="",
            theme_css=theme["css"],
            analytics=analytics_html,
            base_prefix=base_prefix,
            body_html=body,
            year=datetime.date.today().year,
            container_open=theme["container_open"],
            container_close=theme["container_close"],
        )
        (folder / "index.html").write_text(html_out, encoding="utf-8")

def build_tag_pages(
    brand: str,
    site_url: str,
    base_prefix: str,
    theme: Dict,
    posts_meta: List[Dict],
    analytics_html: str,
):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    root = SITE / "tag"

    by_tag: Dict[str, List[Dict]] = {}
    for m in posts_meta:
        for t in m["tags"]:
            by_tag.setdefault(t, []).append(m)

    for t, items in by_tag.items():
        folder = root / slugify(t)
        folder.mkdir(parents=True, exist_ok=True)

        links = "\n".join(
            f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>'
            for m in sorted(items, key=lambda x: x["title"].lower())
        )
        body = f"<h2 class='title is-4'>Tag: {escape(t)}</h2>{links}"

        html_out = PAGE_TPL.format(
            title=f"{t} — Tag",
            brand=escape(brand),
            site_url=site_url.rstrip("/"),
            slug="",
            theme_css=theme["css"],
            analytics=analytics_html,
            base_prefix=base_prefix,
            body_html=body,
            year=datetime.date.today().year,
            container_open=theme["container_open"],
            container_close=theme["container_close"],
        )
        (folder / "index.html").write_text(html_out, encoding="utf-8")

def write_search_index(posts_meta: List[Dict]):
    """Create search.json with quick text for client-side search."""
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    POSTS = SITE / "posts"

    items = []
    for m in posts_meta:
        path = POSTS / m["slug"] / "index.html"
        if not path.exists():
            continue
        html_txt = path.read_text(encoding="utf-8")

        # crude extraction: first paragraph + H2s
        m1 = re.search(r"<p>(.*?)</p>", html_txt, re.S)
        snippet = (m1.group(1) if m1 else "")[:400]
        heads = " ".join(h.strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html_txt, re.S))

        # strip tags
        def strip_tags(s: str) -> str:
            return re.sub(r"<.*?>", " ", s or "")

        items.append(
            {
                "slug": m["slug"],
                "title": re.sub(r"\s+", " ", strip_tags(m["title"])).strip(),
                "category": m["category"],
                "tags": m["tags"],
                "text": re.sub(r"\s+", " ", strip_tags(heads + " " + snippet)).strip(),
            }
        )

    (SITE / "search.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
