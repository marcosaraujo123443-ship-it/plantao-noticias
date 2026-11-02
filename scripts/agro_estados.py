#!/usr/bin/env python3
"""Produção agropecuária por estado e peso do agro no PIB (IBGE/SIDRA) -> agro_estados.json.
PAM (valor da produção agrícola), LSPA (safra do ano em curso), PPM (rebanho bovino) e Contas Regionais (PIB)."""
import json, time, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)"}
S = "https://apisidra.ibge.gov.br/values"
UF = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
      "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
      "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
# produtos da safra (LSPA, tabela 6588): somados quando há mais de um código
LSPA = {"soja": ("Soja", [39443]), "milho": ("Milho", [39441, 39442]), "cafe": ("Café", [39454, 39455]),
        "cana": ("Cana-de-açúcar", [39456]), "algodao": ("Algodão", [39429]), "arroz": ("Arroz", [39432]),
        "trigo": ("Trigo", [39445]), "feijao": ("Feijão", [39436, 39437, 39438]), "laranja": ("Laranja", [39463])}

def get(caminho):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{S}/{caminho}", headers=UA), timeout=90) as r:
                return json.load(r)[1:]
        except Exception:
            if t == 2: raise
            time.sleep(5)

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def main():
    out = {"estados": {u: {} for u in UF.values()}, "periodos": {}, "erros": []}
    E = out["estados"]
    try:   # valor da produção agrícola (mil R$)
        for x in get("t/5457/n3/all/v/215/p/last%201/c782/0"):
            v = num(x["V"]); u = UF.get(x["D1C"])
            if u and v is not None: E[u]["vp_agricola"] = v * 1000
            out["periodos"]["vp_agricola"] = x["D3N"]
    except Exception as ex: out["erros"].append(f"PAM: {ex!r}"[:150])
    try:   # safra do ano (toneladas), estimativa mais recente do LSPA
        cods = ",".join(str(c) for _, cs in LSPA.values() for c in cs)
        dados = get(f"t/6588/n3/all/v/35/p/last%201/c48/{cods}")
        por = {}
        for x in dados:
            por[(x["D1C"], int(x["D4C"]))] = num(x["V"]); out["periodos"]["safra"] = x["D3N"]
        for k, (_, cs) in LSPA.items():
            for c3, u in UF.items():
                vs = [por.get((c3, c)) for c in cs]
                if any(v for v in vs): E[u][k] = sum(v or 0 for v in vs)
    except Exception as ex: out["erros"].append(f"LSPA: {ex!r}"[:150])
    try:   # rebanho bovino (cabeças)
        for x in get("t/3939/n3/all/v/105/p/last%201/c79/2670"):
            v = num(x["V"]); u = UF.get(x["D1C"])
            if u and v is not None: E[u]["bovinos"] = v
            out["periodos"]["bovinos"] = x["D3N"]
    except Exception as ex: out["erros"].append(f"PPM: {ex!r}"[:150])
    try:   # PIB e valor adicionado da agropecuária (último ano com o detalhe por atividade)
        dados = get("t/5938/n3/all/v/37,513,516,514/p/last%205") + get("t/5938/n1/all/v/37,513/p/last%205")
        anos = sorted({x["D3N"] for x in dados if x["D2C"] == "513" and num(x["V"]) is not None})
        ano = anos[-1]
        br_pib = next(num(x["V"]) for x in dados if x["NC"] == "1" and x["D2C"] == "37" and x["D3N"] == ano) * 1000
        br_va = next(num(x["V"]) for x in dados if x["NC"] == "1" and x["D2C"] == "513" and x["D3N"] == ano) * 1000
        for x in dados:
            if x["NC"] != "3" or x["D3N"] != ano: continue
            u = UF.get(x["D1C"]); v = num(x["V"])
            if not u or v is None: continue
            if x["D2C"] == "37": E[u]["pib"] = v * 1000
            if x["D2C"] == "513": E[u]["va_agro"] = v * 1000; E[u]["agro_pib_br"] = round(v * 1000 / br_pib * 100, 3)
            if x["D2C"] == "516": E[u]["agro_no_estado"] = v
            if x["D2C"] == "514": E[u]["part_agro_br"] = v
        out["periodos"]["pib"] = ano; out["brasil"] = {"pib": br_pib, "va_agro": br_va, "agro_no_pib": round(br_va / br_pib * 100, 2)}
    except Exception as ex: out["erros"].append(f"PIB: {ex!r}"[:150])
    try: velho = json.load(open("agro_estados.json", encoding="utf-8"))
    except Exception: velho = {}
    if not any(E.values()) and velho: print("::warning::IBGE indisponível; mantendo o arquivo anterior"); return
    out["produtos"] = {k: n for k, (n, _) in LSPA.items()}
    out["atualizado_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"); out["fonte"] = "IBGE (PAM, LSPA, PPM e Contas Regionais)"
    json.dump(out, open("agro_estados.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for e in out["erros"]: print("::warning::" + e)
    print(out["periodos"], {u: round(E[u].get("soja", 0) / 1e6, 1) for u in ("MT", "PR", "RS", "GO")})

if __name__ == "__main__":
    main()
