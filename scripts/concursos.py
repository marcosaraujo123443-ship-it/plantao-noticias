#!/usr/bin/env python3
"""Concursos com inscrições abertas (lista pública do PCI Concursos) -> concursos.json.
Guarda só o essencial de cada um (órgão, vagas, salário, cargos, nível, prazo) e o link para a página do PCI."""
import html, json, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
URL = "https://www.pciconcursos.com.br/concursos/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
UFS = {"ACRE": "AC", "ALAGOAS": "AL", "AMAPÁ": "AP", "AMAZONAS": "AM", "BAHIA": "BA", "CEARÁ": "CE", "DISTRITO FEDERAL": "DF",
       "ESPÍRITO SANTO": "ES", "GOIÁS": "GO", "MARANHÃO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
       "MINAS GERAIS": "MG", "PARÁ": "PA", "PARAÍBA": "PB", "PARANÁ": "PR", "PERNAMBUCO": "PE", "PIAUÍ": "PI",
       "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS", "RONDÔNIA": "RO", "RORAIMA": "RR",
       "SANTA CATARINA": "SC", "SÃO PAULO": "SP", "SERGIPE": "SE", "TOCANTINS": "TO", "NACIONAL": "BR"}

def txt(t): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()

def valor(t):
    m = re.search(r"R\$\s*([\d.]+,\d{2})", t or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None

def ler(h, hoje):
    out = []
    # cada estado começa com <div id="UF" class="ua"><div class="uf">NOME</div>
    partes = re.split(r'<div id="[^"]*" class="ua"><div class="uf">([^<]+)</div>', h)
    for k in range(1, len(partes), 2):
        uf = UFS.get(txt(partes[k]).upper())
        if not uf: continue
        for b in re.split(r'<div class="(?:da|na|ea)" onclick', partes[k + 1])[1:]:
            a = re.search(r'<div class="ca"><a href="([^"]+)" title="([^"]*)"[^>]*>(.*?)</a>', b, re.S)
            cd = re.search(r'<div class="cd">(.*?)</div>', b, re.S)
            ce = re.search(r'<div class="ce">(.*?)</div>', b, re.S)
            cc = re.search(r'<div class="cc">(.*?)</div>', b, re.S)
            if not a or not cd: continue
            linhas = [txt(x) for x in re.split(r"<br\s*/?>", cd.group(1))]
            linhas = [x for x in linhas if x]
            datas = re.findall(r"\d{2}/\d{2}/\d{4}", txt(ce.group(1)) if ce else "")
            prazo = None
            if datas:
                d = max(datetime.strptime(x, "%d/%m/%Y").date() for x in datas)
                if d < hoje: continue            # inscrições já encerradas
                prazo = str(d)
            vagas = linhas[0] if linhas else ""
            nv = re.match(r"(\d[\d.]*)\s+vagas?", vagas)
            out.append({"orgao": txt(a.group(3)), "titulo": txt(a.group(2)), "link": a.group(1), "uf": uf,
                        "local": txt(cc.group(1)) if cc else "", "resumo": vagas,
                        "vagas": int(nv.group(1).replace(".", "")) if nv else None, "salario": valor(vagas),
                        "cargos": linhas[1] if len(linhas) > 1 else "", "nivel": linhas[2] if len(linhas) > 2 else "",
                        "prazo": prazo})
    return out

def main():
    hoje = datetime.now(BRT).date()
    for t in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=60) as r:
                h = r.read().decode("utf-8", "replace")
            break
        except Exception as ex:
            if t == 2: print(f"::warning::PCI indisponível: {ex!r}"); return
            time.sleep(10)
    lista = ler(h, hoje)
    if len(lista) < 30:   # página mudou ou veio incompleta: mantém a versão anterior
        print(f"::warning::só {len(lista)} concursos lidos; mantendo o arquivo anterior"); return
    vistos, unicos = set(), []
    for c in lista:
        if c["link"] in vistos: continue
        vistos.add(c["link"]); unicos.append(c)
    unicos.sort(key=lambda c: (c["prazo"] or "9999", c["orgao"]))
    json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fonte": "PCI Concursos",
               "url": URL, "total": len(unicos), "concursos": unicos},
              open("concursos.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(unicos)} concursos com inscrições abertas; {sum(1 for c in unicos if c['uf'] == 'BR')} nacionais")

if __name__ == "__main__":
    if len(sys.argv) > 1:   # teste local: python3 concursos.py pagina.html
        r = ler(open(sys.argv[1], encoding="utf-8", errors="replace").read(), datetime.now(BRT).date())
        print(len(r)); [print(x) for x in r[:3]]
        from collections import Counter; print(Counter(x["uf"] for x in r).most_common(30))
    else: main()
