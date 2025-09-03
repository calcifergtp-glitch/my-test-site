import os
from typing import Tuple, Dict

THEMES: Dict[str, Dict[str, str]] = {
    "bulma": {
        "css": "https://cdn.jsdelivr.net/npm/bulma@1.0.2/css/bulma.min.css",
        "container_open": '<section class="section"><div class="container">',
        "container_close": "</div></section>",
    },
    "pico": {
        "css": "https://unpkg.com/@picocss/pico@latest/css/pico.min.css",
        "container_open": '<main class="container">',
        "container_close": "</main>",
    },
    "water": {
        "css": "https://cdn.jsdelivr.net/npm/water.css@2/out/water.css",
        "container_open": '<main class="container">',
        "container_close": "</main>",
    },
}
DEFAULT_THEME = "bulma"

def choose_theme(force: str = None) -> Tuple[str, Dict[str, str]]:
    key = (force or os.environ.get("SITESMITH_THEME") or DEFAULT_THEME).strip().lower()
    return (key, THEMES.get(key, THEMES[DEFAULT_THEME]))
