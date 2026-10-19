#!/usr/bin/env python3
"""Cards dos indicadores econômicos (indicadores.json: Banco Central/SGS e Copom).
Um post a cada divulgação (Copom, IPCA, IPCA-15, IGP-M, INPC, desemprego) e um painel mensal em carrossel.
    python3 scripts/instagram_economia.py copom|ipca|ipca15|igpm|inpc|desemprego|painel [pasta_saida]"""
import os, sys
from datetime import datetime
from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as c
from instagram_contas import tiles

COR = c.COR_SECAO["Mercado"]
MESES_EXT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
             "outubro", "novembro", "dezembro"]
TEXTOS = {
    "ipca": ("Inflação oficial do país · IBGE",
             "Mede a variação dos preços para as famílias com renda de 1 a 40 salários mínimos.",
             "É a referência da meta de inflação e pesa nas decisões do Copom sobre a Selic."),
    "ipca15": ("Prévia da inflação oficial · IBGE",
               "Mesma metodologia do IPCA, com preços coletados de meados do mês anterior a meados deste.",
               "Antecipa a tendência da inflação oficial do mês."),
    "igpm": ("Índice Geral de Preços do Mercado · FGV",
             "Combina preços no atacado, ao consumidor e da construção civil.",
             "É usado para reajustar muitos contratos de aluguel e algumas tarifas."),
    "inpc": ("Inflação das famílias de menor renda · IBGE",
             "Mede a variação dos preços para famílias com renda de 1 a 5 salários mínimos.",
             "É a base do reajuste do salário mínimo e de benefícios do INSS."),
    "desemprego": ("Taxa de desocupação · IBGE (PNAD Contínua)",
                   "Percentual de pessoas que procuraram trabalho e não encontraram, no trimestre.",
                   "Mostra a força do mercado de trabalho e influencia renda e consumo."),
    "copom": ("Taxa básica de juros · Banco Central",
              "A Selic é a taxa básica de juros da economia, definida pelo Copom a cada 45 dias.",
              "Influencia os juros de empréstimos e financiamentos e o rendimento da renda fixa."),
}
ORDEM = ["copom", "ipca", "ipca15", "igpm", "inpc", "desemprego"]   # prioridade quando há mais de um pendente

def pct(v, sinal=False, casas=2): return ("+" if sinal and v > 0 else "") + c.num(v, casas) + "%"
def pct1(v): return pct(v, casas=1)
def pp(v): return ("+" if v > 0 else "−" if v < 0 else "") + c.num(abs(v)) + " p.p."
def mes_ext(m): a, mm = m.split("-"); return MESES_EXT[int(mm) - 1]
def mes_curto(m): a, mm = m.split("-"); return c.MESES[int(mm) - 1]

def ler(): return c.ler("indicadores.json")

def ultimo(chave, ind=None):
    """Identificador da última divulgação (mês ou nº da reunião do Copom)."""
    ind = ind or ler()
    if chave == "copom": return str(ind["copom"][-1]["reuniao"]) if ind.get("copom") else None
    s = ind["series"].get(chave)
    return s["dados"][-1]["mes"] if s and s.get("dados") else None

# ---------------------------------------------------------------- desenho
def grafico(d, x0, y0, w, h, rotulos, valores, destaque=-1, fmt=pct, base_zero=True):
    """Barras com rótulo de valor; aceita negativos (linha de base no zero)."""
    vmax, vmin = max(valores + [0]), min(valores + [0]) if base_zero else min(valores) * 0.9
    faixa = (vmax - vmin) or 1
    zero = y0 + h * vmax / faixa if base_zero else y0 + h
    n = len(valores); passo = w / n; larg = passo * 0.62
    if base_zero: d.line([x0, zero, x0 + w, zero], fill=c.LINHA, width=2)
    for i, (r, v) in enumerate(zip(rotulos, valores)):
        cx = x0 + passo * i + passo / 2
        topo = zero - h * (v - (0 if base_zero else vmin)) / faixa
        cor = c.MARCA if i == (destaque % n) else "#9fb3c8"
        y1, y2 = sorted([topo, zero]); y2 = max(y2, y1 + 3)
        d.rounded_rectangle([cx - larg / 2, y1, cx + larg / 2, y2], radius=6, fill=cor)
        t = fmt(v).replace("%", "").replace(" p.p.", ""); f = c.fonte("semi", 19)
        ty = y1 - 26 if v >= 0 or not base_zero else y2 + 4
        d.text((cx - d.textlength(t, font=f) / 2, ty), t, font=f, fill=c.TINTA)
        f = c.fonte("reg", 19)
        d.text((cx - d.textlength(r, font=f) / 2, y0 + h + (34 if base_zero and vmin < 0 else 12)), r, font=f, fill=c.TINTA2)

