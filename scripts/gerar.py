#!/usr/bin/env python3
"""Gera a página do Plantão de Notícias.
Uso: python3 gerar.py <dir-com-noticias.json> [caminho/mercado.json] [saida/index.html]
Com o 3º argumento, grava só o site nesse caminho (modo GitHub Actions)."""
import json, sys, html
from datetime import datetime, timedelta, timezone
from pathlib import Path

d = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent)
merc_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/home/claude/plantao-noticias/mercado.json")
data = json.loads((d / "noticias.json").read_text(encoding="utf-8"))
mercado = json.loads(merc_path.read_text(encoding="utf-8")) if merc_path.exists() else {}
BRT = timezone(timedelta(hours=-3))
DIAS = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
MESES = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
SECOES = data.get("secoes", ["Política", "IA", "Futebol", "Agro", "Mercado"])
e = html.escape
def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "".join(c if c.isalnum() else "-" for c in s).strip("-")
def parse(s): return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(BRT)

upd = parse(data["atualizado_utc"])
def rel(dt):
    h = int((upd - dt).total_seconds() // 3600)
    if h < 1: return "há menos de 1 h"
    if h < 24: return f"há {h} h"
    return f"{dt.day:02d}/{dt.month:02d}"

itens = sorted(data["itens"], key=lambda i: i["data"], reverse=True)
por_sec = {s: [i for i in itens if i["secao"] == s] for s in SECOES}
fontes = list(dict.fromkeys(i["fonte"] for i in itens))

def meta(i, sec=False):
    s = f'<span class="sec s-{slug(i["secao"])}">{e(i["secao"])}</span>' if sec else ""
    return (f'<div class="meta">{s}<span class="fonte">{e(i["fonte"])}</span>'
            f'<time datetime="{e(i["data"])}">{rel(parse(i["data"]))}</time></div>')
def a(i, cls=""):
    return f'<a{cls} href="{e(i["link"])}" target="_blank" rel="noopener">{e(i["titulo"])}</a>'

def resumo(i): return f'<p>{e(i["resumo"])}</p>' if i.get("resumo") else ""

# Manchete: a mais recente com resumo (senão a mais recente)
lead = itens[0]
lead_html = f'''<article class="lead">
  {meta(lead, True)}
  <h2>{a(lead)}</h2>
  {f'<p>{e(lead["resumo"])}</p>' if lead.get("resumo") else ""}
</article>'''
# Destaques: a mais recente de cada seção (exceto a da manchete)
dest = [por_sec[s][0] for s in SECOES if por_sec[s] and por_sec[s][0]["link"] != lead["link"]][:4]
dest_html = "".join(f'<article class="dest">{meta(i, True)}<h3>{a(i)}</h3></article>' for i in dest)

blocos = ""
for s in SECOES:
    usados = {lead["link"]} | {i["link"] for i in dest}
    lst = [i for i in por_sec[s] if i["link"] not in usados][:5]
    if not lst: continue
    extra = '<div class="mini-ind" data-mini></div>' if s == "Mercado" else ""
    li = "".join(f'<li>{meta(i)}<h4>{a(i)}</h4></li>' for i in lst)
    blocos += f'''<section class="bloco s-{slug(s)}">
  <header><h2>{e(s)}</h2><a class="ver" href="#{slug(s)}" data-tab="{slug(s)}">Ver tudo →</a></header>
  {extra}<ol>{li}</ol>
</section>'''

paginas = ""
for s in SECOES:
    li = "".join(f'<li>{meta(i)}<h4>{a(i)}</h4>{resumo(i)}</li>' for i in por_sec[s])
    painel = ""
    if s == "Política":
        painel = '''<div class="painel contas" data-contas>
  <section class="quadro">
    <header><h3>Contas públicas dos estados</h3>
      <div class="filtros-uf">
        <label>Estado <select data-uf aria-label="Escolher estado"></select></label>
        <div class="seg" role="group" aria-label="Período"><button class="on" data-ep="atual" aria-pressed="true">Ano atual</button><button data-ep="anterior" aria-pressed="false">Ano passado</button></div>
      </div>
      <p class="per" data-per>Carregando dados do Tesouro Nacional…</p></header>
    <div class="ind-grid" data-uc></div>
    <div class="quadros">
      <div class="tw"><table class="tab-m"><thead><tr><th>Receitas</th><th class="n">Arrecadado</th><th class="n">% do previsto</th></tr></thead><tbody data-ur></tbody></table></div>
      <div class="tw"><table class="tab-m"><thead><tr><th>Despesas por tipo</th><th class="n">Empenhado</th><th class="n">Pago</th></tr></thead><tbody data-ud></tbody></table></div>
      <div class="tw"><table class="tab-m"><thead><tr><th>Para onde vai o dinheiro</th><th class="n">Liquidado</th><th class="n">% do total</th></tr></thead><tbody data-uf2></tbody></table></div>
    </div>
    <p class="nota">Fonte: Tesouro Nacional, SICONFI (Relatório Resumido da Execução Orçamentária, enviado pelos próprios estados a cada bimestre). Valores acumulados no ano, sem as operações intraorçamentárias.</p>
  </section>
</div>'''
    if s == "Futebol":
        painel = '''<div class="painel" data-fut>
  <section class="quadro">
    <header><h3>Classificação</h3>
      <div class="filtros-uf"><label>Campeonato <select data-liga aria-label="Escolher campeonato"></select></label></div>
      <p class="per" data-ftemp>Carregando a tabela…</p></header>
    <div data-ftab></div>
    <p class="nota" data-fnota></p>
  </section>
</div>'''
    if s == "Mercado":
        painel = '''<div class="painel">
  <div class="ind-grid" data-ind></div>
  <div class="quadros">
    <section class="quadro" aria-label="Ações">
      <header><h3>Ações</h3>
        <div class="seg" role="group" aria-label="Filtrar ações">
          <button class="on" data-af="altas" aria-pressed="true">Maiores altas</button><button data-af="quedas" aria-pressed="false">Maiores quedas</button><button data-af="maiores" aria-pressed="false">Maiores empresas</button>
        </div></header>
      <div class="tw"><table class="tab-m"><thead data-ah></thead><tbody data-ab></tbody></table></div>
    </section>
    <section class="quadro" aria-label="Fundos imobiliários">
      <header><h3>Fundos imobiliários</h3>
        <div class="seg" role="group" aria-label="Ordenar FIIs">
          <button class="on" data-ff="vm" aria-pressed="true">Valor de mercado</button><button data-ff="dy" aria-pressed="false">Maior DY</button><button data-ff="pvp" aria-pressed="false">Menor P/VP</button><button data-ff="altas" aria-pressed="false">Maiores altas</button><button data-ff="baixas" aria-pressed="false">Maiores baixas</button>
        </div></header>
      <div class="tw"><table class="tab-m"><thead><tr><th>Fundo</th><th class="seg-col">Segmento</th><th class="n">Cotação</th><th class="n">Dia</th><th class="n">DY 12m</th><th class="n">P/VP</th><th class="n">Valor merc.</th></tr></thead><tbody data-fb></tbody></table></div>
    </section>
  </div>
  <p class="nota" data-nota></p>
</div>'''
    paginas += f'''<section class="pagina" id="pg-{slug(s)}" data-pg="{slug(s)}" hidden>
  <div class="sec-t s-{slug(s)}"><h2>{e(s)}</h2><span>{len(por_sec[s])} notícias</span></div>
  {painel}<ol class="lista">{li or "<li><p>Sem notícias nesta atualização.</p></li>"}</ol>
</section>'''

tabs = '<button class="tab on" data-tab="inicio" aria-pressed="true">Início</button>' + "".join(
    f'<button class="tab" data-tab="{slug(s)}" aria-pressed="false">{e(s)}</button>' for s in SECOES)
fontes_txt = ", ".join(e(f) for f in fontes)
horarios = " · ".join(f"{h:02d}h" for h in (1, 5, 9, 13, 17, 21))
merc_json = json.dumps(mercado, ensure_ascii=False).replace("</", "<\\/")

tpl = (Path(__file__).parent / "modelo.html").read_text(encoding="utf-8")
out = tpl
for k, v in {"DATA": f"{DIAS[upd.weekday()]}, {upd.day} de {MESES[upd.month-1]} de {upd.year}",
             "HORA": f"{upd:%H:%M}", "LEAD": lead_html, "DESTAQUES": dest_html, "BLOCOS": blocos,
             "PAGINAS": paginas, "TABS": tabs, "HORARIOS": horarios, "FONTES": fontes_txt,
             "TOTAL": str(len(itens)), "NFONTES": str(len(fontes)), "MERCADO": merc_json}.items():
    out = out.replace("{{" + k + "}}", v)
saida_site = Path(sys.argv[3]) if len(sys.argv) > 3 else None
if not saida_site:
    (d / "noticias.html").write_text(out, encoding="utf-8")
    site = d / "site"; site.mkdir(exist_ok=True)
    saida_site = site / "index.html"
saida_site.write_text(
    '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '<meta name="description" content="Política, IA, futebol, agro e mercado: manchetes de fontes confiáveis, atualizadas 6 vezes por dia.">\n'
    '<link rel="icon" href="favicon.png" type="image/png">\n'
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
    '<meta name="theme-color" content="#0b1f3a">\n'
    '<meta property="og:image" content="https://marcosaraujo123443-ship-it.github.io/plantao-noticias/logo.jpg">\n'
    '<meta property="og:url" content="https://marcosaraujo123443-ship-it.github.io/plantao-noticias/">\n'
    '<meta name="twitter:card" content="summary">\n'
    '<meta property="og:title" content="Plantão de Notícias">\n'
    '<meta property="og:description" content="Manchetes de fontes confiáveis, atualizadas 6 vezes por dia.">\n'
    '</head>\n<body>\n' + out + '\n</body>\n</html>\n', encoding="utf-8")
print("ok", len(itens), "itens", {s: len(v) for s, v in por_sec.items()}, "mercado:", bool(mercado))
