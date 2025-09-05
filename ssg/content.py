import os, json, re
from pathlib import Path
from typing import List

try:
    from openai import OpenAI
except ImportError:
    raise SystemExit("Missing dependency: pip install openai")

def load_keywords(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [k.strip() for k in data.get("keywords", []) if k and k.strip()]

def _safe_json_from_text(text: str):
    m = re.search(r"\{.*\}\s*$", text, re.S)
    if m:
        text = m.group(0)
    return json.loads(text)

def call_openai(keyword: str, model: str = None) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Missing OPENAI_API_KEY. Set it and re-run.")

    client = OpenAI()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""
You are an expert blogger writing helpful, trustworthy content. Make it SCANNABLE and ACTIONABLE.

KEYWORD: "{keyword}"

Return STRICT JSON ONLY (no markdown). Fields:

{{
  "title": "<=65 chars (natural, not stuffed)>",
  "meta_description": "<=155 chars concise benefit-driven summary>",
  "category": "1-2 words (e.g., 'Appliances')",
  "tags": ["3-6 short tags"],
  "summary": "2-3 sentence summary of the whole article",
  "sections": [
    {{"heading":"Quick Take","paragraphs":["2 short paragraphs that summarize your best advice"]}},
    {{"heading":"How It Works (Basics)","paragraphs":["2-3 paragraphs with plain explanations, avoid fluff"]}},
    {{"heading":"Key Buying Factors","paragraphs":["3-5 short bullets or short paragraphs with specifics (sizes, wattage, capacity, materials, safety)"]}},
    {{"heading":"Top Picks & Use Cases","paragraphs":["Explain when to choose each kind of product for different people/budgets"]}},
    {{"heading":"Step-by-Step: Setup & Safety","paragraphs":["Short, safe steps. Add simple safety reminders."]}},
    {{"heading":"Care & Maintenance","paragraphs":["How to keep it working longer, cleaning tips."]}},
    {{"heading":"Alternatives & When Not To Buy","paragraphs":["When a different product might be better; who should skip it."]}}
  ],
  "faq": [
    {{"q":"Beginner question","a":"Short, direct answer."}},
    {{"q":"Safety or care question","a":"Short, direct answer with a caution if relevant."}},
    {{"q":"Value or price question","a":"Short, direct answer."}},
    {{"q":"Longevity or reliability question","a":"Short, direct answer."}}
  ],
  "product_name": "One top pick (short)",
  "product_blurb": "One-sentence benefit statement",
  "comparison": [
     {{"name":"Product A","blurb":"what it's good for","pros":["...","..."],"cons":["..."],"asin":"B000000001"}},
     {{"name":"Product B","blurb":"what it's good for","pros":["...","..."],"cons":["..."],"asin":"B000000002"}},
     {{"name":"Product C","blurb":"what it's good for","pros":["...","..."],"cons":["..."],"asin":"B000000003"}}
  ],
  "internal_topics": ["2-4 related subtopics someone might want next (short)"],
  "sources": [
     {{"title":"General explainer (no paywall)","url":"https://example.com/guide"}},
     {{"title":"Manufacturer safety page","url":"https://example.com/safety"}}
  ]
}}

Rules:
- Be factual. If unsure, keep it general; do not invent statistics.
- Use short paragraphs. Avoid hype.
- DO NOT include markdown or code fences. JSON ONLY.
"""
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Write factual, concise blog content the reader can use immediately."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.55,
    )
    text = res.choices[0].message.content.strip()
    try:
        return _safe_json_from_text(text)
    except Exception:
        # Safe fallback
        return {
            "title": keyword.title(),
            "meta_description": f"Guide about {keyword}.",
            "category": "General",
            "tags": ["general"],
            "summary": f"Quick overview of {keyword}.",
            "sections": [
                {"heading": "Quick Take", "paragraphs": [f"Quick guide to {keyword}.", "Key things buyers should know."]},
                {"heading": "Key Buying Factors", "paragraphs": ["Consider size, budget, and features.", "Look for safety certifications."]},
            ],
            "faq": [],
            "product_name": "Sample Product",
            "product_blurb": "A reliable pick for most people.",
            "comparison": [
                {"name":"Alpha","blurb":"Solid basic pick.","pros":["Affordable"],"cons":["Limited features"],"asin":"B000000001"},
                {"name":"Bravo","blurb":"Balanced option.","pros":["Good value"],"cons":["Sometimes out of stock"],"asin":"B000000002"},
                {"name":"Charlie","blurb":"Premium choice.","pros":["Top performance"],"cons":["Pricey"],"asin":"B000000003"},
            ],
            "internal_topics": ["beginner tips", "care and cleaning"],
            "sources": []
        }