def explicacao(d, chave, y=990):
    _, oque, importa = TEXTOS[chave]
    d.text((c.M, y), "O que é", font=c.fonte("bold", 26), fill=c.TINTA)
    u = c.bloco(d, (c.M, y + 38), oque, "reg", 25, c.TINTA, c.W - 2 * c.M, 70, 1.35, 21)
    y2 = y + 44 + u
    d.text((c.M, y2), "Por que importa", font=c.fonte("bold", 26), fill=c.TINTA)
    c.bloco(d, (c.M, y2 + 38), importa, "reg", 25, c.TINTA, c.W - 2 * c.M, 70, 1.35, 21)

def card(chave, ind=None, pagina=None):
    ind = ind or ler()
    sub = TEXTOS[chave][0]
    if chave == "copom":
        dec = ind["copom"][-1]
        img, d = c.tela("Economia", COR, f"{dec['reuniao']}ª reunião do Copom", pagina)
        acao = {"reduz": "reduz", "eleva": "eleva", "mantém": "mantém"}.get(dec["acao"], dec["acao"])
        c.bloco(d, (c.M, 284), f"Copom {acao} a Selic", "serif", 62, c.TINTA, c.W - 2 * c.M, 80, 1.1, 50)
        d.text((c.M, 362), sub, font=c.fonte("semi", 25), fill=c.TINTA2)
        var = dec.get("variacao", 0)
        cdi = ind["series"].get("cdi", {}).get("atual")
        tiles(d, 414, [("Nova taxa", pct(dec["taxa"]), "ao ano", c.TINTA),
                       ("Decisão", pp(var) if var else "sem mudança", "em relação à reunião anterior",
                        c.SOBE if var < 0 else c.DESCE if var > 0 else c.TINTA),
                       ("CDI hoje", pct(cdi) if cdi else "—", "ao ano", c.TINTA)])
        hist = ind["copom"][-10:]
        d.text((c.M, 610), "Selic nas últimas reuniões (% ao ano)", font=c.fonte("bold", 28), fill=c.TINTA)
        grafico(d, c.M, 690, c.W - 2 * c.M, 220, [f"{mes_curto(h['data'][:7])}/{h['data'][2:4]}" for h in hist],
                [h["taxa"] for h in hist], base_zero=False)
    else:
        s = ind["series"][chave]; dados = s["dados"]; u = dados[-1]
        img, d = c.tela("Economia", COR, f"{mes_ext(u['mes'])} de {u['mes'][:4]}", pagina)
        if chave == "desemprego":
            titulo = f"Desemprego no trimestre até {mes_ext(u['mes'])}"
            ano_antes = next((x for x in dados if x["mes"] == f"{int(u['mes'][:4]) - 1}{u['mes'][4:]}"), None)
            itens = [("Taxa", pct1(u["valor"]), "dos que procuram trabalho", c.TINTA),
                     ("Um ano antes", pct1(ano_antes["valor"]) if ano_antes else "—", "mesmo trimestre", c.TINTA),
                     ("Variação", pp(round(u["valor"] - ano_antes["valor"], 1)).replace(",00", ",0").replace("0 p.p.", " p.p.") if ano_antes else "—", "em 12 meses",
                      c.SOBE if ano_antes and u["valor"] < ano_antes["valor"] else c.DESCE if ano_antes and u["valor"] > ano_antes["valor"] else c.TINTA)]
        else:
            titulo = f"{s['nome']} de {mes_ext(u['mes'])}"
            itens = [("No mês", pct(u["valor"]), "variação dos preços", c.TINTA),
                     ("Em 12 meses", pct(u["doze"]) if "doze" in u else "—", "acumulado", c.TINTA),
                     ("No ano", pct(u["ano"]) if "ano" in u else "—", f"desde janeiro de {u['mes'][:4]}", c.TINTA)]
        c.bloco(d, (c.M, 284), titulo, "serif", 62, c.TINTA, c.W - 2 * c.M, 80, 1.1, 46)
        d.text((c.M, 362), sub, font=c.fonte("semi", 25), fill=c.TINTA2)
        tiles(d, 414, itens)
        ult = dados[-12:]
        d.text((c.M, 610), "Últimos 12 meses (%)" if chave != "desemprego" else "Taxa nos últimos 12 trimestres móveis (%)",
               font=c.fonte("bold", 28), fill=c.TINTA)
        grafico(d, c.M, 690, c.W - 2 * c.M, 200, [mes_curto(x["mes"]) for x in ult], [x["valor"] for x in ult],
                base_zero=chave != "desemprego", fmt=pct1 if chave == "desemprego" else pct)
    explicacao(d, chave)
    return img

