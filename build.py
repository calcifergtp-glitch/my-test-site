import argparse, os, sys
from ssg.render import build
from ssg.utils import ensure_dir

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site_url", required=True)
    ap.add_argument("--brand", required=True)
    ap.add_argument("--ga4", default=os.getenv("GA4_ID",""))
    ap.add_argument("--plausible", default=os.getenv("PLAUSIBLE_DOMAIN",""))
    ap.add_argument("--custom_domain", default=os.getenv("CUSTOM_DOMAIN",""))
    ap.add_argument("--out", default="site")
    ap.add_argument("--templates", default="templates")
    ap.add_argument("--content", default="content")
    args = ap.parse_args()

    ensure_dir(args.out)
    ok = build(
        site_url=args.site_url,
        brand=args.brand,
        out_dir=args.out,
        templates_dir=args.templates,
        content_dir=args.content,
        ga4_id=args.ga4,
        plausible_domain=args.plausible,
        custom_domain=args.custom_domain
    )
    if not ok:
        sys.exit(2)

if __name__ == "__main__":
    main()
