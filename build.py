# build.py — SiteSmith Orchestrator (A+B+C upgrades)
from pathlib import Path
import argparse, json

from ssg.content import load_keywords, call_openai
from ssg.themes import choose_theme
from ssg.render import (
    prepare_dirs, analytics_snippet, write_post, write_standard_pages,
    build_category_pages, build_tag_pages, rebuild_index,
    write_sitemap_and_robots, write_search_index, slugify,
    write_feed, write_404, write_archive_pages
)

def main():
    ap = argparse.ArgumentParser(description="Generate static blog.")
    ap.add_argument("--brand", default="My Test Blog")
    ap.add_argument("--site_url", required=True, help="https://USERNAME.github.io/REPO")
    ap.add_argument("--amazon_tag", default="yourtag-20")
    ap.add_argument("--keywords_file", default="data/keywords.json")
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--force_theme")
    ap.add_argument("--audience", default="readers")
    ap.add_argument("--domain", default="example.com")
    ap.add_argument("--analytics", default="", help='Examples: "plausible:domain" or "ga4:G-XXXX" or both comma-separated')
    # Author / E-E-A-T
    ap.add_argument("--author_name", default="Staff Writer")
    ap.add_argument("--author_url", default="")
    ap.add_argument("--author_bio", default="We test products and write simple, trustworthy guides.")
    args = ap.parse_args()

    # base_prefix for repos served at /REPO
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

    # 1) Collect AI outputs (structured JSON)
    for kw in picked:
        data = call_openai(kw)
        slug = slugify(kw)
        category = data.get("category", "General")
        tags = data.get("tags", [])
        title = data.get("title") or kw.title()

        payload = {
            "keyword": kw,
            "data": data,
            "slug": slug,
            "category": category,
            "tags": tags,
            "title": title,
            "author_name": args.author_name,
            "author_url": args.author_url,
            "author_bio": args.author_bio,
        }
        collected.append(payload)
        posts_meta.append({"slug": slug, "title": title, "category": category, "tags": tags})

    # 2) Render posts (pass small related list for internal links)
    for payload in collected:
        related = [m for m in posts_meta if m["slug"] != payload["slug"]][:4]
        write_post(args.brand, args.site_url, base_prefix, payload, args.amazon_tag, theme, related, analytics_html)
        print("✔ Wrote post:", payload["slug"])

    # 3) Standard pages + category/tag pages + archives
    write_standard_pages(args.brand, args.site_url, base_prefix, theme, analytics_html,
                         audience=args.audience, domain=args.domain)
    if posts_meta:
        build_category_pages(args.brand, args.site_url, base_prefix, theme, posts_meta, analytics_html)
        build_tag_pages(args.brand, args.site_url, base_prefix, theme, posts_meta, analytics_html)
        write_archive_pages(args.brand, args.site_url, base_prefix, theme, posts_meta, analytics_html)

    # 4) Homepage (with pagination) + sitemap + search index + feed + 404
    desc = f"Latest articles: " + ", ".join([c['title'] for c in collected]) if collected else f"{args.brand} blog"
    rebuild_index(args.brand, desc, args.site_url, base_prefix, theme, posts_meta, analytics_html)
    write_sitemap_and_robots(args.site_url, posts_meta)
    write_search_index(posts_meta)
    write_feed(args.brand, args.site_url, posts_meta)
    write_404(args.brand, args.site_url, base_prefix, theme, analytics_html)

    print("✅ Site built successfully.")

if __name__ == "__main__":
    main()
