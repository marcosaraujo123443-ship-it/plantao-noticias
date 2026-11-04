#!/usr/bin/env python3
"""Balanços das empresas listadas na B3 (dados abertos da CVM: ITR trimestral e DFP anual) -> balancos.json.
Para cada empresa: último período entregue, receita, lucro bruto, resultado operacional (EBIT) e lucro líquido
no acumulado do ano e no trimestre, comparados com o mesmo período do ano anterior, e o balanço patrimonial."""
import csv, io, json, re, sys, time, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)"}
BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC"
csv.field_size_limit(10 ** 8)

def baixar(caminho):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{BASE}/{caminho}", headers=UA), timeout=300) as r:
                return zipfile.ZipFile(io.BytesIO(r.read()))
        except Exception:
            if t == 2: raise
            time.sleep(10)

def linhas(z, nome):
    if nome not in z.namelist(): return
    with z.open(nome) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="latin1"), delimiter=";")

def tickers(z):
    """CNPJ -> códigos de negociação na B3 (ações e units)."""
    out = defaultdict(list)
    for r in linhas(z, next(n for n in z.namelist() if "valor_mobiliario" in n)):
        cod = (r.get("Codigo_Negociacao") or "").strip().upper()
        if r.get("Mercado") != "Bolsa" or not re.fullmatch(r"[A-Z0-9]{4}\d{1,2}", cod) or r.get("Data_Fim_Negociacao"): continue
        if not re.search(r"Ações|Units|Certificado", r.get("Valor_Mobiliario") or ""): continue
        if cod not in out[r["CNPJ_Companhia"]]: out[r["CNPJ_Companhia"]].append(cod)
    for k in out: out[k].sort(key=lambda c: (c[-1] != "3", c[-2:] != "11", c))
    return out

sys.path.insert(0, __import__("os").path.dirname(__file__))
try: from mercado import NOMES, IBOV
except Exception: NOMES, IBOV = {}, ""
IBOV = set(IBOV.split() if isinstance(IBOV, str) else IBOV)
MIN = {"de", "da", "do", "das", "dos", "e"}

def curto(tks, nome):
    for t in tks:
        if t in NOMES: return NOMES[t]
    n = re.sub(r"\b(S\.?/?A\.?|S/A|CIA\.?|COMPANHIA|EM RECUPERAÇÃO JUDICIAL|- EM RECUPERACAO JUDICIAL|HOLDING|PARTICIPAÇÕES|PARTICIPACOES)\b", " ", nome, flags=re.I)
    n = re.sub(r"^BCO\b", "Banco", n.strip(), flags=re.I)
    n = re.sub(r"[\s.,-]+$", "", re.sub(r"\s+", " ", n)).strip(" -.")
    n = re.sub(r"\s+(e|de|da|do|das|dos)$", "", n, flags=re.I)
    return " ".join(p.lower() if p.lower() in MIN and i else (p if len(p) <= 3 and p.isalpha() and p not in ("SID",) else p.capitalize()) for i, p in enumerate(n.split()))[:40] or nome

