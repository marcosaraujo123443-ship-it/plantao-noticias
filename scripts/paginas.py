#!/usr/bin/env python3
"""Gera páginas próprias (contas públicas, tabelas, cotações) a partir dos JSON do site.
Roda na publicação do Cloudflare: python3 scripts/paginas.py <pasta de saída>"""
import json, os, sys, html, unicodedata, re
from datetime import datetime, timedelta, timezone

SITE = os.environ.get("SITE_URL") or "https://plantaoinforma.com.br/"
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"
BRT = timezone(timedelta(hours=-3))
e = lambda s: html.escape(str(s), quote=True)
MESES = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]

def ler(nome):
    try: return json.load(open(nome, encoding="utf-8"))
    except Exception: return None

def slug(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if not unicodedata.combining(c))).strip("-")

def br(v, casas=2):
    if v is None: return "–"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def rs(v, longo=False):
    if v is None: return "–"
    a, s = abs(v), "−" if v < 0 else ""
    if a >= 1e12: return f"{s}R$ {br(a / 1e12, 2)} {('trilhão' if a < 2e12 else 'trilhões') if longo else 'tri'}"
    if a >= 1e9: return f"{s}R$ {br(a / 1e9, 1)} {('bilhão' if a < 2e9 else 'bilhões') if longo else 'bi'}"
    if a >= 1e6: return f"{s}R$ {br(a / 1e6, 1)} {('milhão' if a < 2e6 else 'milhões') if longo else 'mi'}"
    return f"{s}R$ {br(a, 0)}"

def pc(a, b): return f"{br(a / b * 100, 1)}%" if a is not None and b else "–"

def var(v, sufixo="%"):
    if v is None: return '<td class="n">–</td>'
    c = "up" if v > 0.005 else "down" if v < -0.005 else ""
    return f'<td class="n {c}">{"+" if v > 0 else ""}{br(v)}{sufixo}</td>'

def quando(iso):
    try: d = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BRT)
    except Exception: return ""
    return f"{d.day} de {MESES[d.month]} de {d.year}, às {d:%H:%M}"

CSS = """:root{--ink:#0a1d3d;--ink2:#4a5568;--paper:#f6f7fa;--card:#fff;--rule:#dde2ea;--brand:#8f0922;--band:#0b1f3a;--up:#0f7a3d;--down:#b3261e}
@media (prefers-color-scheme:dark){:root{--ink:#e8ecf3;--ink2:#a7b0c0;--paper:#0d1420;--card:#141d2c;--rule:#26324a;--brand:#ef5a6f;--up:#4cc27e;--down:#ff6b6b}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:var(--band);padding:12px 16px}.hd{max-width:1000px;margin:0 auto;display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;justify-content:space-between}
header a.marca{color:#fff;text-decoration:none;font:700 20px Georgia,serif;display:inline-flex;gap:10px;align-items:center}header img{width:34px;height:34px;border-radius:50%}
nav.pg{display:flex;flex-wrap:wrap;gap:4px 16px}nav.pg a{color:#cfd8e6;text-decoration:none;font-size:14px}nav.pg a:hover,nav.pg a.on{color:#fff;text-decoration:underline}
main{max-width:1000px;margin:0 auto;padding:22px 16px 48px}.trilha{font-size:13px;color:var(--ink2);margin-bottom:6px}.trilha a{color:var(--ink2)}
h1{font:700 clamp(26px,4vw,34px)/1.2 Georgia,serif;margin:0 0 12px}h2{font:700 21px Georgia,serif;margin:30px 0 10px}
p{max-width:75ch}.lead{font-size:17px}a{color:var(--brand)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--rule);padding:12px 14px}.card span{display:block;font-size:13px;color:var(--ink2)}.card b{font-size:21px}.card i{display:block;font-style:normal;font-size:12.5px;color:var(--ink2)}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--rule)}table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{padding:8px 12px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}th{font-size:12.5px;color:var(--ink2);font-weight:600;white-space:nowrap}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}tr.tot td{font-weight:700}tr.sub td:first-child{padding-left:26px;color:var(--ink2)}
.up{color:var(--up)}.down{color:var(--down)}.esc{width:18px;height:18px;vertical-align:-4px;margin-right:6px}
.zona td:first-child{box-shadow:inset 4px 0 0 var(--z)}.leg{font-size:13px;color:var(--ink2);margin:8px 0 0}.leg i{display:inline-block;width:10px;height:10px;margin:0 5px 0 12px;vertical-align:0}
.lista{columns:3 220px;padding:0;list-style:none}.lista li{padding:3px 0}
.nota{color:var(--ink2);font-size:13.5px;margin-top:28px;border-top:1px solid var(--rule);padding-top:12px}
@media (max-width:600px){th,td{padding:7px 8px}table{font-size:13.5px}td:first-child{min-width:150px}}"""

