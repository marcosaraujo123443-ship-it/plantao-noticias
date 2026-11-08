#!/usr/bin/env python3
"""Resultado das contas públicas mês a mês (Banco Central, NFSP sem desvalorização cambial, R$ milhões), desde
o ano atual menos três: resultado primário e juros nominais da União, estados, municípios, estatais e do setor
público consolidado. No Banco Central, valor positivo é déficit; aqui o sinal é invertido (positivo = superávit).
Grava contas_mensal.json."""
import json, time, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)"}
ESFERAS = {  # nome: (primário, juros nominais)
    "spc": ("Setor público consolidado", 4649, 4616),
    "gf": ("Governo federal", 4640, 4607),
    "bc": ("Banco Central", 4641, 4608),
    "est": ("Governos estaduais", 4643, 4610),
    "mun": ("Governos municipais", 4644, 4611),
    "estatais": ("Empresas estatais", 4645, 4612),
}
DOZE = {"prim_pib": 5793, "divida_liq": 4513, "divida_bruta": 13762}   # % do PIB

def sgs(cod, desde):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados?formato=json&dataInicial={desde}"
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return [(f"{x['data'][6:10]}-{x['data'][3:5]}", float(x["valor"])) for x in json.load(r)]
        except Exception:
            if t == 2: raise
            time.sleep(5)

def main():
    agora = datetime.now(timezone.utc); desde = f"01/01/{agora.year - 3}"
    out = {"esferas": {}, "pib": {}}
    for k, (nome, cp, cj) in ESFERAS.items():
        p = dict(sgs(cp, desde)); j = dict(sgs(cj, desde))
        meses = sorted(set(p) | set(j))
        out["esferas"][k] = {"nome": nome, "m": {m: {"prim": round(-p[m], 1) if m in p else None, "juros": round(-j[m], 1) if m in j else None} for m in meses}}
        time.sleep(0.3)
    for k, c in DOZE.items():
        s = sgs(c, desde); out["pib"][k] = {"mes": s[-1][0], "valor": s[-1][1], "serie": s[-24:]}
    out["atualizado_utc"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    out["fonte"] = "Banco Central (estatísticas fiscais, NFSP sem desvalorização cambial)"
    json.dump(out, open("contas_mensal.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    u = out["esferas"]["spc"]["m"]; ult = max(u)
    print("último mês", ult, u[ult], "| primário 12m % PIB:", out["pib"]["prim_pib"])

if __name__ == "__main__":
    main()