def painel(ind=None):
    ind = ind or ler()
    hoje = datetime.now()
    img, d = c.tela("Economia", COR, f"{MESES_EXT[hoje.month - 1]} de {hoje.year}", "arraste  →")
    d.text((c.M, 284), "Painel da economia", font=c.fonte("serif", 64), fill=c.TINTA)
    d.text((c.M, 364), "Os principais indicadores, na última divulgação", font=c.fonte("semi", 25), fill=c.TINTA2)
    linhas = []
    if ind.get("copom"):
        dec = ind["copom"][-1]; linhas.append(("Selic", pct(dec["taxa"]) + " a.a.", f"Copom de {mes_ext(dec['data'][:7])}"))
    if ind["series"].get("cdi"): linhas.append(("CDI", pct(ind["series"]["cdi"]["atual"]) + " a.a.", "taxa diária anualizada"))
    for k in ("ipca", "ipca15", "igpm", "igpdi", "inpc"):
        s = ind["series"].get(k)
        if s: u = s["dados"][-1]; linhas.append((s["nome"], pct(u["valor"]) + " no mês",
                                                 f"{mes_ext(u['mes'])} · {pct(u['doze'])} em 12 meses" if "doze" in u else mes_ext(u["mes"])))
    s = ind["series"].get("desemprego")
    if s: u = s["dados"][-1]; linhas.append(("Desemprego", pct1(u["valor"]), f"trimestre até {mes_ext(u['mes'])}"))
    for i, (n, v, det) in enumerate(linhas):
        y = 440 + i * 88
        if i % 2 == 0: d.rectangle([c.M - 8, y - 12, c.W - c.M + 8, y + 76], fill="#eef2f7")
        d.text((c.M, y), n, font=c.fonte("bold", 32), fill=c.TINTA)
        d.text((c.M, y + 42), det, font=c.fonte("reg", 22), fill=c.TINTA2)
        f = c.fonte("bold", 32); d.text((c.W - c.M - d.textlength(v, font=f), y + 14), v, font=f, fill=COR)
    d.text((c.M, 1158), "Fontes: IBGE, FGV e Banco Central (SGS e Copom).", font=c.fonte("reg", 20), fill=c.TINTA2)
    return img

PAINEL = ["copom", "ipca", "ipca15", "igpm", "inpc", "desemprego"]

def gerar(chave, saida):
    ind = ler()
    if chave == "painel":
        imgs = [painel(ind)] + [card(k, ind) for k in PAINEL if k == "copom" and ind.get("copom") or ind["series"].get(k)]
    else:
        imgs = [card(chave, ind)]
    return [c.salvar(im, saida, f"economia-{i}.png") for i, im in enumerate(imgs, start=1)]

# ---------------------------------------------------------------- legenda e texto alternativo
TAGS = {"copom": "#selic #copom #juros #economia", "ipca": "#ipca #inflacao #economia", "ipca15": "#ipca15 #inflacao #economia",
        "igpm": "#igpm #aluguel #inflacao", "inpc": "#inpc #salariominimo #inflacao", "desemprego": "#desemprego #emprego #economia",
        "painel": "#economia #inflacao #selic"}

