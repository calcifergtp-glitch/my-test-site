# ssg/render.py — structured pages + longer posts + citations + JSON-LD + safe images
import os, re, json, html, datetime, math
from pathlib import Path
from typing import List, Dict
from .themes import THEMES
from .templates import INDEX_SHELL, POST_TPL, PAGE_TPL, NOT_FOUND_TPL

PAGE_SIZE = 8

def escape(s:str)->str: return html.escape(s or "")

try:
    from slugify import slugify as slugify_lib
    def slugify(s:str)->str: return slugify_lib(s or "")
except Exception:
    import re as _re
    def slugify(s:str)->str:
        s = (s or "").lower()
        s = _re.sub(r"[^a-z0-9]+","-",s).strip("-")
        return s or "post"

# --- optional slug->image mapping (data/images.json) ---
_IMAGE_MAP = None
def load_image_map() -> Dict[str,str]:
    global _IMAGE_MAP
    if _IMAGE_MAP is not None:
        return _IMAGE_MAP
    ROOT = Path(__file__).resolve().parents[1]
    path = ROOT / "data" / "images.json"
    if not path.exists():
        _IMAGE_MAP = {}
        return _IMAGE_MAP
    try:
        _IMAGE_MAP = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(_IMAGE_MAP, dict):
            _IMAGE_MAP = {}
    except Exception:
        _IMAGE_MAP = {}
    return _IMAGE_MAP

def _local_image_for_slug(slug: str) -> str | None:
    """
    Prefer a committed local image:
      site/assets/img/posts/<slug>.(jpg|jpeg|png|webp)
    Returns a site-relative URL or None.
    """
    ROOT = Path(__file__).resolve().parents[1]
    base = ROOT / "site" / "assets" / "img" / "posts"
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = base / f"{slug}{ext}"
        if p.exists():
            return f"/assets/img/posts/{slug}{ext}"
    return None

def img_tag_from_url(url:str, w:int, h:int, alt:str) -> str:
    """Direct URL (local or remote) with a Picsum fallback if remote fails."""
    if not url:
        return img_tag_fallback(alt, w, h, alt)
    if url.startswith("/"):
        return f'<img src="{url}" alt="{escape(alt)}" loading="lazy">'
    fallback = f"https://picsum.photos/seed/{slugify(alt)}/{w}/{h}"
    return (f'<img src="{url}" alt="{escape(alt)}" loading="lazy" '
            f'onerror="this.onerror=null;this.src=\'{fallback}\';">')

def img_tag_fallback(topic:str, w:int, h:int, alt:str) -> str:
    q = (slugify(topic or "kitchen")).replace("-", ",")
    primary = f"https://source.unsplash.com/{w}x{h}/?{q}"
    fallback = f"https://picsum.photos/seed/{slugify(topic)}/{w}/{h}"
    return (f'<img src="{primary}" alt="{escape(alt)}" loading="lazy" '
            f'onerror="this.onerror=null;this.src=\'{fallback}\';">')

def hero_img_for(slug: str, title: str, w: int, h: int) -> str:
    """
    Priority:
      1) local asset: /assets/img/posts/<slug>.(jpg|png|webp)
      2) images.json mapping by slug
      3) stock fallback
    """
    local = _local_image_for_slug(slug)
    if local:
        return f'<img src="{local}" alt="{escape(title)}" loading="lazy">'
    imap = load_image_map()
    mapped = imap.get(slug) or imap.get(slugify(slug))
    if mapped:
        return img_tag_from_url(mapped, w, h, title)
    return img_tag_fallback(title or slug, w, h, title)

def prepare_dirs(ROOT: Path):
    SITE = ROOT/"site"; POSTS = SITE/"posts"; DATA = ROOT/"data"
    SITE.mkdir(exist_ok=True); POSTS.mkdir(parents=True, exist_ok=True); DATA.mkdir(exist_ok=True)
    (SITE/".nojekyll").write_text("\n",encoding="utf-8")
    (SITE/"assets"/"js").mkdir(parents=True, exist_ok=True)
    return SITE, POSTS, DATA

