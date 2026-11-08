#!/usr/bin/env python3
"""Histórico bimestre a bimestre das contas da União e dos estados (SICONFI, RREO Anexo 01), para comparar o mesmo
bimestre entre anos. Guarda os valores acumulados até cada bimestre; o valor só do bimestre é a diferença para o anterior.
Bimestres já baixados não são buscados de novo, então cada execução só procura o próximo de cada governo.
Grava estados_bimestral.json."""
import json, os, sys, time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estados as E

ANOS = 4          # ano atual e os três anteriores
ARQ = "estados_bimestral.json"
CAMPOS = {"rt": "Total arrecadado", "imp": "Impostos, taxas e contribuições de melhoria", "tu": "das quais, da União"}
CAMPOS_D = {"dt": "Total", "pes": "Pessoal e encargos", "inv": "Investimentos"}

def resumo(uf, ano, per):
    a1 = E.rreo(uf, ano, per, "RREO-Anexo 01")
    if not a1: return None
    rec = {x["n"]: x.get("realizado") for x in E.escolher(E.tabela(a1, E.REC), E.RECEITAS)}
    desp = {x["n"]: x.get("liquidado") for x in E.escolher(E.tabela(a1, E.DESP), E.DESPESAS)}
    out = {k: round(rec[n]) for k, n in CAMPOS.items() if rec.get(n) is not None}
    out.update({k: round(desp[n]) for k, n in CAMPOS_D.items() if desp.get(n) is not None})
    return out if out.get("rt") and out.get("dt") else None

def main():
    agora = datetime.now(timezone.utc); ano_atual = agora.year
    try: h = json.load(open(ARQ, encoding="utf-8"))
    except Exception: h = {"entes": {}}
    entes = h.setdefault("entes", {})
    erros, novos, inicio = [], 0, time.time()
    for cod, (sigla, nome) in [(1, ("BR", "Brasil (Governo Federal)"))] + list(E.UFS.items()):
        e = entes.setdefault(sigla, {"nome": nome, "b": {}})
        for ano in range(ano_atual - ANOS + 1, ano_atual + 1):
            for per in range(1, 7):
                k = f"{ano}-{per}"
                if k in e["b"]: continue
                if ano == ano_atual and (agora.month - 1) // 2 + 1 <= per: break   # bimestre ainda não terminou
                if time.time() - inicio > 100 * 60: break                           # deixa o resto para a próxima execução
                try:
                    r = resumo(cod, ano, per)
                except Exception as ex:
                    erros.append(f"{sigla} {k}: {ex!r}"[:150]); break
                if not r: break   # ainda não enviado: os seguintes também não
                e["b"][k] = r; novos += 1
                time.sleep(0.2)
        print(sigla, len(e["b"]), "bimestres", flush=True)
    # soma dos estados em cada bimestre em que os 27 já enviaram
    todos = sorted({k for s, e in entes.items() if s not in ("BR", "UF") for k in e["b"]})
    soma = {}
    for k in todos:
        bs = [entes[s]["b"][k] for s in E_SIGLAS() if k in entes.get(s, {}).get("b", {})]
        if len(bs) == 27: soma[k] = {c: sum(b.get(c) or 0 for b in bs) for c in list(CAMPOS) + list(CAMPOS_D)}
    entes["UF"] = {"nome": "Todos os estados (soma)", "b": soma}
    corte = f"{ano_atual - ANOS + 1}-0"
    for e in entes.values(): e["b"] = {k: v for k, v in sorted(e["b"].items()) if k >= corte}
    h["atualizado_utc"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    h["fonte"] = "Tesouro Nacional (SICONFI, RREO Anexo 1: receitas realizadas e despesas liquidadas)"
    h["erros"] = erros
    json.dump(h, open(ARQ, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for x in erros[:15]: print("::warning::" + x)
    print(f"{novos} bimestres novos; {os.path.getsize(ARQ) // 1024} KB")

def E_SIGLAS(): return [s for s, _ in E.UFS.values()]

if __name__ == "__main__":
    main()