def legenda_e_alt(chave):
    ind = ler()
    fim = "🔗 Bolsa, dólar, cotações e notícias de economia de hora em hora no site: link na bio."
    if chave == "painel":
        hoje = datetime.now()
        dec = ind["copom"][-1]
        ip = ind["series"]["ipca"]["dados"][-1]; ig = ind["series"]["igpm"]["dados"][-1]
        leg = (f"📊 Painel da economia · {MESES_EXT[hoje.month - 1]} de {hoje.year}\n\n"
               f"Selic em {pct(dec['taxa'])} ao ano, IPCA de {pct(ip['doze'])} em 12 meses e IGP-M de {pct(ig['doze'])} em 12 meses.\n\n"
               "➡️ Arraste para ver cada indicador, o que ele mede e por que importa para o seu bolso.\n\n"
               f"{fim}\n\nFontes: IBGE, FGV e Banco Central.")
        alt = ["Painel da economia com Selic, CDI, IPCA, IPCA-15, IGP-M, IGP-DI, INPC e desemprego na última divulgação."]
        alt += [alt_card(k, ind) for k in PAINEL if k == "copom" and ind.get("copom") or ind["series"].get(k)]
        return f"painel {hoje:%Y-%m}", leg, alt
    if chave == "copom":
        dec = ind["copom"][-1]; var = dec.get("variacao", 0)
        frase = {"reduz": f"reduziu a Selic em {c.num(abs(var))} ponto percentual", "eleva": f"elevou a Selic em {c.num(abs(var))} ponto percentual",
                 "mantém": "manteve a Selic"}.get(dec["acao"], dec["acao"])
        leg = (f"🏦 Copom {dec['acao']} a Selic: {pct(dec['taxa'])} ao ano\n\n"
               f"Na {dec['reuniao']}ª reunião, o Comitê de Política Monetária do Banco Central {frase}, para {pct(dec['taxa'])} ao ano.\n\n"
               f"💡 {TEXTOS['copom'][2]}\n\n{fim}\n\nFonte: Banco Central.")
        return f"copom {dec['reuniao']}", leg, [alt_card("copom", ind)]
    s = ind["series"][chave]; u = s["dados"][-1]
    if chave == "desemprego":
        leg = (f"👷 Desemprego de {pct1(u['valor'])} no trimestre até {mes_ext(u['mes'])}\n\n"
               f"É o que mostra a PNAD Contínua, do IBGE.\n\n💡 {TEXTOS[chave][2]}\n\n{fim}\n\nFonte: IBGE, via Banco Central.")
    else:
        doze = f" e acumula {pct(u['doze'])} em 12 meses" if "doze" in u else ""
        leg = (f"📈 {s['nome']} de {mes_ext(u['mes'])}: {pct(u['valor'])}\n\n"
               f"O {s['nome']} ({TEXTOS[chave][0].split(' · ')[0].lower()}) variou {pct(u['valor'])} em {mes_ext(u['mes'])}{doze}.\n\n"
               f"💡 {TEXTOS[chave][2]}\n\n{fim}\n\nFonte: {s['fonte']}, via Banco Central.")
    return f"{chave} {u['mes']}", leg, [alt_card(chave, ind)]

def alt_card(chave, ind):
    if chave == "copom":
        dec = ind["copom"][-1]
        return f"Card: Copom {dec['acao']} a Selic para {pct(dec['taxa'])} ao ano, com gráfico da taxa nas últimas reuniões."
    s = ind["series"][chave]; u = s["dados"][-1]
    if chave == "desemprego":
        return f"Card: desemprego de {pct1(u['valor'])} no trimestre até {mes_ext(u['mes'])}, com gráfico dos últimos 12 trimestres móveis."
    return (f"Card: {s['nome']} de {mes_ext(u['mes'])}, {pct(u['valor'])} no mês"
            + (f" e {pct(u['doze'])} em 12 meses" if "doze" in u else "") + ", com gráfico dos últimos 12 meses.")

if __name__ == "__main__":
    k = sys.argv[1] if len(sys.argv) > 1 else "painel"
    for a in gerar(k, sys.argv[2] if len(sys.argv) > 2 else os.path.join(c.RAIZ, "instagram")): print(a)