def paginate(items:List[Dict], page:int, size:int=PAGE_SIZE):
    total = max(1, math.ceil(len(items)/size)); page = max(1, min(page,total))
    s=(page-1)*size; e=s+size
    return items[s:e], page, total

def pagination_html(base_prefix,current,total,base_path):
    if total<=1: return ""
    def url_for(n):
        if base_path=="": return f"{base_prefix}/" if n==1 else f"{base_prefix}/page/{n}/"
        else: return f"{base_prefix}/{base_path}/" if n==1 else f"{base_prefix}/{base_path}/page/{n}/"
    pages = []
    for n in range(1,total+1):
        cls="pagination-link is-current" if n==current else "pagination-link"
        pages.append(f'<li><a class="{cls}" href="{url_for(n)}">{n}</a></li>')
    return f'<nav class="pagination is-centered"><ul class="pagination-list">{"".join(pages)}</ul></nav>'

def analytics_snippet(analytics:str)->str:
    if not analytics: return ""
    parts=[p.strip() for p in analytics.split(",") if p.strip()]
    out=[]
    for p in parts:
        if p.startswith("plausible:"):
            domain=p.split(":",1)[1].strip()
            out.append(f'<script defer data-domain="{escape(domain)}" src="https://plausible.io/js/script.js"></script>')
        elif p.startswith("ga4:"):
            mid=p.split(":",1)[1].strip()
            out.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={escape(mid)}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{escape(mid)}");</script>')
    return "\n".join(out)

def render_tags(base_prefix,tags:List[str])->str:
    tags=[t for t in (tags or []) if t]
    if not tags: return '<span class="tag is-light">none</span>'
    return " ".join(f'<a class="tag is-link is-light" href="{base_prefix}/tag/{slugify(t)}/">{escape(t)}</a>' for t in tags)

def render_sections(sections):
    out=[]
    # Expand sections with H2/H3 variety and paragraph spacing
    for s in sections or []:
        h=escape(s.get("heading",""))
        if h:
            anchor = slugify(h)
            out.append(f'<h2 id="{anchor}" class="title is-4">{h}</h2>')
        # paragraphs
        for p in s.get("paragraphs",[]) or []:
            out.append(f"<p>{escape(p)}</p>")
        # optional bullets
        for lst in s.get("bullets",[]) or []:
            if isinstance(lst, list) and lst:
                out.append("<ul>" + "".join(f"<li>{escape(x)}</li>" for x in lst) + "</ul>")
    return "\n".join(out)

def render_faq(faq):
    if not faq: return ""
    out=['<h2 class="title is-4" id="faq">FAQ</h2>']
    for it in faq:
        q=escape(it.get("q","")); a=escape(it.get("a",""))
        if q: out.append(f"<h3 class='title is-6' id='{slugify(q)}'>{q}</h3><p>{a}</p>")
    return "\n".join(out)

def render_sources(sources):
    if not sources: return ""
    lis=[]
    for s in sources:
        title=escape(s.get("title","Source")); url=(s.get("url") or "").strip()
        if url.startswith("http"): lis.append(f'<li><a href="{escape(url)}" target="_blank" rel="nofollow noopener">{title}</a></li>')
        else: lis.append(f"<li>{title}</li>")
    return f"<h2 class='title is-5'>Sources & citations</h2><ul>{''.join(lis)}</ul>"

def product_box(title, blurb, url):
    return f'''<div class="box product-box"><p class="title is-6">{escape(title)}</p><p class="subtitle is-6">{escape(blurb)}</p><p><a class="button is-link" href="{escape(url)}" target="_blank" rel="sponsored nofollow noopener">Check price →</a></p></div>'''
