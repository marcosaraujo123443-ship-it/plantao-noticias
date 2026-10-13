"""Teste temporário: robots completos e caminhos do feed da CNN."""
import sys, re, collections
sys.path.insert(0, "scripts")
from noticias import baixar, itens_do_feed
for site in ("https://ge.globo.com", "https://g1.globo.com", "https://www.cnnbrasil.com.br"):
    t = baixar(site + "/robots.txt").decode("utf-8", "replace")
    print("ROBOTS", site); print("\n".join("  " + l for l in t.splitlines() if l.strip() and not l.startswith("#"))[:1500])
its = list(itens_do_feed(baixar("https://www.cnnbrasil.com.br/feed/")))
c = collections.Counter("/".join(i["link"].split("/")[3:5]) for i in its)
print("CNN caminhos:", c.most_common(40))
for i in its[:60]: print("  CNN", i["data"], i["link"][29:90], "|", i["titulo"][:60])
