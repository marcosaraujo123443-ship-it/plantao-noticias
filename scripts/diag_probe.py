import json, urllib.request, sys, re
sys.path.insert(0, "scripts")
import agro
UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)", "Accept": "application/json"}
def get(u, t=40):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
out = {}
for nome, u in [
    ("cam_vot", "https://dadosabertos.camara.leg.br/api/v2/votacoes?idOrgao=180&ordem=DESC&ordenarPor=dataHoraRegistro&itens=15"),
    ("cam_vot2", "https://dadosabertos.camara.leg.br/api/v2/votacoes?ordem=DESC&ordenarPor=dataHoraRegistro&itens=15&dataInicio=2026-10-15"),
    ("sen_vot", "https://legis.senado.leg.br/dadosabertos/votacao?dataInicio=2026-10-01&dataFim=2026-10-30"),
    ("sen_vot2", "https://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/20261001/20261030"),
    ("sen_vot3", "https://legis.senado.leg.br/dadosabertos/plenario/resultado/veto/2026"),
]:
    try: out[nome] = json.loads(get(u))
    except Exception as e: out[nome] = repr(e)
try:
    v = out["cam_vot"]["dados"][0]["id"]
    out["cam_det"] = json.loads(get(f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{v}"))
    out["cam_orient"] = json.loads(get(f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{v}/orientacoes"))
except Exception as e: out["cam_det"] = repr(e)
POLOS = {"Sorriso": 5107925, "Sinop": 5107909, "Rio Verde": 5218805, "Cascavel": 4104808, "Londrina": 4113700, "Passo Fundo": 4314100,
         "Cruz Alta": 4306106, "Dourados": 5003702, "Uberaba": 3170107, "LEM": 2919553, "Balsas": 2101400, "Uruçuí": 2211209,
         "Ribeirão Preto": 3543402, "Chapecó": 4204202, "Patos de Minas": 3148004, "Barreiras": 2903201, "Primavera do Leste": 5107040, "Araguaína": 1702109}
pol = {}
for n, c in POLOS.items():
    try:
        d = json.loads(get(f"https://apiprevmet3.inmet.gov.br/previsao/{c}"))[str(c)]
        k = list(d)[0]; v = d[k].get("manha") or d[k]
        pol[n] = [c, v.get("entidade"), v.get("uf"), len(d)]
    except Exception as e: pol[n] = repr(e)[:100]
out["polos"] = pol
ag = {}
for p in ["soja", "milho", "boi-gordo", "cafe"]:
    try: ag[p] = [(t["titulo"], len(t["linhas"]), t["linhas"][:2]) for t in agro.tabelas(agro.texto(agro.BASE + p))]
    except Exception as e: ag[p] = repr(e)
out["agro"] = ag
json.dump(out, open("d/probe.json", "w"), ensure_ascii=False, indent=1)
