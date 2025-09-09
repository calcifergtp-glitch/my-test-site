def ga4(ga_id: str) -> str:
    if not ga_id:
        return ""
    return f"""<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date()); gtag('config', '{ga_id}');
</script>
"""

def plausible(domain: str) -> str:
    if not domain:
        return ""
    return f"""<script defer data-domain="{domain}" src="https://plausible.io/js/plausible.js"></script>
"""
