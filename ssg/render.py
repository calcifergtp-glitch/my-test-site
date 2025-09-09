from pathlib import Path
from .templates import get_env
from .utils import ensure_dir, write_text, slugify, minify_html, build_stamp, jsonld
from .content import load_posts
from .monetize import inject_blocks
from . import analytics as analytics_mod
import datetime

def build(site_url: str, brand: str, out_dir: str, templates_dir: str, content_dir: str,
          ga4_id: str = "", plausible_domain: str = "", custom_domain: str = ""):
    env = get_env(templates_dir)
    posts = load_posts(content_dir)

    categories, tags = {}, {}
    for p in posts:
        for c in (p['meta'].get('categories') or []):
            categories.setdefault(c, []).append(p)
        for t in (p['meta'].get('tags') or []):
            tags.setdefault(t, []).append(p)

    analytics = (analytics_mod.ga4(ga4_id) if ga4_id else "") + (analytics_mod.plausible(plausible_domain) if plausible_domain else "")

    common = {
        'brand': brand,
        'site_url': site_url.rstrip('/'),
        'now': datetime.datetime.utcnow(),
        'build': build_stamp(),
        'analytics': analytics,
        'categories': categories,
        'tags': tags,
    }

    ensure_dir(out_dir)
    if custom_domain:
        write_text(str(Path(out_dir)/"CNAME"), custom_domain.strip())

    idx_tpl = env.get_template("index.html")
    write_text(str(Path(out_dir)/"index.html"), minify_html(idx_tpl.render(**common, posts=posts[:12])))

    for page in ["about","privacy","disclosure","contact"]:
        tpl = env.get_template("page.html")
        html = tpl.render(**common, page=page.title(), content=env.get_template(f"pages/{page}.html").render(**common))
        write_text(str(Path(out_dir)/f"{page}.html"), minify_html(html))

    post_tpl = env.get_template("post.html")
    for p in posts:
        html = inject_blocks(p['html'], p['meta'].get('products', []))
        url = f"/posts/{p['slug']}.html"
        outp = Path(out_dir)/"posts"/f"{p['slug']}.html"
        ld = {
            "@context":"https://schema.org",
            "@type":"Article",
            "headline":p['meta']['title'],
            "datePublished":str(p['meta'].get('date')),
            "author":{"@type":"Person","name":brand},
            "mainEntityOfPage": site_url.rstrip('/') + url
        }
        rendered = post_tpl.render(**common, post=p, content=html, jsonld=jsonld(ld))
        write_text(str(outp), minify_html(rendered))

    cat_tpl = env.get_template("category.html")
    for c, plist in categories.items():
        write_text(str(Path(out_dir)/"category"/f"{slugify(c)}.html"), minify_html(cat_tpl.render(**common, title=c, posts=plist)))
    tag_tpl = env.get_template("tag.html")
    for t, plist in tags.items():
        write_text(str(Path(out_dir)/"tag"/f"{slugify(t)}.html"), minify_html(tag_tpl.render(**common, title=t, posts=plist)))

    robots = f"User-agent: *\nAllow: /\nSitemap: {common['site_url']}/sitemap.xml\n"
    write_text(str(Path(out_dir)/"robots.txt"), robots)

    urls = [common['site_url'] + "/"]
    for p in posts:
        urls.append(common['site_url'] + f"/posts/{p['slug']}.html")
    for c in categories:
        urls.append(common['site_url'] + f"/category/{slugify(c)}.html")
    for t in tags:
        urls.append(common['site_url'] + f"/tag/{slugify(t)}.html")
    for page in ["about","privacy","disclosure","contact"]:
        urls.append(common['site_url'] + f"/{page}.html")
    lastmod = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    items = "".join([f"<url><loc>{u}</loc><lastmod>{lastmod}</lastmod></url>" for u in urls])
    sm = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>'
    write_text(str(Path(out_dir)/"sitemap.xml"), sm)

    write_text(str(Path(out_dir)/"favicon.ico"), "")
    return True

