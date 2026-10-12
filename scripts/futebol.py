#!/usr/bin/env python3
"""Classificação dos campeonatos (API pública da ESPN) e grava futebol.json (roda no GitHub Actions)."""
import json, time, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)"}
LIGAS = [("bra.1", "Brasileirão Série A"), ("bra.2", "Brasileirão Série B"), ("eng.1", "Premier League (Inglaterra)"),
         ("esp.1", "La Liga (Espanha)"), ("ita.1", "Serie A (Itália)"), ("ger.1", "Bundesliga (Alemanha)"),
         ("fra.1", "Ligue 1 (França)"), ("por.1", "Liga Portugal"), ("uefa.champions", "Champions League"),
         ("arg.1", "Campeonato Argentino")]

def get(url):
    for tent in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception:
            if tent == 2: raise
            time.sleep(3)

def stat(e, nome):
    for s in e.get("stats", []):
        if s.get("name") == nome:
            return s.get("value") if s.get("value") is not None else s.get("displayValue")
    return None

def inteiro(v):
    try: return int(float(v))
    except (TypeError, ValueError): return None

def grupo(st, nome):
    linhas = []
    for e in st.get("entries", []):
        t, nota = e.get("team", {}), e.get("note") or {}
        logo = next((l.get("href") for l in t.get("logos") or [] if l.get("href")), None)
        linhas.append({"pos": inteiro(stat(e, "rank")), "time": t.get("shortDisplayName") or t.get("displayName"),
                       "sigla": t.get("abbreviation"), "escudo": logo,
                       "j": inteiro(stat(e, "gamesPlayed")), "v": inteiro(stat(e, "wins")), "e": inteiro(stat(e, "ties")),
                       "d": inteiro(stat(e, "losses")), "gp": inteiro(stat(e, "pointsFor")), "gc": inteiro(stat(e, "pointsAgainst")),
                       "sg": inteiro(stat(e, "pointDifferential")), "pts": inteiro(stat(e, "points")),
                       "nota": nota.get("description"), "cor": nota.get("color")})
    linhas.sort(key=lambda l: (l["pos"] is None, l["pos"] or 0, -(l["pts"] or 0)))
    for i, l in enumerate(linhas, 1):
        if l["pos"] is None: l["pos"] = i
    return {"nome": nome, "linhas": linhas}

def main():
    anterior = {}
    try: anterior = {l["id"]: l for l in json.load(open("futebol.json", encoding="utf-8")).get("ligas", [])}
    except Exception: pass
    ligas, erros = [], []
    for cod, nome in LIGAS:
        try:
            d = get(f"https://site.api.espn.com/apis/v2/sports/soccer/{cod}/standings?region=br&lang=pt")
            filhos = d.get("children") or ([d] if d.get("standings") else [])
            grupos = [grupo(c.get("standings", {}), c.get("name") if len(filhos) > 1 else "") for c in filhos]
            grupos = [g for g in grupos if g["linhas"]]
            if not grupos: raise ValueError("sem tabela")
            st = filhos[0].get("standings", {})
            ligas.append({"id": cod, "nome": nome, "temporada": st.get("seasonDisplayName") or str(st.get("season") or ""),
                          "grupos": grupos})
        except Exception as e:
            erros.append(f"{cod}: {e}")
            if cod in anterior: ligas.append(anterior[cod])
        time.sleep(0.3)
    if not ligas: raise SystemExit("Nenhuma tabela coletada: " + "; ".join(erros))
    with open("futebol.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "ESPN",
                   "ligas": ligas, "erros": erros}, f, ensure_ascii=False, separators=(",", ":"))
    print(", ".join(f"{l['id']} {sum(len(g['linhas']) for g in l['grupos'])} times/{len(l['grupos'])} grupos" for l in ligas), "erros:", erros)

if __name__ == "__main__":
    main()
