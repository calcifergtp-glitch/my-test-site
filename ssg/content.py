# ssg/content.py — provides load_keywords() and call_openai() with a safe stub (no extra deps)
import os, json, random

def load_keywords(path):
    """
    Read data/keywords.json and return the list under {"keywords": [...] }.
    If the file is missing or invalid, return an empty list.
    """
    try:
        # 'path' can be a pathlib.Path or a string
        if hasattr(path, "read_text"):
            blob = path.read_text(encoding="utf-8")
        else:
            with open(path, "r", encoding="utf-8") as f:
                blob = f.read()
        data = json.loads(blob)
        kws = data.get("keywords", [])
        # Keep only non-empty strings
        return [str(k).strip() for k in kws if str(k).strip()]
    except Exception:
        return []

def _stub_post(keyword: str) -> dict:
    """
    Returns a structured content dict expected by ssg.render.write_post().
    No external calls; safe for CI. You can later replace this with real AI generation.
    """
    kw = (keyword or "").strip()
    title = kw.title() if kw else "Untitled"
    summary = f"Quick guide to {kw} — what it is, how it works, and what to consider."
    sections = [
        {"heading": "Overview", "paragraphs": [
            f"{title} explained in plain language.",
            "Key features, typical price range, and who it’s for."
        ]},
        {"heading": "Buying Tips", "paragraphs": [
            "What to look for: capacity, build quality, warranty, and support.",
            "Consider your budget and space constraints."
        ]},
        {"heading": "Alternatives", "paragraphs": [
            f"Other options you might compare to {kw} and when they make sense."
        ]},
    ]
    faq = [
        {"q": "Is it worth it?", "a": "It depends on your needs and budget. Consider usage frequency and features."},
        {"q": "How long does it last?", "a": "Typically 3–5 years with proper care, but varies by brand and usage."}
    ]
    sources = [
        {"title": "Manufacturer", "url": "https://www.example.com"},
        {"title": "Independent review", "url": "https://www.example.org/review"}
    ]
    # Simple demo comparison set (replace with real product data later)
    comparison = [
        {"name": "Model A", "asin": "B000000001", "pros": ["Quiet", "Easy to clean"], "cons": ["Higher price"]},
        {"name": "Model B", "asin": "B000000002", "pros": ["Affordable"], "cons": ["Limited features"]},
    ]

    return {
        "title": title,
        "meta_description": f"{title} — buyer’s guide and tips.",
        "summary": summary,
        "sections": sections,
        "faq": faq,
        "category": "General",
        "tags": [t for t in kw.lower().split() if t] or ["guide", "tips"],
        "sources": sources,
        "product_name": "Editor’s Choice",
        "product_blurb": "Great balance of features and value.",
        "comparison": comparison,
        "internal_topics": ["Setup", "Maintenance", "Alternatives"]
    }

def call_openai(keyword: str) -> dict:
    """
    Hook for AI generation. Right now it returns the stub to avoid any external dependency.
    If you set OPENAI_API_KEY later, you can replace this with real API calls.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    # For now, always return stub so CI never fails on missing deps
    # Later: if api_key: call the API and return structured content.
    return _stub_post(keyword)

