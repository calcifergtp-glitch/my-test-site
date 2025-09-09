from typing import List, Dict

DISCLOSURE_INLINE = '<p class="disclosure">We may earn commissions from links on this page (no extra cost to you).</p>'

def product_box(p: Dict) -> str:
    title = p.get('title', 'Product')
    url = p.get('url', '#')
    price = p.get('price', '')
    features = p.get('features', [])
    rel = 'sponsored nofollow noopener noreferrer'
    li = "".join(f"<li>{f}</li>" for f in features)
    price_html = f'<div class="price">{price}</div>' if price else ''
    return f"""<div class="product-box">
  <div class="product-header">
    <h3>{title}</h3>
    {price_html}
  </div>
  <ul class="features">{li}</ul>
  <a class="btn-cta" href="{url}" target="_blank" rel="{rel}">Check Price</a>
</div>
"""

def inject_blocks(html: str, products: List[Dict]) -> str:
    blocks = ''.join(product_box(p) for p in (products or []))
    return DISCLOSURE_INLINE + (blocks or '') + html