def cta_banner(text, url):
    return f'''<div class="notification is-link is-light cta-banner"><span>{escape(text)}</span><a class="button is-link" href="{escape(url)}" target="_blank" rel="sponsored nofollow noopener">View on Amazon</a></div>'''
def comparison_rows(items, tag):
    if not items: return ""
    rows=[]
    for it in items:
        asin = (it.get("asin") or "B000000000")
        url=f"https://www.amazon.com/dp/{asin}?tag={escape(tag)}"
        rows.append(f"<tr><td>{escape(it.get('name',''))}</td><td>{escape(', '.join(it.get('pros',[]) or []))}</td><td>{escape(', '.join(it.get('cons',[]) or []))}</td><td><a class='button is-small is-link' href='{url}' target='_blank' rel='sponsored nofollow noopener'>Buy</a></td></tr>")
    return "\n".join(rows)

def render_related(base_prefix, related):
    if not related: return ""
    items="".join(f'<li><a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></li>' for m in related[:6])
    return f'<div class="box"><h2 class="title is-5">Related posts</h2><ul>{items}</ul></div>'

def _cards_for(posts_meta, base_prefix):
    cards=[]
    for m in posts_meta:
        slug=m["slug"]; title=escape(m["title"]); cat=escape(m["category"]); cat_slug=slugify(m["category"])
        img_html = hero_img_for(slug, m.get("title") or slug, 600, 338)
        cards.append(f"""
<div class="column is-half">
  <div class="card">
    <div class="card-image"><figure class="image">{img_html}</figure></div>
    <div class="card-content">
      <p class="tags"><span class="tag is-info is-light">Category</span> <a class="tag is-link is-light" href="{base_prefix}/category/{cat_slug}/">{cat}</a></p>
      <p class="title is-5"><a href="{base_prefix}/posts/{slug}/">{title}</a></p>
      <p><a class="button is-link is-light is-small" href="{base_prefix}/posts/{slug}/">Read →</a></p>
    </div>
  </div>
</div>""")
    return "\n".join(cards) if cards else "<p>No posts yet.</p>"

def _search_bar_html(base_prefix):
    return f"""
<div class="field has-addons" style="margin:1rem 0">
  <div class="control is-expanded"><input id="q" class="input" type="search" placeholder="Search posts…" aria-label="Search" /></div>
  <div class="control"><button id="qbtn" class="button is-link">Search</button></div>
</div>
<div id="qresults" class="content"></div>
<script>
(function(){{
  const q=document.getElementById('q'), btn=document.getElementById('qbtn'), out=document.getElementById('qresults'); let idx=[];
  fetch('{base_prefix}/search.json').then(r=>r.json()).then(d=>idx=d);
  function run(){{
    const term=(q.value||'').toLowerCase().trim(); if(!term){{out.innerHTML='';return;}}
    const parts=term.split(/\\s+/);
    const res=idx.map(it=>{{let score=0; const hay=(it.title+' '+it.category+' '+it.tags.join(' ')+' '+it.text).toLowerCase(); for(const p of parts) if(hay.includes(p)) score+=1; return [score,it];}})
      .filter(x=>x[0]>0).sort((a,b)=>b[0]-a[0]).slice(0,20).map(x=>x[1]);
    out.innerHTML = res.length ? '<ul>'+res.map(it=>`<li><a href="{base_prefix}/posts/${{it.slug}}/">${{it.title}}</a> <span class="tag is-light">${{it.category}}</span></li>`).join('') : '<p><em>No results</em></p>';
  }}
  btn.addEventListener('click',run); q.addEventListener('keydown',e=>{{if(e.key==='Enter') run();}});
}})();
</script>
"""

# ----------------- JSON-LD helpers -----------------