NAV = [("contas/", "Contas públicas"), ("tabelas/", "Tabelas do futebol"), ("agro.html", "Cotações do agro"),
       ("acoes.html", "Ações"), ("fiis.html", "Fundos imobiliários")]
PAGINAS = []

def limpa_url(caminho):
    """O Cloudflare Pages serve /contas/sp.html como /contas/sp (e index.html como a pasta)."""
    return caminho[:-10] if caminho.endswith("index.html") else caminho[:-5] if caminho.endswith(".html") else caminho

def pagina(caminho, titulo, descricao, corpo, trilha=None, atualizado=None):
    PAGINAS.append(caminho)
    raiz = "../" * caminho.count("/")
    url = SITE + limpa_url(caminho)
    nav = "".join(f'<a href="{raiz}{h}"{" class=on" if caminho.startswith(h.split(".")[0]) else ""}>{e(t)}</a>' for h, t in NAV)
    tr = '<div class="trilha"><a href="' + raiz + './">Início</a>' + "".join(
        f' › <a href="{raiz}{h}">{e(t)}</a>' for h, t in (trilha or [])) + "</div>"
    upd = f'<p class="nota">Atualizado em {quando(atualizado)} (horário de Brasília). ' if atualizado else '<p class="nota">'
    doc = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)} · Plantão Informa</title><meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{e(url)}"><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta name="theme-color" content="#0b1f3a">
