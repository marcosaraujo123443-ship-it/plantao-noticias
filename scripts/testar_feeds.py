"""Teste temporário de feeds candidatos (status, nº de itens, exemplo, robots)."""
import sys, urllib.request
sys.path.insert(0, "scripts")
from noticias import baixar, itens_do_feed, UA
C = {
 "g1 política": "https://g1.globo.com/rss/g1/politica/",
 "g1 economia": "https://g1.globo.com/rss/g1/economia/",
 "g1 agro": "https://g1.globo.com/rss/g1/economia/agronegocios/",
 "g1 tecnologia": "https://g1.globo.com/rss/g1/tecnologia/",
 "g1 geral": "https://g1.globo.com/rss/g1/",
 "ge futebol": "https://ge.globo.com/rss/ge/futebol/",
 "ge geral": "https://ge.globo.com/rss/ge/",
 "cnn política": "https://www.cnnbrasil.com.br/politica/feed/",
 "cnn economia": "https://www.cnnbrasil.com.br/economia/feed/",
 "cnn esportes": "https://www.cnnbrasil.com.br/esportes/feed/",
 "cnn futebol": "https://www.cnnbrasil.com.br/esportes/futebol/feed/",
 "cnn tecnologia": "https://www.cnnbrasil.com.br/tecnologia/feed/",
 "cnn agro": "https://www.cnnbrasil.com.br/economia/agro/feed/",
 "cnn geral": "https://www.cnnbrasil.com.br/feed/",
 "folha poder": "https://feeds.folha.uol.com.br/poder/rss091.xml",
 "folha mercado": "https://feeds.folha.uol.com.br/mercado/rss091.xml",
 "folha esporte": "https://feeds.folha.uol.com.br/esporte/rss091.xml",
 "folha tec": "https://feeds.folha.uol.com.br/tec/rss091.xml",
 "estadão política": "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/politica/",
 "estadão economia": "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/economia/",
 "estadão esportes": "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/esportes/",
 "estadão agro": "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/agro/",
}
for nome, url in C.items():
    try:
        its = list(itens_do_feed(baixar(url)))
        ok = [i for i in its if i["titulo"] and i["link"] and i["data"]]
        ex = ok[0] if ok else (its[0] if its else {})
        print(f"OK   {nome:18} {len(its):3} itens, {len(ok):3} completos | {ex.get('data','')} | {ex.get('titulo','')[:70]} | resumo {len(ex.get('resumo') or '')} | {ex.get('link','')[:60]}")
    except Exception as e:
        print(f"ERRO {nome:18} {str(e)[:100]}")
for site in ("https://g1.globo.com", "https://ge.globo.com", "https://www.cnnbrasil.com.br", "https://www.folha.uol.com.br", "https://www.estadao.com.br"):
    try:
        t = baixar(site + "/robots.txt").decode("utf-8", "replace")
        print("ROBOTS", site, "|", " ; ".join(l.strip() for l in t.splitlines() if l.lower().startswith(("disallow", "user-agent")) and ("rss" in l.lower() or "feed" in l.lower() or l.strip() in ("Disallow: /", "User-agent: *")))[:300])
    except Exception as e:
        print("ROBOTS", site, "erro", e)
