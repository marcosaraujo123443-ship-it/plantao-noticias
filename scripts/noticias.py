#!/usr/bin/env python3
"""Lê os feeds RSS das seções e atualiza noticias.json (roda no GitHub Actions, sem IA)."""
import json, re, html, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept": "application/rss+xml, application/xml, text/xml, */*"}
SECOES = ["Política", "IA", "Futebol", "Agro", "Mercado"]
POR_SECAO, MAX_DIAS = 12, 7
FUT = re.compile(r"futebol|sele[çc][ãa]o|brasileir[ãa]o|libertadores|copa do brasil|sul-americana|t[ée]cnico|gol|"
                 r"flamengo|palmeiras|corinthians|s[ãa]o paulo|santos|vasco|gr[êe]mio|internacional|botafogo|"
                 r"fluminense|cruzeiro|atl[ée]tico|bahia|fortaleza|cbf|fifa", re.I)

def link_tem(*partes):
    return lambda it: any(p in it["link"] for p in partes)

FEEDS = [
    ("Política", "Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml", None),
    ("Política", "Poder360", "https://www.poder360.com.br/feed/",
     link_tem("/poder-eleicoes", "/poder-governo", "/poder-congresso", "/poder-justica")),
    ("Política", "Agência Senado", "https://www12.senado.leg.br/noticias/feed/todasnoticias/RSS",
     lambda it: not re.match(r"(Áudio|Vídeo|Audio|Video):", it["titulo"])),
    ("Política", "Agência Câmara", "https://www.camara.leg.br/noticias/rss/ultimas-noticias", None),
    ("Política", "InfoMoney", "https://www.infomoney.com.br/feed/", link_tem("/politica/")),
    ("IA", "Olhar Digital", "https://olhardigital.com.br/editorias/pro/inteligencia-artificial/feed/", None),
    ("IA", "Tecnoblog", "https://tecnoblog.net/tema/inteligencia-artificial/feed/", None),
    ("Futebol", "Gazeta Esportiva", "https://www.gazetaesportiva.com/futebol/feed/", None),
    ("Futebol", "Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/esportes/feed.xml",
     lambda it: bool(FUT.search(it["titulo"] + " " + it["resumo"]))),
    ("Agro", "Canal Rural", "https://www.canalrural.com.br/feed/", lambda it: "/opiniao" not in it["link"]),
    ("Mercado", "Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml", None),
    ("Mercado", "InfoMoney", "https://www.infomoney.com.br/feed/",
     link_tem("/mercados/", "/economia/", "/consumo/", "/business/", "/onde-investir/")),
]

def baixar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()

def limpa(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    return re.sub(r"\s+", " ", t).strip()

def sem_credito(t):
    """Tira o crédito da foto do começo do texto ("Foto: Fulano/Agência Brasil Texto...")."""
    m = re.match(r"(Foto|Imagem|Crédito)s?:\s*", t or "")
    if not m: return t
    r = t[m.end():]
    if "/" in r[:60]:
        r = r[r.index("/") + 1:].lstrip()
        ws = r.split(" ")
        for k in (2, 1):
            if len(ws) > k and all(w[:1].isupper() for w in ws[:k]) and ws[k][:1].isupper():
                return " ".join(ws[k:])
        return " ".join(ws[1:])
    ws = r.split(" ")
    for i in range(1, min(len(ws), 5)):
        if ws[i][:1].isupper(): return " ".join(ws[i:])
    return ""

def resumo(t):
    t = sem_credito(limpa(t))
    t = re.sub(r"\s*(The post|O post|Leia mais|Continue lendo).*$", "", t)
    m = re.match(r"(.{40,240}?[.!?])(\s|$)", t)
    r = m.group(1) if m else t[:220]
    if re.match(r"(Foto|Imagem|Crédito)s?:", r): return ""
    return r if len(r) > 20 else ""

def data_iso(s):
    if not s: return None
    s = s.strip()
    try: dt = parsedate_to_datetime(s)
    except Exception:
        try: dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def local(tag): return tag.rsplit("}", 1)[-1]

def itens_do_feed(xml):
    raiz = ET.fromstring(xml)
    for el in raiz.iter():
        if local(el.tag) not in ("item", "entry"): continue
        campos = {}
        for c in el:
            n = local(c.tag)
            if n == "link":
                campos.setdefault("link", (c.text or "").strip() or c.get("href", ""))
            elif n in ("title", "description", "summary", "pubDate", "date", "published", "updated"):
                campos.setdefault(n, c.text or "")
        yield {"titulo": limpa(campos.get("title")), "link": campos.get("link", "").strip(),
               "resumo": resumo(campos.get("description") or campos.get("summary")),
               "data": data_iso(campos.get("pubDate") or campos.get("date") or campos.get("published") or campos.get("updated"))}

def main():
    try:
        atual = json.load(open("noticias.json", encoding="utf-8"))
    except Exception:
        atual = {"itens": []}
    por_link = {i["link"]: i for i in atual.get("itens", [])}
    erros, cache = [], {}
    for secao, fonte, url, filtro in FEEDS:
        try:
            if url not in cache: cache[url] = list(itens_do_feed(baixar(url)))
            n = 0
            for it in cache[url]:
                if not it["titulo"] or not it["link"] or not it["data"]: continue
                if filtro and not filtro(it): continue
                velho = por_link.get(it["link"], {})
                por_link[it["link"]] = {"secao": velho.get("secao", secao), "fonte": fonte, "editoria": velho.get("secao", secao),
                                        "titulo": it["titulo"], "link": it["link"], "data": it["data"],
                                        "resumo": it["resumo"] or resumo(velho.get("resumo", ""))}
                n += 1
            print(f"{secao:8} {fonte:17} {n} itens")
        except Exception as e:
            erros.append(f"{fonte} ({secao}): {e}"); print(f"ERRO {fonte}: {e}")
    limite = (datetime.now(timezone.utc) - timedelta(days=MAX_DIAS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    final = []
    for s in SECOES:
        lst = sorted((i for i in por_link.values() if i["secao"] == s and i["data"] >= limite), key=lambda i: i["data"], reverse=True)
        final += lst[:POR_SECAO]
    if not final:
        raise SystemExit("Nenhuma notícia coletada: " + "; ".join(erros))
    novo = {"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "secoes": SECOES,
            "itens": final, "erros": erros}
    json.dump(novo, open("noticias.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(final), "notícias;", len(erros), "erros")

if __name__ == "__main__":
    main()
