#!/usr/bin/env python3
"""IndexNow (Bing, Yandex, Seznam e outros): avisa na hora os buscadores sobre páginas novas do site.
Compara o sitemap que vai ao ar (dist/sitemap.xml) com o que está publicado e envia só os endereços novos,
mais a página inicial. A chave fica em /21339fef03e31e51ad22be47a0abe380.txt.
    python3 scripts/indexnow.py dist sitemap_publicado.xml"""
import json, os, re, sys, urllib.request
SITE, CHAVE = "https://plantaoinforma.com.br/", "21339fef03e31e51ad22be47a0abe380"
def locs(caminho):
    try: return set(re.findall(r"<loc>([^<]+)</loc>", open(caminho, encoding="utf-8").read()))
    except Exception: return set()
novo, antigo = locs(sys.argv[1] + "/sitemap.xml"), locs(sys.argv[2] if len(sys.argv) > 2 else "")
urls = sorted(novo) if os.environ.get("INDEXNOW_TUDO") else sorted(novo - antigo) if antigo else []
if not urls: print("IndexNow: nenhuma página nova."); sys.exit()
urls = list(dict.fromkeys([SITE] + urls))[:500]
corpo = json.dumps({"host": "plantaoinforma.com.br", "key": CHAVE, "keyLocation": f"{SITE}{CHAVE}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=corpo, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r: print("IndexNow:", r.status, len(urls), "endereços")
except Exception as e: print("::warning::IndexNow:", e)