def v(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def ler_doc(z, pref, ano, docs, cnpjs):
    """Guarda, por empresa e data de referência (última versão), as contas da DRE e do balanço."""
    meta = {}
    for r in linhas(z, f"{pref}_cia_aberta_{ano}.csv"):
        if r["CNPJ_CIA"] not in cnpjs: continue
        k = (r["CNPJ_CIA"], r["DT_REFER"])
        if k not in meta or int(r["VERSAO"]) > int(meta[k]["VERSAO"]): meta[k] = r
    for (cnpj, dt), m in meta.items():
        docs[cnpj][dt] = {"tipo": pref.upper(), "versao": m["VERSAO"], "nome": m["DENOM_CIA"], "recebido": m["DT_RECEB"],
                          "link": m["LINK_DOC"], "dre": {}, "bpa": {}, "bpp": {}, "grupo": None}
    for grupo in ("con", "ind"):
        for parte in ("DRE", "BPA", "BPP"):
            for r in linhas(z, f"{pref}_cia_aberta_{parte}_{grupo}_{ano}.csv"):
                d = docs.get(r["CNPJ_CIA"], {}).get(r["DT_REFER"])
                if not d or r["VERSAO"] != d["versao"] or (d["grupo"] and d["grupo"] != grupo): continue
                d["grupo"] = grupo
                mult = 1000 if r.get("ESCALA_MOEDA") == "MIL" else 1
                val = v(r["VL_CONTA"]);  val = val * mult if val is not None else None
                if parte == "DRE":
                    d["dre"].setdefault(r["CD_CONTA"], {"ds": r["DS_CONTA"]})[(r["ORDEM_EXERC"], r["DT_INI_EXERC"])] = val
                else:
                    if r["ORDEM_EXERC"] == "ÚLTIMO": d[parte.lower()][r["CD_CONTA"]] = (r["DS_CONTA"], val)

def conta_dre(dre, rx, nivel=None):
    for cod in sorted(dre, key=lambda c: [int(p) for p in c.split(".")]):
        if nivel and cod.count(".") != nivel: continue
        if re.search(rx, dre[cod]["ds"], re.I): return dre[cod]
    return None

def resumo(cnpj, dt, d, tks):
    dre, ano = d["dre"], dt[:4]
    def per(c, ordem, ini):
        return c.get((ordem, ini)) if c else None
    rec = dre.get("3.01"); bruto = conta_dre(dre, r"^Resultado Bruto", 1)
    ebit = conta_dre(dre, r"Antes do Resultado Financeiro", 1)
    tot = conta_dre(dre, r"^(Lucro|Resultado|Prejuízo).*(Período|Exercício)", 1) or dre.get("3.11") or dre.get("3.09")
    luc = conta_dre(dre, r"Atribuído a Sócios da Empresa Controladora", 2) if d["grupo"] == "con" else None
    if not luc or not any(x for k_, x in luc.items() if k_ != "ds"): luc = tot   # algumas empresas deixam a linha dos controladores zerada
    ini_ano, ini_ant = f"{ano}-01-01", f"{int(ano) - 1}-01-01"
    mes = int(dt[5:7]); ini_tri = f"{ano}-{mes - 2:02d}-01"; ini_tri_ant = f"{int(ano) - 1}-{mes - 2:02d}-01"
    def bloco(ini_u, ini_p):
        return {"receita": per(rec, "ÚLTIMO", ini_u), "receita_ant": per(rec, "PENÚLTIMO", ini_p),
                "bruto": per(bruto, "ÚLTIMO", ini_u), "ebit": per(ebit, "ÚLTIMO", ini_u),
                "lucro": per(luc, "ÚLTIMO", ini_u), "lucro_ant": per(luc, "PENÚLTIMO", ini_p)}
    ytd = bloco(ini_ano, ini_ant)
    tri = bloco(ini_tri, ini_tri_ant) if d["tipo"] == "ITR" and mes > 3 else (ytd if d["tipo"] == "ITR" else None)
    bpa, bpp = d["bpa"], d["bpp"]
    def pega(B, rx, nivel):
        for cod, (ds, val) in sorted(B.items(), key=lambda kv: [int(p) for p in kv[0].split(".")]):
            if cod.count(".") == nivel and re.search(rx, ds, re.I): return val
        return None
    divida = sum(val or 0 for cod, (ds, val) in bpp.items() if cod.count(".") == 2 and re.fullmatch(r"Empréstimos e Financiamentos", ds.strip(), re.I)) or None
    caixa = (pega(bpa, r"^Caixa e Equivalentes", 2) or pega(bpa, r"^Caixa e Equivalentes", 1) or 0) + (pega(bpa, r"^Aplicações Financeiras", 2) or 0)
    pl = pega(bpp, r"^Patrimônio Líquido", 1)
    tri_n = {3: "1T", 6: "2T", 9: "3T", 12: "4T"}.get(mes, "")
    return {"cnpj": cnpj, "tickers": tks, "nome": d["nome"], "curto": curto(tks, d["nome"]), "ibov": any(t in IBOV for t in tks), "ref": dt, "periodo": ano if d["tipo"] == "DFP" else tri_n + ano[2:],
            "tipo": d["tipo"], "recebido": d["recebido"], "link": d["link"], "consolidado": d["grupo"] == "con",
            "rotulo_receita": (rec or {}).get("ds"), "ano": {k: round(x) for k, x in ytd.items() if x is not None},
            "tri": {k: round(x) for k, x in (tri or {}).items() if x is not None},
            "ativo": (bpa.get("1") or (None, None))[1], "pl": pl, "caixa": caixa or None, "divida": divida}

def main():
    agora = datetime.now(timezone.utc); ano = agora.year
    fca = baixar(f"FCA/DADOS/fca_cia_aberta_{ano}.zip")
    tk = tickers(fca)
    docs = defaultdict(dict)
    for pref, a in (("dfp", ano - 1), ("itr", ano)):
        try: ler_doc(baixar(f"{pref.upper()}/DADOS/{pref}_cia_aberta_{a}.zip"), pref, a, docs, set(tk))
        except Exception as ex: print(f"::warning::{pref} {a}: {ex!r}")
    out = []
    for cnpj, por_data in docs.items():
        dt = max(por_data)
        tks = sorted(tk[cnpj], key=lambda c: (c not in IBOV, c[-1] not in "4" and c[-2:] != "11", c))
        try: r = resumo(cnpj, dt, por_data[dt], tks)
        except Exception as ex: print("erro", cnpj, ex); continue
        if r["ano"].get("receita") is None and r["ano"].get("lucro") is None: continue
        out.append(r)
    out.sort(key=lambda r: r["recebido"], reverse=True)
    if len(out) < 100: raise SystemExit(f"Poucas empresas ({len(out)}); mantendo o arquivo anterior")
    json.dump({"atualizado_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "CVM (dados abertos: ITR e DFP)", "empresas": out},
              open("balancos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for t in ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3"):
        x = next((r for r in out if t in r["tickers"]), None)
        if x: print(t, x["periodo"], x["recebido"], {k: round(v_ / 1e9, 2) for k, v_ in x["ano"].items()}, round((x["pl"] or 0) / 1e9, 1))
    print(len(out), "empresas")

if __name__ == "__main__":
    main()
