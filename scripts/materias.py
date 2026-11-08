#!/usr/bin/env python3
"""Matérias próprias do Plantão Informa (análises, artigos), escritas em materias/*.md:
cabeçalho "campo: valor" (titulo, subtitulo, data, autor, rotulo, editoria), uma linha "---" e o texto
(parágrafos separados por linha em branco; "## " para intertítulos)."""
import glob, html, os, re, unicodedata
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e = html.escape

def slug(s):
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def inline(t):
    t = e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)

def corpo_html(texto):
    out = []
    for bloco in re.split(r"\n\s*\n", texto.strip()):
        b = bloco.strip()
        img = re.match(r"!\[(.*?)\]\(([\w.-]+)\)$", b)
        if img:
            out.append(f'<figure><img src="{img.group(2)}" alt="{e(img.group(1))}" loading="lazy" width="1200" height="640">'
                       f'<figcaption>{e(img.group(1))}</figcaption></figure>'); continue
        if b.startswith("## "): out.append(f"<h2>{inline(b[3:])}</h2>")
        elif b.startswith("### "): out.append(f"<h3>{inline(b[4:])}</h3>")
        elif all(l.strip().startswith("- ") for l in b.splitlines()):
            out.append("<ul>" + "".join(f"<li>{inline(l.strip()[2:])}</li>" for l in b.splitlines()) + "</ul>")
        else: out.append(f"<p>{inline(' '.join(b.splitlines()))}</p>")
    return "\n".join(out)

def ler_materias(pasta="materias"):
    lista = []
    for arq in sorted(glob.glob(os.path.join(RAIZ, pasta, "*.md"))):
        bruto = open(arq, encoding="utf-8").read()
        cab, _, texto = bruto.partition("\n---\n")
        m = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in cab.splitlines() if ":" in l)}
        if not m.get("titulo") or not texto.strip(): continue
        nome = os.path.basename(arq)[:-3]
        m["slug"] = slug(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", nome))
        m["dt"] = datetime.fromisoformat(m.get("data") or nome[:10])
        m["texto"] = texto
        m["html"] = corpo_html(texto)
        m["palavras"] = len(re.findall(r"\w+", texto))
        m["minutos"] = max(1, round(m["palavras"] / 200))
        m.setdefault("rotulo", "Análise"); m.setdefault("autor", "Redação Plantão Informa")
        lista.append(m)
    return sorted(lista, key=lambda m: m["dt"], reverse=True)

def imagem(m, destino):
    """Imagem de compartilhamento 1200x630 da matéria."""
    import sys
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import instagram_cards as c
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), c.PAPEL); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 150], fill=c.FAIXA)
    img.paste(c.logo(100), (60, 25), c.logo(100))
    d.text((180, 46), "Plantão", font=c.fonte("serif-semi", 46), fill=c.FAIXA_TINTA)
    d.text((180 + d.textlength("Plantão ", font=c.fonte("serif-semi", 46)), 46), "Informa", font=c.fonte("serif", 46), fill=c.FAIXA_TINTA)
    d.rectangle([0, 150, W, 158], fill=c.MARCA)
    d.rectangle([60, 200, 70, 232], fill=c.MARCA)
    d.text((86, 200), m["rotulo"].upper(), font=c.fonte("bold", 26), fill=c.MARCA)
    c.bloco(d, (60, 254), m["titulo"], "serif", 54, c.TINTA, W - 120, 300, 1.14, 40)
    d.text((60, H - 62), "plantaoinforma.com.br", font=c.fonte("semi", 24), fill=c.TINTA2)
    img.save(destino, "PNG", optimize=True)

if __name__ == "__main__":
    pasta = os.path.join(RAIZ, "materias", "img"); os.makedirs(pasta, exist_ok=True)
    for m in ler_materias():
        arq = os.path.join(pasta, m["slug"] + ".png")
        if not os.path.exists(arq): imagem(m, arq); print("imagem:", arq)
