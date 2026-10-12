#!/usr/bin/env python3
"""Receitas e despesas dos estados (Tesouro Nacional, SICONFI/RREO) e grava estados.json (roda no GitHub Actions)."""
import json, re, time, urllib.parse, urllib.request
from datetime import datetime, timezone

API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"
UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)"}
UFS = {11: ("RO", "Rondônia"), 12: ("AC", "Acre"), 13: ("AM", "Amazonas"), 14: ("RR", "Roraima"), 15: ("PA", "Pará"),
       16: ("AP", "Amapá"), 17: ("TO", "Tocantins"), 21: ("MA", "Maranhão"), 22: ("PI", "Piauí"), 23: ("CE", "Ceará"),
       24: ("RN", "Rio Grande do Norte"), 25: ("PB", "Paraíba"), 26: ("PE", "Pernambuco"), 27: ("AL", "Alagoas"),
       28: ("SE", "Sergipe"), 29: ("BA", "Bahia"), 31: ("MG", "Minas Gerais"), 32: ("ES", "Espírito Santo"),
       33: ("RJ", "Rio de Janeiro"), 35: ("SP", "São Paulo"), 41: ("PR", "Paraná"), 42: ("SC", "Santa Catarina"),
       43: ("RS", "Rio Grande do Sul"), 50: ("MS", "Mato Grosso do Sul"), 51: ("MT", "Mato Grosso"), 52: ("GO", "Goiás"),
       53: ("DF", "Distrito Federal")}

def get(params):
    itens, offset = [], 0
    while True:
        url = API + "?" + urllib.parse.urlencode({**params, "offset": offset})
        for tent in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                    d = json.load(r); break
            except Exception:
                if tent == 2: raise
                time.sleep(3)
        itens += d.get("items", [])
        if not d.get("hasMore"): return itens
        offset += d.get("limit") or len(d.get("items", [])) or 5000

def rreo(uf, ano, periodo, anexo):
    return get({"an_exercicio": ano, "nr_periodo": periodo, "co_tipo_demonstrativo": "RREO",
                "no_anexo": anexo, "co_esfera": "E", "id_ente": uf})

def intra(cod):
    return "Intra" in cod and "Exceto" not in cod

def tabela(itens, colunas):
    """Agrupa as linhas por conta, na ordem do relatório, com as colunas pedidas {chave: regex da coluna}."""
    out, idx = [], {}
    for i in itens:
        cod, conta = i.get("cod_conta") or "", (i.get("conta") or "").strip()
        if intra(cod): continue
        for chave, rx in colunas.items():
            if re.fullmatch(rx, i.get("coluna") or "", re.I):
                k = (cod, conta)
                if k not in idx:
                    idx[k] = {"cod": cod, "conta": conta}; out.append(idx[k])
                idx[k].setdefault(chave, i.get("valor"))
    return out

REC = {"previsto": r"PREVISÃO ATUALIZADA.*", "realizado": r"Até o Bimestre.*"}
DESP = {"dotacao": r"DOTAÇÃO ATUALIZADA.*", "empenhado": r"DESPESAS EMPENHADAS ATÉ O BIMESTRE.*",
        "liquidado": r"DESPESAS LIQUIDADAS ATÉ O BIMESTRE.*", "pago": r"DESPESAS PAGAS ATÉ O BIMESTRE.*"}

def balanco(uf, ano, periodo):
    a1 = rreo(uf, ano, periodo, "RREO-Anexo 01")
    if not a1: return None
    rec = [r for r in tabela(a1, REC) if "realizado" in r]
    desp = [r for r in tabela(a1, DESP) if "liquidado" in r or "empenhado" in r]
    try:
        func = [r for r in tabela(rreo(uf, ano, periodo, "RREO-Anexo 02"), DESP) if "liquidado" in r or "empenhado" in r]
    except Exception:
        func = []
    pop = next((i.get("populacao") for i in a1 if i.get("populacao")), None)
    return {"ano": ano, "periodo": periodo, "populacao": pop, "receitas": rec, "despesas": desp, "funcoes": func}

def main():
    agora = datetime.now(timezone.utc)
    anterior = {}
    try: anterior = json.load(open("estados.json", encoding="utf-8")).get("estados", {})
    except Exception: pass
    estados, erros = {}, []
    for cod, (sigla, nome) in UFS.items():
        e = {"sigla": sigla, "nome": nome, "ibge": cod}
        try:
            atual = None
            for ano, per in [(agora.year, p) for p in range(6, 0, -1)] + [(agora.year - 1, 6)]:
                atual = balanco(cod, ano, per)
                if atual: break
            e["atual"] = atual
            if atual and (atual["ano"], atual["periodo"]) != (agora.year - 1, 6):
                e["anterior"] = balanco(cod, agora.year - 1, 6)
        except Exception as ex:
            erros.append(f"{sigla}: {ex}")
            e = anterior.get(sigla, e)
        estados[sigla] = e
        time.sleep(0.5)
    if not any(e.get("atual") for e in estados.values()):
        raise SystemExit("Nenhum estado coletado: " + "; ".join(erros))
    with open("estados.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "Tesouro Nacional, SICONFI (RREO)",
                   "estados": estados, "erros": erros}, f, ensure_ascii=False, separators=(",", ":"))
    ok = [s for s, e in estados.items() if e.get("atual")]
    print(f"{len(ok)} estados: " + ", ".join(f"{s} {estados[s]['atual']['periodo']}º bim/{estados[s]['atual']['ano']}" for s in ok), "erros:", erros)

if __name__ == "__main__":
    main()
