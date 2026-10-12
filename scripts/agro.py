#!/usr/bin/env python3
"""Cotações do agro (páginas públicas de cotações do Notícias Agrícolas) e grava agro.json (roda no GitHub Actions)."""
import json, re, sys, time, html as H, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
BASE = "https://www.noticiasagricolas.com.br/cotacoes/"
PAGINAS = ["soja", "milho", "boi-gordo", "cafe", "trigo", "algodao", "sucroenergetico", "arroz", "feijao",
           "leite", "frango", "suinos", "laranja"]

def texto(url):
    for tent in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if tent == 2: raise
            time.sleep(3)

def limpo(s):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def tabelas(pg):
    """Cada tabela da página com o título mais próximo antes dela, cabeçalho e linhas."""
    out = []
    for m in re.finditer(r"<table\b.*?</table>", pg, re.S | re.I):
        antes = pg[max(0, m.start() - 4000):m.start()]
        tits = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", antes, re.S | re.I)
        fonte = re.findall(r"Fonte:\s*([^<]{2,60})", antes)
        tab = m.group(0)
        cab = [limpo(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", tab, re.S | re.I)]
        linhas = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tab, re.S | re.I):
            cel = [limpo(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
            if cel and any(cel): linhas.append(cel)
        if linhas:
            out.append({"titulo": limpo(tits[-1]) if tits else "", "fonte": fonte[-1].strip() if fonte else "",
                        "cab": cab, "linhas": linhas[:12]})
    return out

def main():
    paginas, erros = {}, []
    for p in PAGINAS:
        try:
            paginas[p] = tabelas(texto(BASE + p))
        except Exception as e:
            erros.append(f"{p}: {e}")
        time.sleep(1)
    if not any(paginas.values()): raise SystemExit("Nada coletado: " + "; ".join(erros))
    with open("agro.json", "w", encoding="utf-8") as f:
        json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "paginas": paginas, "erros": erros},
                  f, ensure_ascii=False, indent=0)
    print({p: len(t) for p, t in paginas.items()}, erros)

if __name__ == "__main__":
    main()
