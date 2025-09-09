# ssg/themes.py — minimal theme registry
THEMES = {
    "bulma": {
        "css": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.4/css/bulma.min.css",
        "container_open": "<section class='section'><div class='container'>",
        "container_close": "</div></section>",
    }
}

def choose_theme(force=None):
    key = force or "bulma"
    return key, THEMES["bulma"]
