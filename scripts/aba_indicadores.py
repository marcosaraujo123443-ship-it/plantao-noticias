"""Aba "Indicadores" do site: cartões com o último dado de cada indicador (indicadores.json e indicadores2.json), agrupados por tema."""
import html, json
from pathlib import Path

e = html.escape
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()
MESES_EXT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
def br(v, c=2): return f"{v:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(v, c=2, s=False): return ("+" if s and v > 0 else "−" if v < 0 else "") + br(abs(v), c) + "%"
def rot(m): return f"{MESES[int(m[5:7]) - 1]}/{m[2:4]}"
def ext(m): return f"{MESES_EXT[int(m[5:7]) - 1]} de {m[:4]}"

TXT = {"ipca": ("Inflação oficial", "IPCA · IBGE", "Brasil · Inflação", "É a referência da meta de inflação e guia o Copom."),
       "ipca15": ("Prévia da inflação", "IPCA-15 · IBGE", "Brasil · Inflação", "Antecipa a tendência da inflação oficial do mês."),
       "igpm": ("Inflação do aluguel", "IGP-M · FGV", "Brasil · Inflação", "Reajusta muitos contratos de aluguel e tarifas."),
       "inpc": ("Inflação da baixa renda", "INPC · IBGE", "Brasil · Inflação", "Base do reajuste do salário mínimo e do INSS.")}

def originais(ind):
    out = {}
    cp = ind.get("copom") or []
    if cp:
        u = cp[-1]; var = u.get("variacao", 0); cdi = (ind["series"].get("cdi") or {}).get("atual")
        out["selic"] = {"tag": "Brasil · Juros", "titulo": "Taxa Selic", "sub": f"{u['reuniao']}ª reunião do Copom", "ref_txt": f"{u['data'][8:]}/{u['data'][5:7]}/{u['data'][:4]}",
                        "valor": pct(u["taxa"]), "cor": "neutro", "selo": (("▼ CORTE DE " if var < 0 else "▲ ALTA DE ") + br(abs(var)) + " P.P." if var else "= MANTIDA", "neutro"),
                        "frase": "ao ano, a taxa básica de juros da economia.",
                        "apoio": [("CDI", pct(cdi) if cdi else "—", "ao ano"), ("Decisão", u["acao"], "na última reunião"), ("Reunião anterior", pct(cp[-2]["taxa"]) if len(cp) > 1 else "—", "")],
                        "graf": [(rot(x["data"]), x["taxa"]) for x in cp[-10:]], "base_zero": False, "fonte": "Banco Central", "id": "selic"}
    for k, (tit, sub, tag, porque) in TXT.items():
        s = ind["series"].get(k)
        if not s or not s.get("dados"): continue
        d = s["dados"]; u = d[-1]; a = d[-2]
        out[k] = {"tag": tag, "titulo": tit, "sub": sub, "ref_txt": ext(u["mes"]), "valor": pct(u["valor"], 2, True), "cor": "ruim" if u["valor"] > a["valor"] else "bom",
                  "selo": ("▲ ACELERA" if u["valor"] > a["valor"] else "▼ DESACELERA", "ruim" if u["valor"] > a["valor"] else "bom") if u["valor"] != a["valor"] else None,
                  "frase": f"no mês. {porque}",
                  "apoio": [("Em 12 meses", pct(u["doze"]) if "doze" in u else "—", "acumulado"), ("No ano", pct(u["ano"]) if "ano" in u else "—", "acumulado"),
                            ("Mês anterior", pct(a["valor"], 2, True), rot(a["mes"]))],
                  "graf": [(rot(x["mes"]), x["valor"]) for x in d[-12:]], "fonte": s["fonte"], "id": k}
    s = ind["series"].get("desemprego")
    if s and s.get("dados"):
        d = s["dados"]; u = d[-1]; aa = next((x for x in d if x["mes"] == f"{int(u['mes'][:4]) - 1}{u['mes'][4:]}"), None)
        out["desemprego"] = {"tag": "Brasil · Trabalho", "titulo": "Desemprego", "sub": "PNAD Contínua · IBGE", "ref_txt": f"trimestre até {rot(u['mes'])}",
                             "valor": pct(u["valor"], 1), "cor": "neutro", "selo": None, "frase": "das pessoas que procuram trabalho não encontram.",
                             "apoio": [("Um ano antes", pct(aa["valor"], 1) if aa else "—", rot(aa["mes"]) if aa else ""),
                                       ("Trimestre anterior", pct(d[-4]["valor"], 1) if len(d) > 3 else "—", rot(d[-4]["mes"]) if len(d) > 3 else ""), ("", "", "")],
                             "graf": [(rot(x["mes"]), x["valor"]) for x in d[-12:]], "base_zero": False, "fonte": s["fonte"], "id": "desemprego"}
    return out

