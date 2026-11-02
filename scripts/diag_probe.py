import sys, json
sys.path.insert(0, "scripts"); import estados as E
out = []
for ano in (2014, 2015, 2016, 2017, 2018, 2020, 2023):
    try:
        b = E.balanco(35, ano, 6)
        if not b: out.append(f"{ano}: vazio"); continue
        r = {x["n"]: x.get("realizado") for x in b["receitas"]}; d = {x["n"]: x.get("liquidado") for x in b["despesas"]}
        out.append(f"{ano}: pop {b['populacao']} rec {len(b['receitas'])} desp {len(b['despesas'])} func {len(b['funcoes'])} RT {r.get('Total arrecadado')} DT {d.get('Total')} imp {r.get('Impostos, taxas e contribuições de melhoria')} tu {r.get('das quais, da União')} inv {d.get('Investimentos')} edu {[f['liquidado'] for f in b['funcoes'] if f['n']=='Educação']}")
    except Exception as ex: out.append(f"{ano}: ERRO {ex!r}"[:200])
try:
    a = E.rreo(35, 2016, 6, "RREO-Anexo 01"); out.append("2016 contas: " + "; ".join(sorted({(i.get('cod_conta') or '')[:40] for i in a})[:25]))
except Exception as ex: out.append(repr(ex))
print("::notice::" + "%0A".join(out))