def jsonld_site(brand, site_url):
    data = {
        "@context":"https://schema.org",
        "@type":"WebSite",
        "name":brand,
        "url":site_url.rstrip("/"),
        "potentialAction": {
            "@type":"SearchAction",
            "target": f"{site_url.rstrip('/')}/?q={{search_term_string}}",
            "query-input":"required name=search_term_string"
        }
    }
    return '<script type="application/ld+json">'+json.dumps(data)+'</script>'

def jsonld_webpage(title, site_url, url):
    data = {
        "@context":"https://schema.org",
        "@type":"WebPage",
        "name": title,
        "url": url
    }
    return '<script type="application/ld+json">'+json.dumps(data)+'</script>'

def jsonld_article(title, site_url, slug, author_name, published_iso, tags, faq_items=None):
    url=f"{site_url.rstrip('/')}/posts/{slug}/"
    data = {
        "@context":"https://schema.org",
        "@type":"Article",
        "headline": title,
        "author": {"@type":"Person","name": author_name},
        "datePublished": published_iso,
        "dateModified": published_iso,
        "mainEntityOfPage": {"@type":"WebPage","@id": url},
        "keywords": ", ".join(tags or [])
    }
    blocks = ['<script type="application/ld+json">'+json.dumps(data)+'</script>']
    if faq_items:
        faq = {
            "@context":"https://schema.org",
            "@type":"FAQPage",
            "mainEntity": [
                {"@type":"Question","name": q.get("q",""),
                 "acceptedAnswer":{"@type":"Answer","text": q.get("a","")}}
                for q in faq_items if q.get("q")
            ]
        }
        blocks.append('<script type="application/ld+json">'+json.dumps(faq)+'</script>')
    return "\n".join(blocks)

# ----------------- Build main pages -----------------

