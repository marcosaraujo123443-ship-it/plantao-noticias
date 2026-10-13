#!/usr/bin/env python3
"""Lê os feeds RSS das seções e atualiza noticias.json (roda no GitHub Actions, sem IA)."""
import json, re, html, math, unicodedata, urllib.request
from collections import Counter
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept": "application/rss+xml, application/xml, text/xml, */*"}
SECOES = ["Política", "IA", "Futebol", "Agro", "Mercado"]
POR_SECAO, POR_FONTE, MAX_DIAS = 15, 4, 7
FUT = re.compile(r"futebol|sele[çc][ãa]o|brasileir[ãa]o|libertadores|copa do brasil|sul-americana|t[ée]cnico|gol|"
                 r"flamengo|palmeiras|corinthians|s[ãa]o paulo|santos|vasco|gr[êe]mio|internacional|botafogo|"
                 r"fluminense|cruzeiro|atl[ée]tico|bahia|fortaleza|cbf|fifa", re.I)

IA = re.compile(r"\bIA\b|\bAI\b|intelig[êe]ncia artificial|ChatGPT|OpenAI|Anthropic|\bClaude\b|Gemini|Copilot|chatbot|"
                r"\bLLM|Nvidia|deepfake|algoritmo")

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
    ("Política", "g1", "https://g1.globo.com/rss/g1/politica/", None),
    ("Política", "CNN Brasil", "https://www.cnnbrasil.com.br/feed/", link_tem("/politica/", "/eleicoes/")),
    ("IA", "g1", "https://g1.globo.com/rss/g1/tecnologia/", lambda it: bool(IA.search(it["titulo"] + " " + it["resumo"]))),
    ("IA", "CNN Brasil", "https://www.cnnbrasil.com.br/feed/", link_tem("/inteligencia-artificial/")),
    ("IA", "Olhar Digital", "https://olhardigital.com.br/editorias/pro/inteligencia-artificial/feed/", None),
    ("IA", "Tecnoblog", "https://tecnoblog.net/tema/inteligencia-artificial/feed/", None),
    ("Futebol", "Gazeta Esportiva", "https://www.gazetaesportiva.com/futebol/feed/", None),
    ("Futebol", "Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/esportes/feed.xml",
     lambda it: bool(FUT.search(it["titulo"] + " " + it["resumo"]))),
    ("Futebol", "ge", "https://ge.globo.com/rss/ge/futebol/", None),
    ("Futebol", "CNN Brasil", "https://www.cnnbrasil.com.br/feed/", link_tem("/esportes/futebol/")),
    ("Agro", "g1", "https://g1.globo.com/rss/g1/economia/agronegocios/", None),
    ("Agro", "CNN Brasil", "https://www.cnnbrasil.com.br/feed/", link_tem("/agro/")),
    ("Agro", "Canal Rural", "https://www.canalrural.com.br/feed/", lambda it: "/opiniao" not in it["link"]),
    ("Mercado", "Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml", None),
    ("Mercado", "InfoMoney", "https://www.infomoney.com.br/feed/",
     link_tem("/mercados/", "/economia/", "/consumo/", "/business/", "/onde-investir/")),
    ("Mercado", "g1", "https://g1.globo.com/rss/g1/economia/", lambda it: "/agronegocios/" not in it["link"]),
    ("Mercado", "CNN Brasil", "https://www.cnnbrasil.com.br/feed/",
     lambda it: "/economia/" in it["link"] and not re.search(r"branded-content|/inteligencia-artificial/|/tecnologia/", it["link"])),
]

# Agrupamento de notícias sobre o mesmo assunto (títulos e resumos parecidos, com peso maior para palavras raras)
VAZIAS = set("""a o as os de da do das dos e em no na nos nas um uma uns umas para por pelo pela pelos pelas com sem sobre que
se ao aos à às é ser foi são diz após apos contra entre mais menos como sua seu suas seus já ja até ate não nao tem ter vai faz
confira veja entenda saiba hoje ao vivo the of to and in""".split())
GENERICAS = set("confir veja entend saiba melhor semana hoje vivo noticia brasil govern anunci".split())

def raizes(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w[:6] for w in re.findall(r"[a-z0-9]+", t) if len(w) > 2 and w not in VAZIAS}

def agrupar(itens, limiar=0.35):
    """Mantém a notícia mais recente de cada assunto; as demais viram "também em"."""
    tit = [raizes(i["titulo"]) for i in itens]
    doc = [tit[k] | raizes(i["resumo"][:200]) for k, i in enumerate(itens)]
    df, n = Counter(w for d in doc for w in d), len(doc)
    vet = []
    for k, d in enumerate(doc):
        v = {w: math.log((n + 1) / (df[w] + 0.5)) * (2 if w in tit[k] else 1) for w in d}
        vet.append((v, math.sqrt(sum(x * x for x in v.values())) or 1))
    def parecido(a, b):
        comum = vet[a][0].keys() & vet[b][0].keys()
        if len((tit[a] & tit[b]) - GENERICAS) < 2: return False
        return sum(vet[a][0][w] * vet[b][0][w] for w in comum) / (vet[a][1] * vet[b][1]) >= limiar
    ordem = sorted(range(n), key=lambda k: itens[k]["data"], reverse=True)
    lideres, saida = [], []
    for k in ordem:
        lider = next((l for l in lideres if parecido(l, k)), None)
        if lider is None:
            lideres.append(k); itens[k]["tambem"] = []; saida.append(itens[k])
        elif itens[k]["fonte"] != itens[lider]["fonte"] and all(t["fonte"] != itens[k]["fonte"] for t in itens[lider]["tambem"]):
            itens[lider]["tambem"].append({"fonte": itens[k]["fonte"], "link": itens[k]["link"]})
    for i in saida:
        if not i["tambem"]: del i["tambem"]
    return saida

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
        link = campos.get("link", "").strip()
        yield {"titulo": limpa(campos.get("title")), "link": link,
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
    ativas = {f for _, f, _, _ in FEEDS}  # fonte retirada da lista some do site na hora
    unicos = agrupar([dict(i) for i in por_link.values() if i["data"] >= limite and i["fonte"] in ativas])
    final = []
    for s in SECOES:
        lst, por_fonte = [], Counter()
        for i in sorted((i for i in unicos if i["secao"] == s), key=lambda i: i["data"], reverse=True):
            if por_fonte[i["fonte"]] >= POR_FONTE or len(lst) >= POR_SECAO: continue
            por_fonte[i["fonte"]] += 1; lst.append(i)
        final += lst
    if not final:
        raise SystemExit("Nenhuma notícia coletada: " + "; ".join(erros))
    novo = {"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "secoes": SECOES,
            "itens": final, "erros": erros}
    json.dump(novo, open("noticias.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(final), "notícias;", sum(len(i.get("tambem", [])) for i in final), "repetidas agrupadas;", len(erros), "erros")

if __name__ == "__main__":
    main()
