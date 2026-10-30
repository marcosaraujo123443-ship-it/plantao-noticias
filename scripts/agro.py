#!/usr/bin/env python3
"""Cotações do agro (páginas públicas de cotações do Notícias Agrícolas) e grava agro.json (roda no GitHub Actions)."""
import json, re, sys, time, html as H, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
BASE = "https://www.noticiasagricolas.com.br/cotacoes/"
PAGINAS = ["soja", "milho", "boi-gordo", "cafe", "trigo", "algodao", "sucroenergetico", "arroz", "feijao",
           "leite", "frango", "suinos", "laranja"]

def texto(url):
    for tent in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if tent == 2: raise
            time.sleep(3)

def limpo(s):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def tabelas(pg):
    """Cada tabela da página com o título mais próximo antes dela, cabeçalho e linhas."""
    out = []
    for m in re.finditer(r"<table\b.*?</table>", pg, re.S | re.I):
        antes = pg[max(0, m.start() - 4000):m.start()]
        tits = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", antes, re.S | re.I)
        fonte = re.findall(r"Fonte:\s*([^<]{2,60})", antes)
        tab = m.group(0)
        cab = [limpo(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", tab, re.S | re.I)]
        linhas = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tab, re.S | re.I):
            cel = [limpo(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
            if cel and any(cel): linhas.append(cel)
        if linhas:
            out.append({"titulo": limpo(tits[-1]) if tits else "", "fonte": fonte[-1].strip() if fonte else "",
                        "cab": cab, "linhas": linhas[:60]})
    return out

def num(s):
    s = (s or "").replace("%", "").replace("+", "").replace(".", "").replace(",", ".").strip()
    try: return float(s)
    except ValueError: return None

# (página, regex do título, nome no site, unidade, coluna do preço, coluna da variação, variação em pontos?)
INDICADORES = [
    ("soja", r"Indicador da Soja ESALQ/B3 - Paranaguá", "Soja (Paranaguá)", "R$/sc 60 kg", 1, 2, False),
    ("milho", r"Indicador do Milho", "Milho (Campinas)", "R$/sc 60 kg", 1, 2, False),
    ("boi-gordo", r"Indicador do Boi Gordo", "Boi gordo (SP)", "R$/@", 1, 2, False),
    ("boi-gordo", r"Bezerro", "Bezerro (MS)", "R$/cabeça", 1, 2, False),
    ("cafe", r"Café Arábica - Cepea", "Café arábica", "R$/sc 60 kg", 1, 2, False),
    ("cafe", r"Café Robusta", "Café robusta", "R$/sc 60 kg", 1, 2, False),
    ("trigo", r"Preço Médio do Trigo", "Trigo (PR)", "R$/t", 2, 3, False),
    ("algodao", r"Algodão - Indicador", "Algodão em pluma", "centavos de R$/lb", 1, 2, False),
    ("sucroenergetico", r"Açúcar Cristal Cepea/Esalq - SP$", "Açúcar cristal (SP)", "R$/sc 50 kg", 1, 2, False),
    ("sucroenergetico", r"Indicador Semanal Etanol Hidratado Cepea", "Etanol hidratado (semanal)", "R$/litro", 1, 2, False),
    ("arroz", r"Indicador Arroz em Casca", "Arroz em casca (RS)", "R$/sc 50 kg", 1, 2, False),
    ("frango", r"Frango Congelado", "Frango congelado", "R$/kg", 1, 2, False),
    ("suinos", r"Indicador do Suíno Vivo", "Suíno vivo", "R$/kg", 2, 3, False),
    ("laranja", r"Laranja Indústria", "Laranja (indústria)", "R$/cx 40,8 kg", 1, 2, False),
]
BOLSAS = [
    ("boi-gordo", r"Boi Gordo - B3", "B3", "Boi gordo", "R$/@", 1, 2, False),
    ("milho", r"Milho - B3", "B3", "Milho", "R$/sc 60 kg", 1, 2, False),
    ("soja", r"Soja CME - B3", "B3", "Soja", "US$/sc 60 kg", 1, 2, False),
    ("cafe", r"Café Arábica 4/5 - B3", "B3", "Café arábica", "US$/sc 60 kg", 1, 2, False),
    ("sucroenergetico", r"Etanol - B3", "B3", "Etanol", "R$/m³", 1, 2, False),
    ("soja", r"^Soja - Bolsa de Chicago", "Chicago", "Soja", "US$/bushel", 1, 3, False),
    ("soja", r"Farelo de Soja - Bolsa de Chicago", "Chicago", "Farelo de soja", "US$/t curta", 1, 3, False),
    ("soja", r"Óleo de Soja - Bolsa de Chicago", "Chicago", "Óleo de soja", "US$/lb", 1, 3, False),
    ("milho", r"Milho - Bolsa de Chicago", "Chicago", "Milho", "US$/bushel", 1, 3, False),
    ("trigo", r"Trigo - Bolsa de Chicago", "Chicago", "Trigo", "US$/bushel", 1, 3, False),
    ("cafe", r"Café - Bolsa de Nova Iorque", "Nova York", "Café arábica", "¢/lb", 1, 3, True),
    ("cafe", r"Café - Bolsa de Londres", "Londres", "Café robusta", "US$/t", 1, 2, True),
    ("sucroenergetico", r"Açúcar - Bolsa de Nova Iorque", "Nova York", "Açúcar", "¢/lb", 1, 2, True),
    ("algodao", r"Algodão - Bolsa de Nova Iorque", "Nova York", "Algodão", "¢/lb", 1, 3, True),
    ("laranja", r"Suco de Laranja - Bolsa", "Nova York", "Suco de laranja", "¢/lb", 1, 2, True),
]
PRACAS = [("soja", r"^Soja - Mercado Físico$", "Soja", "R$/sc 60 kg"), ("milho", r"^Milho - Mercado Físico$", "Milho", "R$/sc 60 kg"),
          ("boi-gordo", r"Mercado Físico - Scot", "Boi gordo (à vista)", "R$/@"),
          ("cafe", r"Café Arábica-Mercado Físico \(Tipo 6 ", "Café arábica (tipo 6)", "R$/sc 60 kg"),
          ("trigo", r"^Trigo - Mercado Físico$", "Trigo", "R$/sc"), ("arroz", r"^Arroz - Mercado Físico$", "Arroz", "R$/sc 50 kg"),
          ("algodao", r"Algodão - IMEA", "Algodão (MT)", "R$/@"), ("leite", r"Leite - Preços ao Produtor", "Leite ao produtor", "R$/litro"),
          ("suinos", r"Suínos - Bolsas", "Suíno vivo", "R$/kg"), ("feijao", r"Feijão Preto Tipo 1", "Feijão preto", "R$/sc")]

def achar(paginas, pag, rx):
    return next((t for t in paginas.get(pag, []) if re.search(rx, t["titulo"])), None)

def pct(preco, var, pontos):
    if var is None: return None
    if not pontos: return var
    base = (preco or 0) - var
    return var / base * 100 if base else None

def montar(paginas):
    ind, bol, pr = [], [], []
    for pag, rx, nome, un, cp, cv, pts in INDICADORES:
        t = achar(paginas, pag, rx)
        if not t: continue
        l = t["linhas"][0]
        if len(l) <= max(cp, cv) or num(l[cp]) is None: continue
        ind.append({"nome": nome, "un": un, "preco": num(l[cp]), "var": pct(num(l[cp]), num(l[cv]), pts),
                    "data": l[0] if re.match(r"\d", l[0]) else "", "fonte": t["fonte"]})
    for pag, rx, bolsa, nome, un, cp, cv, pts in BOLSAS:
        t = achar(paginas, pag, rx)
        if not t: continue
        l = next((l for l in t["linhas"] if len(l) > max(cp, cv) and num(l[cp]) is not None), None)
        if not l: continue
        bol.append({"bolsa": bolsa, "nome": nome, "un": un, "venc": l[0], "preco": num(l[cp]),
                    "var": pct(num(l[cp]), num(l[cv]), pts)})
    for pag, rx, nome, un in PRACAS:
        t = achar(paginas, pag, rx)
        if not t: continue
        linhas = [[l[0], num(l[1]), num(l[-1]) if len(l) > 2 else None] for l in t["linhas"] if len(l) >= 2 and num(l[1]) is not None]
        if t["titulo"].startswith("Mercado Físico - Scot"):
            linhas = [[l[0], num(l[1]), None] for l in t["linhas"] if len(l) >= 2 and num(l[1]) is not None]
        if linhas: pr.append({"nome": nome, "un": un, "fonte": t["fonte"], "linhas": linhas[:12]})
    return ind, bol, pr

UF_NOME = {"acre": "AC", "alagoas": "AL", "amapá": "AP", "amazonas": "AM", "bahia": "BA", "ceará": "CE", "distrito federal": "DF",
           "espírito santo": "ES", "goiás": "GO", "maranhão": "MA", "mato grosso": "MT", "mato grosso do sul": "MS",
           "minas gerais": "MG", "pará": "PA", "paraíba": "PB", "paraná": "PR", "pernambuco": "PE", "piauí": "PI",
           "rio de janeiro": "RJ", "rio grande do norte": "RN", "rio grande do sul": "RS", "rondônia": "RO", "roraima": "RR",
           "santa catarina": "SC", "são paulo": "SP", "sergipe": "SE", "tocantins": "TO"}
UFS = set(UF_NOME.values())
# (produto, página, regex do título, como achar a UF: "barra" = "Cidade/UF", "inicio" = "UF Cidade", "nome" = nome do estado, ou a sigla fixa)
ESTADOS = [
    ("soja", "soja", r"^Soja - Mercado Físico$", "barra"), ("soja", "soja", r"^Soja - Mercado Físico - MS$", "MS"),
    ("soja", "soja", r"^Soja Disponível - IMEA", "MT"),
    ("milho", "milho", r"^Milho - Mercado Físico$", "barra"), ("milho", "milho", r"^Milho - Mercado Físico - MS$", "MS"),
    ("milho", "milho", r"^Milho Disponível - IMEA", "MT"),
    ("cafe", "cafe", r"^Café Arábica-Mercado Físico \(Tipo 6 Bebida", "barra"),
    ("boi", "boi-gordo", r"^Mercado Físico - Scot", "inicio"), ("boi", "boi-gordo", r"^Boi à Vista - IMEA", "MT"),
    ("boi", "boi-gordo", r"^Indicador do Boi$", "nome"),
]
PRODUTOS = [("soja", "Soja", "R$/sc 60 kg"), ("milho", "Milho", "R$/sc 60 kg"), ("cafe", "Café arábica", "R$/sc 60 kg"),
            ("boi", "Boi gordo", "R$/@")]

def estados(paginas):
    """Preço médio por estado das praças de cada produto (soja, milho, café arábica, boi gordo)."""
    soma = {}
    for prod, pag, rx, modo in ESTADOS:
        for t in paginas.get(pag, []):
            if not re.search(rx, t["titulo"]): continue
            for l in t["linhas"]:
                if len(l) < 2: continue
                v = num(l[1])
                if v is None or v <= 0: continue
                if prod == "boi" and v < 150: continue      # algumas praças cotam em R$/kg, não por arroba
                nome = l[0]
                if modo == "barra":
                    m = re.search(r"/([A-Z]{2})\b", nome); uf = m.group(1) if m else None
                elif modo == "inicio":
                    uf = nome.split(" ")[0] if nome.split(" ")[0] in UFS else None
                elif modo == "nome":
                    uf = UF_NOME.get(nome.strip().lower())
                else: uf = modo
                if uf not in UFS: continue
                if prod == "boi" and modo == "nome" and (uf, prod) in soma and soma[(uf, prod)][2] != "nome": continue
                s = soma.setdefault((uf, prod), [0.0, 0, modo])
                s[0] += v; s[1] += 1
            break
    linhas = {}
    for (uf, prod), (tot, n, _) in soma.items():
        linhas.setdefault(uf, {"uf": uf})[prod] = {"media": round(tot / n, 2), "pracas": n}
    ordem = sorted(linhas.values(), key=lambda l: (-sum(1 for p, _, _ in PRODUTOS if p in l), l["uf"]))
    return {"produtos": [{"id": p, "nome": n, "un": u} for p, n, u in PRODUTOS], "linhas": ordem}

def main():
    paginas, erros = {}, []
    if len(sys.argv) > 1: paginas = json.load(open(sys.argv[1], encoding="utf-8"))["paginas"]
    for p in ([] if paginas else PAGINAS):
        try:
            paginas[p] = tabelas(texto(BASE + p))
        except Exception as e:
            erros.append(f"{p}: {e}")
        time.sleep(1)
    if not any(paginas.values()): raise SystemExit("Nada coletado: " + "; ".join(erros))
    with open("agro.json", "w", encoding="utf-8") as f:
        ind, bol, pr = montar(paginas)
        json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "Notícias Agrícolas",
                   "indicadores": ind, "bolsas": bol, "pracas": pr, "estados": estados(paginas), "erros": erros}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(ind)} indicadores, {len(bol)} bolsas, {len(pr)} tabelas por praça", erros)

if __name__ == "__main__":
    main()
