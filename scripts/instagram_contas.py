#!/usr/bin/env python3
"""Carrosséis das contas públicas dos estados (dados do site: estados.json, Tesouro Nacional/SICONFI-RREO).
Um carrossel por região (capa + um slide por estado) e um consolidado com as 5 regiões.
    python3 scripts/instagram_contas.py norte|nordeste|centro_oeste|sudeste|sul|brasil [pasta_saida]"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as c

REGIOES = {  # ordem de publicação da série
    "norte": ("Norte", ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]),
    "nordeste": ("Nordeste", ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]),
    "centro_oeste": ("Centro-Oeste", ["DF", "GO", "MT", "MS"]),
    "sudeste": ("Sudeste", ["ES", "MG", "RJ", "SP"]),
    "sul": ("Sul", ["PR", "RS", "SC"]),
}
ORDEM = ["contas_" + r for r in REGIOES] + ["contas_brasil"]
COR = "#334155"                       # cor da editoria "Contas públicas"
FATIAS = [("pessoal", "Pessoal", "#1d4ed8"), ("custeio", "Custeio e repasses", "#0f766e"),
          ("invest", "Investimentos", "#15803d"), ("divida", "Dívida", "#c0262d"), ("outros", "Outros", "#94a3b8")]
AREAS = ["Educação", "Saúde", "Segurança Pública"]
MESES = c.MESES

# ---------------------------------------------------------------- números
def periodo_modal(est):
    """(ano, bimestre) que a maioria dos 27 estados já entregou e quantos estão nele."""
    pers = [(e["atual"]["ano"], e["atual"]["periodo"]) for s, e in est.items()
            if s not in ("BR", "UF") and e.get("atual")]
    alvo = max(set(pers), key=pers.count)
    return alvo, pers.count(alvo)

def _linha(lista, nome):
    return next((r for r in lista if r["n"] == nome), {})

def metricas(b):
    """Indicadores de um balanço (de um estado ou soma)."""
    rec = _linha(b["receitas"], "Total arrecadado")
    d = {r["n"]: r for r in b["despesas"]}
    liq = lambda n: (d.get(n) or {}).get("liquidado") or 0
    total = liq("Total")
    m = {"arrecadado": rec.get("realizado") or 0, "previsto": rec.get("previsto") or 0,
         "gasto": total, "dotacao": (d.get("Total") or {}).get("dotacao") or 0,
         "pessoal": liq("Pessoal e encargos"), "custeio": liq("Custeio, repasses e outras"),
         "invest": liq("Investimentos"), "divida": liq("Juros da dívida") + liq("Amortização da dívida"),
         "pop": b.get("populacao") or 0}
    m["outros"] = max(0, total - m["pessoal"] - m["custeio"] - m["invest"] - m["divida"])
    m["resultado"] = m["arrecadado"] - m["gasto"]
    f = {r["n"]: r.get("liquidado") or 0 for r in b.get("funcoes", [])}
    m["areas"] = {a: f.get(a, 0) for a in AREAS}
    return m

def somar(ms):
    out = {}
    for k in ("arrecadado", "previsto", "gasto", "dotacao", "pessoal", "custeio", "invest", "divida", "outros", "pop", "resultado"):
        out[k] = sum(m[k] for m in ms)
    out["areas"] = {a: sum(m["areas"][a] for m in ms) for a in AREAS}
    return out

def dados(est, siglas, alvo=None):
    """Métricas de cada estado e soma dos que estão no período alvo."""
    por = {}
    for s in siglas:
        e = est.get(s, {})
        if e.get("atual"): por[s] = (e["nome"], e["atual"], metricas(e["atual"]))
    no_alvo = [m for (_, b, m) in por.values() if alvo is None or (b["ano"], b["periodo"]) == alvo]
    return por, somar(no_alvo), len(no_alvo)

# ---------------------------------------------------------------- formatação
def brl(v, sinal=False):
    s = "+" if sinal and v > 0 else "−" if v < 0 else ""
    a = abs(v)
    if a >= 1e9: t = c.num(a / 1e9, 1) + " bi"
    elif a >= 1e6: t = c.num(a / 1e6, 0 if a >= 1e8 else 1) + " mi"
    else: t = c.num(a, 0)
    return f"{s}R$ {t}"

def por_hab(v, pop): return "R$ " + c.num(v / pop, 0) if pop else "—"
def pct(a, b): return c.num(100 * a / b, 0) + "%" if b else "—"
def periodo_txt(ano, p): return f"jan a {MESES[2 * p - 1]} de {ano}"
def periodo_curto(ano, p): return f"jan–{MESES[2 * p - 1]}/{ano}"

# ---------------------------------------------------------------- desenho
def tiles(d, y, itens, h=150):
    w = (c.W - 2 * c.M - 2 * 18) / 3
    for i, (rot, val, sub, cor) in enumerate(itens):
        x = c.M + i * (w + 18)
        d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=c.CARTAO, outline=c.LINHA, width=2)
        d.text((x + 22, y + 18), rot, font=c.fonte("semi", 23), fill=c.TINTA2)
        f = c.fonte("bold", 38)
        while d.textlength(val, font=f) > w - 40: f = c.fonte("bold", f.size - 2)
        d.text((x + 22, y + 56), val, font=f, fill=cor)
        fs = c.fonte("reg", 21)
        while d.textlength(sub, font=fs) > w - 36: fs = c.fonte("reg", fs.size - 1)
        d.text((x + 22, y + 108), sub, font=fs, fill=c.TINTA2)

def barra(d, x, y, w, h, m):
    total = sum(m[k] for k, _, _ in FATIAS) or 1
    pos = x
    for k, _, cor in FATIAS:
        larg = w * m[k] / total
        if larg >= 1: d.rectangle([pos, y, pos + larg, y + h], fill=cor)
        pos += larg

def legenda(d, x, y, m, colunas=2, largura=None):
    largura = largura or (c.W - 2 * c.M)
    total = sum(m[k] for k, _, _ in FATIAS) or 1
    for i, (k, rot, cor) in enumerate(FATIAS):
        cx = x + (i % colunas) * largura / colunas
        cy = y + (i // colunas) * 42
        d.rectangle([cx, cy + 7, cx + 20, cy + 27], fill=cor)
        d.text((cx + 32, cy), f"{rot}  {c.num(100 * m[k] / total, 0)}%", font=c.fonte("semi", 25), fill=c.TINTA)

def cor_res(v): return c.SOBE if v >= 0 else c.DESCE

def slide_estado(sigla, nome, b, m, regiao):
    img, d = c.tela(f"Contas públicas · {regiao}", COR, f"{b['periodo']}º bimestre de {b['ano']}")
    d.text((c.M, 284), nome, font=c.fonte("serif", 60), fill=c.TINTA)
    d.text((c.M, 360), f"Governo do estado · {periodo_txt(b['ano'], b['periodo'])}", font=c.fonte("semi", 25), fill=c.TINTA2)
    tiles(d, 414, [("Arrecadou", brl(m["arrecadado"]), f"{pct(m['arrecadado'], m['previsto'])} do previsto no ano", c.TINTA),
                   ("Gastou", brl(m["gasto"]), f"{pct(m['gasto'], m['dotacao'])} do orçamento do ano", c.TINTA),
                   ("Saldo no período", brl(m["resultado"], True), "arrecadou mais que gastou" if m["resultado"] >= 0
                    else "gastou mais que arrecadou", cor_res(m["resultado"]))])
    y = 606
    d.text((c.M, y), "Para onde foi o gasto", font=c.fonte("bold", 30), fill=c.TINTA)
    barra(d, c.M, y + 52, c.W - 2 * c.M, 40, m)
    legenda(d, c.M, y + 112, m)
    y = 900
    d.text((c.M, y), "Gasto por área", font=c.fonte("bold", 30), fill=c.TINTA)
    d.text((c.W - c.M - d.textlength("por habitante", font=c.fonte("semi", 22)), y + 8), "por habitante",
           font=c.fonte("semi", 22), fill=c.TINTA2)
    for i, a in enumerate(AREAS):
        yy = y + 52 + i * 52
        d.line([c.M, yy - 6, c.W - c.M, yy - 6], fill=c.LINHA, width=2)
        d.text((c.M, yy + 2), "Segurança" if a == "Segurança Pública" else a, font=c.fonte("semi", 28), fill=c.TINTA)
        t = brl(m["areas"][a]); f = c.fonte("bold", 28)
        d.text((680 - d.textlength(t, font=f), yy + 2), t, font=f, fill=c.TINTA)
        t = por_hab(m["areas"][a], m["pop"]); f = c.fonte("reg", 28)
        d.text((c.W - c.M - d.textlength(t, font=f), yy + 2), t, font=f, fill=c.TINTA2)
    d.text((c.M, 1118), f"Arrecadação por habitante: {por_hab(m['arrecadado'], m['pop'])} · população: "
           f"{c.num(m['pop'] / 1e6, 1)} mi" if m["pop"] else "", font=c.fonte("semi", 23), fill=c.TINTA)
    d.text((c.M, 1158), "Fonte: Tesouro Nacional (SICONFI/RREO). Valores liquidados; receita inclui empréstimos.",
           font=c.fonte("reg", 20), fill=c.TINTA2)
    return img

def slide_capa_regiao(regiao, por, soma, n, alvo, total_estados):
    ano, p = alvo
    img, d = c.tela("Contas públicas", COR, f"{p}º bimestre de {ano}", "arraste  →")
    d.text((c.M, 284), f"Região {regiao}", font=c.fonte("serif", 64), fill=c.TINTA)
    d.text((c.M, 364), f"Contas dos {total_estados} governos estaduais · {periodo_txt(ano, p)}",
           font=c.fonte("semi", 25), fill=c.TINTA2)
    tiles(d, 418, [("Arrecadaram", brl(soma["arrecadado"]), f"{pct(soma['arrecadado'], soma['previsto'])} do previsto", c.TINTA),
                   ("Gastaram", brl(soma["gasto"]), f"{pct(soma['gasto'], soma['dotacao'])} do orçamento", c.TINTA),
                   ("Saldo", brl(soma["resultado"], True), "soma dos estados", cor_res(soma["resultado"]))])
    y = 610
    cols = [("Arrecadou", 600), ("Saldo", 800), ("Por hab.", c.W - c.M)]
    for rot, x in cols:
        f = c.fonte("bold", 22); d.text((x - d.textlength(rot, font=f), y), rot, font=f, fill=c.TINTA2)
    linhas = sorted(por.items(), key=lambda kv: kv[1][2]["arrecadado"], reverse=True)
    alt = min(58, int(540 / max(1, len(linhas))))
    for i, (s, (nome, b, m)) in enumerate(linhas):
        yy = y + 40 + i * alt
        if i % 2 == 0: d.rectangle([c.M - 8, yy - 6, c.W - c.M + 8, yy + alt - 10], fill="#eef2f7")
        nm = nome + ("*" if (b["ano"], b["periodo"]) != alvo else "")
        d.text((c.M, yy), nm, font=c.fonte("semi", 27), fill=c.TINTA)
        for val, x, cor in ((brl(m["arrecadado"]), 600, c.TINTA), (brl(m["resultado"], True), 800, cor_res(m["resultado"])),
                            (por_hab(m["arrecadado"], m["pop"]), c.W - c.M, c.TINTA2)):
            f = c.fonte("semi", 26); d.text((x - d.textlength(val, font=f), yy), val, font=f, fill=cor)
    nota = "Por hab. = arrecadação por habitante. Fonte: Tesouro Nacional (SICONFI/RREO)."
    if n < len(por): nota = "* estado com dados de outro bimestre (fora da soma). " + nota
    d.text((c.M, 1158), nota, font=c.fonte("reg", 20), fill=c.TINTA2)
    return img

def slide_chamada(texto, itens):
    img, d = c.tela("No site", c.MARCA, "plantaoinforma.com.br")
    c.bloco(d, (c.M, 320), texto, "serif", 64, c.TINTA, c.W - 2 * c.M, 260, 1.15, 44)
    y = 640
    for t in itens:
        d.ellipse([c.M, y + 12, c.M + 18, y + 30], fill=c.MARCA)
        d.text((c.M + 40, y), t, font=c.fonte("reg", 34), fill=c.TINTA); y += 66
    d.rounded_rectangle([c.M, c.H - 290, c.W - c.M, c.H - 160], radius=65, fill=c.MARCA)
    f = c.fonte("bold", 40); t = "Acesse pelo link na bio"
    d.text(((c.W - d.textlength(t, font=f)) / 2, c.H - 250), t, font=f, fill="#ffffff")
    return img

ITENS_SITE = ["Receitas e despesas de cada estado", "Gasto por área: saúde, educação, segurança",
              "Comparação com o ano anterior", "Contas da União"]

def carrossel_regiao(chave, saida, est, alvo):
    regiao, siglas = REGIOES[chave]
    por, soma, n = dados(est, siglas, alvo)
    slides = [slide_capa_regiao(regiao, por, soma, n, alvo, len(siglas))]
    for s in sorted(por, key=lambda s: por[s][0]):
        nome, b, m = por[s]
        slides.append(slide_estado(s, nome, b, m, regiao))
    if len(slides) < 10:   # o Instagram aceita até 10 imagens por carrossel
        slides.append(slide_chamada("Os números completos de cada estado estão no site", ITENS_SITE))
    return slides

def carrossel_brasil(saida, est, alvo):
    ano, p = alvo
    regs = {k: dados(est, s, alvo) for k, (_, s) in REGIOES.items()}
    tot = somar([r[1] for r in regs.values()])
    n_tot = sum(r[2] for r in regs.values())
    slides = []
    # 1. capa
    img, d = c.tela("Contas públicas", COR, f"{p}º bimestre de {ano}", "arraste  →")
    d.text((c.M, 284), "Contas dos estados", font=c.fonte("serif", 64), fill=c.TINTA)
    d.text((c.M, 364), f"Por região · {periodo_txt(ano, p)} · {n_tot} estados", font=c.fonte("semi", 25), fill=c.TINTA2)
    tiles(d, 418, [("Arrecadaram", brl(tot["arrecadado"]), f"{pct(tot['arrecadado'], tot['previsto'])} do previsto", c.TINTA),
                   ("Gastaram", brl(tot["gasto"]), f"{pct(tot['gasto'], tot['dotacao'])} do orçamento", c.TINTA),
                   ("Saldo", brl(tot["resultado"], True), "soma dos estados", cor_res(tot["resultado"]))])
    d.text((c.M, 620), "Fatia de cada região na arrecadação", font=c.fonte("bold", 30), fill=c.TINTA)
    maior = max(r[1]["arrecadado"] for r in regs.values()) or 1
    for i, (k, (nome, _)) in enumerate(REGIOES.items()):
        yy = 690 + i * 88; v = regs[k][1]["arrecadado"]
        d.text((c.M, yy), nome, font=c.fonte("semi", 27), fill=c.TINTA)
        w = (c.W - 2 * c.M - 520) * v / maior
        d.rounded_rectangle([c.M + 220, yy + 4, c.M + 220 + max(w, 6), yy + 34], radius=8, fill=COR)
        t = f"{pct(v, tot['arrecadado'])} · {brl(v)}"; f = c.fonte("semi", 24)
        d.text((c.W - c.M - d.textlength(t, font=f), yy + 4), t, font=f, fill=c.TINTA2)
    d.text((c.M, 1158), "Fonte: Tesouro Nacional (SICONFI/RREO). Valores liquidados; receita inclui empréstimos.",
           font=c.fonte("reg", 20), fill=c.TINTA2)
    slides.append(img)
    # 2. comparativo
    img, d = c.tela("Contas públicas", COR, f"{p}º bimestre de {ano}")
    d.text((c.M, 284), "Comparativo das regiões", font=c.fonte("serif", 56), fill=c.TINTA)
    d.text((c.M, 356), periodo_txt(ano, p), font=c.fonte("semi", 25), fill=c.TINTA2)
    y = 430
    cols = [("Arrecadou", 610), ("Gastou", 810), ("Saldo", c.W - c.M)]
    for rot, x in cols:
        f = c.fonte("bold", 22); d.text((x - d.textlength(rot, font=f), y), rot, font=f, fill=c.TINTA2)
    for i, (k, (nome, siglas)) in enumerate(REGIOES.items()):
        _, s, n = regs[k]; yy = y + 50 + i * 120
        d.rounded_rectangle([c.M - 8, yy - 10, c.W - c.M + 8, yy + 98], radius=16, fill=c.CARTAO, outline=c.LINHA, width=2)
        d.text((c.M + 12, yy + 4), nome, font=c.fonte("bold", 30), fill=c.TINTA)
        d.text((c.M + 12, yy + 50), f"{n} estados · {por_hab(s['arrecadado'], s['pop'])}/hab.", font=c.fonte("reg", 21), fill=c.TINTA2)
        for val, x, cor in ((brl(s["arrecadado"]), 610, c.TINTA), (brl(s["gasto"]), 810, c.TINTA),
                            (brl(s["resultado"], True), c.W - c.M - 12, cor_res(s["resultado"]))):
            f = c.fonte("semi", 27); d.text((x - d.textlength(val, font=f), yy + 24), val, font=f, fill=cor)
    d.text((c.M, 1158), "Por hab. = arrecadação por habitante. Fonte: Tesouro Nacional (SICONFI/RREO).",
           font=c.fonte("reg", 20), fill=c.TINTA2)
    slides.append(img)
    # 3. para onde vai o gasto
    img, d = c.tela("Contas públicas", COR, f"{p}º bimestre de {ano}")
    d.text((c.M, 284), "Para onde vai o gasto", font=c.fonte("serif", 56), fill=c.TINTA)
    d.text((c.M, 356), "Divisão das despesas liquidadas, por região", font=c.fonte("semi", 25), fill=c.TINTA2)
    for i, (k, (nome, _)) in enumerate(REGIOES.items()):
        s = regs[k][1]; yy = 440 + i * 104
        d.text((c.M, yy), nome, font=c.fonte("semi", 27), fill=c.TINTA)
        t = f"pessoal {pct(s['pessoal'], s['gasto'])} · investimento {pct(s['invest'], s['gasto'])}"
        f = c.fonte("reg", 22); d.text((c.W - c.M - d.textlength(t, font=f), yy + 4), t, font=f, fill=c.TINTA2)
        barra(d, c.M, yy + 44, c.W - 2 * c.M, 34, s)
    legenda(d, c.M, 980, tot)
    d.text((c.M, 1158), "Fonte: Tesouro Nacional (SICONFI/RREO).", font=c.fonte("reg", 20), fill=c.TINTA2)
    slides.append(img)
    # 4. áreas por habitante
    img, d = c.tela("Contas públicas", COR, f"{p}º bimestre de {ano}")
    d.text((c.M, 284), "Gasto por habitante", font=c.fonte("serif", 56), fill=c.TINTA)
    d.text((c.M, 356), f"Educação, saúde e segurança · {periodo_txt(ano, p)}", font=c.fonte("semi", 25), fill=c.TINTA2)
    y = 440
    xs = [560, 760, c.W - c.M]
    for rot, x in zip(["Educação", "Saúde", "Segurança"], xs):
        f = c.fonte("bold", 23); d.text((x - d.textlength(rot, font=f), y), rot, font=f, fill=c.TINTA2)
    for i, (k, (nome, _)) in enumerate(list(REGIOES.items()) + [("_t", ("Média dos estados", None))]):
        s = regs[k][1] if k != "_t" else tot; yy = y + 56 + i * 96
        if k == "_t": d.line([c.M, yy - 20, c.W - c.M, yy - 20], fill=c.TINTA2, width=2)
        elif i % 2 == 0: d.rectangle([c.M - 8, yy - 14, c.W - c.M + 8, yy + 62], fill="#eef2f7")
        d.text((c.M, yy + 6), nome, font=c.fonte("bold" if k == "_t" else "semi", 28), fill=c.TINTA)
        for a, x in zip(AREAS, xs):
            t = por_hab(s["areas"][a], s["pop"]); f = c.fonte("semi", 28)
            d.text((x - d.textlength(t, font=f), yy + 6), t, font=f, fill=c.TINTA)
    d.text((c.M, 1158), "Gasto liquidado no período dividido pela população. Fonte: Tesouro Nacional (SICONFI/RREO).",
           font=c.fonte("reg", 20), fill=c.TINTA2)
    slides.append(img)
    slides.append(slide_chamada("Veja as contas de cada estado no site", ITENS_SITE))
    return slides

def gerar(chave, saida):
    est = c.ler("estados.json")["estados"]
    alvo, _ = periodo_modal(est)
    sub = chave.replace("contas_", "")
    slides = carrossel_brasil(saida, est, alvo) if sub == "brasil" else carrossel_regiao(sub, saida, est, alvo)
    return [c.salvar(img, saida, f"contas-{i}.png") for i, img in enumerate(slides, start=1)]

# ---------------------------------------------------------------- legenda e texto alternativo
def legenda_e_alt(chave):
    est = c.ler("estados.json")["estados"]
    alvo, _ = periodo_modal(est)
    ano, p = alvo
    sub = chave.replace("contas_", "")
    fim = ("🔗 Receitas, despesas e gasto por área de cada estado no site: link na bio.\n\n"
           "Fonte: Tesouro Nacional (SICONFI/RREO). Valores liquidados; a receita inclui operações de crédito.")
    if sub == "brasil":
        regs = {k: dados(est, s, alvo) for k, (_, s) in REGIOES.items()}
        tot = somar([r[1] for r in regs.values()])
        leg = (f"🏛️ Contas dos estados por região · {periodo_curto(ano, p)}\n\n"
               f"Juntos, os governos estaduais arrecadaram {brl(tot['arrecadado'])} e gastaram {brl(tot['gasto'])} "
               f"até o {p}º bimestre.\n"
               + "\n".join(f"• {REGIOES[k][0]}: arrecadou {brl(r[1]['arrecadado'])}" for k, r in regs.items())
               + "\n\n➡️ Arraste para ver o comparativo, para onde vai o gasto e o gasto por habitante.\n\n" + fim)
        alt = [f"Capa: contas dos estados por região, {periodo_txt(ano, p)}. Arrecadaram {brl(tot['arrecadado'])} e gastaram {brl(tot['gasto'])}.",
               "Tabela comparando arrecadação, gasto e saldo das cinco regiões.",
               "Barras com a divisão do gasto de cada região entre pessoal, custeio, investimentos, dívida e outros.",
               "Tabela de gasto por habitante em educação, saúde e segurança por região.",
               "Chamada para ver as contas de cada estado no site plantaoinforma.com.br."]
        return f"contas {ano}-{p}", leg, alt
    regiao, siglas = REGIOES[sub]
    por, soma, n = dados(est, siglas, alvo)
    nomes = sorted(v[0] for v in por.values())
    leg = (f"🏛️ Contas públicas · Região {regiao} · {periodo_curto(ano, p)}\n\n"
           f"Os governos estaduais da região arrecadaram {brl(soma['arrecadado'])} e gastaram {brl(soma['gasto'])} "
           f"até o {p}º bimestre de {ano}.\n\n"
           f"➡️ Arraste para ver: {', '.join(nomes)}.\n\n" + fim)
    alt = [f"Capa: contas dos governos estaduais da região {regiao}, {periodo_txt(ano, p)}, com arrecadação, saldo e "
           f"arrecadação por habitante de cada estado."]
    for s in sorted(por, key=lambda s: por[s][0]):
        nome, b, m = por[s]
        alt.append(f"{nome}: arrecadou {brl(m['arrecadado'])} e gastou {brl(m['gasto'])} até o {b['periodo']}º bimestre "
                   f"de {b['ano']}; saldo {brl(m['resultado'], True)}. Pessoal {pct(m['pessoal'], m['gasto'])} do gasto. "
                   f"Educação {brl(m['areas']['Educação'])}, saúde {brl(m['areas']['Saúde'])}, "
                   f"segurança {brl(m['areas']['Segurança Pública'])}.")
    alt.append("Chamada para ver os números completos de cada estado no site plantaoinforma.com.br.")
    return f"contas {ano}-{p}", leg, alt

if __name__ == "__main__":
    k = "contas_" + (sys.argv[1] if len(sys.argv) > 1 else "norte")
    for a in gerar(k, sys.argv[2] if len(sys.argv) > 2 else os.path.join(c.RAIZ, "instagram")): print(a)
