#!/usr/bin/env python3
"""Guarda um ponto por dia de cada cotação do agro (agro.json -> agro_historico.json), para os gráficos de tendência.
A fonte só mostra o preço do dia; o histórico é montado pelo próprio site a partir da primeira coleta."""
import json
from datetime import datetime

DIAS = 120   # quantos dias guardar

def data_iso(d):
    """'14/10/2026' ou '05 - 09/10/2026' (semanal) -> '2026-10-14' / '2026-10-09'."""
    d = (d or "").split("-")[-1].strip()
    try: return datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError: return None

def main():
    a = json.load(open("agro.json", encoding="utf-8"))
    try: h = json.load(open("agro_historico.json", encoding="utf-8"))
    except Exception: h = {"indicadores": {}, "pracas": {}}
    hoje = datetime.now().strftime("%Y-%m-%d")
    for i in a.get("indicadores", []):
        dia = data_iso(i.get("data")) or hoje
        if i.get("preco") is not None:
            h["indicadores"].setdefault(i["nome"], {"un": i["un"], "pontos": {}})["pontos"][dia] = i["preco"]
    for p in a.get("pracas", []):
        for praca, preco, _ in p.get("linhas", []):
            if preco is not None:
                h["pracas"].setdefault(f"{p['nome']}|{praca}", {"un": p["un"], "pontos": {}})["pontos"][hoje] = preco
    for grupo in ("indicadores", "pracas"):
        for s in h[grupo].values():
            s["pontos"] = dict(sorted(s["pontos"].items())[-DIAS:])
    h["atualizado"] = a.get("atualizado_utc")
    json.dump(h, open("agro_historico.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    n = max((len(s["pontos"]) for s in h["indicadores"].values()), default=0)
    print(f"Histórico do agro: {len(h['indicadores'])} indicadores, {len(h['pracas'])} praças, até {n} dias")

if __name__ == "__main__":
    main()
