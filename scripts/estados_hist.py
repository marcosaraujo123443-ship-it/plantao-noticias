#!/usr/bin/env python3
"""Histórico anual (desde 2015) das contas da União e dos estados: o RREO do 6º bimestre de cada ano (SICONFI)
e o IPCA para corrigir os valores pela inflação. Grava estados_historico.json. Anos fechados não mudam,
então só busca os que faltam (uma vez por mês confere se o ano passado já foi enviado)."""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estados as E

INICIO = 2015
ARQ = "estados_historico.json"

def resumo(b):
    r = {x["n"]: x.get("realizado") for x in b["receitas"]}
    d = {x["n"]: x.get("liquidado") for x in b["despesas"]}
    return {"pop": b.get("populacao"), "rt": r.get("Total arrecadado"), "imp": r.get("Impostos, taxas e contribuições de melhoria"),
            "tu": r.get("das quais, da União"), "dt": d.get("Total"), "pes": d.get("Pessoal e encargos"), "inv": d.get("Investimentos"),
            "f": {x["n"]: round(x["liquidado"], 2) for x in b.get("funcoes", []) if x.get("liquidado")}}

def ipca():
    """Fator para levar o valor de cada ano a preços de hoje: índice do último mês ÷ média do índice no ano."""
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/01/%d&dataFinal=%s" % (
        INICIO, datetime.now().strftime("%d/%m/%Y"))
    dados = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=E.UA), timeout=60))
    idx, nivel, por_ano = [], 1.0, {}
    for x in dados:
        nivel *= 1 + float(x["valor"]) / 100
        ano = int(x["data"][-4:]); por_ano.setdefault(ano, []).append(nivel)
    ultimo = nivel
    return {str(a): round(ultimo / (sum(v) / len(v)), 4) for a, v in por_ano.items()}, dados[-1]["data"][3:]

def main():
    agora = datetime.now(timezone.utc)
    try: h = json.load(open(ARQ, encoding="utf-8"))
    except Exception: h = {"estados": {}}
    est = h.setdefault("estados", {})
    fim = agora.year - 1
    erros, novos = [], 0
    for cod, (sigla, nome) in [(1, ("BR", "Brasil (Governo Federal)"))] + list(E.UFS.items()):
        e = est.setdefault(sigla, {"nome": nome, "anos": {}})
        for ano in range(INICIO, fim + 1):
            if str(ano) in e["anos"]: continue
            try:
                b = E.balanco(cod, ano, 6)
                if b: e["anos"][str(ano)] = resumo(b); novos += 1
            except Exception as ex:
                erros.append(f"{sigla} {ano}: {ex!r}"[:150])
            time.sleep(0.3)
        print(sigla, sorted(e["anos"]), flush=True)
    # soma dos estados por ano (só anos com os 27)
    uf = {"nome": "Todos os estados (soma)", "anos": {}}
    for ano in range(INICIO, fim + 1):
        bs = [est[s]["anos"][str(ano)] for s in est if s not in ("BR", "UF") and str(ano) in est[s]["anos"]]
        if len(bs) < 27: continue
        t = {k: sum(b.get(k) or 0 for b in bs) for k in ("pop", "rt", "imp", "tu", "dt", "pes", "inv")}
        f = {}
        for b in bs:
            for n, v in b["f"].items(): f[n] = round(f.get(n, 0) + v, 2)
        t["f"] = f; t["estados"] = len(bs); uf["anos"][str(ano)] = t
    est["UF"] = uf
    if "BR" in est:   # o RREO da União traz a população errada; usa a soma dos estados
        for a, v in est["BR"]["anos"].items():
            if a in uf["anos"]: v["pop"] = uf["anos"][a]["pop"]
    try: h["ipca"], h["ipca_ate"] = ipca()
    except Exception as ex: erros.append(f"IPCA: {ex!r}"[:150])
    h["atualizado_utc"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ"); h["fonte"] = "Tesouro Nacional (SICONFI, RREO do 6º bimestre) e IBGE (IPCA)"
    h["erros"] = erros
    json.dump(h, open(ARQ, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for x in erros[:20]: print("::warning::" + x)
    print(f"{novos} anos novos; {os.path.getsize(ARQ) // 1024} KB")

if __name__ == "__main__":
    main()
