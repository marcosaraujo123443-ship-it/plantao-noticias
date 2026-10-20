#!/usr/bin/env python3
"""Classificação, últimos resultados e próximos jogos dos campeonatos (API pública da ESPN); grava futebol.json."""
import json, time, urllib.request
from datetime import datetime, timedelta, timezone

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

def time_jogo(c):
    t = c.get("team", {})
    return {"nome": t.get("shortDisplayName") or t.get("displayName"), "sigla": t.get("abbreviation"),
            "escudo": t.get("logo"), "gols": inteiro(c.get("score")), "venceu": c.get("winner")}

def jogos(cod):
    """Jogos de 10 dias atrás a 14 dias à frente: até 10 últimos resultados e 10 próximos (inclui os em andamento)."""
    hoje = datetime.now(timezone.utc)
    ini, fim = (hoje - timedelta(days=10)).strftime("%Y-%m-%d"), (hoje + timedelta(days=14)).strftime("%Y-%m-%d")
    # a API não aceita intervalo de dias, mas aceita o mês inteiro: mês anterior, atual e seguinte
    meses = sorted({(hoje + timedelta(days=dd)).strftime("%Y%m") for dd in (-10, 0, 14)})
    eventos = {}
    for m in meses:
        d = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{cod}/scoreboard?dates={m}&limit=500&region=br&lang=pt")
        for ev in d.get("events", []): eventos[ev.get("id")] = ev
    out = []
    for ev in eventos.values():
        if not (ini <= (ev.get("date") or "")[:10] <= fim): continue
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors") or []
        casa = next((c for c in cs if c.get("homeAway") == "home"), cs[0] if cs else {})
        fora = next((c for c in cs if c.get("homeAway") == "away"), cs[1] if len(cs) > 1 else {})
        st = (ev.get("status") or comp.get("status") or {}).get("type", {})
        out.append({"data": ev.get("date"), "estado": st.get("state"), "detalhe": st.get("shortDetail") or st.get("detail"),
                    "casa": time_jogo(casa), "fora": time_jogo(fora), "local": (comp.get("venue") or {}).get("fullName")})
    out.sort(key=lambda j: j["data"] or "")
    feitos = [j for j in out if j["estado"] == "post"][-10:]
    proximos = [j for j in out if j["estado"] in ("pre", "in")][:10]
    return {"ultimos": feitos[::-1], "proximos": proximos}

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
            liga = {"id": cod, "nome": nome, "temporada": st.get("seasonDisplayName") or str(st.get("season") or ""),
                    "grupos": grupos}
            try: liga["jogos"] = jogos(cod)
            except Exception as e:
                erros.append(f"{cod} jogos: {e}")
                if anterior.get(cod, {}).get("jogos"): liga["jogos"] = anterior[cod]["jogos"]
            ligas.append(liga)
        except Exception as e:
            erros.append(f"{cod}: {e}")
            if cod in anterior: ligas.append(anterior[cod])
        time.sleep(0.3)
    if not ligas: raise SystemExit("Nenhuma tabela coletada: " + "; ".join(erros))
    with open("futebol.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "ESPN",
                   "ligas": ligas, "erros": erros}, f, ensure_ascii=False, separators=(",", ":"))
    print(", ".join(f"{l['id']} {sum(len(g['linhas']) for g in l['grupos'])} times, {len((l.get('jogos') or {}).get('ultimos', []))}/"
                    f"{len((l.get('jogos') or {}).get('proximos', []))} jogos" for l in ligas), "erros:", erros)
    for er in erros: print("::warning::" + er)

if __name__ == "__main__":
    main()
