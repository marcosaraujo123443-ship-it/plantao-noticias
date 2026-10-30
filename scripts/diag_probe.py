import json, urllib.request, re, sys
sys.path.insert(0, "scripts"); import noticias as N
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=N.UA), timeout=40).read()
out = []
for u in ["https://www.cnnbrasil.com.br/feed/", "https://g1.globo.com/rss/g1/saude/", "https://canaltech.com.br/rss/saude/", "https://agenciabrasil.ebc.com.br/rss/saude/feed.xml",
          "https://agenciabrasil.ebc.com.br/rss/geral/feed.xml", "https://agencia.fiocruz.br/rss.xml", "https://www.gov.br/saude/pt-br/assuntos/noticias/RSS",
          "https://canaltech.com.br/rss/ciencia/", "https://olhardigital.com.br/editorias/ciencia-e-espaco/feed/", "https://g1.globo.com/rss/g1/ciencia/"]:
    it = list(N.itens_do_feed(get(u)))
    out.append(f"== {u} n={len(it)} datas {min(i['data'] or 'z' for i in it)} .. {max(i['data'] or '' for i in it)}")
    for i in it[:3]: out.append(f"   {i['data']} {i['titulo'][:80]} | {i['link'][:90]}")
    if "cnnbrasil" in u: out.append("   paths: " + str(sorted({ '/'.join(i['link'].split('/')[3:4]) for i in it})))
open("/tmp/out", "w").write("\n".join(out))
