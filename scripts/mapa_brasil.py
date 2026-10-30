#!/usr/bin/env python3
"""Contornos dos estados para o mapa da aba Tempo (SVG). A projeção fica aqui e é usada também pelo tempo.py
para desenhar as áreas de alerta do INMET no mesmo mapa.
    python3 scripts/mapa_brasil.py brazil-states.geojson   # gera scripts/brasil_mapa.json (uma vez)"""
import json, math, os, sys

LON0, LAT0, K = -74.2, 5.6, 15.0          # canto superior esquerdo e pixels por grau
COS = math.cos(math.radians(14))
W, H = round((74.2 - 32.6) * K * COS), round((5.6 + 33.9) * K)

def proj(lon, lat):
    return (lon - LON0) * K * COS, (LAT0 - lat) * K

def simplificar(pts, tol):
    """Douglas-Peucker (em pixels)."""
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1; n = math.hypot(dx, dy) or 1e-9
    i, dmax = 0, -1
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + x2 * y1 - y2 * x1) / n
        if d > dmax: i, dmax = k, d
    if dmax <= tol: return [pts[0], pts[-1]]
    return simplificar(pts[:i + 1], tol)[:-1] + simplificar(pts[i:], tol)

def caminho(aneis, tol=0.6, min_area=4):
    d = []
    for anel in aneis:
        pts = [proj(x, y) for x, y in anel]
        area = abs(sum(pts[k][0] * pts[k - 1][1] - pts[k - 1][0] * pts[k][1] for k in range(len(pts)))) / 2
        if area < min_area: continue          # ilhas minúsculas
        # anel fechado: divide no ponto mais distante do início antes de simplificar
        m = max(range(len(pts)), key=lambda k: (pts[k][0] - pts[0][0]) ** 2 + (pts[k][1] - pts[0][1]) ** 2)
        pts = simplificar(pts[:m + 1], tol)[:-1] + simplificar(pts[m:], tol)
        if len(pts) < 4: continue
        d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(d)

def aneis_de(geom):
    if geom["type"] == "Polygon": return geom["coordinates"][:1]
    if geom["type"] == "MultiPolygon": return [p[0] for p in geom["coordinates"]]
    return []

if __name__ == "__main__":
    g = json.load(open(sys.argv[1], encoding="utf-8"))
    out = {"w": W, "h": H, "ufs": {}}
    for f in g["features"]:
        out["ufs"][f["properties"]["sigla"]] = caminho(aneis_de(f["geometry"]))
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brasil_mapa.json")
    json.dump(out, open(destino, "w", encoding="utf-8"), separators=(",", ":"))
    print(W, H, os.path.getsize(destino), "bytes")
