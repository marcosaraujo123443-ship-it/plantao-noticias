#!/usr/bin/env python3
"""Coleta indicadores e cotações da B3 e grava mercado.json (roda no GitHub Actions)."""
import json, os, re, time, html as H, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)"}
ACOES = [("PETR4", "Petrobras"), ("VALE3", "Vale"), ("ITUB4", "Itaú"), ("BBDC4", "Bradesco"),
         ("BBAS3", "Banco do Brasil"), ("B3SA3", "B3"), ("ABEV3", "Ambev"), ("WEGE3", "WEG"),
         ("ITSA4", "Itaúsa"), ("BPAC11", "BTG Pactual"), ("SUZB3", "Suzano"), ("PRIO3", "PRIO"),
         ("RENT3", "Localiza"), ("EMBJ3", "Embraer"), ("GGBR4", "Gerdau"),
         ("RADL3", "Raia Drogasil"), ("LREN3", "Renner"), ("MGLU3", "Magazine Luiza"), ("AXIA3", "Axia (Eletrobras)"), ("CMIG4", "Cemig")]

IBOV = """ALOS3 ABEV3 ASAI3 AURE3 AZZA3 B3SA3 BBSE3 BBDC3 BBDC4 BRAP4 BBAS3 BRKM5 BRAV3 BPAC11 CXSE3 CEAB3 CMIG4
COGN3 CPLE3 CSAN3 CPFE3 CMIN3 CURY3 CVCB3 CYRE3 DIRR3 AXIA3 AXIA6 EMBJ3 ENGI11 ENEV3 EGIE3 EQTL3 FLRY3 GGBR4 GOAU4
HAPV3 HYPE3 IGTI11 IRBR3 ISAE4 ITSA4 ITUB4 KLBN11 RENT3 LREN3 MGLU3 POMO4 MRVE3 MULT3 NATU3 PCAR3 PETR3 PETR4 RECV3
PRIO3 PSSA3 RADL3 RAIZ4 RDOR3 RAIL3 SBSP3 SANB11 STBP3 SMTO3 CSNA3 SLCE3 SMFT3 SUZB3 TAEE11 VIVT3 TIMS3 TOTS3 UGPA3
USIM5 VALE3 VAMO3 VBBR3 VIVA3 WEGE3 YDUQ3 MOTV3 MBRF3 EZTC3""".split()
NOMES = {"PETR4": "Petrobras", "PETR3": "Petrobras", "VALE3": "Vale", "ITUB4": "Itaú", "BBDC4": "Bradesco", "BBDC3": "Bradesco",
  "BBAS3": "Banco do Brasil", "B3SA3": "B3", "ABEV3": "Ambev", "WEGE3": "WEG", "ITSA4": "Itaúsa", "BPAC11": "BTG Pactual",
  "SUZB3": "Suzano", "PRIO3": "PRIO", "RENT3": "Localiza", "EMBJ3": "Embraer", "GGBR4": "Gerdau", "RADL3": "Raia Drogasil",
  "AXIA3": "Axia (Eletrobras)", "AXIA6": "Axia (Eletrobras)", "SBSP3": "Sabesp", "VIVT3": "Telefônica Vivo", "TIMS3": "TIM",
  "EQTL3": "Equatorial", "RDOR3": "Rede D'Or", "SANB11": "Santander", "BBSE3": "BB Seguridade", "KLBN11": "Klabin",
  "CMIG4": "Cemig", "EGIE3": "Engie", "ENEV3": "Eneva", "CPFE3": "CPFL", "VBBR3": "Vibra", "UGPA3": "Ultrapar",
  "TOTS3": "Totvs", "RAIL3": "Rumo", "HAPV3": "Hapvida", "CSAN3": "Cosan", "LREN3": "Renner", "MBRF3": "MBRF (BRF+Marfrig)",
  "CMIN3": "CSN Mineração", "PSSA3": "Porto Seguro", "CXSE3": "Caixa Seguridade", "MGLU3": "Magazine Luiza",
  "ASAI3": "Assaí", "NATU3": "Natura", "CSNA3": "CSN", "USIM5": "Usiminas", "BRAP4": "Bradespar", "GOAU4": "Gerdau Met.",
  "CPLE3": "Copel", "TAEE11": "Taesa", "ENGI11": "Energisa", "MULT3": "Multiplan", "ALOS3": "Allos", "CYRE3": "Cyrela",
  "MRVE3": "MRV", "COGN3": "Cogna", "YDUQ3": "Yduqs", "CVCB3": "CVC", "AZZA3": "Azzas 2154", "BRKM5": "Braskem",
  "IRBR3": "IRB", "SMTO3": "São Martinho", "SLCE3": "SLC Agrícola", "MOTV3": "Motiva", "VIVA3": "Vivara", "HYPE3": "Hypera",
  "FLRY3": "Fleury", "CEAB3": "C&A", "PCAR3": "GPA", "RAIZ4": "Raízen", "RECV3": "PetroReconcavo", "BRAV3": "Brava",
  "STBP3": "Santos Brasil", "SMFT3": "Smart Fit", "VAMO3": "Vamos", "CURY3": "Cury", "DIRR3": "Direcional", "EZTC3": "EZTec",
  "IGTI11": "Iguatemi", "ISAE4": "ISA Energia", "POMO4": "Marcopolo", "AURE3": "Auren"}
