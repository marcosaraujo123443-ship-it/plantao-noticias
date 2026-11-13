#!/usr/bin/env python3
"""Cards dos indicadores adicionais (indicadores2.json): número em destaque, selo, três números de apoio e gráfico.
    python3 scripts/instagram_dados.py caged|inadimplencia|... [pasta_saida]"""
import os, sys
from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as c
from instagram_contas import tiles

COR = c.COR_SECAO["Mercado"]
TOM = {"bom": c.SOBE, "ruim": c.DESCE, "neutro": c.TINTA}
FUNDO_SELO = {"bom": "#e3f3e8", "ruim": "#fbe4e6", "neutro": "#e7ecf3"}
IDS = ["focus", "caged", "industria", "varejo", "inadimplencia", "contas_externas", "incc", "payroll", "fed", "bce", "cpi_eua", "pce_eua", "pib_eua"]

def ler(): return c.ler("indicadores2.json")["itens"]
def ultimo(k, itens=None):
    it = (itens or ler()).get(k)
    return f"{k} {it['ref']}" if it else None

def fmt_num(tipo):
    casas = {"num0": 0, "num1": 1, "num2": 2}.get(tipo, 1)
    return lambda v: c.num(v, casas)

def grafico(d, x0, y0, w, h, dados, fmt, base_zero=True, completo=False):
    rot = [r for r, _ in dados]; val = [v for _, v in dados]
    if base_zero: vmax, vmin = max(val + [0]), min(val + [0])
    else:
        lo, hi = min(val), max(val); pad = (hi - lo) * 0.35 or abs(hi) * 0.05 or 1
        vmax, vmin = hi, lo - pad
    faixa = (vmax - vmin) or 1
    zero = y0 + h * vmax / faixa if base_zero else y0 + h
    n = len(val); passo = w / n; larg = passo * 0.64
    if base_zero: d.line([x0, zero, x0 + w, zero], fill=c.LINHA, width=2)
    for i, (r, v) in enumerate(zip(rot, val)):
        cx = x0 + passo * i + passo / 2
        topo = zero - h * (v - (0 if base_zero else vmin)) / faixa
        ult = i == n - 1
        cor = (c.FAIXA if ult else ("#e3a4ab" if v < 0 and base_zero else "#a9c4b2" if base_zero else "#a9bad0"))
        y1, y2 = sorted([topo, zero]); y2 = max(y2, y1 + 3)
        d.rounded_rectangle([cx - larg / 2, y1, cx + larg / 2, y2], radius=5, fill=cor)
        t = fmt(v); f = c.fonte("bold" if ult else "semi", 19 if n > 8 else 22)
        ty = y1 - 27 if v >= 0 or not base_zero else y2 + 5
        d.text((cx - d.textlength(t, font=f) / 2, ty), t, font=f, fill=c.TINTA)
        f = c.fonte("bold" if ult else "reg", 18 if n > 8 else 21)
        r = r if completo else r.split("/")[0]
        d.text((cx - d.textlength(r, font=f) / 2, y0 + h + (36 if base_zero and vmin < 0 else 14)), r, font=f,
               fill=c.TINTA if ult else c.TINTA2)

def card(k, itens=None, pagina=None):
    it = (itens or ler())[k]
    img, d = c.tela(it["tag"], COR, it["ref_txt"], pagina)
    c.bloco(d, (c.M, 290), it["titulo"], "serif", 58, c.TINTA, c.W - 2 * c.M, 70, 1.1, 44)
    d.text((c.M, 362), it["sub"], font=c.fonte("semi", 25), fill=c.TINTA2)
    # número em destaque e selo
    tam = 150
    while d.textlength(it["valor"], font=c.fonte("bold", tam)) > c.W - 2 * c.M - (300 if it.get("selo") else 0) and tam > 80: tam -= 6
    fv = c.fonte("bold", tam)
    d.text((c.M - 4, 404), it["valor"], font=fv, fill=TOM.get(it["cor"], c.TINTA))
    xs = c.M + d.textlength(it["valor"], font=fv) + 28
    if it.get("selo"):
        txt, tom = it["selo"]; fs = c.fonte("bold", 21); tw = d.textlength(txt, font=fs)
        if xs + tw + 32 > c.W - c.M: xs, ys = c.M, 404 + tam + 22
        else: ys = 404 + tam * 0.30
        d.rounded_rectangle([xs, ys, xs + tw + 32, ys + 42], radius=21, fill=FUNDO_SELO[tom])
        d.text((xs + 16, ys + 9), txt, font=fs, fill=TOM[tom] if tom != "neutro" else c.TINTA)
    y = 404 + tam + 30 + (56 if it.get("selo") and xs == c.M else 0)
    y += c.bloco(d, (c.M, y), it["frase"], "reg", 27, c.TINTA2, c.W - 2 * c.M, 80, 1.35, 22) + 26
    tiles(d, y, [(a, b, s, c.TINTA) for a, b, s in it["apoio"]])
    y += 196
    d.text((c.M, y), it["graf_tit"].upper(), font=c.fonte("bold", 22), fill=c.TINTA2)
    gy = y + 66; gh = 1350 - 108 - 150 - gy
    grafico(d, c.M, gy, c.W - 2 * c.M, max(gh, 120), it["graf"], fmt_num(it.get("graf_fmt")), it.get("base_zero", True), it.get("graf_rot") == "completo")
    c.bloco(d, (c.M, 1350 - 108 - 92), it["porque"], "semi", 24, COR, c.W - 2 * c.M, 66, 1.3, 20)
    d.text((c.M, 1350 - 108 - 30), "Fonte: " + it["fonte"], font=c.fonte("reg", 19), fill="#8a96ab")
    return img

def gerar(k, saida):
    return [c.salvar(card(k), saida, "economia-1.png")]

def legenda_e_alt(k):
    it = ler()[k]
    emoji = {"caged": "👷", "payroll": "🇺🇸", "inadimplencia": "💳", "contas_externas": "🌎", "incc": "🏗️", "industria": "🏭",
             "varejo": "🛒", "focus": "🔮", "fed": "🏦", "bce": "🇪🇺", "cpi_eua": "🇺🇸", "pce_eua": "🇺🇸", "pib_eua": "🇺🇸"}.get(k, "📊")
    apoio = "\n".join(f"• {a}: {b} ({s})" if s else f"• {a}: {b}" for a, b, s in it["apoio"])
    selo = f" · {it['selo'][0].replace('▲ ', '').replace('▼ ', '').replace('= ', '').capitalize()}" if it.get("selo") else ""
    leg = (f"{emoji} {it['titulo']}: {it['valor']}{selo}\n\n{it['valor']} {it['frase']}\n\n{apoio}\n\n"
           f"💡 {it['porque']}\n\n🔗 Indicadores, cotações e notícias de economia no site: link na bio.\n\nFonte: {it['fonte']}.")
    alt = (f"{it['titulo']}, {it['ref_txt']}: {it['valor']}. {it['frase']} " + " ".join(f"{a}: {b}." for a, b, _ in it["apoio"]) +
           f" Gráfico: {it['graf_tit']}, " + ", ".join(f"{r} {v}" for r, v in it["graf"]) + f". Fonte: {it['fonte']}.")
    return ultimo(k), leg, [alt]

TAGS = {}
def tags(k):
    try: return ler()[k]["tags"]
    except Exception: return "#economia"

if __name__ == "__main__":
    k = sys.argv[1] if len(sys.argv) > 1 else "caged"
    saida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(c.RAIZ, "instagram")
    print(c.salvar(card(k), saida, f"dados-{k}.png"))
    print(legenda_e_alt(k)[1])
