# ssg/analytics.py
from pathlib import Path

TELEMETRY_JS = r"""(function(){
  function isPlausible(){ return typeof window.plausible === 'function'; }
  function hasGA(){ return typeof window.gtag === 'function'; }
  function sendEvent(name, props){
    try{
      if(isPlausible()){ window.plausible(name, { props: props || {} }); }
      if(hasGA()){ window.gtag('event', name, props || {}); }
    }catch(e){}
  }
  function onLinkClick(e){
    const a = e.target.closest('a');
    if(!a) return;
    const isExternal = a.host && a.host !== window.location.host;
    const ev = (a.dataset.event || (isExternal ? 'outbound_click' : null));
    if(!ev) return;
    const props = {
      href: a.href,
      net: a.dataset.net || '',
      asin: a.dataset.asin || '',
      sku: a.dataset.sku || '',
      label: a.dataset.label || a.textContent.trim().slice(0,80)
    };
    sendEvent(ev, props);
  }
  document.addEventListener('click', onLinkClick, {capture:true});
  function ctaImpressions(){
    document.querySelectorAll('[data-event="cta_impression"]').forEach(function(el){
      if(el.dataset._sent) return;
      el.dataset._sent = '1';
      sendEvent('cta_impression', {id: el.id || '', label: el.dataset.label || ''});
    });
  }
  if(document.readyState !== 'loading') ctaImpressions();
  else document.addEventListener('DOMContentLoaded', ctaImpressions);
  window.SS_trackSearch = function(q){
    if(!q) return;
    sendEvent('search', {query: String(q).slice(0,120)});
  };
  window.SS_markImpression = function(el, label){
    try{
      if(!el) return;
      el.dataset.event = 'cta_impression';
      el.dataset.label = label || el.id || '';
      sendEvent('cta_impression', {id: el.id || '', label: el.dataset.label || ''});
    }catch(e){}
  };
})();"""

def write_telemetry_js(site_dir: Path, base_prefix: str):
    assets = site_dir / "assets" / "js"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "telemetry.js").write_text(TELEMETRY_JS, encoding="utf-8")
