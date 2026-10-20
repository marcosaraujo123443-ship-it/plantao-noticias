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
    return {"id": t.get("id"), "nome": t.get("shortDisplayName") or t.get("displayName"), "sigla": t.get("abbreviation"),
            "escudo": t.get("logo"), "gols": inteiro(c.get("score")), "venceu": c.get("winner")}

def jogo(ev):
    comp = (ev.get("competitions") or [{}])[0]
    cs = comp.get("competitors") or []
    casa = next((c for c in cs if c.get("homeAway") == "home"), cs[0] if cs else {})
    fora = next((c for c in cs if c.get("homeAway") == "away"), cs[1] if len(cs) > 1 else {})
    st = (ev.get("status") or comp.get("status") or {}).get("type", {})
    return {"data": ev.get("date"), "estado": st.get("state"), "detalhe": st.get("shortDetail") or st.get("detail"),
            "casa": time_jogo(casa), "fora": time_jogo(fora), "local": (comp.get("venue") or {}).get("fullName"),
            "_temp": "{year}/{type}/{slug}".format(**{"year": "", "type": "", "slug": "", **(ev.get("season") or {})})}

def ts(iso): return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()

def numerar_rodadas(js, n_times):
    """A ESPN não informa a rodada: os jogos de uma rodada acontecem num bloco de datas (folga de 30 h entre blocos).
    Blocos grandes são rodadas, numeradas em ordem; jogos soltos (adiados/antecipados) vão para a rodada que falta
    aos dois times."""
    js.sort(key=lambda g: g["data"])
    blocos, atual = [], []
    for g in js:
        if atual and ts(g["data"]) - ts(atual[-1]["data"]) > 30 * 3600: blocos.append(atual); atual = []
        atual.append(g)
    if atual: blocos.append(atual)
    meio = max(1, n_times // 2)
    grande = lambda b: len(b) >= max(3, round(meio * 0.5))
    rod_time, n, soltos, jogados = {}, 0, [], {}
    for bi, b in enumerate(blocos):
        normais = b
        if not grande(b):
            soltos += [(bi, g) for g in b]
        else:
            # jogo cujos dois times jogam duas vezes no mesmo bloco = adiado encaixado no meio de outra rodada
            cont = {}
            for g in b:
                for t in (g["casa"]["id"], g["fora"]["id"]): cont[t] = cont.get(t, 0) + 1
            normais = []
            for g in b:
                if cont[g["casa"]["id"]] > 1 and cont[g["fora"]["id"]] > 1:
                    soltos.append((bi, g)); cont[g["casa"]["id"]] -= 1; cont[g["fora"]["id"]] -= 1
                    for t in (g["casa"]["id"], g["fora"]["id"]): jogados[t] = jogados.get(t, 0) + 1   # já conta o extra
                else: normais.append(g)
            # número da rodada = o que a maioria dos times do bloco está jogando (jogos anteriores + 1)
            cand = [jogados.get(t, 0) + 1 for g in normais for t in (g["casa"]["id"], g["fora"]["id"])]
            n = max(set(cand), key=cand.count)
            for g in normais:
                g["rodada"] = n
                for t in (g["casa"]["id"], g["fora"]["id"]): rod_time.setdefault(t, set()).add(n)
            for bb_i, g in soltos:
                if bb_i == bi: g.setdefault("_bloco_rod", n)
        for g in (normais if grande(b) else b):
            for t in (g["casa"]["id"], g["fora"]["id"]): jogados[t] = jogados.get(t, 0) + 1
    n = max((r for rs in rod_time.values() for r in rs), default=0)
    total = n
    for bi, g in soltos:
        # rodada "do momento" em que o jogo acontece, para marcar se ele está atrasado em relação a ela
        anterior = g.pop("_bloco_rod", None) or max((x["rodada"] for bb in blocos[:bi] for x in bb if "rodada" in x), default=0)
        usadas = rod_time.get(g["casa"]["id"], set()) | rod_time.get(g["fora"]["id"], set())
        livre = next((r for r in range(1, total + 2) if r not in usadas), anterior or 1)
        g["rodada"] = livre
        if livre < anterior: g["adiado"] = True
        for t in (g["casa"]["id"], g["fora"]["id"]): rod_time.setdefault(t, set()).add(livre)
    return js

def jogos(cod, n_times):
    """Temporada inteira (para numerar as rodadas); guarda 2 rodadas antes e 2 depois da atual."""
    hoje = datetime.now(timezone.utc)
    eventos = {}
    for ano in sorted({hoje.year - 1, hoje.year, hoje.year + 1}):
        try:
            d = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{cod}/scoreboard?dates={ano}&limit=1000&region=br&lang=pt")
        except Exception:
            continue
        for ev in d.get("events", []): eventos[ev.get("id")] = ev
    todos = [jogo(ev) for ev in eventos.values() if ev.get("date")]
    if not todos: raise ValueError("sem jogos")
    # temporada vigente: a mais frequente entre os jogos de 10 dias atrás a 14 dias à frente
    ini, fim = (hoje - timedelta(days=10)).isoformat()[:10], (hoje + timedelta(days=14)).isoformat()[:10]
    perto = [g["_temp"] for g in todos if ini <= g["data"][:10] <= fim] or [max(todos, key=lambda g: g["data"])["_temp"]]
    temp = max(set(perto), key=perto.count)
    js = numerar_rodadas([g for g in todos if g["_temp"] == temp], n_times)
    pend = [g["rodada"] for g in js if g["estado"] != "post" and not g.get("adiado")]
    atual = min(pend) if pend else max(g["rodada"] for g in js)
    rodadas = []
    for r in range(max(1, atual - 2), atual + 3):
        lista = [g for g in js if g["rodada"] == r]
        if not lista: continue
        for g in lista:
            g.pop("_temp", None); g["casa"].pop("id", None); g["fora"].pop("id", None)
        rodadas.append({"n": r, "jogos": lista})
    return {"atual": atual, "rodadas": rodadas}

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
            try: liga["jogos"] = jogos(cod, sum(len(g["linhas"]) for g in grupos))
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
    print(", ".join(f"{l['id']} {sum(len(g['linhas']) for g in l['grupos'])} times, rodada {(l.get('jogos') or {}).get('atual')}: "
                    + "/".join(str(len(r["jogos"])) for r in (l.get("jogos") or {}).get("rodadas", [])) for l in ligas), "erros:", erros)
    for er in erros: print("::warning::" + er)

if __name__ == "__main__":
    main()
