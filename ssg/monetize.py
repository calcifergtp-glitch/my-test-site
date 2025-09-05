# ssg/monetize.py
# Reusable monetization components. All external links include sponsored/nofollow + noopener.

import html

def esc(s: str) -> str:
    return html.escape(s or "")

def product_box(name: str, blurb: str, url: str) -> str:
    return f"""
<div class="box product-box" data-event="cta_impression" data-label="top_pick_box">
  <div class="level">
    <div class="level-left">
      <div>
        <p class="title is-6">{esc(name)}</p>
        <p class="subtitle is-7">{esc(blurb)}</p>
      </div>
    </div>
    <div class="level-right">
      <a class="button is-link is-light" href="{esc(url)}" target="_blank"
         rel="sponsored nofollow noopener" data-event="affiliate_click" data-net="amazon" data-label="{esc(name)}">Check price →</a>
    </div>
  </div>
</div>
"""

def cta_banner(text: str, url: str) -> str:
    return f"""
<div class="notification is-link is-light cta-banner" data-event="cta_impression" data-label="inline_banner">
  <strong>{esc(text)}</strong>
  <a class="button is-link is-light is-small" style="margin-left:.5rem" href="{esc(url)}" target="_blank"
     rel="sponsored nofollow noopener" data-event="affiliate_click" data-net="amazon" data-label="{esc(text)}">Shop now →</a>
</div>
"""

def pros_cons(name: str, pros: list, cons: list, url: str) -> str:
    pros_li = "".join(f"<li>{esc(p)}</li>" for p in (pros or []))
    cons_li = "".join(f"<li>{esc(c)}</li>" for c in (cons or []))
    return f"""
<div class="box pros-cons" data-event="cta_impression" data-label="pros_cons_{esc(name)}">
  <p class="title is-6">{esc(name)}</p>
  <div class="columns">
    <div class="column">
      <p><strong>Pros</strong></p>
      <ul>{pros_li or "<li>—</li>"}</ul>
    </div>
    <div class="column">
      <p><strong>Cons</strong></p>
      <ul>{cons_li or "<li>—</li>"}</ul>
    </div>
  </div>
  <p><a class="button is-link is-light is-small" href="{esc(url)}" target="_blank"
        rel="sponsored nofollow noopener" data-event="affiliate_click" data-net="amazon" data-label="{esc(name)}">View price →</a></p>
</div>
"""

def comparison_rows(items: list, amazon_tag: str) -> str:
    rows = []
    for it in items or []:
        asin = (it.get("asin") or "B000000000").strip()
        url = f"https://www.amazon.com/dp/{asin}?tag={amazon_tag}"
        rows.append(f"""
<tr>
  <td><strong>{esc(it.get('name','Product'))}</strong><br/><small>{esc(it.get('blurb',''))}</small></td>
  <td>{esc(", ".join(it.get('pros') or [])) or "—"}</td>
  <td>{esc(", ".join(it.get('cons') or [])) or "—"}</td>
  <td><a class="button is-link is-light is-small" href="{url}" target="_blank"
         rel="sponsored nofollow noopener" data-event="affiliate_click" data-net="amazon" data-asin="{esc(asin)}" data-label="{esc(it.get('name','Product'))}">Check price →</a></td>
</tr>""")
    return "".join(rows)
