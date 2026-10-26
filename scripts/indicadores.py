#!/usr/bin/env python3
"""Indicadores econômicos do Banco Central (SGS) e decisões do Copom; grava indicadores.json (roda no GitHub Actions)."""
import json, re, time, urllib.request
from datetime import datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)", "Accept": "application/json"}
SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados"
# chave: (código SGS, nome, fonte, tipo) — tipo "mensal" = variação % no mês; "nivel" = taxa
SERIES = {
    "ipca": (433, "IPCA", "IBGE", "mensal"),
    "ipca15": (7478, "IPCA-15", "IBGE", "mensal"),
    "igpm": (189, "IGP-M", "FGV", "mensal"),
    "igpdi": (190, "IGP-DI", "FGV", "mensal"),
    "inpc": (188, "INPC", "IBGE", "mensal"),
    "desemprego": (24369, "Desemprego", "IBGE (PNAD Contínua)", "nivel"),
    "cdi": (4389, "CDI", "B3/Banco Central", "nivel"),
}

def get(url):
    for tent in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if tent == 2: raise
            time.sleep(4)

def mes(data):                       # "01/09/2026" -> "2026-09"
    d, m, a = data.split("/"); return f"{a}-{m}"

def serie(cod, diaria=False):
    """Mensais: os últimos ~30 meses por intervalo de datas (a API limita 'ultimos' a 20). Diárias: só o último."""
    if diaria:
        url = SGS.format(cod) + "/ultimos/1?formato=json"
    else:
        hoje = datetime.now(timezone.utc)
        ini = (hoje - timedelta(days=930)).strftime("%d/%m/%Y")
        url = SGS.format(cod) + f"?formato=json&dataInicial={ini}&dataFinal={hoje:%d/%m/%Y}"
    return [{"data": i["data"], "valor": float(i["valor"])} for i in get(url)]

def acumulado(valores):
    p = 1.0
    for v in valores: p *= 1 + v / 100
    return (p - 1) * 100

def main():
    agora = datetime.now(timezone.utc)
    try: anterior = json.load(open("indicadores.json", encoding="utf-8"))
    except Exception: anterior = {}
    out, erros = {"atualizado_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "Banco Central (SGS)", "series": {}}, []
    for chave, (cod, nome, fonte, tipo) in SERIES.items():
        try:
            pts = serie(cod, diaria=(chave == "cdi"))
            if tipo == "mensal":
                dados = [{"mes": mes(p["data"]), "valor": p["valor"]} for p in pts]
                for i, d in enumerate(dados):
                    if i >= 11: d["doze"] = round(acumulado([x["valor"] for x in dados[i - 11:i + 1]]), 2)
                    ano = [x["valor"] for x in dados[:i + 1] if x["mes"][:4] == d["mes"][:4]]
                    if len(ano) == int(d["mes"][5:]): d["ano"] = round(acumulado(ano), 2)
                out["series"][chave] = {"nome": nome, "fonte": fonte, "tipo": tipo, "dados": dados[-25:]}
            elif chave == "desemprego":
                out["series"][chave] = {"nome": nome, "fonte": fonte, "tipo": tipo,
                                        "dados": [{"mes": mes(p["data"]), "valor": p["valor"]} for p in pts][-25:]}
            else:  # diário: guarda só o último valor
                out["series"][chave] = {"nome": nome, "fonte": fonte, "tipo": tipo,
                                        "atual": pts[-1]["valor"], "data": pts[-1]["data"]}
        except Exception as ex:
            erros.append(f"{chave}: {ex}")
            # a API às vezes responde vazio; mantém o último dado bom em vez de sumir com a série
            if chave in (anterior.get("series") or {}): out["series"][chave] = anterior["series"][chave]
    # Selic: decisões do Copom (comunicados) + histórico da meta para o gráfico
    try:
        com = get("https://www.bcb.gov.br/api/servico/sitebcb/copom/comunicados?quantidade=12")["conteudo"]
        decisoes = []
        for c in com:
            t = re.sub(r"\s+", " ", c.get("titulo") or "")
            m = re.search(r"(reduz|eleva|mant[ée]m|aumenta|corta)\D+([\d.,]+)\s*%", t, re.I)
            if not m: continue
            acao = m.group(1).lower().replace("aumenta", "eleva").replace("corta", "reduz").replace("mantem", "mantém")
            decisoes.append({"reuniao": c.get("nro_reuniao"), "data": c.get("dataReferencia"), "titulo": t,
                             "acao": acao, "taxa": float(m.group(2).replace(".", "").replace(",", "."))})
        decisoes.sort(key=lambda d: d["reuniao"])
        for i, d in enumerate(decisoes):
            if i: d["variacao"] = round(d["taxa"] - decisoes[i - 1]["taxa"], 2)
        out["copom"] = decisoes
    except Exception as ex:
        erros.append(f"copom: {ex}")
        if anterior.get("copom"): out["copom"] = anterior["copom"]
    out["erros"] = erros
    for e in erros: print("::warning::" + e)
    if not out["series"]:
        print("::error::Nada coletado: " + "; ".join(erros)); raise SystemExit(1)
    with open("indicadores.json", "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, indent=1)
    print("Indicadores:", ", ".join(f"{k} {v['dados'][-1]['mes'] if 'dados' in v else v.get('data')}" for k, v in out["series"].items()),
          "| Copom:", (out.get("copom") or [{}])[-1].get("titulo"), "| erros:", erros)

if __name__ == "__main__":
    main()
