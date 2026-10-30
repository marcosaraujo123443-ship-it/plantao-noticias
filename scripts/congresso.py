#!/usr/bin/env python3
"""Votações recentes no Plenário da Câmara e do Senado (dados abertos oficiais) -> congresso.json."""
import json, re, time, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0; +https://plantaoinforma.com.br)", "Accept": "application/json"}
CAM = "https://dadosabertos.camara.leg.br/api/v2"
# votações de mérito (o projeto em si), não requerimentos, emendas, destaques ou redação final
MERITO = re.compile(r"^(Aprovad|Rejeitad)[oa]s?,?( em (primeiro|segundo) turno,| por unanimidade,| em apreciação preliminar,)? (o|a) "
                    r"(Projeto|Substitutivo|Proposta de Emenda|Medida Provisória|Emenda Substitutiva Global|Parecer .*Medida)", re.I)
NAO = re.compile(r"pressupostos|apreciação preliminar", re.I)
NOMES = {"PL": "Projeto de lei", "PLP": "Projeto de lei complementar", "PEC": "Proposta de emenda à Constituição",
         "MPV": "Medida provisória", "PDL": "Projeto de decreto legislativo", "PLV": "Projeto de lei de conversão",
         "PRC": "Projeto de resolução", "PLN": "Projeto de lei do Congresso"}

def get(url, timeout=40):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            if t == 2: raise
            time.sleep(3)

def curto(t, n=220):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

def camara(hoje, n=8):
    d = get(f"{CAM}/votacoes?idOrgao=180&ordem=DESC&ordenarPor=dataHoraRegistro&itens=200&dataInicio={hoje - timedelta(days=45)}&dataFim={hoje}")
    out, vistos = [], set()
    for v in d.get("dados", []):
        desc = v.get("descricao") or ""
        if not MERITO.search(desc) or NAO.search(desc): continue
        try: det = get(f"{CAM}/votacoes/{v['id']}")["dados"]
        except Exception: continue
        props = [p for p in (det.get("proposicoesAfetadas") or []) if p.get("ano")] or \
                [p for p in (det.get("objetosPossiveis") or []) if p.get("ano")]
        if not props: continue
        p = props[0]
        chave = (p.get("siglaTipo"), p.get("numero"), p.get("ano"))
        if chave in vistos: continue
        vistos.add(chave)
        sim = nao = 0
        try:
            votos = get(f"{CAM}/votacoes/{v['id']}/votos").get("dados", [])
            c = Counter((x.get("tipoVoto") or "").strip() for x in votos)
            sim, nao = c.get("Sim", 0), c.get("Não", 0)
        except Exception: pass
        out.append({"casa": "Câmara", "data": v.get("data"), "hora": (v.get("dataHoraRegistro") or "")[11:16],
                    "materia": f"{p.get('siglaTipo')} {p.get('numero')}/{p.get('ano')}", "tipo": NOMES.get(p.get("siglaTipo"), ""),
                    "ementa": curto(p.get("ementa")), "resultado": "Aprovado" if v.get("aprovacao") == 1 else "Rejeitado" if v.get("aprovacao") == 0 else "",
                    "descricao": curto(desc, 200), "sim": sim or None, "nao": nao or None,
                    "link": f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={p.get('id')}"})
        if len(out) >= n: break
        time.sleep(0.3)
    return out

def senado(hoje, n=8):
    d = get(f"https://legis.senado.leg.br/dadosabertos/votacao?dataInicio={hoje - timedelta(days=60)}&dataFim={hoje}")
    out, vistos = [], set()
    for v in sorted(d if isinstance(d, list) else [], key=lambda x: (x.get("dataSessao") or "", x.get("sequencialSessao") or 0), reverse=True):
        ident = v.get("identificacao") or ""
        if not ident or ident in vistos or v.get("votacaoSecreta") == "S": continue
        vistos.add(ident)
        c = Counter(x.get("siglaVotoParlamentar") for x in v.get("votos") or [])
        res = {"A": "Aprovado", "R": "Rejeitado"}.get(v.get("resultadoVotacao"), "")
        turno = re.search(r"(primeiro|segundo) turno", v.get("descricaoVotacao") or "")
        out.append({"casa": "Senado", "data": v.get("dataSessao"), "hora": "", "materia": ident,
                    "tipo": NOMES.get(v.get("sigla"), ""), "ementa": curto(v.get("ementa")), "resultado": res,
                    "descricao": curto(v.get("descricaoVotacao"), 200),
                    "sim": c.get("Sim") or None, "nao": c.get("Não") or None,
                    "link": f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{v.get('codigoMateria')}"})
        if len(out) >= n: break
    return out

def main():
    hoje = datetime.now(BRT).date()
    try: velho = json.load(open("congresso.json", encoding="utf-8"))
    except Exception: velho = {}
    itens, erros = [], []
    for nome, f in (("Câmara", camara), ("Senado", senado)):
        try: itens += f(hoje)
        except Exception as ex:
            erros.append(f"{nome}: {ex!r}"[:200]); itens += [i for i in velho.get("votacoes", []) if i["casa"] == nome]
    itens.sort(key=lambda i: (i["data"] or "", i["hora"]), reverse=True)
    json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "votacoes": itens[:12], "erros": erros},
              open("congresso.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for e in erros: print("::warning::congresso " + e)
    print(f"{len(itens)} votações: " + "; ".join(f"{i['casa']} {i['materia']} {i['resultado']}" for i in itens[:12]))

if __name__ == "__main__":
    main()
