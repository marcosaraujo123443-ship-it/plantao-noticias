#!/usr/bin/env python3
"""As 20 maiores economias do mundo: PIB, crescimento, exportações, importações e saldo comercial de bens e serviços
(Banco Mundial, World Development Indicators) -> economias.json."""
import json, time, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)"}
WB = "https://api.worldbank.org/v2"
IND = {"pib": "NY.GDP.MKTP.CD", "cresc": "NY.GDP.MKTP.KD.ZG", "exp": "NE.EXP.GNFS.CD", "imp": "NE.IMP.GNFS.CD",
       "saldo": "NE.RSB.GNFS.CD", "pib_pc": "NY.GDP.PCAP.CD"}
NOMES = {"USA": "Estados Unidos", "CHN": "China", "DEU": "Alemanha", "JPN": "Japão", "GBR": "Reino Unido", "IND": "Índia",
         "FRA": "França", "RUS": "Rússia", "ITA": "Itália", "CAN": "Canadá", "BRA": "Brasil", "ESP": "Espanha",
         "KOR": "Coreia do Sul", "MEX": "México", "AUS": "Austrália", "TUR": "Turquia", "IDN": "Indonésia",
         "NLD": "Países Baixos", "SAU": "Arábia Saudita", "CHE": "Suíça", "POL": "Polônia", "TWN": "Taiwan",
         "BEL": "Bélgica", "IRL": "Irlanda", "ARG": "Argentina", "SWE": "Suécia", "ISR": "Israel", "SGP": "Singapura",
         "ARE": "Emirados Árabes", "THA": "Tailândia", "AUT": "Áustria", "NOR": "Noruega", "NGA": "Nigéria", "EGY": "Egito"}
BANDEIRA = {k: "".join(chr(0x1F1E6 + ord(c) - 65) for c in v) for k, v in {
    "USA": "US", "CHN": "CN", "DEU": "DE", "JPN": "JP", "GBR": "GB", "IND": "IN", "FRA": "FR", "RUS": "RU", "ITA": "IT", "CAN": "CA",
    "BRA": "BR", "ESP": "ES", "KOR": "KR", "MEX": "MX", "AUS": "AU", "TUR": "TR", "IDN": "ID", "NLD": "NL", "SAU": "SA", "CHE": "CH",
    "POL": "PL", "TWN": "TW", "BEL": "BE", "IRL": "IE", "ARG": "AR", "SWE": "SE", "ISR": "IL", "SGP": "SG", "ARE": "AE", "THA": "TH",
    "AUT": "AT", "NOR": "NO", "NGA": "NG", "EGY": "EG"}.items()}

def get(caminho):
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{WB}/{caminho}", headers=UA), timeout=90) as r:
                return json.load(r)
        except Exception:
            if t == 2: raise
            time.sleep(5)

def main():
    paises = {p["id"]: p for p in get("country?format=json&per_page=400")[1] if p["region"]["value"] != "Aggregates"}
    dados = {}
    for k, cod in IND.items():
        for x in get(f"country/all/indicator/{cod}?format=json&per_page=400&mrnev=1")[1] or []:
            iso = x["countryiso3code"]
            if iso in paises and x["value"] is not None: dados.setdefault(iso, {})[k] = (x["value"], x["date"])
    top = sorted((i for i in dados if "pib" in dados[i]), key=lambda i: -dados[i]["pib"][0])[:20]
    lista = []
    for i in top:
        d = dados[i]
        lista.append({"iso": i, "nome": NOMES.get(i, paises[i]["name"]), "bandeira": BANDEIRA.get(i, ""),
                      **{k: round(v[0], 2) for k, v in d.items()}, "anos": {k: v[1] for k, v in d.items()}})
    if len(lista) < 20: raise SystemExit("Banco Mundial incompleto")
    json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "fonte": "Banco Mundial (World Development Indicators)", "paises": lista},
              open("economias.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print([(p["nome"], round(p["pib"] / 1e9), p["anos"]["pib"]) for p in lista])

if __name__ == "__main__":
    main()