# uma ação por empresa, para o ranking de valor de mercado
GRANDES = """PETR4 VALE3 ITUB4 BBDC4 BBAS3 B3SA3 ABEV3 WEGE3 ITSA4 BPAC11 SUZB3 PRIO3 RENT3 EMBJ3 GGBR4 RADL3 AXIA3 SBSP3
VIVT3 TIMS3 EQTL3 RDOR3 SANB11 BBSE3 KLBN11 CMIG4 EGIE3 ENEV3 CPFE3 VBBR3 UGPA3 TOTS3 RAIL3 HAPV3 CSAN3 LREN3 MBRF3
CMIN3 PSSA3 CXSE3""".split()


def get(url, headers=UA):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
        return json.loads(r.read().decode())

def yahoo(sym):
    m = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=1d")["chart"]["result"][0]["meta"]
    preco, ant = m["regularMarketPrice"], m.get("chartPreviousClose") or m.get("previousClose")
    return preco, (preco / ant - 1) * 100 if ant else None

def brapi(tickers):
    tok = os.environ.get("BRAPI_TOKEN")
    if not tok: return {}
    d = get(f"https://brapi.dev/api/quote/{','.join(tickers)}?token={tok}")
    return {r["symbol"]: (r["regularMarketPrice"], r.get("regularMarketChangePercent")) for r in d.get("results", [])}

