#!/usr/bin/env python3
"""Previsão do tempo nas 27 capitais e alertas meteorológicos ativos, ambos do INMET (dados públicos) -> tempo.json."""
import json, os, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapa_brasil import caminho, proj

BRT = timezone(timedelta(hours=-3))
UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0; +https://plantaoinforma.com.br)", "Accept": "application/json"}
API = "https://apiprevmet3.inmet.gov.br"
CAPITAIS = [  # uf, cidade, código IBGE, latitude, longitude, região
    ("AC", "Rio Branco", 1200401, -9.97, -67.81, "Norte"), ("AP", "Macapá", 1600303, 0.03, -51.07, "Norte"),
    ("AM", "Manaus", 1302603, -3.12, -60.02, "Norte"), ("PA", "Belém", 1501402, -1.46, -48.50, "Norte"),
    ("RO", "Porto Velho", 1100205, -8.76, -63.90, "Norte"), ("RR", "Boa Vista", 1400100, 2.82, -60.67, "Norte"),
    ("TO", "Palmas", 1721000, -10.18, -48.33, "Norte"),
    ("AL", "Maceió", 2704302, -9.67, -35.74, "Nordeste"), ("BA", "Salvador", 2927408, -12.97, -38.50, "Nordeste"),
    ("CE", "Fortaleza", 2304400, -3.73, -38.53, "Nordeste"), ("MA", "São Luís", 2111300, -2.53, -44.30, "Nordeste"),
    ("PB", "João Pessoa", 2507507, -7.12, -34.86, "Nordeste"), ("PE", "Recife", 2611606, -8.05, -34.90, "Nordeste"),
    ("PI", "Teresina", 2211001, -5.09, -42.80, "Nordeste"), ("RN", "Natal", 2408102, -5.79, -35.21, "Nordeste"),
    ("SE", "Aracaju", 2800308, -10.91, -37.07, "Nordeste"),
    ("DF", "Brasília", 5300108, -15.79, -47.88, "Centro-Oeste"), ("GO", "Goiânia", 5208707, -16.68, -49.25, "Centro-Oeste"),
    ("MT", "Cuiabá", 5103403, -15.60, -56.10, "Centro-Oeste"), ("MS", "Campo Grande", 5002704, -20.44, -54.65, "Centro-Oeste"),
    ("ES", "Vitória", 3205309, -20.32, -40.34, "Sudeste"), ("MG", "Belo Horizonte", 3106200, -19.92, -43.94, "Sudeste"),
    ("RJ", "Rio de Janeiro", 3304557, -22.91, -43.17, "Sudeste"), ("SP", "São Paulo", 3550308, -23.55, -46.63, "Sudeste"),
    ("PR", "Curitiba", 4106902, -25.43, -49.27, "Sul"), ("RS", "Porto Alegre", 4314902, -30.03, -51.23, "Sul"),
    ("SC", "Florianópolis", 4205407, -27.60, -48.55, "Sul"),
]
UF_COD = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
          "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
          "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
NIVEL = {"Perigo Potencial": 1, "Perigo": 2, "Grande Perigo": 3}

def get(url, timeout=45):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            if t == 2: raise
            time.sleep(4)

def num(x):
    try: return int(round(float(x)))
    except Exception: return None

def periodo(p):
    return {"resumo": (p.get("resumo") or "").strip(), "max": num(p.get("temp_max")), "min": num(p.get("temp_min")),
            "icone": p.get("cod_icone") or ""}

