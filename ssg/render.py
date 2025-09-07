import os, re, json, html, datetime, math
from pathlib import Path
from typing import List, Dict

from .themes import THEMES
from .templates import INDEX_SHELL, POST_TPL, PAGE_TPL, NOT_FOUND_TPL
from .monetize import product_box, cta_banner, pros_cons, comparison_rows
from .analytics import write_telemetry_js

PAGE_SIZE = 6  # posts per page on home/category/tag

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

def paginate(items: List[Dict], page: int, size: int = PAGE_SIZE):
    total = max(1, math.ceil(len(items) / size))
    page = max(1, min(page, total))
    start = (page - 1) * size
    end = start + size
    return items[start:end], page, total

def pagination_html(base_prefix: str, current: int, total: int, base_path: str):
    if total <= 1: return ""
    # base_path: "" for home, "category/cat-slug", "tag/tag-slug"
    def url_for(n):
        if base_path == "":
            return f"{base_prefix}/" if n == 1 else f"{base_prefix}/page/{n}/"
        else:
            return f"{base_prefix}/{base_path}/" if n == 1 else f"{base_prefix}/{base_path}/page/{n}/"

    links = []
    if current > 1:
        links.append(f'<li><a class="pagination-previous" href="{url_for(current-1)}">Previous</a></li>')
    if current < total:
        links.append(f'<li><a class="pagination-next" href="{url_for(current+1)}">Next</a></li>')

    pages = []
    for n in range(1, total + 1):
        cls = "pagination-link is-current" if n == current else "pagination-link"
        pages.append(f'<li><a class="{cls}" href="{url_for(n)}">{n}</a></li>')

    return f"""
<nav class="pagination is-centered" role="navigation" aria-label="pagination">
  <ul class="pagination-list">
    {''.join(pages)}
  </ul>
  <ul class="pagination-list">
    {''.join(links)}
  </ul>
</nav>
"""

# ---------------------------
# Analytics
# ---------------------------

def analytics_snippet(analytics: str) -> str:
    """Accepts 'plausible:domain' or 'ga4:G-XXXX' or 'plausible:domain,ga4:G-XXXX'."""
    if not analytics:
        return ""
    parts = [p.strip() for p in analytics.split(",") if p.strip()]
    out = []
    for p in parts:
        if p.startswith("plausible:"):
            domain = p.split(":", 1)[1].strip()
            out.append(f'<script defer data-domain="{escape(domain)}" src="https://plausible.io/js/script.js"></script>')
        elif p.startswith("ga4:"):
            mid = p.split(":", 1)[1].strip()
            out.append(
                f'<script async src="https://www.googletagmanager.com/gtag/js?id={escape(mid)}"></script>'
                f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
                f"gtag('js', new Date());gtag('config','{escape(mid)}');</script>"
            )
    return "\n".join(out)

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

def render_comparison_table(items, amazon_tag):
    if not items:
        return ""
    rows = comparison_rows(items, amazon_tag)
    return f"""
<h2 class="title is-5">Comparison Table</h2>
<div class="table-container">
<table class="table is-striped is-fullwidth">
  <thead><tr><th>Product</th><th>Pros</th><th>Cons</th><th></th></tr></thead>
  <tbody>
  {rows}
  </tbody>
</table>
</div>
"""