def texto(url):
    req = urllib.request.Request(url, headers={**UA, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("iso-8859-1")

def num(s):
    s = s.strip().replace("%", "").replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None

def cotacoes(tickers):
    """Preço e variação do dia via Yahoo (spark em lotes; reserva: chart por ação)."""
    res = {}
    for i in range(0, len(tickers), 20):
        lote = tickers[i:i + 20]
        try:
            d = get("https://query1.finance.yahoo.com/v8/finance/spark?range=1d&interval=1d&symbols=" + ",".join(t + ".SA" for t in lote))
            for t in lote:
                x = d.get(t + ".SA") or {}
                close = [c for c in (x.get("close") or []) if c is not None]
                ant = x.get("chartPreviousClose") or x.get("previousClose")
                if close and ant: res[t] = (close[-1], (close[-1] / ant - 1) * 100)
        except Exception:
            pass
    for t in tickers:
        if t in res: continue
        try:
            res[t] = yahoo(t + ".SA"); time.sleep(0.2)
        except Exception:
            pass
    return res

def valor_mercado(cache):
    """Valor de mercado (Fundamentus, detalhes.php), renovado uma vez por dia."""
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if cache.get("data") == hoje and cache.get("vm"): return cache
    vm = {}
    for t in GRANDES:
        try:
            pg = texto(f"https://www.fundamentus.com.br/detalhes.php?papel={t}")
            m = re.search(r"Valor de mercado</span></td>\s*<td[^>]*><span class=\"txt\">([\d.]+)", pg)
            c = re.search(r"Cota[^<]*</span></td>\s*<td[^>]*><span class=\"txt\">([\d.,]+)", pg)
            if m: vm[t] = {"vm": float(m.group(1).replace(".", "")), "preco": num(c.group(1)) if c else None}
            time.sleep(0.7)
        except Exception:
            pass
    return {"data": hoje, "vm": vm} if vm else cache

def fiis():
    pg = texto("https://www.fundamentus.com.br/fii_resultado.php")
    corpo = pg[pg.find("<tbody"):pg.find("</tbody>")]
    out = []
    for linha in re.findall(r"<tr[^>]*>(.*?)</tr>", corpo, re.S):
        cel = [H.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", linha, re.S)]
        if len(cel) < 8: continue
        f = {"papel": cel[0], "segmento": cel[1], "cotacao": num(cel[2]), "dy": num(cel[4]), "pvp": num(cel[5]),
             "vm": num(cel[6]), "liq": num(cel[7])}
        if f["cotacao"] and f["vm"] and (f["liq"] or 0) >= 500_000: out.append(f)
    out.sort(key=lambda f: f["vm"], reverse=True)
    return out[:80]

def main():
    ind, acoes, erros = [], [], []
    try:
        p, v = yahoo("%5EBVSP"); ind.append({"nome": "Ibovespa", "valor": p, "var": v, "tipo": "pts"})
    except Exception as e: erros.append(f"ibov: {e}")
    try:
        fx = get("https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,BTC-BRL")
        for k, nome in (("USDBRL", "Dólar"), ("EURBRL", "Euro"), ("BTCBRL", "Bitcoin")):
            ind.append({"nome": nome, "valor": float(fx[k]["bid"]), "var": float(fx[k]["pctChange"]), "tipo": "brl"})
    except Exception as e:
        erros.append(f"moedas (awesomeapi): {e}")
        usd = None
        for sym, nome in (("BRL%3DX", "Dólar"), ("EURBRL%3DX", "Euro")):
            try:
                p, v = yahoo(sym); ind.append({"nome": nome, "valor": p, "var": v, "tipo": "brl"})
                if nome == "Dólar": usd = p
            except Exception as e2: erros.append(f"{nome}: {e2}")
        try:
            p, v = yahoo("BTC-USD")
            if usd: ind.append({"nome": "Bitcoin", "valor": p * usd, "var": v, "tipo": "brl"})
        except Exception as e2: erros.append(f"Bitcoin: {e2}")
    for serie, nome in ((432, "Selic"), (13522, "IPCA 12m")):
        try:
            v = get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados/ultimos/1?formato=json")[-1]["valor"]
            ind.append({"nome": nome, "valor": float(v), "var": None, "tipo": "pct"})
        except Exception as e: erros.append(f"{nome}: {e}")
    falhas = []
    for t, nome in ACOES:
        try:
            p, v = yahoo(f"{t}.SA"); acoes.append({"ticker": t, "nome": nome, "preco": p, "var": v})
        except Exception:
            falhas.append((t, nome))
    if falhas:
        try:
            b = brapi([t for t, _ in falhas])
            for t, nome in falhas:
                if t in b: acoes.append({"ticker": t, "nome": nome, "preco": b[t][0], "var": b[t][1]})
        except Exception as e: erros.append(f"brapi: {e}")
    ordem = {t: i for i, (t, _) in enumerate(ACOES)}
    acoes.sort(key=lambda a: ordem[a["ticker"]])
    if not ind and not acoes:
        raise SystemExit("Nenhum dado coletado: " + "; ".join(erros))
    anterior = {}
    try:
        anterior = json.load(open("mercado.json", encoding="utf-8"))
    except Exception:
        pass
    cot = cotacoes(IBOV)
    ibov = [{"ticker": t, "nome": NOMES.get(t, ""), "preco": p, "var": v} for t, (p, v) in cot.items() if v is not None]
    vmc = valor_mercado(anterior.get("vm_cache", {}))
    maiores = []
    for t, x in vmc.get("vm", {}).items():
        p, v = cot.get(t, (None, None))
        vm = x["vm"] * (p / x["preco"]) if p and x.get("preco") else x["vm"]
        maiores.append({"ticker": t, "nome": NOMES.get(t, ""), "preco": p, "var": v, "vm": vm})
    maiores.sort(key=lambda a: a["vm"], reverse=True)
    try:
        lista_fii = fiis()
        cf = cotacoes([f["papel"] for f in lista_fii])
        for f in lista_fii:
            if f["papel"] in cf:
                f["cotacao"], f["var"] = cf[f["papel"]]
    except Exception as e:
        erros.append(f"fiis: {e}"); lista_fii = anterior.get("fiis", [])
    out = {"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "indicadores": ind, "acoes": acoes, "ibov": ibov,
           "maiores": maiores[:20], "fiis": lista_fii, "vm_cache": vmc, "erros": erros}
    with open("mercado.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{len(ind)} indicadores, {len(acoes)} ações, {len(ibov)} do Ibovespa, {len(maiores)} com valor de mercado, {len(lista_fii)} FIIs ({sum(1 for f in lista_fii if f.get("var") is not None)} com variação), erros: {erros}")

if __name__ == "__main__":
    main()
