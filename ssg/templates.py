# ssg/templates.py
# NOTE: Any literal { } in CSS/JS must be doubled {{ }} so Python .format() doesn't treat them as placeholders.

INDEX_SHELL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{brand} — Blog</title>
<meta name="description" content="{desc}"/>
<link rel="canonical" href="{site_url}/"/>
<link rel="alternate" type="application/atom+xml" title="{brand} Feed" href="{base_prefix}/feed.xml">
<link rel="stylesheet" href="{theme_css}">
{analytics}
<style>
:root {{ --brand: #2f6feb; }}
.navbar {{ background: var(--brand); }}
.navbar a, .navbar .navbar-item {{ color:#fff; }}
.card-image img {{ object-fit:cover; width:100%; height:180px }}
.pagination-list .pagination-link.is-current {{ background:var(--brand); color:#fff; border-color:var(--brand);}}
</style>
</head><body>

<nav class="navbar"><div class="container">
  <div class="navbar-brand"><a class="navbar-item" href="{base_prefix}/">🔥 {brand}</a></div>
  <div class="navbar-menu">
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
</div></nav>

{container_open}
<div class="columns">
  <div class="column is-three-quarters">
    <h2 class="title is-4">Latest Posts</h2>
    {search_bar}
    <div class="columns is-multiline">
      {post_cards}
    </div>
    {pagination}
  </div>
  <aside class="column">
    <div class="box"><h3 class="title is-5">Categories</h3>{category_list}</div>
    <div class="box"><h3 class="title is-5">Tags</h3><div class="tags">{tag_cloud}</div></div>
    <div class="box"><h3 class="title is-6">Affiliate Disclosure</h3><p>We may earn a commission from links on this page.</p></div>
  </aside>
</div>
<footer class="footer"><div class="content has-text-centered"><p>© {year} {brand}</p></div></footer>
{container_close}
<script src="{base_prefix}/assets/js/telemetry.js"></script>
</body></html>
"""

POST_TPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — {brand}</title>
<meta name="description" content="{meta_desc}"/>
<link rel="canonical" href="{site_url}/posts/{slug}/"/>
<link rel="stylesheet" href="{theme_css}">
{analytics}
<style>.tag.is-link {{ text-decoration:none }}</style>
</head><body>

{container_open}
<h1 class="title">{title}</h1>
<p class="subtitle">Published {date}</p>
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

  {inline_cta}
  {body_html}
  {intext_related}
  {sources_html}

  <hr/>
  <p><strong>Share:</strong>
    <a href="https://twitter.com/intent/tweet?url={site_url}/posts/{slug}/&text={title}" target="_blank" rel="noopener nofollow">X</a> ·
    <a href="https://www.facebook.com/sharer/sharer.php?u={site_url}/posts/{slug}/" target="_blank" rel="noopener nofollow">Facebook</a> ·
    <a href="https://www.reddit.com/submit?url={site_url}/posts/{slug}/&title={title}" target="_blank" rel="noopener nofollow">Reddit</a>
  </p>

  <article class="box" style="margin-top:1rem">
    <p class="title is-6">About the author</p>
    <p><strong>{author_name}</strong> — {author_bio} {author_link}</p>
  </article>
</div>

{related_html}
<hr/><h2 class="title is-5">Top Pick</h2>{top_pick_box}
{comparison_table}

<footer class="footer"><div class="content has-text-centered"><p>© {year} {brand}</p></div></footer>
{container_close}
<script src="{base_prefix}/assets/js/telemetry.js"></script>
</body></html>
"""

PAGE_TPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} — {brand}</title>
<link rel="canonical" href="{site_url}/{slug}.html"/>
<link rel="stylesheet" href="{theme_css}">{analytics}</head><body>
{container_open}<div class="content">{body_html}</div>
<footer class="footer"><div class="content has-text-centered"><p>© {year} {brand}</p></div></footer>
{container_close}<script src="{base_prefix}/assets/js/telemetry.js"></script></body></html>
"""

NOT_FOUND_TPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Not Found — {brand}</title>
<link rel="stylesheet" href="{theme_css}"></head><body>
{container_open}<h1 class="title">404 — Page not found</h1><p><a class="button is-link is-light" href="{base_prefix}/">Back to Home</a></p>{container_close}
</body></html>
"""