def rebuild_index(brand, desc, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"
    (SITE/"assets"/"js").mkdir(parents=True, exist_ok=True)
    write_telemetry_js(SITE, base_prefix="")
    items=posts_meta[:]

    page_items, page, total = paginate(items[::-1], 1, PAGE_SIZE)
    post_cards=_cards_for(page_items, base_prefix)
    pagination=pagination_html(base_prefix, page, total, "")

    cat_counts={}; tag_counts={}
    for m in posts_meta:
        cat_counts[m["category"]]=cat_counts.get(m["category"],0)+1
        for t in m["tags"]: tag_counts[t]=tag_counts.get(t,0)+1
    category_list = "\n".join(f'<p>• <a href="{base_prefix}/category/{slugify(c)}/">{escape(c)}</a> <span class="tag is-light">{n}</span></p>' for c,n in sorted(cat_counts.items(), key=lambda x:(-x[1],x[0].lower()))) or "<p><em>None yet</em></p>"
    tag_cloud = " ".join(f'<a class="tag is-link is-light" href="{base_prefix}/tag/{slugify(t)}/">{escape(t)} ({n})</a>' for t,n in sorted(tag_counts.items(), key=lambda x:(-x[1],x[0].lower()))) or '<span class="tag is-light">none</span>'

    html_out = INDEX_SHELL.format(
      brand=escape(brand), desc=escape(desc), site_url=site_url.rstrip("/"), theme_css=THEMES["bulma"]["css"],
      analytics=analytics_html, jsonld=jsonld_site(brand, site_url),
      container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"],
      post_cards=post_cards, category_list=category_list, tag_cloud=tag_cloud,
      year=datetime.date.today().year, base_prefix=base_prefix, search_bar=_search_bar_html(base_prefix), pagination=pagination
    )
    (SITE/"index.html").write_text(html_out, encoding="utf-8")

    if total>1:
        for n in range(2,total+1):
            page_items, _, _ = paginate(items[::-1], n, PAGE_SIZE)
            post_cards=_cards_for(page_items, base_prefix); pagination=pagination_html(base_prefix, n, total, "")
            out = INDEX_SHELL.format(
              brand=escape(brand), desc=escape(desc), site_url=site_url.rstrip("/"), theme_css=THEMES["bulma"]["css"],
              analytics=analytics_html, jsonld=jsonld_site(brand, site_url),
              container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"],
              post_cards=post_cards, category_list=category_list, tag_cloud=tag_cloud,
              year=datetime.date.today().year, base_prefix=base_prefix, search_bar=_search_bar_html(base_prefix), pagination=pagination
            )
            folder = SITE/"page"/str(n); folder.mkdir(parents=True, exist_ok=True); (folder/"index.html").write_text(out, encoding="utf-8")

def write_sitemap_and_robots(site_url, posts_meta):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"; site_url=site_url.rstrip("/")
    urls=[f"{site_url}/"]
    for m in posts_meta: urls.append(f"{site_url}/posts/{m['slug']}/")
    cats=sorted({m["category"] for m in posts_meta})
    for c in cats: urls.append(f"{site_url}/category/{slugify(c)}/")
    tags=sorted({t for m in posts_meta for t in m["tags"]})
    for t in tags: urls.append(f"{site_url}/tag/{slugify(t)}/")
    urls += [f"{site_url}/archive.html", f"{site_url}/privacy.html", f"{site_url}/disclosure.html", f"{site_url}/about.html", f"{site_url}/contact.html", f"{site_url}/feed.xml"]
    out=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'] + [f"  <url><loc>{u}</loc></url>" for u in urls] + ["</urlset>\n"]
    (SITE/"sitemap.xml").write_text("\n".join(out), encoding="utf-8")
    (SITE/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n", encoding="utf-8")

def build_category_pages(brand, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"; root=SITE/"category"
    by_cat={}
    for m in posts_meta: by_cat.setdefault(m["category"],[]).append(m)
    for cat, items in by_cat.items():
        items=items[:]
        page_items, page, total = paginate(items[::-1], 1, PAGE_SIZE)
        folder=root/slugify(cat); folder.mkdir(parents=True, exist_ok=True)
        body=f"<h2 class='title is-4'>{escape(cat)}</h2>" + "".join(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>' for m in page_items) + pagination_html(base_prefix, page, total, f"category/{slugify(cat)}")
        html_out = PAGE_TPL.format(title=f"{cat} — Category", brand=escape(brand), site_url=site_url.rstrip("/"), slug="", theme_css=THEMES["bulma"]["css"], analytics=analytics_html, base_prefix=base_prefix, body_html=body, year=datetime.date.today().year, container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"], jsonld=jsonld_webpage(f"Category: {cat}", site_url, f"{site_url.rstrip('/')}/category/{slugify(cat)}/"))
        (folder/"index.html").write_text(html_out, encoding="utf-8")
        if total>1:
            for n in range(2,total+1):
                page_items, _, _ = paginate(items[::-1], n, PAGE_SIZE)
                body=f"<h2 class='title is-4'>{escape(cat)}</h2>" + "".join(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>' for m in page_items) + pagination_html(base_prefix, n, total, f"category/{slugify(cat)}")
                pdir = folder/"page"/str(n); pdir.mkdir(parents=True, exist_ok=True)
                (pdir/"index.html").write_text(PAGE_TPL.format(title=f"{cat} — Category", brand=escape(brand), site_url=site_url.rstrip("/"), slug="", theme_css=THEMES["bulma"]["css"], analytics=analytics_html, base_prefix=base_prefix, body_html=body, year=datetime.date.today().year, container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"], jsonld=jsonld_webpage(f"Category: {cat}", site_url, f"{site_url.rstrip('/')}/category/{slugify(cat)}/page/{n}/")), encoding="utf-8")

def build_tag_pages(brand, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"; root=SITE/"tag"
    by_tag={}
    for m in posts_meta:
        for t in m["tags"]: by_tag.setdefault(t,[]).append(m)
    for t, items in by_tag.items():
        items=items[:]
        page_items, page, total = paginate(items[::-1], 1, PAGE_SIZE)
        folder=root/slugify(t); folder.mkdir(parents=True, exist_ok=True)
        body=f"<h2 class='title is-4'>Tag: {escape(t)}</h2>" + "".join(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>' for m in page_items) + pagination_html(base_prefix, page, total, f"tag/{slugify(t)}")
        html_out = PAGE_TPL.format(title=f"{t} — Tag", brand=escape(brand), site_url=site_url.rstrip("/"), slug="", theme_css=THEMES["bulma"]["css"], analytics=analytics_html, base_prefix=base_prefix, body_html=body, year=datetime.date.today().year, container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"], jsonld=jsonld_webpage(f"Tag: {t}", site_url, f"{site_url.rstrip('/')}/tag/{slugify(t)}/"))
        (folder/"index.html").write_text(html_out, encoding="utf-8")
        if total>1:
            for n in range(2,total+1):
                page_items, _, _ = paginate(items[::-1], n, PAGE_SIZE)
                body=f"<h2 class='title is-4'>Tag: {escape(t)}</h2>" + "".join(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>' for m in page_items) + pagination_html(base_prefix, n, total, f"tag/{slugify(t)}")
                pdir = folder/"page"/str(n); pdir.mkdir(parents=True, exist_ok=True)
                (pdir/"index.html").write_text(PAGE_TPL.format(title=f"{t} — Tag", brand=escape(brand), site_url=site_url.rstrip("/"), slug="", theme_css=THEMES["bulma"]["css"], analytics=analytics_html, base_prefix=base_prefix, body_html=body, year=datetime.date.today().year, container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"], jsonld=jsonld_webpage(f"Tag: {t}", site_url, f"{site_url.rstrip('/')}/tag/{slugify(t)}/page/{n}/")), encoding="utf-8")

def write_search_index(posts_meta):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"; POSTS=SITE/"posts"
    items=[]
    for m in posts_meta:
        path=POSTS/m["slug"]/ "index.html"
        if not path.exists(): continue
        html_txt=path.read_text(encoding="utf-8")
        m1=re.search(r"<p>(.*?)</p>", html_txt, re.S); snippet=(m1.group(1) if m1 else "")[:500]
        heads=" ".join(h.strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html_txt, re.S))
        strip=lambda s: re.sub(r"<.*?>"," ", s or "")
        items.append({"slug": m["slug"], "title": re.sub(r"\s+"," ", strip(m["title"])).strip(), "url": f"/posts/{m['slug']}/", "category": m["category"], "tags": m["tags"], "text": re.sub(r"\s+"," ", strip(heads+" "+snippet)).strip()})
    (SITE/"search.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

def write_feed(brand, site_url, posts_meta):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"; POSTS=SITE/"posts"; site_url=site_url.rstrip("/")
    entries=[]
    for m in posts_meta[::-1][:20]:
        slug=m["slug"]; url=f"{site_url}/posts/{slug}/"
        path=POSTS/slug/"index.html"
        if not path.exists(): continue
        txt=path.read_text(encoding="utf-8")
        m1=re.search(r"<p>(.*?)</p>", txt, re.S); import html as _html
        summary=_html.escape(re.sub(r"<.*?>","", m1.group(1) if m1 else "")[:300])
        updated=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        entries.append(f"""
  <entry>
    <title>{_html.escape(m["title"])}</title>
    <link href="{url}"/>
    <id>{url}</id>
    <updated>{updated}</updated>
    <summary>{summary}</summary>
  </entry>""")
    feed=f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{html.escape(brand)}</title>
  <link href="{site_url}/feed.xml" rel="self"/>
  <link href="{site_url}/"/>
  <updated>{datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</updated>
  <id>{site_url}/</id>
  {''.join(entries)}
</feed>
"""
    (SITE/"feed.xml").write_text(feed, encoding="utf-8")

def write_404(brand, site_url, base_prefix, theme, analytics_html):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"
    html_out = NOT_FOUND_TPL.format(brand=escape(brand), theme_css=THEMES["bulma"]["css"], base_prefix=base_prefix,
          container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"])
    (SITE/"404.html").write_text(html_out, encoding="utf-8")

def _page_jsonld(title, site_url, slug_html):
    url = f"{site_url.rstrip('/')}/{slug_html}"
    return jsonld_webpage(title, site_url, url)

def write_standard_pages(brand, site_url, base_prefix, theme, analytics_html, audience="readers", domain="example.com"):
    # Rich, scannable copy for core pages
    PAGES={
      "about":{
        "title":"About",
        "body":f"""
<h2 class="title is-4">Our mission</h2>
<p><strong>{escape(brand)}</strong> publishes practical, evidence-aware guides and reviews for {escape(audience)}. We value clarity, useful details, and honest recommendations.</p>

<h2 class="title is-4">Editorial standards</h2>
<ul>
  <li>We cite credible sources and link to primary research where relevant.</li>
  <li>We disclose affiliate relationships and avoid pay-to-play rankings.</li>
  <li>We update content as products and evidence evolve.</li>
</ul>

<h2 class="title is-4">Who we are</h2>
<p>Independent editors and testers who care about helping you buy once, buy well.</p>
"""
      },
      "contact":{
        "title":"Contact",
        "body":f"""
<p>Email us: <a href="mailto:contact@{escape(domain)}">contact@{escape(domain)}</a></p>
<p>We read every message and reply when we can. For partnership requests, include timelines, product details, and any embargo info.</p>
"""
      },
      "privacy":{
        "title":"Privacy",
        "body":"""
<h2 class="title is-4">Overview</h2>
<p>We respect your privacy. This site may use cookies or analytics to understand traffic and improve the experience. We do not sell personal data.</p>

<h2 class="title is-4">Analytics</h2>
<p>We measure page views and clicks in aggregate to see what’s helpful. You can block analytics with your browser or privacy tools.</p>

<h2 class="title is-4">Cookies</h2>
<p>Cookies may be used to remember preferences or attribute affiliate visits. You can clear or block cookies anytime in your browser settings.</p>
"""
      },
      "disclosure":{
        "title":"Affiliate Disclosure",
        "body":"""
<p>Some links on this site are affiliate links. If you purchase through them, we may earn a commission—at no extra cost to you. We only recommend products we believe bring genuine value.</p>
<p><em>As an Amazon Associate we earn from qualifying purchases.</em></p>
"""
      }
    }
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"
    for slug_name, meta in PAGES.items():
        out = PAGE_TPL.format(
          title=meta["title"], brand=escape(brand), site_url=site_url.rstrip("/"),
          slug=slug_name, theme_css=THEMES["bulma"]["css"], analytics=analytics_html,
          base_prefix=base_prefix, body_html=meta["body"], year=datetime.date.today().year,
          container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"],
          jsonld=_page_jsonld(meta["title"], site_url, f"{slug_name}.html")
        )
        (SITE/f"{slug_name}.html").write_text(out, encoding="utf-8")

def write_post(brand, site_url, base_prefix, payload, amazon_tag, theme, related_list, analytics_html):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"; POSTS=SITE/"posts"
    slug=payload["slug"]; data=payload["data"]; category=payload["category"]; tags=payload["tags"]; title=payload["title"]
    today=datetime.date.today().isoformat()
    aff_url=f"https://www.amazon.com/dp/B000000000?tag={amazon_tag}"
    inline_cta=cta_banner("Our top pick is in stock with fast shipping.", aff_url)
    top_pick_box=product_box(data.get("product_name","Our Pick"), data.get("product_blurb","Solid choice for most."), aff_url)

    # Expanded body content (intro + sections + FAQ)
    body=[]
    if data.get("summary"): body.append(f"<p><em>{escape(data['summary'])}</em></p>")
    # Encourage longer content by repeating sections with details if present
    body.append(render_sections(data.get("sections",[])))
    body.append(render_faq(data.get("faq",[])))
    # Internal related inline links
    links=[f'<a href="{base_prefix}/posts/{r["slug"]}/">{escape(r["title"])}</a>' for r in related_list[:3]]
    intext_related = "<p><em>Related:</em> " + " • ".join(links) + "</p>" if links else ""

    body_html="\n".join([b for b in body if b])
    sources_html=render_sources(data.get("sources",[]))

    a_name = escape(payload.get("author_name") or "Staff Writer")
    a_bio  = escape(payload.get("author_bio") or "")
    a_url  = (payload.get("author_url") or "").strip()
    author_link = f'• <a href="{escape(a_url)}" target="_blank" rel="nofollow noopener">Profile</a>' if a_url else ""

    hero_img_tag = hero_img_for(slug, title, 1200, 630)

    jsonld = jsonld_article(
        title=title, site_url=site_url, slug=slug,
        author_name=a_name, published_iso=today, tags=tags, faq_items=data.get("faq",[])
    )

    html_out = POST_TPL.format(
        title=escape(title), brand=escape(brand),
        meta_desc=escape(data.get("meta_description","")),
        site_url=site_url.rstrip("/"), slug=slug, base_prefix=base_prefix,
        theme_css=THEMES["bulma"]["css"], analytics=analytics_html, date=today,
        hero_img_tag=hero_img_tag, jsonld=jsonld,
        body_html=body_html, inline_cta=inline_cta, intext_related=intext_related, sources_html=sources_html,
        top_pick_box=top_pick_box, comparison_table="", year=datetime.date.today().year,
        container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"],
        category=escape(category), cat_slug=slugify(category), tags_html=render_tags(base_prefix,tags),
        related_html=render_related(base_prefix, related_list),
        author_name=a_name, author_bio=a_bio, author_link=author_link,
    )
    folder=POSTS/slug; folder.mkdir(parents=True, exist_ok=True)
    (folder/"index.html").write_text(html_out, encoding="utf-8")
    return slug

def write_archive_pages(brand, site_url, base_prefix, theme, posts_meta, analytics_html):
    ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/"site"
    by_cat={}
    for m in posts_meta: by_cat.setdefault(m["category"],[]).append(m)
    sections=["<h2 class='title is-4'>All posts (A–Z)</h2>"]
    for m in sorted(posts_meta, key=lambda x:x["title"].lower()):
        sections.append(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a> <span class="tag is-light">{escape(m["category"])}</span></p>')
    sections.append("<hr/><h2 class='title is-4'>By Category</h2>")
    for cat in sorted(by_cat.keys(), key=lambda s:s.lower()):
        sections.append(f"<h3 class='title is-6'>{escape(cat)}</h3>")
        for m in sorted(by_cat[cat], key=lambda x:x["title"].lower()):
            sections.append(f'<p>• <a href="{base_prefix}/posts/{m["slug"]}/">{escape(m["title"])}</a></p>')
    body_html="\n".join(sections)
    out = PAGE_TPL.format(
        title="Archive", brand=escape(brand), site_url=site_url.rstrip("/"), slug="archive",
        theme_css=THEMES["bulma"]["css"], analytics=analytics_html, base_prefix=base_prefix,
        body_html=body_html, year=datetime.date.today().year,
        container_open=THEMES["bulma"]["container_open"], container_close=THEMES["bulma"]["container_close"],
        jsonld=_page_jsonld("Archive", site_url, "archive.html")
    )
    (SITE/"archive.html").write_text(out, encoding="utf-8")

def write_telemetry_js(SITE:Path, base_prefix:str):
    (SITE/"assets"/"js").mkdir(parents=True, exist_ok=True)
    (SITE/"assets"/"js"/"telemetry.js").write_text("window.SS_trackSearch=function(q){console.log('search',q)};", encoding="utf-8")