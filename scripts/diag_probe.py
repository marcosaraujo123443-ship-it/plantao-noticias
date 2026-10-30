import json, urllib.request, re, sys
sys.path.insert(0, "scripts"); import noticias as N
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=N.UA), timeout=40).read()
out = []
for u in ["https://blog.grancursosonline.com.br/feed/", "https://www.direcaoconcursos.com.br/artigos/feed/", "https://concursosnobrasil.com/feed/",
          "https://www.qconcursos.com/noticias/feed", "https://agenciabrasil.ebc.com.br/rss/educacao/feed.xml", "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
          "https://news.google.com/rss/search?q=concurso+p%C3%BAblico+edital+when:2d&hl=pt-BR&gl=BR&ceid=BR:pt-419",
          "https://g1.globo.com/rss/g1/economia/", "https://canaltech.com.br/rss/"]:
    it = list(N.itens_do_feed(get(u)))
    out.append(f"== {u} n={len(it)} datas {min(i['data'] or 'z' for i in it)} .. {max(i['data'] or '' for i in it)}")
    for i in it[:3]: out.append(f"   {i['data']} {i['titulo'][:80]} | {i['link'][:90]}")
    if "canaltech" in u: out.append("   paths: " + str(sorted({ '/'.join(i['link'].split('/')[3:4]) for i in it})))
h = get("https://www.pciconcursos.com.br/concursos/").decode("utf-8", "replace")
i = h.find('class="ca"'); out.append("PCI ca at " + str(i) + " :: " + re.sub(r"\s+", " ", h[i-200:i+900]))
open("/tmp/out", "w").write("\n".join(out))