def previsao(cod):
    bruto = get(f"{API}/previsao/{cod}")[str(cod)]
    dias = []
    for data, v in bruto.items():
        d = datetime.strptime(data, "%d/%m/%Y").date()
        base = v.get("tarde") or v.get("manha") or v if isinstance(v, dict) and "manha" in v else v
        p = {k: base.get(k) for k in ("resumo",)}
        maxs = [num(x.get("temp_max")) for x in ([v[k] for k in ("manha", "tarde", "noite") if k in v] or [v])]
        mins = [num(x.get("temp_min")) for x in ([v[k] for k in ("manha", "tarde", "noite") if k in v] or [v])]
        dia = {"data": str(d), "semana": (base.get("dia_semana") or "").split("-")[0], "resumo": (base.get("resumo") or "").strip(),
               "icone": base.get("cod_icone") or "", "max": max([m for m in maxs if m is not None], default=None),
               "min": min([m for m in mins if m is not None], default=None),
               "umid_max": num(base.get("umidade_max")), "umid_min": num(base.get("umidade_min")),
               "vento": " ".join(x for x in (base.get("int_vento"), base.get("dir_vento")) if x).strip(),
               "nascer": base.get("nascer"), "ocaso": base.get("ocaso")}
        if "manha" in v:
            dia["periodos"] = {k: periodo(v[k]) for k in ("manha", "tarde", "noite") if k in v}
        dias.append(dia)
    return sorted(dias, key=lambda d: d["data"])

def avisos():
    a = get(f"{API}/avisos/ativos", timeout=60)
    out, vistos = [], set()
    for x in (a.get("hoje") or []) + (a.get("futuro") or []):
        if x.get("encerrado") or x.get("id") in vistos: continue
        vistos.add(x.get("id"))
        ufs = sorted({UF_COD.get(g.strip()[:2]) for g in (x.get("geocodes") or "").split(",") if UF_COD.get(g.strip()[:2])})
        try:
            geo = json.loads(x.get("poligono") or "null")
            aneis = geo["coordinates"] if geo["type"] == "Polygon" else [p[0] for p in geo["coordinates"]]
            d = caminho(aneis[:1] if geo["type"] == "Polygon" else aneis, tol=0.8, min_area=1)
        except Exception:
            d = ""
        out.append({"id": x.get("id"), "evento": x.get("descricao"), "severidade": x.get("severidade"),
                    "nivel": NIVEL.get(x.get("severidade"), 1), "cor": x.get("aviso_cor"),
                    "inicio": (x.get("inicio") or "").replace(" ", "T"), "fim": (x.get("fim") or "").replace(" ", "T"),
                    "ufs": ufs, "riscos": [r.strip() for r in (x.get("riscos") or []) if r.strip()][:2],
                    "instrucoes": [r.strip() for r in (x.get("instrucoes") or []) if r.strip()][:4],
                    "municipios": len((x.get("geocodes") or "").split(",")), "d": d})
    out.sort(key=lambda a: (a["inicio"], -a["nivel"]))
    return out

def main():
    try: velho = json.load(open("tempo.json", encoding="utf-8"))
    except Exception: velho = {}
    antes = {c["uf"]: c for c in velho.get("capitais", [])}
    capitais, erros = [], []
    for uf, nome, cod, lat, lon, reg in CAPITAIS:
        x, y = proj(lon, lat)
        c = {"uf": uf, "nome": nome, "cod": cod, "regiao": reg, "x": round(x, 1), "y": round(y, 1)}
        try: c["dias"] = previsao(cod)
        except Exception as ex:
            erros.append(f"{nome}: {ex!r}"[:160]); c["dias"] = antes.get(uf, {}).get("dias", [])
        capitais.append(c)
    try: al = avisos()
    except Exception as ex:
        erros.append(f"avisos: {ex!r}"[:160]); al = velho.get("avisos", [])
    if all(not c["dias"] for c in capitais): raise SystemExit("INMET indisponível: " + "; ".join(erros))
    json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "INMET",
               "capitais": capitais, "avisos": al, "erros": erros},
              open("tempo.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for e in erros: print("::warning::tempo " + e)
    print(f"{sum(1 for c in capitais if c['dias'])} capitais, {len(al)} alertas, {os.path.getsize('tempo.json') // 1024} KB")

if __name__ == "__main__":
    main()
