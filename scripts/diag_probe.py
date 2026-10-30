import json, urllib.request, re, sys
sys.path.insert(0, "scripts"); import noticias as N
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=N.UA), timeout=40).read()
out = []
a = json.loads(get("https://apiprevmet3.inmet.gov.br/avisos/ativos"))
out.append("chaves " + str(list(a.keys())) + " hoje=" + str(len(a.get("hoje", []))) + " futuro=" + str(len(a.get("futuro", []))))
x = dict(a["hoje"][0]); 
for k, v in x.items():
    s = json.dumps(v, ensure_ascii=False); out.append(f"{k}: {s[:160]}")
for u in ["https://g1.globo.com/rss/g1/concursos-e-emprego/", "https://www.estrategiaconcursos.com.br/blog/feed/",
          "https://agenciagov.ebc.com.br/noticias/RSS", "https://www.gov.br/pt-br/noticias/RSS", "https://www.cnnbrasil.com.br/feed/",
          "https://agenciabrasil.ebc.com.br/rss/geral/feed.xml", "https://agencia.fiocruz.br/rss.xml", "https://www.gov.br/saude/pt-br/assuntos/noticias/RSS",
          "https://canaltech.com.br/rss/ciencia/", "https://olhardigital.com.br/editorias/ciencia-e-espaco/feed/", "https://g1.globo.com/rss/g1/ciencia/"]:
    it = list(N.itens_do_feed(get(u)))
    out.append(f"== {u} n={len(it)} datas {min(i['data'] or 'z' for i in it)} .. {max(i['data'] or '' for i in it)}")
    for i in it[:5]: out.append(f"   {i['data']} {i['titulo'][:80]} | {i['link'][:90]}")
    if "cnnbrasil" in u: out.append("   paths: " + str(sorted({ '/'.join(i['link'].split('/')[3:5]) for i in it})))
open("/tmp/out", "w").write("\n".join(out))
