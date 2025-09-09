# ssg/content.py — no external deps; simple stub generator
import os

def generate_posts(keywords):
    posts = []
    for kw in keywords:
        title = kw.title()
        slug = kw.replace(" ", "-").lower()
        body = (
            f"<h1>{title}</h1>"
            f"<p>This is an auto-generated stub article about <strong>{kw}</strong>. "
            "You can enable AI later to expand this into a long, high-quality post.</p>"
            "<h2>Overview</h2><p>Key points, tips, and a quick summary go here.</p>"
            "<h2>Buying Tips</h2><p>What to look for, specs, and budget advice.</p>"
            "<h2>Alternatives</h2><p>Comparable options and pros/cons.</p>"
            "<h2>FAQ</h2><p><strong>Q:</strong> Is it worth it?<br><strong>A:</strong> Depends on your needs and budget.</p>"
        )
        posts.append({
            "title": title,
            "slug": slug,
            "content": body,
            "tags": [t for t in kw.lower().split() if t],
            "category": "General"
        })
    return posts
