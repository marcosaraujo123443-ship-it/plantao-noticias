#!/usr/bin/env python3
"""Desenha os cards do Instagram (PNG 1080x1350) a partir dos JSON do site.
Usado por scripts/instagram.py; pode rodar sozinho para ver os cards:
    python3 scripts/instagram_cards.py resumo|mercado|agro [pasta_saida]"""
import json, os, sys
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FONTES = os.path.join(AQUI, "fontes")
BRT = timezone(timedelta(hours=-3))
W, H = 1080, 1350
M = 72                      # margem lateral
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()

# Cores do site (scripts/modelo.html)
PAPEL, CARTAO, TINTA, TINTA2, LINHA = "#f5f7fa", "#ffffff", "#0a1d3d", "#4a5873", "#d9e0ea"
MARCA, FAIXA, FAIXA_TINTA = "#8f0922", "#0b1f3a", "#eef2f8"
SOBE, DESCE = "#137a3d", "#c0262d"
COR_SECAO = {"Política": "#1d4ed8", "IA": "#7c3aed", "Futebol": "#15803d", "Agro": "#a16207", "Mercado": "#0f766e"}

_cache = {}
def fonte(nome, tam):
    arq = {"serif": "SourceSerif4-Bold.ttf", "serif-semi": "SourceSerif4-Semibold.ttf",
           "reg": "Inter-Regular.otf", "semi": "Inter-SemiBold.otf", "bold": "Inter-Bold.otf"}[nome]
    chave = (arq, tam)
    if chave not in _cache: _cache[chave] = ImageFont.truetype(os.path.join(FONTES, arq), tam)
    return _cache[chave]

def ler(nome):
    with open(os.path.join(RAIZ, nome), encoding="utf-8") as f: return json.load(f)

def quebrar(d, texto, f, largura):
    linhas = []
    for par in texto.split("\n"):
        atual = ""
        for p in par.split():
            teste = (atual + " " + p).strip()
            if d.textlength(teste, font=f) <= largura: atual = teste
            else:
                if atual: linhas.append(atual)
                atual = p
        linhas.append(atual)
    return linhas

def bloco(d, xy, texto, nome_fonte, tam, cor, largura, altura_max, entrelinha=1.42, minimo=26):
    """Escreve o texto quebrado, reduzindo a fonte até caber em altura_max. Devolve a altura usada."""
    x, y = xy
    while True:
        f = fonte(nome_fonte, tam)
        linhas = quebrar(d, texto, f, largura)
        passo = int(tam * entrelinha)
        if len(linhas) * passo <= altura_max or tam <= minimo: break
        tam -= 2
    for i, l in enumerate(linhas):
        d.text((x, y + i * passo), l, font=f, fill=cor)
    return len(linhas) * passo

def num(v, casas=2):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def var_txt(v):
    return ("+" if v > 0 else "") + num(v) + "%"

def seta(d, x, y, v, tam=18):
    """Triângulo de alta/baixa com o canto superior esquerdo em (x, y)."""
    if v is None: return
    if v > 0: d.polygon([(x, y + tam), (x + tam, y + tam), (x + tam / 2, y)], fill=SOBE)
    elif v < 0: d.polygon([(x, y), (x + tam, y), (x + tam / 2, y + tam)], fill=DESCE)
    else: d.rectangle([x, y + tam / 2 - 3, x + tam, y + tam / 2 + 3], fill=TINTA2)

def cor_var(v): return SOBE if v and v > 0 else DESCE if v and v < 0 else TINTA2

def logo(tam):
    img = Image.open(os.path.join(RAIZ, "logo.jpg")).convert("RGBA").resize((tam, tam), Image.LANCZOS)
    mascara = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(mascara).ellipse([0, 0, tam - 1, tam - 1], fill=255)
    img.putalpha(mascara)
    return img

def data_extenso(dt): return f"{dt.day} {MESES[dt.month - 1]} {dt.year}"

def tela(rotulo, cor_rotulo, quando, pagina=None):
    """Base comum: faixa azul com logo, rótulo da editoria e rodapé com o endereço do site."""
    img = Image.new("RGB", (W, H), PAPEL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 168], fill=FAIXA)
    img.paste(logo(104), (M, 32), logo(104))
    d.text((M + 128, 52), "Plantão", font=fonte("serif-semi", 44), fill=FAIXA_TINTA)
    d.text((M + 128 + d.textlength("Plantão ", font=fonte("serif-semi", 44)), 52), "Informa",
           font=fonte("serif", 44), fill=FAIXA_TINTA)
    f = fonte("semi", 26)
    d.text((W - M - d.textlength(quando, font=f), 66), quando, font=f, fill="#b9c4d6")
    d.rectangle([0, 168, W, 176], fill=MARCA)
    # rótulo da editoria
    f = fonte("bold", 26)
    d.rectangle([M, 232, M + 10, 268], fill=cor_rotulo)
    d.text((M + 26, 234), rotulo.upper(), font=f, fill=cor_rotulo)
    # rodapé
    d.rectangle([0, H - 108, W, H], fill=FAIXA)
    d.text((M, H - 72), "plantaoinforma.com.br", font=fonte("semi", 30), fill=FAIXA_TINTA)
    dica = "link na bio  →" if pagina is None else pagina
    f = fonte("reg", 26)
    d.text((W - M - d.textlength(dica, font=f), H - 70), dica, font=f, fill="#b9c4d6")
    return img, d

