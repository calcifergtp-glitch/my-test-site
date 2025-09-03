# ssg/templates.py
# HTML templates for homepage, posts, and pages
# NOTE: all CSS braces are doubled {{ }} so Python .format() doesn't treat them as placeholders.

INDEX_SHELL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{brand} — Blog</title>
<meta name="description" content="{desc}"/>
<link rel="canonical" href="{site_url}/"/>
<link rel="stylesheet" href="{theme_css}">
{analytics}
<style>
.tag.is-link {{ text-decoration:none }}
.card-image img {{ object-fit:cover; width:100%; height:180px }}
.hero.is-dark a {{ color: #fff; text-decoration: underline }}
</style>
</head><body>
<section class="hero is-dark">
  <div class="hero-body">
    <div class="container">
      <h1 class="title">🔥 {brand}</h1>
      <p class="subtitle">Fresh, helpful articles — generated automatically.</p>
      <p><a class="button is-light is-outlined" href="{base_prefix}/about.html">About</a>
         <a class="button is-light is-outlined" href="{base_prefix}/contact.html">Contact</a>
         <a class="button is-light is-outlined" href="{base_prefix}/privacy.html">Privacy</a>
         <a class="button is-light is-outlined" href="{base_prefix}/disclosure.html">Disclosure</a></p>
    </div>
  </div>
</section>

{container_open}
<div class="columns">
  <div class="column is-three-quarters">
    <h2 class="title is-4">Latest Posts</h2>
    {search_bar}
    <div class="columns is-multiline">
      {post_cards}
    </div>
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
      <h3 class="title is-5">Affiliate Disclosure</h3>
      <p>This site contains affiliate links. We may earn a commission at no extra cost to you.</p>
    </div>
  </aside>
</div>

<footer class="footer">
  <div class="content has-text-centered">
    <p>© {year} {brand} • <a href="{base_prefix}/sitemap.xml">Sitemap</a></p>
  </div>
</footer>
{container_close}
</body></html>
"""

POST_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — {brand}</title>
<meta name="description" content="{meta_desc}"/>
<link rel="canonical" href="{site_url}/posts/{slug}/"/>
<link rel="stylesheet" href="{theme_css}">
{analytics}
<style>.tag.is-link {{ text-decoration:none }}</style>
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

    <div class="content">
      <p>
        <span class="tag is-info is-light">Category</span>
        <a class="tag is-link is-light" href="{base_prefix}/category/{cat_slug}/">{category}</a>
        &nbsp;
        <span class="tag is-info is-light">Tags</span>
        {tags_html}
      </p>
      {body_html}
    </div>

    {related_html}

    <hr/>
    <h2 class="title is-5">Top Pick</h2>
    <div class="box">
      <strong>{product_name}</strong>
      <p>{product_blurb} <a class="button is-link is-light" href="{aff_url}" rel="sponsored nofollow noopener" target="_blank">Check price →</a></p>
    </div>

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
<script type="application/ld+json">{schema}</script>
</body></html>
"""

PAGE_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
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
</body></html>
"""