def barras(dados, base_zero=True):
    if not dados: return ""
    val = [v for _, v in dados]; n = len(val); W, H = 240, 64
    if base_zero: hi, lo = max(val + [0]), min(val + [0])
    else:
        hi, lo = max(val), min(val); lo -= (hi - lo) * 0.4 or abs(hi) * 0.05 or 1
    f = (hi - lo) or 1; zero = H * hi / f if base_zero else H; passo = W / n; out = ""
    for i, v in enumerate(val):
        y = H - (v - (0 if base_zero else lo)) / f * H if not base_zero else zero - v / f * H
        y1, y2 = sorted([y, zero]); y2 = max(y2, y1 + 1.5)
        cls = "ul" if i == n - 1 else ("ng" if v < 0 and base_zero else "")
        out += f'<rect class="{cls}" x="{i * passo + passo * .16:.1f}" y="{y1:.1f}" width="{passo * .68:.1f}" height="{y2 - y1:.1f}" rx="1.5"><title>{e(dados[i][0])}: {br(v)}</title></rect>'
    return (f'<svg class="ix-g" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">{out}</svg>'
            f'<div class="ix-gl"><span>{e(dados[0][0])}</span><span>{e(dados[-1][0])}</span></div>')

def cartao(it):
    selo = ""
    if it.get("selo"): selo = f'<span class="ix-s {it["selo"][1]}">{e(it["selo"][0])}</span>'
    apoio = "".join(f'<div><span>{e(a)}</span><b>{e(b)}</b><small>{e(c)}</small></div>' for a, b, c in it["apoio"] if a)
    return (f'<article class="ix" id="ix-{it["id"]}"><p class="ix-t">{e(it["tag"])} · <span>{e(it["ref_txt"])}</span></p>'
            f'<h3>{e(it["titulo"])}</h3><p class="ix-sub">{e(it["sub"])}</p>'
            f'<div class="ix-v"><b class="{it["cor"]}">{e(it["valor"])}</b>{selo}</div><p class="ix-f">{e(it["frase"])}</p>'
            f'<div class="ix-a">{apoio}</div>{barras(it["graf"], it.get("base_zero", True))}'
            f'<p class="ix-fn">Fonte: {e(it["fonte"])}</p></article>')

GRUPOS = [("Inflação e juros", "Quanto os preços sobem e quanto custa o dinheiro", ["selic", "ipca", "ipca15", "focus", "igpm", "inpc", "incc"]),
          ("Emprego e atividade", "Vagas, produção e consumo", ["desemprego", "caged", "industria", "varejo"]),
          ("Crédito e setor externo", "Endividamento das famílias e as contas do país com o exterior", ["inadimplencia", "contas_externas"]),
          ("Mundo", "Juros e emprego nas maiores economias", ["fed", "bce", "payroll"])]

def aba(raiz, economias_html=""):
    try: ind = json.loads((Path(raiz) / "indicadores.json").read_text(encoding="utf-8"))
    except Exception: ind = {"series": {}}
    try: novos = json.loads((Path(raiz) / "indicadores2.json").read_text(encoding="utf-8"))["itens"]
    except Exception: novos = {}
    for k, v in novos.items(): v["id"] = k
    todos = {**originais(ind), **novos}
    nav = "".join(f'<button data-ixgo="{i}">{e(g)}</button>' for i, (g, _, _) in enumerate(GRUPOS)) + ('<button data-ixgo="eco">Maiores economias</button>' if economias_html else "")
    corpo = ""
    for i, (g, desc, ids) in enumerate(GRUPOS):
        cards = "".join(cartao(todos[k]) for k in ids if k in todos)
        if cards: corpo += f'<section class="ix-g0" id="ix-grupo-{i}"><header class="mk-gh"><h2>{e(g)}</h2><p>{e(desc)}</p></header><div class="ix-grade">{cards}</div></section>'
    if economias_html: corpo += f'<section class="ix-g0" id="ix-grupo-eco"><header class="mk-gh"><h2>Maiores economias do mundo</h2><p>PIB e balança comercial</p></header>{economias_html}</section>'
    return (f'<section class="pagina" id="pg-indicadores" data-pg="indicadores" hidden>\n'
            f'  <div class="sec-t s-indicadores"><h2>Indicadores</h2><span>O último dado de cada indicador, com fonte oficial</span></div>\n'
            f'  <div class="painel ixp"><nav class="mk-nav" aria-label="Grupos de indicadores">{nav}</nav>{corpo}'
            f'<p class="nota">Fontes: IBGE, FGV, Banco Central, Ministério do Trabalho e FRED (Federal Reserve Bank of St. Louis). Atualizado várias vezes ao dia. '
            f'<a href="indicadores">Séries históricas em detalhe →</a></p></div>\n</section>')
