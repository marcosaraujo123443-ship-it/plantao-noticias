#!/usr/bin/env python3
"""Contornos das 137 mesorregiões (para os mapas de calor e chuva da aba Tempo) e uma cidade de referência em cada uma
(a capital, se estiver nela, ou a cidade mais perto do centro da região). Roda uma vez:
    python3 scripts/mapa_meso.py mesorregiao.json municipios.csv   # gera scripts/brasil_meso.json"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapa_brasil import caminho

def dentro(x, y, anel):
    ok = False
    for i in range(len(anel)):
        (x1, y1), (x2, y2) = anel[i - 1], anel[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: ok = not ok
    return ok

def main(geo, mun):
    g = json.load(open(geo, encoding="utf-8"))
    cidades = list(csv.DictReader(open(mun, encoding="utf-8")))
    out = []
    for f in g["features"]:
        p, geom = f["properties"], f["geometry"]
        aneis = geom["coordinates"][:1] if geom["type"] == "Polygon" else [q[0] for q in geom["coordinates"]]
        cod_uf = p["GEOCODIGO"][:2]
        dent = [c for c in cidades if c["codigo_uf"] == cod_uf and any(dentro(float(c["longitude"]), float(c["latitude"]), a) for a in aneis)]
        if not dent: print("sem cidade:", p["MESO"]); continue
        cap = [c for c in dent if c["capital"] == "1"]
        if cap: ref = cap[0]
        else:
            maior = max(aneis, key=len)
            cx = sum(x for x, _ in maior) / len(maior); cy = sum(y for _, y in maior) / len(maior)
            ref = min(dent, key=lambda c: (float(c["longitude"]) - cx) ** 2 + (float(c["latitude"]) - cy) ** 2)
        out.append({"id": p["GEOCODIGO"], "nome": p["MESO"].title().replace(" Do ", " do ").replace(" Da ", " da ").replace(" De ", " de ").replace(" Dos ", " dos ").replace(" E ", " e "),
                    "uf": p["UF"], "cod": int(ref["codigo_ibge"]), "cidade": ref["nome"], "d": caminho(aneis, tol=0.7, min_area=2)})
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brasil_meso.json")
    json.dump(out, open(destino, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(len(out), "mesorregiões,", os.path.getsize(destino) // 1024, "KB")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
