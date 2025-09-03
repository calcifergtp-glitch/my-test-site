# build.py — SiteSmith Orchestrator
from pathlib import Path
import argparse, json

from ssg.content import load_keywords, call_openai
from ssg.themes import choose_theme
from ssg.render import (
    prepare_dirs, analytics_snippet, write_post, write_standard_pages,
    build_category_pages, build_tag_pages, rebuild_index,
    write_sitemap_and_robots, write_search_index, slugify
)

def main():
    ap = argparse.ArgumentParser(description="Generate static blog.")
    ap.add_argument("--brand", default="My Test Blog")
    ap.add_argument("--site_url", required=True, help="https://USERNAME.github.io/REPO")
    ap.add_argument("--amazon_tag", default="yourtag-20")
    ap.add_argument("--keywords_file", default="data/keywords.json")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--force_theme")
    ap.add_argument("--audience", default="home cooks in US")
    ap.add_argument("--domain", default="example.com")
    ap.add_argument("--analytics", default="", help='"plausible:DOMAIN" or "ga4:G-XXXX"')
    args = ap.parse_args()

    base_prefix = "/" + args.site_url.rstrip("/").split("github.io/")[-1]
    if base_prefix == "/": base_prefix = ""

    ROOT = Path(__file__).parent
    SITE, POSTS, DATA = prepare_dirs(ROOT)

    theme_key, theme = choose_theme(args.force_theme)
    print("🎨 Theme:", theme_key)

    analytics_html = analytics_snippet(args.analytics)

    keywords = load_keywords(ROOT / args.keywords_file)
    if not keywords:
        (ROOT / args.keywords_file).write_text(json.dumps({"keywords": ["sample post"]}, indent=2), encoding="utf-8")
        keywords = []

    picked = keywords[: max(0, args.limit)]
    posts_meta, collected = [], []

    # Collect OpenAI outputs
    for kw in picked:
        data = call_openai(kw)
        slug = slugify(kw)
        category = data.get("category", "General")
        tags = data.get("tags", [])
        title = data.get("title") or kw.title()

        payload = {"keyword": kw, "data": data, "slug": slug, "category": category, "tags": tags, "title": title}
        collected.append(payload)
        posts_meta.append({"slug": slug, "title": title, "category": category, "tags": tags})

    # Render posts
    for payload in collected:
        related = [m for m in posts_meta if m["slug"] != payload["slug"]][:3]
        write_post(args.brand, args.site_url, base_prefix, payload, args.amazon_tag, theme, related, analytics_html)
        print("✔ Wrote post:", payload["slug"])

    # Standard pages
    write_standard_pages(args.brand, args.site_url, base_prefix, theme, analytics_html,
                         audience=args.audience, domain=args.domain)

    if posts_meta:
        build_category_pages(args.brand, args.site_url, base_prefix, theme, posts_meta, analytics_html)
        build_tag_pages(args.brand, args.site_url, base_prefix, theme, posts_meta, analytics_html)

    desc = f"Articles about {', '.join([c['title'] for c in collected])}"
    rebuild_index(args.brand, desc, args.site_url, base_prefix, theme, posts_meta, analytics_html)
    write_sitemap_and_robots(args.site_url, posts_meta)
    write_search_index(posts_meta)

    print("✅ Site built successfully.")

if __name__ == "__main__":
    main()