def render_sources(sources: list) -> str:
    if not sources:
        return ""
    lis = []
    for s in sources:
        title = escape(s.get("title","Source"))
        url = (s.get("url") or "").strip()
        if url.startswith("http"):
            lis.append(f'<li><a href="{escape(url)}" target="_blank" rel="nofollow noopener">{title}</a></li>')
        else:
            lis.append(f"<li>{title}</li>")
    return f"<h2 class='title is-5'>Further reading</h2><ul>{''.join(lis)}</ul><p><small>AI-suggested references. Verify details with primary sources.</small></p>"

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

    # Inline monetization
    aff_url = f"https://www.amazon.com/dp/B000000000?tag={amazon_tag}"
    inline_cta = cta_banner("Our top pick is in stock with fast shipping.", aff_url)
    top_pick_box = product_box(data.get("product_name","Our Pick"), data.get("product_blurb","Solid choice for most."), aff_url)

    body_parts = []
    if data.get("summary"):
        body_parts.append(f"<p><em>{escape(data['summary'])}</em></p>")
    body_parts.append(render_sections(data.get("sections", [])))
    body_parts.append(render_faq(data.get("faq", [])))
    body = "\n".join([b for b in body_parts if b])

    sources_html = render_sources(data.get("sources", []))
    comparison_table = render_comparison_table(data.get("comparison", []), amazon_tag)

    # In-text related: first two related links OR internal_topics hints
    intext_related = ""
    links = []
    for r in related_list[:2]:
        links.append(f'<a href="{base_prefix}/posts/{r["slug"]}/">{escape(r["title"])}</a>')
    if data.get("internal_topics"):
        hints = ", ".join([escape(x) for x in data["internal_topics"][:3]])
        links.append(f"<span>(You may also like: {hints})</span>")
    if links:
        intext_related = f'<p><em>Related reading:</em> ' + " • ".join(links) + '</p>'

    # Author box
    a_name = escape(payload.get("author_name") or "Staff Writer")
    a_bio = escape(payload.get("author_bio") or "")
    a_url = (payload.get("author_url") or "").strip()
    author_link = f'• <a href="{escape(a_url)}" target="_blank" rel="nofollow noopener">Profile</a>' if a_url else ""
    author_html = f"{a_name}"
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "datePublished": today,
        "mainEntityOfPage": f"{site_url.rstrip('/')}/posts/{slug}/",
        "author": {"@type": "Person", "name": a_name} if a_name else {"@type": "Organization", "name": brand}
    }

    html_out = POST_TPL.format(
        title=escape(title),
        brand=escape(brand),
        meta_desc=escape(data.get("meta_description", "")),
        site_url=site_url.rstrip("/"),
        slug=slug,
        base_prefix=base_prefix,
        theme_css=THEMES["bulma"]["css"],  # keep post page on Bulma
        analytics=analytics_html,
        date=today,
        hero_img=hero_url(slug),
        body_html=body,
        inline_cta=inline_cta,
        intext_related=intext_related,
        sources_html=sources_html,
        top_pick_box=top_pick_box,
        comparison_table=comparison_table,
        schema=json.dumps(schema),
        year=datetime.date.today().year,
        container_open=THEMES["bulma"]["container_open"],
        container_close=THEMES["bulma"]["container_close"],
        category=escape(category),
        cat_slug=slugify(category),
        tags_html=render_tags(base_prefix, tags),
        related_html=render_related(base_prefix, related_list),
        author_name=a_name,
        author_bio=a_bio,
        author_link=author_link,
    )

    ROOT = Path(__file__).resolve().parents[1]
    POSTS = ROOT / "site" / "posts"
    folder = POSTS / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(html_out, encoding="utf-8")
    return slug

def write_standard_pages(brand, site_url, base_prefix, theme, analytics_html, audience="readers", domain="example.com"):
    PAGES = {
        "about": {"title": "About", "body": f"<p><strong>{escape(brand)}</strong> provides practical guides, reviews, and tips. Our mission is to help {escape(audience)} make informed decisions.</p>"},
        "contact": {"title": "Contact Us", "body": f"<p>Email: contact@{escape(domain)}</p><p>We value transparency. Reach out with any questions.</p>"},
        "privacy": {"title": "Privacy Notice", "body": "<p>This site may use cookies for analytics. By continuing, you accept our use of cookies.</p>"},
        "disclosure": {"title": "Affiliate Disclosure", "body": "<p>Disclosure: As an Amazon Associate we earn from qualifying purchases.</p>"},
    }
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    for slug_name, meta in PAGES.items():
        html_out = PAGE_TPL.format(
            title=meta["title"], brand=escape(brand), site_url=site_url.rstrip("/"),
            slug=slug_name, theme_css=THEMES["bulma"]["css"], analytics=analytics_html,
            base_prefix=base_prefix, body_html=meta["body"], year=datetime.date.today().year,
            container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"],
        )
        (SITE / f"{slug_name}.html").write_text(html_out, encoding="utf-8")

