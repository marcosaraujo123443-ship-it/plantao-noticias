#!/usr/bin/env python3
"""Coleta indicadores e cotações da B3 e grava mercado.json (roda no GitHub Actions)."""
import json, os, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)"}
ACOES = [("PETR4", "Petrobras"), ("VALE3", "Vale"), ("ITUB4", "Itaú"), ("BBDC4", "Bradesco"),
         ("BBAS3", "Banco do Brasil"), ("B3SA3", "B3"), ("ABEV3", "Ambev"), ("WEGE3", "WEG"),
         ("ITSA4", "Itaúsa"), ("BPAC11", "BTG Pactual"), ("SUZB3", "Suzano"), ("PRIO3", "PRIO"),
         ("JBSS3", "JBS"), ("RENT3", "Localiza"), ("EMBR3", "Embraer"), ("GGBR4", "Gerdau"),
         ("RADL3", "Raia Drogasil"), ("LREN3", "Renner"), ("MGLU3", "Magazine Luiza"), ("ELET3", "Eletrobras")]

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

def main():
    ind, acoes, erros = [], [], []
    try:
        p, v = yahoo("%5EBVSP"); ind.append({"nome": "Ibovespa", "valor": p, "var": v, "tipo": "pts"})
    except Exception as e: erros.append(f"ibov: {e}")
    try:
        fx = get("https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,BTC-BRL")
        for k, nome in (("USDBRL", "Dólar"), ("EURBRL", "Euro"), ("BTCBRL", "Bitcoin")):
            ind.append({"nome": nome, "valor": float(fx[k]["bid"]), "var": float(fx[k]["pctChange"]), "tipo": "brl"})
    except Exception as e: erros.append(f"moedas: {e}")
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
    out = {"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "indicadores": ind, "acoes": acoes, "erros": erros}
    with open("mercado.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{len(ind)} indicadores, {len(acoes)} ações, erros: {erros}")

if __name__ == "__main__":
    main()
