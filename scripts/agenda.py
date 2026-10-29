#!/usr/bin/env python3
"""Agenda do dia ("O que acompanhar hoje"): plenários da Câmara e do Senado, Copom e jogos; grava agenda.json.
Roda junto com as notícias (de hora em hora). Fontes: dados abertos da Câmara e do Senado, Banco Central e futebol.json."""
import json, re, time, urllib.request
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)", "Accept": "application/json"}
LIGAS_DESTAQUE = {"bra.1": "Brasileirão", "bra.2": "Série B", "uefa.champions": "Champions"}

def get(url, timeout=40):
    for tent in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            if tent == 1: raise
            time.sleep(3)

def curto(t, n=140):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

def lista(x):
    return x if isinstance(x, list) else [x] if x else []

def camara(hoje):
    """Sessões do Plenário da Câmara hoje e os primeiros itens da pauta."""
    out = []
    d = get(f"https://dadosabertos.camara.leg.br/api/v2/eventos?idOrgao=180&dataInicio={hoje}&dataFim={hoje}&itens=10&ordem=ASC&ordenarPor=dataHoraInicio")
    for ev in d.get("dados", []):
        if "cancel" in (ev.get("situacao") or "").lower(): continue
        hora = (ev.get("dataHoraInicio") or "")[11:16]
        itens = []
        try:
            for p in get(f"https://dadosabertos.camara.leg.br/api/v2/eventos/{ev['id']}/pauta").get("dados", [])[:4]:
                pr = p.get("proposicao_") or {}
                nome = f"{pr.get('siglaTipo', '')} {pr.get('numero', '')}/{pr.get('ano', '')}".strip(" /")
                ementa = curto(pr.get("ementa") or p.get("titulo") or "", 110)
                if nome or ementa: itens.append(f"{nome}: {ementa}" if nome else ementa)
        except Exception:
            pass
        out.append({"hora": hora, "tipo": "politica", "rotulo": "Câmara",
                    "titulo": curto(ev.get("descricaoTipo") or "Sessão do Plenário", 60) + " no Plenário",
                    "detalhe": itens[:3], "link": ev.get("urlRegistro") or "https://www.camara.leg.br/agenda",
                    "estado": ev.get("situacao")})
    return out

def senado(hoje):
    d = get(f"https://legis.senado.leg.br/dadosabertos/plenario/agenda/dia/{hoje:%Y%m%d}")
    out = []
    for s in lista(((d.get("AgendaPlenario") or {}).get("Sessoes") or {}).get("Sessao")):
        tipo = (s.get("TipoSessao") or "Sessão").strip().capitalize()
        if "não deliberativa" in tipo.lower() and not s.get("Materias"): continue
        itens = []
        for m in lista((s.get("Materias") or {}).get("Materia"))[:4]:
            ident = (m.get("DescricaoIdentificacaoMateria") or m.get("IdentificacaoMateria") or "").strip()
            ementa = curto(m.get("Ementa") or m.get("EmentaMateria") or "", 110)
            if ident or ementa: itens.append(f"{ident}: {ementa}" if ident else ementa)
        casa = "Congresso" if (s.get("Casa") or "").upper() == "CN" else "Senado"
        out.append({"hora": (s.get("Hora") or "").strip()[:5], "tipo": "politica", "rotulo": casa,
                    "titulo": curto(tipo, 60), "detalhe": itens[:3], "link": "https://www25.senado.leg.br/web/atividade/plenario",
                    "estado": s.get("SituacaoSessao")})
    return out

def copom(hoje):
    """A série da meta Selic vai até o dia da próxima reunião: esse é o dia da decisão."""
    u = get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json")[-1]
    dia = datetime.strptime(u["data"], "%d/%m/%Y").date()
    if dia == hoje:
        return [{"hora": "18:30", "tipo": "economia", "rotulo": "Copom", "titulo": "Copom anuncia a nova taxa Selic",
                 "detalhe": [f"Hoje a Selic está em {u['valor'].replace('.', ',')}% ao ano; a decisão sai no início da noite."],
                 "link": "https://www.bcb.gov.br/publicacoes/comunicadoscopom"}]
    if dia == hoje + timedelta(days=1):
        return [{"hora": "", "tipo": "economia", "rotulo": "Copom", "titulo": "Copom começa a reunião sobre a Selic",
                 "detalhe": ["A decisão sai amanhã, no início da noite."], "link": "https://www.bcb.gov.br/publicacoes/comunicadoscopom"}]
    return []

def jogos(hoje):
    try: fut = json.load(open("futebol.json", encoding="utf-8"))
    except Exception: return [], 0
    out, outros = [], 0
    for l in fut.get("ligas", []):
        for r in (l.get("jogos") or {}).get("rodadas", []):
            for j in r["jogos"]:
                try: d = datetime.fromisoformat(j["data"].replace("Z", "+00:00")).astimezone(BRT)
                except Exception: continue
                if d.date() != hoje: continue
                if l["id"] not in LIGAS_DESTAQUE: outros += 1; continue
                c, f = j["casa"], j["fora"]
                placar = f" {c.get('gols')} × {f.get('gols')}" if j["estado"] in ("in", "post") and c.get("gols") is not None else " ×"
                out.append({"hora": f"{d:%H:%M}", "tipo": "futebol", "rotulo": LIGAS_DESTAQUE[l["id"]],
                            "titulo": f"{c['nome']}{placar} {f['nome']}", "detalhe": [f"{r['n']}ª rodada" + (" · adiado" if j.get("adiado") else "")],
                            "estado": {"in": "ao vivo", "post": "encerrado"}.get(j["estado"], ""), "link": "tabelas/"})
    return out, outros

def main():
    import os
    agora = datetime.now(BRT); hoje = agora.date()
    if os.environ.get("AGENDA_DATA"): hoje = datetime.strptime(os.environ["AGENDA_DATA"], "%Y-%m-%d").date()   # para testes
    try: anterior = json.load(open("agenda.json", encoding="utf-8"))
    except Exception: anterior = {}
    ant_por_fonte = anterior.get("fontes", {}) if anterior.get("data") == str(hoje) else {}
    itens, erros, fontes = [], [], {}
    for nome, f in (("camara", camara), ("senado", senado), ("copom", copom)):
        try: fontes[nome] = f(hoje)
        except Exception as ex:
            erros.append(f"{nome}: {ex!r}"); fontes[nome] = ant_por_fonte.get(nome, [])   # mantém o que já tinha hoje
        itens += fontes[nome]
    js, outros = jogos(hoje)
    itens += js
    itens.sort(key=lambda i: (i["hora"] or "99:99", i["tipo"]))
    json.dump({"data": str(hoje), "atualizado": agora.strftime("%Y-%m-%dT%H:%M:%S%z"), "itens": itens,
               "outros_jogos": outros, "fontes": fontes, "erros": erros},
              open("agenda.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for e in erros: print("::warning::agenda " + e)
    print(f"Agenda de {hoje:%d/%m}: {len(itens)} itens ({', '.join(f'{k} {len(v)}' for k, v in fontes.items())}, jogos {len(js)}, outros {outros})")

if __name__ == "__main__":
    main()