# ---------------------------------------------------------------- resumo
def cards_resumo(saida, video=False):
    """video=True tira a paginação do carrossel (1/7, arraste) para usar no reel."""
    r = ler("resumo.json")
    quando = datetime.strptime(r["gerado_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(BRT)
    secoes = r["secoes"]
    total = len(secoes) + 2
    arquivos = []

    img, d = tela("Resumo do Plantão", MARCA, f"{data_extenso(quando)} · {quando:%H}h", "" if video else f"1/{total}  ·  arraste  →")
    usado = bloco(d, (M, 320), r["abertura"], "serif", 76, TINTA, W - 2 * M, 560, 1.18, 52)
    y = 320 + usado + 60
    d.text((M, y), "Neste resumo", font=fonte("semi", 28), fill=TINTA2)
    y += 56
    x = M
    for s in secoes:
        f = fonte("semi", 30)
        larg = d.textlength(s["secao"], font=f) + 48
        if x + larg > W - M: x, y = M, y + 76
        d.rounded_rectangle([x, y, x + larg, y + 58], radius=29, fill=CARTAO, outline=COR_SECAO.get(s["secao"], TINTA), width=3)
        d.text((x + 24, y + 11), s["secao"], font=f, fill=COR_SECAO.get(s["secao"], TINTA))
        x += larg + 16
    arquivos.append(salvar(img, saida, "resumo-1.png"))

    for i, s in enumerate(secoes, start=2):
        cor = COR_SECAO.get(s["secao"], TINTA)
        img, d = tela(s["secao"], cor, f"{data_extenso(quando)} · {quando:%H}h", "" if video else f"{i}/{total}")
        # mede o texto num rascunho para o cartão abraçar o conteúdo
        rascunho = ImageDraw.Draw(Image.new("RGB", (W, H)))
        alt = bloco(rascunho, (0, 0), s["texto"], "reg", 44, TINTA, W - 2 * M - 80, H - 150 - 360 - 40, 1.45, 30)
        d.rounded_rectangle([M - 8, 310, W - M + 8, 310 + alt + 90], radius=24, fill=CARTAO, outline=LINHA, width=2)
        bloco(d, (M + 40, 360), s["texto"], "reg", 44, TINTA, W - 2 * M - 80, H - 150 - 360 - 40, 1.45, 30)
        arquivos.append(salvar(img, saida, f"resumo-{i}.png"))

    img, d = tela("No site", MARCA, f"{data_extenso(quando)}", "" if video else f"{total}/{total}")
    usado = bloco(d, (M, 330), "Tudo isso e muito mais, atualizado de hora em hora", "serif", 72, TINTA, W - 2 * M, 300, 1.15, 50)
    itens = ["Manchetes de 11 veículos confiáveis", "Bolsa, dólar, ações e fundos imobiliários",
             "Cotações de soja, milho, boi e café", "Tabelas do Brasileirão e das maiores ligas",
             "Contas da União e de cada estado"]
    y = 330 + usado + 70
    for t in itens:
        d.ellipse([M, y + 12, M + 18, y + 30], fill=MARCA)
        d.text((M + 40, y), t, font=fonte("reg", 36), fill=TINTA)
        y += 70
    d.rounded_rectangle([M, H - 290, W - M, H - 160], radius=65, fill=MARCA)
    f = fonte("bold", 40)
    t = "Acesse pelo link na bio"
    d.text(((W - d.textlength(t, font=f)) / 2, H - 250), t, font=f, fill="#ffffff")
    arquivos.append(salvar(img, saida, f"resumo-{total}.png"))
    return arquivos

# ---------------------------------------------------------------- mercado
def cards_mercado(saida):
    m = ler("mercado.json")
    quando = datetime.strptime(m["atualizado_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(BRT)
    img, d = tela("Mercado", COR_SECAO["Mercado"], f"{data_extenso(quando)} · {quando:%H:%M}")
    d.text((M, 292), "Como fechou o mercado", font=fonte("serif", 64), fill=TINTA)

    ind = [i for i in m["indicadores"] if i.get("valor") is not None][:6]
    cw, ch, gap = (W - 2 * M - 24) / 2, 120, 16
    y0 = 392
    for k, i in enumerate(ind):
        x = M + (k % 2) * (cw + 24)
        y = y0 + (k // 2) * (ch + gap)
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=CARTAO, outline=LINHA, width=2)
        d.text((x + 28, y + 20), i["nome"], font=fonte("semi", 26), fill=TINTA2)
        if i["tipo"] == "pts": v = num(i["valor"], 0) + " pts"
        elif i["tipo"] == "pct": v = num(i["valor"]) + "%"
        elif i["valor"] > 1000: v = "R$ " + num(i["valor"], 0)
        else: v = "R$ " + num(i["valor"], 4 if i["valor"] < 10 else 2)
        d.text((x + 28, y + 62), v, font=fonte("bold", 40), fill=TINTA)
        if i.get("var") is not None:
            t = var_txt(i["var"]); f = fonte("semi", 26)
            tx = x + cw - 28 - d.textlength(t, font=f)
            d.text((tx, y + 26), t, font=f, fill=cor_var(i["var"]))
            seta(d, tx - 28, y + 31, i["var"])

    acoes = {a["ticker"]: a for a in m.get("maiores", []) + m.get("acoes", []) if a.get("var") is not None}
    ordem = sorted(acoes.values(), key=lambda a: a["var"], reverse=True)
    y = y0 + 3 * (ch + gap) + 24
    for col, (titulo, lista) in enumerate((("Maiores altas", ordem[:5]), ("Maiores baixas", ordem[::-1][:5]))):
        x = M + col * (cw + 24)
        d.text((x, y), titulo, font=fonte("bold", 30), fill=TINTA)
        for j, a in enumerate(lista):
            yy = y + 52 + j * 52
            d.line([x, yy - 8, x + cw, yy - 8], fill=LINHA, width=2)
            d.text((x, yy + 2), a["ticker"], font=fonte("semi", 30), fill=TINTA)
            t = var_txt(a["var"]); f = fonte("semi", 30)
            d.text((x + cw - d.textlength(t, font=f), yy + 2), t, font=f, fill=cor_var(a["var"]))
    d.text((M, H - 146), "Cotações com atraso, apenas informativas. Não é recomendação de investimento.",
           font=fonte("reg", 22), fill=TINTA2)
    return [salvar(img, saida, "mercado-1.png")]

# ---------------------------------------------------------------- agro
AGRO_ITENS = ["Soja (Paranaguá)", "Milho (Campinas)", "Boi gordo (SP)", "Café arábica", "Café robusta",
              "Trigo (PR)", "Açúcar cristal (SP)", "Algodão em pluma", "Frango congelado", "Suíno vivo"]

def cards_agro(saida):
    a = ler("agro.json")
    por_nome = {i["nome"]: i for i in a["indicadores"] if i.get("preco") is not None}
    itens = [por_nome[n] for n in AGRO_ITENS if n in por_nome][:10]
    data = itens[0]["data"] if itens else ""
    img, d = tela("Agro", COR_SECAO["Agro"], f"Fechamento de {data}")
    d.text((M, 292), "Cotações do agro", font=fonte("serif", 64), fill=TINTA)
    y = 404
    d.rounded_rectangle([M - 8, y - 16, W - M + 8, y + len(itens) * 70 + 8], radius=20, fill=CARTAO, outline=LINHA, width=2)
    for k, i in enumerate(itens):
        yy = y + k * 70
        if k: d.line([M + 20, yy - 4, W - M - 20, yy - 4], fill=LINHA, width=2)
        d.text((M + 24, yy + 6), i["nome"], font=fonte("semi", 30), fill=TINTA)
        d.text((M + 24, yy + 42), i["un"], font=fonte("reg", 19), fill=TINTA2)
        t = var_txt(i["var"]) if i.get("var") is not None else ""
        f = fonte("semi", 26)
        vx = W - M - 24 - 150
        d.text((W - M - 24 - d.textlength(t, font=f), yy + 14), t, font=f, fill=cor_var(i.get("var")))
        p = "R$ " + num(i["preco"]) if i["un"].startswith("R$") else num(i["preco"])
        f = fonte("bold", 32)
        d.text((vx - 24 - d.textlength(p, font=f), yy + 10), p, font=f, fill=TINTA)
    d.text((M, H - 150), "Fonte: Cepea/Esalq, via Notícias Agrícolas. Apenas informativo.", font=fonte("reg", 22), fill=TINTA2)
    return [salvar(img, saida, "agro-1.png")]

def salvar(img, saida, nome):
    os.makedirs(saida, exist_ok=True)
    caminho = os.path.join(saida, nome)
    img.save(caminho, "PNG", optimize=True)
    return caminho

GERADORES = {"resumo": cards_resumo, "mercado": cards_mercado, "agro": cards_agro}

if __name__ == "__main__":
    tipo = sys.argv[1] if len(sys.argv) > 1 else "resumo"
    for c in GERADORES[tipo](sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "instagram")):
        print(c)