<meta property="og:type" content="website"><meta property="og:site_name" content="Plantão Informa"><meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}"><meta property="og:url" content="{e(url)}"><meta property="og:image" content="{SITE}logo.jpg">
<style>{CSS}</style></head><body>
<header><div class="hd"><a class="marca" href="{raiz}./"><img src="{raiz}apple-touch-icon.png" alt="">Plantão Informa</a><nav class="pg">{nav}</nav></div></header>
<main>{tr}<h1>{e(titulo)}</h1>
{corpo}
{upd}Dados com atraso, apenas informativos. <a href="{raiz}./">Notícias</a> · <a href="{raiz}sobre.html">Sobre</a> · <a href="{raiz}privacidade.html">Privacidade</a></p>
</main></body></html>"""
    destino = os.path.join(OUT, caminho)
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    open(destino, "w", encoding="utf-8").write(doc)

def tabela(cab, linhas):
    th = "".join(f'<th{" class=n" if n else ""}>{e(c)}</th>' for c, n in cab)
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'

# ---------------- Contas públicas ----------------
def periodo(b):
    return f"o ano de {b['ano']} completo" if b["periodo"] == 6 else f"janeiro a {MESES[b['periodo'] * 2]} de {b['ano']}"

def linha(L, n): return next((r for r in L or [] if r["n"] == n), {})

def contas(est):
    E = est["estados"]
    def nome_pg(s): return {"BR": "brasil", "UF": "estados"}.get(s, s.lower())
    def quem(x): return "o governo federal" if x["sigla"] == "BR" else "os 27 estados somados" if x["sigla"] == "UF" else f"o governo de {x['nome']}"
    ordem = sorted(E.values(), key=lambda x: ({"BR": 0, "UF": 1}.get(x["sigla"], 2), slug(x["nome"])))
    resumo = []
    for x in ordem:
        b = x.get("atual")
        if not b: continue
        rt, dt = linha(b["receitas"], "Total arrecadado"), linha(b["despesas"], "Total")
        saldo = (rt.get("realizado") or 0) - (dt.get("liquidado") or 0)
        resumo.append((x, b, rt, dt, saldo))
        inv = linha(b["despesas"], "Investimentos")
        func = [f for f in b.get("funcoes", []) if f["n"] != "Encargos Especiais"][:3]
        txt = (f"<p class=lead>De {periodo(b)}, {quem(x)} arrecadou <b>{rs(rt.get('realizado'), True)}</b>, "
               f"{pc(rt.get('realizado'), rt.get('previsto'))} do previsto para o ano, e gastou <b>{rs(dt.get('liquidado'), True)}</b> "
               f"(despesa liquidada). {'Sobraram' if saldo >= 0 else 'Faltaram'} {rs(abs(saldo), True)} no período")
        txt += (f". Os investimentos somaram {rs(inv.get('liquidado'), True)}, {pc(inv.get('liquidado'), dt.get('liquidado'))} do gasto." if inv.get("liquidado") else ".")
        if func: txt += " As áreas com mais gasto, fora a dívida e os repasses, foram " + ", ".join(f"{f['n'].lower()} ({rs(f['liquidado'])})" for f in func[:-1]) + f" e {func[-1]['n'].lower()} ({rs(func[-1]['liquidado'])})."
        ant = x.get("anterior")
        if ant:
            ra, da = linha(ant["receitas"], "Total arrecadado"), linha(ant["despesas"], "Total")
            txt += f" Em todo o ano de {ant['ano']}, arrecadou {rs(ra.get('realizado'), True)} e gastou {rs(da.get('liquidado'), True)}."
        txt += "</p>"
        if x["sigla"] == "UF": txt = txt.replace(" arrecadou ", " arrecadaram ").replace(" gastou ", " gastaram ").replace("Em todo o ano", "Em todo o ano")
        cards = (f'<div class="cards"><div class="card"><span>Arrecadado</span><b>{rs(rt.get("realizado"))}</b><i>{pc(rt.get("realizado"), rt.get("previsto"))} do previsto</i></div>'
                 f'<div class="card"><span>Gasto (liquidado)</span><b>{rs(dt.get("liquidado"))}</b><i>{rs(dt.get("pago"))} já pago</i></div>'
                 f'<div class="card"><span>Saldo</span><b class="{"up" if saldo >= 0 else "down"}">{rs(saldo)}</b><i>{"arrecadou mais do que gastou" if saldo >= 0 else "gastou mais do que arrecadou"}</i></div>'
                 + (f'<div class="card"><span>Arrecadado por habitante</span><b>{rs(rt["realizado"] / b["populacao"])}</b><i>{br(b["populacao"], 0)} habitantes</i></div>' if b.get("populacao") and rt.get("realizado") else "")
                 + "</div>")
        rec = [f'<tr{" class=tot" if r["n"] == "Total arrecadado" else " class=sub" if r["n"][0].islower() else ""}><td>{e(r["n"])}</td>'
               f'<td class="n">{rs(r.get("previsto"))}</td><td class="n">{rs(r.get("realizado"))}</td><td class="n">{pc(r.get("realizado"), r.get("previsto"))}</td></tr>'
               for r in b["receitas"] if r.get("realizado") and not (x["sigla"] == "BR" and r["n"].startswith("das quais"))]
        desp = [f'<tr{" class=tot" if r["n"] == "Total" else " class=sub" if r["n"][0].islower() else ""}><td>{e(r["n"])}</td>'
                f'<td class="n">{rs(r.get("dotacao"))}</td><td class="n">{rs(r.get("empenhado"))}</td><td class="n">{rs(r.get("liquidado"))}</td><td class="n">{rs(r.get("pago"))}</td></tr>'
                for r in b["despesas"] if r.get("empenhado") or r.get("pago")]
        fun = [f'<tr><td>{e("Encargos especiais (dívida, repasses e outros)" if f["n"] == "Encargos Especiais" else f["n"])}</td>'
               f'<td class="n">{rs(f["liquidado"])}</td><td class="n">{pc(f["liquidado"], dt.get("liquidado"))}</td></tr>' for f in b.get("funcoes", [])]
        outros = " · ".join(f'<a href="{nome_pg(o["sigla"])}.html">{e(o["sigla"] if o["sigla"] not in ("BR", "UF") else o["nome"])}</a>'
                            for o in ordem if o["sigla"] != x["sigla"])
        corpo = (txt + cards + "<h2>Receitas</h2>" + tabela([("Receita", 0), ("Previsto no ano", 1), ("Arrecadado", 1), ("% do previsto", 1)], rec)
                 + "<h2>Despesas por tipo</h2>" + tabela([("Despesa", 0), ("Orçamento do ano", 1), ("Empenhado", 1), ("Liquidado", 1), ("Pago", 1)], desp)
                 + ("<h2>Gasto por área</h2>" + tabela([("Área", 0), ("Liquidado", 1), ("% do gasto", 1)], fun) if fun else "")
                 + f'<h2>Outros governos</h2><p>{outros}</p>'
                 + f'<p class="nota">Fonte: Tesouro Nacional, Relatório Resumido da Execução Orçamentária (RREO) enviado ao SICONFI. '
                   f'Empenhado é o gasto contratado, liquidado é o serviço entregue e pago é o dinheiro que já saiu do caixa.</p>')
        alvo = "o governo federal" if x["sigla"] == "BR" else "os estados" if x["sigla"] == "UF" else x["nome"]
        tit = f"Contas públicas: {'Brasil (Governo Federal)' if x['sigla'] == 'BR' else 'todos os estados' if x['sigla'] == 'UF' else x['nome']} em {b['ano']}"
        pagina(f"contas/{nome_pg(x['sigla'])}.html", tit,
               f"Quanto {alvo} arrecadou e gastou em {b['ano']}: receitas, despesas, saldo e gasto por área (saúde, educação, segurança), com dados do Tesouro Nacional.",
               corpo, [("contas/", "Contas públicas")], est.get("atualizado_utc"))
    linhas = []
    for x, b, rt, dt, saldo in resumo:
        if x["sigla"] in ("BR", "UF"): continue
        pcap = rt["realizado"] / b["populacao"] if b.get("populacao") and rt.get("realizado") else None
        linhas.append(f'<tr><td><a href="{nome_pg(x["sigla"])}.html">{e(x["nome"])}</a></td><td class="n">{rs(rt.get("realizado"))}</td>'
                      f'<td class="n">{rs(dt.get("liquidado"))}</td><td class="n {"up" if saldo >= 0 else "down"}">{rs(saldo)}</td><td class="n">{rs(pcap)}</td>'
                      f'<td class="n">{b["periodo"] * 2 if b["periodo"] < 6 else 12}/{b["ano"]}</td></tr>')
    corpo = ('<p class=lead>Quanto cada governo arrecadou e gastou neste ano, com os dados que os próprios estados e a União enviam ao Tesouro Nacional. '
             'Clique em um estado para ver receitas, despesas e o gasto por área.</p>'
             '<p><a href="brasil.html"><b>Brasil (Governo Federal)</b></a> · <a href="estados.html"><b>Todos os estados somados</b></a></p>'
             + tabela([("Estado", 0), ("Arrecadado", 1), ("Gasto", 1), ("Saldo", 1), ("Por habitante", 1), ("Dados até", 1)], linhas))
    pagina("contas/index.html", "Contas públicas dos estados e da União",
           "Receitas, despesas e saldo do governo federal e dos 27 estados em 2026, com dados do Tesouro Nacional (SICONFI) atualizados diariamente.",
           corpo, None, est.get("atualizado_utc"))

# ---------------- Tabelas do futebol ----------------
SLUG_LIGA = {"bra.1": "brasileirao-serie-a", "bra.2": "brasileirao-serie-b", "eng.1": "premier-league", "esp.1": "la-liga",
             "ita.1": "serie-a-italia", "ger.1": "bundesliga", "fra.1": "ligue-1", "por.1": "liga-portugal",
             "uefa.champions": "champions-league", "arg.1": "campeonato-argentino"}
ZONAS = {"bra.1": [(1, 6, "#2e7d32", "Zona da Libertadores"), (7, 12, "#1565c0", "Zona da Sul-Americana"),
                   (17, 20, "#c62828", "Zona de rebaixamento")],
         "bra.2": [(1, 4, "#2e7d32", "Zona de acesso"), (17, 20, "#c62828", "Zona de rebaixamento")]}

def futebol(fut):
    itens = []
    for l in fut.get("ligas", []):
        sl = SLUG_LIGA.get(l["id"], slug(l["nome"]))
        itens.append((sl, l))
        blocos, z = [], ZONAS.get(l["id"], [])
        for g in l["grupos"]:
            rows = []
            for r in g["linhas"]:
                cor = next((c for a, b, c, _ in z if a <= (r["pos"] or 0) <= b), None) or (f'#{r["cor"]}' if r.get("cor") and not z else None)
                esc = f'<img class="esc" src="{e(r["escudo"])}" alt="" loading="lazy" onerror="this.remove()">' if r.get("escudo") else ""
                rows.append(f'<tr{f" class=zona style=--z:{cor}" if cor else ""}><td class="n">{r["pos"]}</td><td>{esc}{e(r["time"])}</td>'
                            + "".join(f'<td class="n">{"" if r[k] is None else r[k]}</td>' for k in ("pts", "j", "v", "e", "d", "gp", "gc", "sg")) + "</tr>")
            leg = " ".join(f'<i style="background:{c}"></i>{e(t)}' for _, _, c, t in z) or " ".join(
                f'<i style="background:#{c}"></i>{e(t)}' for t, c in dict((r["nota"], r["cor"]) for r in g["linhas"] if r.get("nota") and r.get("cor")).items())
            blocos.append((f"<h2>{e(g['nome'])}</h2>" if g["nome"] else "")
                          + tabela([("#", 1), ("Time", 0), ("P", 1), ("J", 1), ("V", 1), ("E", 1), ("D", 1), ("GP", 1), ("GC", 1), ("SG", 1)], rows)
                          + (f'<p class="leg">{leg}</p>' if leg else ""))
        lin = l["grupos"][0]["linhas"]
        txt = ""
        if len(l["grupos"]) == 1 and len(lin) >= 2 and lin[0].get("pts") is not None:
            a, b = lin[0], lin[1]
            dif = (a["pts"] or 0) - (b["pts"] or 0)
            txt = (f"<p class=lead>{e(a['time'])} lidera {e(l['nome'])} com {a['pts']} pontos em {a['j']} jogos"
                   + (f", {dif} {'ponto' if dif == 1 else 'pontos'} à frente do {e(b['time'])}" if dif else f", empatado em pontos com o {e(b['time'])}")
                   + f". {e(lin[-1]['time'])} é o último colocado, com {lin[-1]['pts']} pontos.</p>")
        outras = " · ".join(f'<a href="{SLUG_LIGA.get(o["id"], slug(o["nome"]))}.html">{e(o["nome"])}</a>' for o in fut["ligas"] if o["id"] != l["id"])
        ano = re.search(r"\d{4}(?:[-/]\d{2,4})?", l.get("temporada") or "")
        pagina(f"tabelas/{sl}.html", f"Tabela {l['nome']} {ano.group(0).replace("-", "/") if ano else ''}".strip(),
               f"Classificação atualizada de {l['nome']}: pontos, jogos, vitórias, saldo de gols e zonas de classificação e rebaixamento.",
               txt + "".join(blocos) + f"<h2>Outros campeonatos</h2><p>{outras}</p>"
               + '<p class="nota">P = pontos, J = jogos, V = vitórias, E = empates, D = derrotas, GP = gols pró, GC = gols contra, SG = saldo. Fonte: ESPN.</p>',
               [("tabelas/", "Tabelas do futebol")], fut.get("atualizado_utc"))
    lista = "".join(f'<li><a href="{sl}.html">{e(l["nome"])}</a> <small>· líder: {e(l["grupos"][0]["linhas"][0]["time"]) if len(l["grupos"]) == 1 else "fase de grupos"}</small></li>'
                    for sl, l in itens)
    pagina("tabelas/index.html", "Tabelas do futebol",
           "Classificação atualizada do Brasileirão Série A e B, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League e mais.",
           f'<p class=lead>Classificação dos principais campeonatos, atualizada de hora em hora.</p><ul class="lista">{lista}</ul>', None, fut.get("atualizado_utc"))

# ---------------- Agro ----------------
def agro(ag):
    ind = [f'<tr><td>{e(i["nome"])}</td><td class="n">{br(i["preco"])}</td>{var(i.get("var"))}<td>{e(i["un"])}</td><td>{e(i.get("data") or "")}</td><td>{e(i.get("fonte") or "")}</td></tr>'
           for i in ag.get("indicadores", [])]
    bol = [f'<tr><td>{e(b["nome"])}</td><td>{e(b["bolsa"])}</td><td>{e(b["venc"])}</td><td class="n">{br(b["preco"])}</td>{var(b.get("var"))}<td>{e(b["un"])}</td></tr>'
           for b in ag.get("bolsas", [])]
    pr = "".join(f"<h2>{e(p['nome'])} por praça <small>({e(p['un'])})</small></h2>"
                 + tabela([("Praça", 0), ("Preço", 1), ("Variação", 1)], [f'<tr><td>{e(l[0])}</td><td class="n">{br(l[1])}</td>{var(l[2])}</tr>' for l in p["linhas"]])
                 for p in ag.get("pracas", []))
    soja = next((i for i in ag.get("indicadores", []) if i["nome"].startswith("Soja")), None)
    boi = next((i for i in ag.get("indicadores", []) if i["nome"].startswith("Boi")), None)
    txt = "<p class=lead>Preços de referência das principais commodities agrícolas, contratos nas bolsas e cotações por praça."
    if soja and boi: txt += f" A saca de soja em Paranaguá está em R$ {br(soja['preco'])} e a arroba do boi gordo em São Paulo, R$ {br(boi['preco'])}."
    pagina("agro.html", "Cotações do agro hoje",
           "Preço da soja, milho, boi gordo, café, trigo, algodão, açúcar e etanol: indicadores Cepea/Esalq, contratos na B3, Chicago e Nova York e preços por praça.",
           txt + "</p><h2>Indicadores</h2>" + tabela([("Produto", 0), ("Preço", 1), ("Variação", 1), ("Unidade", 0), ("Data", 0), ("Fonte", 0)], ind)
           + "<h2>Bolsas</h2>" + tabela([("Produto", 0), ("Bolsa", 0), ("Vencimento", 0), ("Preço", 1), ("Variação", 1), ("Unidade", 0)], bol) + pr
           + '<p class="nota">Fontes: Cepea/Esalq, B3, CME Group, ICE e cooperativas, reunidos pelo Notícias Agrícolas.</p>',
           None, ag.get("atualizado_utc"))

# ---------------- Mercado ----------------
def mercado(m):
    ib = [a for a in m.get("ibov", []) if a.get("var") is not None]
    altas = sorted(ib, key=lambda a: a["var"], reverse=True)[:10]
    quedas = sorted(ib, key=lambda a: a["var"])[:10]
    lin = lambda L: [f'<tr><td><b>{e(a["ticker"])}</b> {e(a["nome"])}</td><td class="n">R$ {br(a["preco"])}</td>{var(a["var"])}</tr>' for a in L]
    cab = [("Ação", 0), ("Preço", 1), ("Dia", 1)]
    ibov = next((i for i in m.get("indicadores", []) if i["nome"] == "Ibovespa"), None)
    txt = "<p class=lead>Maiores altas e quedas do dia entre as ações do Ibovespa e as maiores empresas da bolsa por valor de mercado."
    if ibov and altas and quedas:
        txt += (f" O Ibovespa está em {br(ibov['valor'], 0)} pontos ({'+' if ibov['var'] > 0 else ''}{br(ibov['var'])}%). "
                f"A maior alta é {e(altas[0]['nome'])} ({e(altas[0]['ticker'])}, +{br(altas[0]['var'])}%) e a maior queda, {e(quedas[0]['nome'])} ({e(quedas[0]['ticker'])}, {br(quedas[0]['var'])}%).")
    mai = [f'<tr><td><b>{e(a["ticker"])}</b> {e(a["nome"])}</td><td class="n">R$ {br(a["preco"])}</td>{var(a.get("var"))}<td class="n">{rs(a.get("vm"))}</td></tr>' for a in m.get("maiores", [])]
    todas = sorted(ib, key=lambda a: a["ticker"])
    pagina("acoes.html", "Ações: maiores altas e quedas do Ibovespa hoje",
           "Maiores altas e quedas do Ibovespa hoje, cotação das ações e as maiores empresas da B3 por valor de mercado.",
           txt + "</p><h2>Maiores altas</h2>" + tabela(cab, lin(altas)) + "<h2>Maiores quedas</h2>" + tabela(cab, lin(quedas))
           + "<h2>Maiores empresas por valor de mercado</h2>" + tabela([("Ação", 0), ("Preço", 1), ("Dia", 1), ("Valor de mercado", 1)], mai)
           + "<h2>Todas as ações acompanhadas</h2>" + tabela(cab, lin(todas))
           + '<p class="nota">Fontes: Yahoo Finance e Fundamentus. Não é recomendação de investimento.</p>', None, m.get("atualizado_utc"))
    f = m.get("fiis", [])
    linf = [f'<tr><td><b>{e(x["papel"])}</b></td><td>{e(x.get("segmento") or "")}</td><td class="n">R$ {br(x.get("cotacao"))}</td>{var(x.get("var"))}'
            f'<td class="n">{br(x.get("dy"))}%</td><td class="n">{br(x.get("pvp"))}</td><td class="n">{rs(x.get("vm"))}</td></tr>'
            for x in sorted(f, key=lambda x: x.get("vm") or 0, reverse=True)]
    dy = sorted((x for x in f if x.get("dy")), key=lambda x: x["dy"], reverse=True)[:3]
    txt = "<p class=lead>Os maiores fundos imobiliários da bolsa com dividend yield (DY), preço sobre valor patrimonial (P/VP) e variação do dia."
    if dy: txt += " Maiores DY entre os listados: " + ", ".join(f"{e(x['papel'])} ({br(x['dy'])}%)" for x in dy) + "."
    pagina("fiis.html", "Fundos imobiliários (FIIs): dividend yield e P/VP",
           "Lista dos maiores fundos imobiliários da B3 com dividend yield, P/VP, valor de mercado, segmento e variação do dia.",
           txt + "</p>" + tabela([("Fundo", 0), ("Segmento", 0), ("Cotação", 1), ("Dia", 1), ("DY 12m", 1), ("P/VP", 1), ("Valor de mercado", 1)], linf)
           + '<p class="nota">Fundos com liquidez diária acima de R$ 500 mil. Fontes: Fundamentus e Yahoo Finance. Não é recomendação de investimento.</p>',
           None, m.get("atualizado_utc"))

def main():
    for nome, f in (("estados.json", contas), ("futebol.json", futebol), ("agro.json", agro), ("mercado.json", mercado)):
        d = ler(nome)
        if d:
            try: f(d)
            except Exception as ex: print("ERRO", nome, ex)
    urls = [SITE + limpa_url(p) for p in ["", "sobre.html", "privacidade.html"] + PAGINAS]
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    xml = "".join(f"  <url><loc>{e(u)}</loc><lastmod>{hoje}</lastmod></url>\n" for u in urls)
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{xml}</urlset>\n')
    print(len(PAGINAS), "páginas geradas")

if __name__ == "__main__":
    main()
