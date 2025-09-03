import os, json, re
from pathlib import Path
from typing import List

# deps
try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("Missing dependency: pip install openai")

def load_keywords(path: Path) -> List[str]:
    """Load keywords.json"""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [k.strip() for k in data.get("keywords", []) if k and k.strip()]

def _safe_json_from_text(text: str):
    """extract JSON if model adds extra text"""
    m = re.search(r"\{.*\}\s*$", text, re.S)
    if m:
        text = m.group(0)
    return json.loads(text)

def call_openai(keyword: str, model: str = None) -> dict:
    """Use OpenAI to generate a structured blog post"""
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Missing OPENAI_API_KEY. Set it and re-run.")

    client = OpenAI()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""
You are a concise, helpful blogger. Write a short, useful article.

Keyword: "{keyword}"

Return STRICT JSON only (no markdown), with fields:
{{
  "title": "<=65 chars",
  "meta_description": "<=155 chars",
  "category": "short category",
  "tags": ["tag1","tag2","tag3"],
  "sections": [{{"heading":"...","paragraphs":["...","..."]}}],
  "faq": [{{"q":"...","a":"..."}}, ...],
  "product_name": "short name",
  "product_blurb": "short sentence",
  "comparison": [
     {{"name":"Product A","blurb":"short","pros":["..."],"cons":["..."],"asin":"B000000001"}},
     {{"name":"Product B","blurb":"short","pros":["..."],"cons":["..."],"asin":"B000000002"}},
     {{"name":"Product C","blurb":"short","pros":["..."],"cons":["..."],"asin":"B000000003"}}
  ]
}}
"""
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Write factual, concise blog content the reader can use immediately."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    text = res.choices[0].message.content.strip()
    try:
        return _safe_json_from_text(text)
    except Exception:
        # fallback
        return {
            "title": keyword.title(),
            "meta_description": f"Guide about {keyword}.",
            "category": "General",
            "tags": ["general"],
            "sections": [{"heading": "Overview", "paragraphs": [f"Quick guide to {keyword}."]}],
            "faq": [],
            "product_name": "Sample Product",
            "product_blurb": "A reliable pick for most people.",
            "comparison": [
                {"name":"Alpha","blurb":"Solid basic pick.","pros":["Affordable"],"cons":["Limited features"],"asin":"B000000001"},
                {"name":"Bravo","blurb":"Balanced option.","pros":["Good value"],"cons":["Sometimes out of stock"],"asin":"B000000002"},
                {"name":"Charlie","blurb":"Premium choice.","pros":["Top performance"],"cons":["Pricey"],"asin":"B000000003"},
            ]
        }
