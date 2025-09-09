# ssg/templates.py
# NOTE: CSS/JS literal braces are doubled {{ }} for Python .format() escaping.

INDEX_SHELL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'self' https: data:; img-src https: data:; script-src 'self' https://plausible.io https://www.googletagmanager.com https://www.google-analytics.com 'unsafe-inline'; style-src 'self' https: 'unsafe-inline'; connect-src https:; object-src 'none'; base-uri 'self'; form-action 'self' https://formspree.io; upgrade-insecure-requests">
<meta name="referrer" content="no-referrer-when-downgrade">
<title>{brand} — Blog</title>
<meta name="description" content="{desc}"/>
<link rel="canonical" href="{site_url}/"/>
<link rel="alternate" type="application/atom+xml" title="{brand} Feed" href="{base_prefix}/feed.xml">
<link rel="stylesheet" href="{theme_css}">
{analytics}
<style>
:root {{ --brand: #2f6feb; }}
.navbar {{ background: var(--brand); }}
.navbar a, .navbar .navbar-item {{ color: #fff; }}
.tag.is-link {{ text-decoration:none }}
.card-image img {{ object-fit:cover; width:100%; height:180px }}
.hero.is-dark a {{ color: #fff; text-decoration: underline }}
.hero .title a {{ color:#fff; text-decoration:none }}
.product-box .subtitle {{ margin:0; }}
.cta-banner {{ display:flex; align-items:center; justify-content:space-between }}
.pagination-list .pagination-link.is-current {{ background:var(--brand); color:#fff; border-color:var(--brand);}}
.section-title {{ margin-top:2rem }}
.toc-box {{ position:sticky; top:1rem }}
</style>

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "{brand}",
  "url": "{site_url}/",
  "potentialAction": {{
    "@type": "SearchAction",
    "target": "{site_url}/?q={{q}}",
    "query-input": "required name=q"
  }}
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{brand}",
  "url": "{site_url}/"
}}
</script>
</head><body>

<nav class="navbar" role="navigation" aria-label="main navigation">
  <div class="container">
    <div class="navbar-brand">
      <a class="navbar-item" href="{base_prefix}/">🔥 {brand}</a>
      <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navMain">
        <span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span>
      </a>
    </div>
    <div id="navMain" class="navbar-menu">
      <div class="navbar-start">
        <a class="navbar-item" href="{base_prefix}/">Home</a>
        <a class="navbar-item" href="{base_prefix}/about.html">About</a>
        <a class="navbar-item" href="{base_prefix}/contact.html">Contact</a>
        <a class="navbar-item" href="{base_prefix}/privacy.html">Privacy</a>
        <a class="navbar-item" href="{base_prefix}/disclosure.html">Disclosure</a>
        <a class="navbar-item" href="{base_prefix}/archive.html">Archive</a>
        <a class="navbar-item" href="{base_prefix}/sitemap.xml">Sitemap</a>
        <a class="navbar-item" href="{base_prefix}/feed.xml">RSS</a>
      </div>
    </div>
  </div>
</nav>

<!-- FEATURED HERO -->
<section class="hero is-dark">
  <div class="hero-body">
    <div class="container">
      <p class="subtitle">Today on</p>
      <h1 class="title"><a href="{base_prefix}/posts/{hero_slug}/">{hero_title}</a></h1>
      <p style="max-width:720px">{hero_summary}</p>
      <p style="margin-top:1rem">
        <a class="button is-light is-outlined" href="{base_prefix}/posts/{hero_slug}/">Read the feature →</a>
      </p>
    </div>
  </div>
</section>

{container_open}
<div class="columns">
  <div class="column is-three-quarters">
    <!-- Latest Posts -->
    <h2 class="title is-4 section-title">Latest Posts</h2>
    {search_bar}
    <div class="columns is-multiline">
      {post_cards}
    </div>
    {pagination}

    <!-- Category Sections -->
    {category_sections}
  </div>

  <aside class="column">
    <div class="box">
      <h3 class="title is-5">Categories</h3>
      {category_list}
    </div>
    <div class="box">
      <h3 class="title is-5">Tags</h3>
      <div class="tags">{tag_cloud}</div>
    </div>
    <div class="box">
      <h3 class="title is-6">Affiliate Disclosure</h3>
      <p>This site contains affiliate links. We may earn a commission at no extra cost to you.</p>
    </div>
  </aside>
</div>

<footer class="footer">
  <div class="content has-text-centered">
    <p>© {year} {brand} • <a href="{base_prefix}/sitemap.xml" rel="nofollow">Sitemap</a></p>
  </div>
</footer>
{container_close}

<script src="{base_prefix}/assets/js/telemetry.js"></script>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  const b = document.querySelector('.navbar-burger');
  const m = document.getElementById('navMain');
  if (b && m) b.addEventListener('click', () => {{ b.classList.toggle('is-active'); m.classList.toggle('is-active'); }});
}});
</script>
</body></html>
"""

POST_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'self' https: data:; img-src https: data:; script-src 'self' https://plausible.io https://www.googletagmanager.com https://www.google-analytics.com 'unsafe-inline'; style-src 'self' https: 'unsafe-inline'; connect-src https:; object-src 'none'; base-uri 'self'; form-action 'self' https://formspree.io; upgrade-insecure-requests">
<meta name="referrer" content="no-referrer-when-downgrade">
<title>{title} — {brand}</title>
<meta name="description" content="{meta_desc}"/>
<meta property="og:title" content="{title} — {brand}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{site_url}/posts/{slug}/">
<meta property="og:image" content="{hero_img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} — {brand}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{hero_img}">
<link rel="canonical" href="{site_url}/posts/{slug}/"/>
<link rel="stylesheet" href="{theme_css}">
{analytics}
<style>.tag.is-link {{ text-decoration:none }}</style>

<!-- Article JSON-LD + Breadcrumb + (optional) FAQ -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "{site_url}/"
    }},
    {{
      "@type": "ListItem",
      "position": 2,
      "name": "{category}",
      "item": "{site_url}/category/{cat_slug}/"
    }},
    {{
      "@type": "ListItem",
      "position": 3,
      "name": "{title}",
      "item": "{site_url}/posts/{slug}/"
    }}
  ]
}}
</script>
<script type="application/ld+json">
{article_schema}
</script>
{faq_schema}
</head><body>

<section class="hero is-link">
  <div class="hero-body">
    <div class="container">
      <nav class="breadcrumb is-small" aria-label="breadcrumbs">
        <ul>
          <li><a href="{base_prefix}/">Home</a></li>
          <li><a href="{base_prefix}/category/{cat_slug}/">{category}</a></li>
          <li class="is-active"><a aria-current="page">{title}</a></li>
        </ul>
      </nav>
      <h1 class="title">{title}</h1>
      <p class="subtitle">Published {date}</p>
    </div>
  </div>
</section>

{container_open}
<div class="columns">
  <div class="column is-three-quarters">
    <figure class="image is-16by9" style="margin-bottom:1rem">
      <img src="{hero_img}" alt="{title}" loading="lazy">
    </figure>

    <!-- Table of Contents -->
    {toc_html}

    <div class="content">
      <p>
        <span class="tag is-info is-light">Category</span>
        <a class="tag is-link is-light" href="{base_prefix}/category/{cat_slug}/">{category}</a>
        &nbsp;
        <span class="tag is-info is-light">Tags</span>
        {tags_html}
      </p>

      <!-- Inline CTA -->
      {inline_cta}

      {body_html}

      <!-- Further reading internal links -->
      {intext_related}

      <!-- Sources -->
      {sources_html}

      <hr/>
      <div class="level">
        <div class="level-left">
          <div>
            <p class="has-text-weight-bold">Share</p>
            <p class="buttons">
              <a class="button is-small" href="https://twitter.com/intent/tweet?url={site_url}/posts/{slug}/&text={title}" target="_blank" rel="noopener nofollow">Twitter/X</a>
              <a class="button is-small" href="https://www.facebook.com/sharer/sharer.php?u={site_url}/posts/{slug}/" target="_blank" rel="noopener nofollow">Facebook</a>
              <a class="button is-small" href="https://www.reddit.com/submit?url={site_url}/posts/{slug}/&title={title}" target="_blank" rel="noopener nofollow">Reddit</a>
              <button class="button is-small" onclick="navigator.clipboard.writeText('{site_url}/posts/{slug}/');this.innerText='Copied!';">Copy link</button>
            </p>
          </div>
        </div>
      </div>

      <article class="box" style="margin-top:1rem">
        <p class="title is-6">About the author</p>
        <p><strong>{author_name}</strong> — {author_bio} {author_link}</p>
      </article>
    </div>

    {related_html}

    <hr/>
    <h2 class="title is-5">Top Pick</h2>
    {top_pick_box}

    {comparison_table}
  </div>

  <aside class="column">
    <div class="box">
      <p><strong>Disclosure</strong><br/>As an Amazon Associate we earn from qualifying purchases.</p>
    </div>
  </aside>
</div>

<footer class="footer">
  <div class="content has-text-centered">
    <p>© {year} {brand}</p>
  </div>
</footer>
{container_close}
<script src="{base_prefix}/assets/js/telemetry.js"></script>
</body></html>
"""

PAGE_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="Content-Security-Policy" content="default-src 'self' https: data:; img-src https: data:; script-src 'self' https://plausible.io https://www.googletagmanager.com https://www.google-analytics.com 'unsafe-inline'; style-src 'self' https: 'unsafe-inline'; connect-src https:; object-src 'none'; base-uri 'self'; form-action 'self' https://formspree.io; upgrade-insecure-requests">
<meta name="referrer" content="no-referrer-when-downgrade">
<title>{title} — {brand}</title>
<link rel="canonical" href="{site_url}/{slug}.html"/>
<link rel="stylesheet" href="{theme_css}">
{analytics}
</head><body>
<section class="hero is-dark"><div class="hero-body"><div class="container">
  <h1 class="title">{title}</h1>
  <p><a href="{base_prefix}/" class="button is-light is-outlined is-small">Home</a></p>
</div></div></section>

{container_open}
<div class="content">
  {body_html}
</div>
<footer class="footer">
  <div class="content has-text-centered">
    <p>© {year} {brand}</p>
  </div>
</footer>
{container_close}
<script src="{base_prefix}/assets/js/telemetry.js"></script>
</body></html>
"""

NOT_FOUND_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Not Found — {brand}</title>
<link rel="stylesheet" href="{theme_css}">
</head><body>
{container_open}
<h1 class="title">404 — Page not found</h1>
<p>Sorry, we can’t find that page.</p>
<p><a class="button is-link is-light" href="{base_prefix}/">Back to Home</a></p>
{container_close}
</body></html>
"""