def _cards_for(posts_meta, base_prefix):
    cards = []
    for m in posts_meta:
        slug = m["slug"]; title = escape(m["title"])
        cat = escape(m["category"]); cat_slug = slugify(m["category"])
        img = card_url(slug)
        cards.append(f"""
<div class="column is-half">
  <div class="card">
    <div class="card-image">
      <figure class="image">
        <img src="{img}" alt="{title}" loading="lazy">
      </figure>
    </div>
    <div class="card-content">
      <p class="tags"><span class="tag is-info is-light">Category</span> <a class="tag is-link is-light" href="{base_prefix}/category/{cat_slug}/">{cat}</a></p>
      <p class="title is-5"><a href="{base_prefix}/posts/{slug}/">{title}</a></p>
      <p><a class="button is-link is-light is-small" href="{base_prefix}/posts/{slug}/">Read →</a></p>
    </div>
  </div>
</div>
""")
    return "\n".join(cards) if cards else "<p>No posts yet.</p>"

def rebuild_index(brand, desc, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"

    # Ensure telemetry asset exists
    write_telemetry_js(SITE, base_prefix)

    # Sort newest first by slug name similarity (we do not store dates; keep order as given)
    items = posts_meta[:]  # already ordered by generation; treat as newest first
    # Build page 1
    page_items, page, total = paginate(items, 1, PAGE_SIZE)
    post_cards = _cards_for(page_items, base_prefix)
    pagination = pagination_html(base_prefix, page, total, "")

    # Sidebar lists
    cat_counts, tag_counts = {}, {}
    for m in posts_meta:
        cat_counts[m["category"]] = cat_counts.get(m["category"], 0) + 1
        for t in m["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    category_list = "\n".join(
        f'<p>• <a href="{base_prefix}/category/{slugify(c)}/">{escape(c)}</a> <span class="tag is-light">{n}</span></p>'
        for c, n in sorted(cat_counts.items(), key=lambda x: (-x[1], x[0].lower()))
    ) or "<p><em>None yet</em></p>"

    tag_cloud = "\n".join(
        f'<a class="tag is-link is-light" href="{base_prefix}/tag/{slugify(t)}/">{escape(t)} ({n})</a>'
        for t, n in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0].lower()))
    ) or '<span class="tag is-light">none</span>'

    html_out = INDEX_SHELL.format(
        brand=escape(brand), desc=escape(desc), site_url=site_url.rstrip("/"),
        theme_css=theme["css"], analytics=analytics_html,
        container_open=theme["container_open"], container_close=theme["container_close"],
        post_cards=post_cards, category_list=category_list, tag_cloud=tag_cloud,
        year=datetime.date.today().year, base_prefix=base_prefix,
        search_bar=_search_bar_html(base_prefix),
        pagination=pagination,
    )
    (SITE / "index.html").write_text(html_out, encoding="utf-8")

    # Additional pages /page/2/ ... /page/N/
    if total > 1:
        for n in range(2, total + 1):
            page_items, _, _ = paginate(items, n, PAGE_SIZE)
            post_cards = _cards_for(page_items, base_prefix)
            pagination = pagination_html(base_prefix, n, total, "")
            out = INDEX_SHELL.format(
                brand=escape(brand), desc=escape(desc), site_url=site_url.rstrip("/"),
                theme_css=theme["css"], analytics=analytics_html,
                container_open=theme["container_open"], container_close=theme["container_close"],
                post_cards=post_cards, category_list=category_list, tag_cloud=tag_cloud,
                year=datetime.date.today().year, base_prefix=base_prefix,
                search_bar=_search_bar_html(base_prefix),
                pagination=pagination,
            )
            folder = SITE / "page" / str(n)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(out, encoding="utf-8")

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

  function run(){{
    const term = (q.value||'').toLowerCase().trim();
    if (!term) {{ out.innerHTML = ''; return; }}
    if (window.SS_trackSearch) window.SS_trackSearch(term);
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
    # pagination URLs are optional in sitemap; we skip to keep it small

    for m in posts_meta:
        urls.append(f"{site_url}/posts/{m['slug']}/")
    cats = sorted({m["category"] for m in posts_meta})
    for c in cats:
        urls.append(f"{site_url}/category/{slugify(c)}/")
    tags = sorted({t for m in posts_meta for t in m["tags"]})
    for t in tags:
        urls.append(f"{site_url}/tag/{slugify(t)}/")
    urls.append(f"{site_url}/archive.html")
    urls.append(f"{site_url}/privacy.html")
    urls.append(f"{site_url}/disclosure.html")
    urls.append(f"{site_url}/about.html")
    urls.append(f"{site_url}/contact.html")
    urls.append(f"{site_url}/feed.xml")

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    out += [f"  <url><loc>{u}</loc></url>" for u in urls]
    out.append("</urlset>\n")
    (SITE / "sitemap.xml").write_text("\n".join(out), encoding="utf-8")

    robots = f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n"
    (SITE / "robots.txt").write_text(robots, encoding="utf-8")

def _list_links(items: List[Dict], base_prefix: str):
    return "\n".join(
        f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>'
        for m in items
    )

def build_category_pages(brand, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"; root = SITE / "category"
    by_cat = {}
    for m in posts_meta:
        by_cat.setdefault(m["category"], []).append(m)
    for cat, items in by_cat.items():
        items = items[:]  # newest first as given
        # page 1
        page_items, page, total = paginate(items, 1, PAGE_SIZE)
        folder = root / slugify(cat); folder.mkdir(parents=True, exist_ok=True)
        body = f"<h2 class='title is-4'>{escape(cat)}</h2>" + _list_links(page_items, base_prefix) + pagination_html(base_prefix, page, total, f"category/{slugify(cat)}")
        html_out = PAGE_TPL.format(
            title=f"{cat} — Category", brand=escape(brand), site_url=site_url.rstrip("/"),
            slug="", theme_css=theme["css"], analytics=analytics_html,
            base_prefix=base_prefix, body_html=body, year=datetime.date.today().year,
            container_open=theme["container_open"], container_close=theme["container_close"],
        )
        (folder / "index.html").write_text(html_out, encoding="utf-8")
        # page 2+
        if total > 1:
            for n in range(2, total + 1):
                page_items, _, _ = paginate(items, n, PAGE_SIZE)
                body = f"<h2 class='title is-4'>{escape(cat)}</h2>" + _list_links(page_items, base_prefix) + pagination_html(base_prefix, n, total, f"category/{slugify(cat)}")
                pdir = folder / "page" / str(n); pdir.mkdir(parents=True, exist_ok=True)
                (pdir / "index.html").write_text(PAGE_TPL.format(
                    title=f"{cat} — Category", brand=escape(brand), site_url=site_url.rstrip("/"),
                    slug="", theme_css=theme["css"], analytics=analytics_html,
                    base_prefix=base_prefix, body_html=body, year=datetime.date.today().year,
                    container_open=theme["container_open"], container_close=theme["container_close"],
                ), encoding="utf-8")

def build_tag_pages(brand, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"; root = SITE / "tag"
    by_tag = {}
    for m in posts_meta:
        for t in m["tags"]:
            by_tag.setdefault(t, []).append(m)
    for t, items in by_tag.items():
        items = items[:]
        page_items, page, total = paginate(items, 1, PAGE_SIZE)
        folder = root / slugify(t); folder.mkdir(parents=True, exist_ok=True)
        body = f"<h2 class='title is-4'>Tag: {escape(t)}</h2>" + _list_links(page_items, base_prefix) + pagination_html(base_prefix, page, total, f"tag/{slugify(t)}")
        html_out = PAGE_TPL.format(
            title=f"{t} — Tag", brand=escape(brand), site_url=site_url.rstrip("/"),
            slug="", theme_css=theme["css"], analytics=analytics_html,
            base_prefix=base_prefix, body_html=body, year=datetime.date.today().year,
            container_open=theme["container_open"], container_close=theme["container_close"],
        )
        (folder / "index.html").write_text(html_out, encoding="utf-8")
        if total > 1:
            for n in range(2, total + 1):
                page_items, _, _ = paginate(items, n, PAGE_SIZE)
                body = f"<h2 class='title is-4'>Tag: {escape(t)}</h2>" + _list_links(page_items, base_prefix) + pagination_html(base_prefix, n, total, f"tag/{slugify(t)}")
                pdir = folder / "page" / str(n); pdir.mkdir(parents=True, exist_ok=True)
                (pdir / "index.html").write_text(PAGE_TPL.format(
                    title=f"{t} — Tag", brand=escape(brand), site_url=site_url.rstrip("/"),
                    slug="", theme_css=theme["css"], analytics=analytics_html,
                    base_prefix=base_prefix, body_html=body, year=datetime.date.today().year,
                    container_open=theme["container_open"], container_close=theme["container_close"],
                ), encoding="utf-8")

def write_search_index(posts_meta: List[Dict]):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"; POSTS = SITE / "posts"
    items = []
    for m in posts_meta:
        path = POSTS / m["slug"] / "index.html"
        if not path.exists():
            continue
        html_txt = path.read_text(encoding="utf-8")
        m1 = re.search(r"<p>(.*?)</p>", html_txt, re.S)
        snippet = (m1.group(1) if m1 else "")[:500]
        heads = " ".join(h.strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html_txt, re.S))

        def strip_tags(s: str) -> str:
            return re.sub(r"<.*?>", " ", s or "")

        items.append({
            "slug": m["slug"],
            "title": re.sub(r"\s+", " ", strip_tags(m["title"])).strip(),
            "url": f"/{SITE.name}/posts/{m['slug']}/" if SITE.name else f"/posts/{m['slug']}/",
            "category": m["category"],
            "tags": m["tags"],
            "text": re.sub(r"\s+", " ", strip_tags(heads + " " + snippet)).strip()
        })
    (SITE / "search.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

def write_feed(brand: str, site_url: str, posts_meta: List[Dict]):
    """Atom feed."""
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"; POSTS = SITE / "posts"
    site_url = site_url.rstrip("/")

    entries = []
    for m in posts_meta[:20]:  # latest 20
        slug = m["slug"]; url = f"{site_url}/posts/{slug}/"
        path = POSTS / slug / "index.html"
        if not path.exists(): continue
        txt = path.read_text(encoding="utf-8")
        # crude extract first paragraph
        m1 = re.search(r"<p>(.*?)</p>", txt, re.S)
        summary = html.escape(re.sub(r"<.*?>", "", m1.group(1) if m1 else "")[:300])
        updated = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        entries.append(f"""
  <entry>
    <title>{html.escape(m["title"])}</title>
    <link href="{url}"/>
    <id>{url}</id>
    <updated>{updated}</updated>
    <summary>{summary}</summary>
  </entry>""")

    feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{html.escape(brand)}</title>
  <link href="{site_url}/feed.xml" rel="self"/>
  <link href="{site_url}/"/>
  <updated>{datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</updated>
  <id>{site_url}/</id>
  {''.join(entries)}
</feed>
"""
    (SITE / "feed.xml").write_text(feed, encoding="utf-8")

def write_404(brand, site_url, base_prefix, theme, analytics_html):
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"
    html_out = NOT_FOUND_TPL.format(
        brand=escape(brand),
        theme_css=THEMES["bulma"]["css"],
        base_prefix=base_prefix,
        container_open=THEMES["bulma"]["container_open"],
        container_close=THEMES["bulma"]["container_close"],
    )
    (SITE / "404.html").write_text(html_out, encoding="utf-8")

def write_archive_pages(brand, site_url, base_prefix, theme, posts_meta, analytics_html):
    """Simple archive page (we lack real dates; show alphabetical by title and by category)."""
    ROOT = Path(__file__).resolve().parents[1]
    SITE = ROOT / "site"

    by_cat = {}
    for m in posts_meta:
        by_cat.setdefault(m["category"], []).append(m)

    sections = []
    sections.append("<h2 class='title is-4'>All posts (A–Z)</h2>")
    for m in sorted(posts_meta, key=lambda x: x["title"].lower()):
        sections.append(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a> <span class="tag is-light">{escape(m["category"])}</span></p>')

    sections.append("<hr/><h2 class='title is-4'>By Category</h2>")
    for cat in sorted(by_cat.keys(), key=lambda s: s.lower()):
        sections.append(f"<h3 class='title is-6'>{escape(cat)}</h3>")
        for m in sorted(by_cat[cat], key=lambda x: x["title"].lower()):
            sections.append(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>')

    body_html = "\n".join(sections)
    html_out = PAGE_TPL.format(
        title="Archive", brand=escape(brand), site_url=site_url.rstrip("/"),
        slug="archive", theme_css=theme["css"], analytics=analytics_html,
        base_prefix=base_prefix, body_html=body_html, year=datetime.date.today().year,
        container_open=theme["container_open"], container_close=theme["container_close"],
    )
    (SITE / "archive.html").write_text(html_out, encoding="utf-8")
