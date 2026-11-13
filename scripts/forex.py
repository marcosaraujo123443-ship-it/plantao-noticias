#!/usr/bin/env python3
"""Forex: as principais moedas contra o real e os pares mais negociados do mundo, com variação no dia, em 30 dias
e o histórico de 30 dias (Yahoo Finance). Grava forex.json; roda junto com a bolsa, no máximo a cada 45 minutos."""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)"}
REAL = [("BRL=X", "Dólar americano", "USD/BRL", "🇺🇸"), ("EURBRL=X", "Euro", "EUR/BRL", "🇪🇺"), ("GBPBRL=X", "Libra esterlina", "GBP/BRL", "🇬🇧"),
        ("CNYBRL=X", "Yuan chinês", "CNY/BRL", "🇨🇳"), ("JPYBRL=X", "Iene japonês", "JPY/BRL", "🇯🇵"), ("ARSBRL=X", "Peso argentino", "ARS/BRL", "🇦🇷"),
        ("CHFBRL=X", "Franco suíço", "CHF/BRL", "🇨🇭"), ("CADBRL=X", "Dólar canadense", "CAD/BRL", "🇨🇦")]
PARES = [("EURUSD=X", "Euro / dólar", "EUR/USD", "🇪🇺"), ("GBPUSD=X", "Libra / dólar", "GBP/USD", "🇬🇧"), ("JPY=X", "Dólar / iene", "USD/JPY", "🇯🇵"),
         ("CNY=X", "Dólar / yuan", "USD/CNY", "🇨🇳"), ("CHF=X", "Dólar / franco suíço", "USD/CHF", "🇨🇭"), ("AUDUSD=X", "Dólar australiano / dólar", "AUD/USD", "🇦🇺"),
         ("CAD=X", "Dólar / dólar canadense", "USD/CAD", "🇨🇦"), ("MXN=X", "Dólar / peso mexicano", "USD/MXN", "🇲🇽"), ("ARS=X", "Dólar / peso argentino", "USD/ARS", "🇦🇷")]
DXY = ("DX-Y.NYB", "Índice DXY", "DXY", "💵")

def serie(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(sym)}?range=1mo&interval=1d"
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                res = json.load(r)["chart"]["result"][0]
            break
        except Exception:
            if t == 2: raise
            time.sleep(3)
    m = res["meta"]; fech = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
    preco = m["regularMarketPrice"]
    prev = m.get("previousClose") or (fech[-2] if len(fech) > 1 else None)
    return {"preco": preco, "dia": (preco / prev - 1) * 100 if prev else None,
            "mes": (preco / fech[0] - 1) * 100 if fech else None, "hist": [round(x, 6) for x in fech[-30:]]}

def main():
    agora = datetime.now(timezone.utc)
    try:
        ant = json.load(open("forex.json", encoding="utf-8"))
        idade = (agora - datetime.strptime(ant["atualizado_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds()
        if idade < 45 * 60 and not os.environ.get("FOREX_FORCAR"): print("Forex atualizado há menos de 45 minutos."); return
    except Exception: pass
    out, erros = {"real": [], "pares": [], "dxy": None}, []
    for grupo, lista in (("real", REAL), ("pares", PARES), ("dxy", [DXY])):
        for sym, nome, par, band in lista:
            try:
                x = {"par": par, "nome": nome, "bandeira": band, **serie(sym)}
                if grupo == "dxy": out["dxy"] = x
                else: out[grupo].append(x)
            except Exception as ex: erros.append(f"{par}: {ex!r}"[:120])
            time.sleep(0.3)
    # yuan em reais: o par direto quase não negocia no Yahoo; calcula pelo cruzamento USD/BRL ÷ USD/CNY
    usd = next((x for x in out["real"] if x["par"] == "USD/BRL"), None); cny = next((x for x in out["pares"] if x["par"] == "USD/CNY"), None)
    yuan = next((x for x in out["real"] if x["par"] == "CNY/BRL"), None)
    if usd and cny and yuan:
        n = min(len(usd["hist"]), len(cny["hist"]))
        yuan.update({"preco": usd["preco"] / cny["preco"],
                     "dia": ((1 + usd["dia"] / 100) / (1 + cny["dia"] / 100) - 1) * 100 if usd["dia"] is not None and cny["dia"] is not None else None,
                     "mes": ((1 + usd["mes"] / 100) / (1 + cny["mes"] / 100) - 1) * 100 if usd["mes"] is not None and cny["mes"] is not None else None,
                     "hist": [round(a / b, 6) for a, b in zip(usd["hist"][-n:], cny["hist"][-n:])]})
    if not out["real"]: sys.exit("Forex: nada coletado " + "; ".join(erros))
    out.update({"atualizado_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "Yahoo Finance (cotações de mercado, com atraso)", "erros": erros})
    json.dump(out, open("forex.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(len(out["real"]), "moedas,", len(out["pares"]), "pares; erros:", erros)

if __name__ == "__main__":
    main()
