#!/usr/bin/env python3
"""Imagem de compartilhamento (og.png, 1200x630) com a abertura do Resumo do Plantão; refeita a cada atualização."""
import json, os, sys
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as c

W, H = 1200, 630
BRT = timezone(timedelta(hours=-3))

def main(saida="og.png"):
    try:
        r = json.load(open(os.path.join(c.RAIZ, "resumo.json"), encoding="utf-8"))
        texto, quando = r["abertura"], datetime.strptime(r["gerado_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(BRT)
    except Exception:
        texto, quando = "As notícias mais importantes do dia, de veículos confiáveis, atualizadas de hora em hora.", datetime.now(BRT)
    img = Image.new("RGB", (W, H), c.PAPEL)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 150], fill=c.FAIXA)
    img.paste(c.logo(100), (60, 25), c.logo(100))
    d.text((180, 46), "Plantão", font=c.fonte("serif-semi", 46), fill=c.FAIXA_TINTA)
    d.text((180 + d.textlength("Plantão ", font=c.fonte("serif-semi", 46)), 46), "Informa", font=c.fonte("serif", 46), fill=c.FAIXA_TINTA)
    q = f"{c.data_extenso(quando)} · {quando:%H}h"
    f = c.fonte("semi", 28); d.text((W - 60 - d.textlength(q, font=f), 62), q, font=f, fill="#b9c4d6")
    d.rectangle([0, 150, W, 158], fill=c.MARCA)
    d.rectangle([60, 206, 70, 238], fill=c.MARCA)
    d.text((86, 206), "RESUMO DO PLANTÃO", font=c.fonte("bold", 26), fill=c.MARCA)
    c.bloco(d, (60, 262), texto, "serif", 58, c.TINTA, W - 120, 270, 1.16, 36)
    d.text((60, H - 62), "plantaoinforma.com.br · notícias, cotações e tabelas de hora em hora", font=c.fonte("semi", 24), fill=c.TINTA2)
    img.save(os.path.join(c.RAIZ, saida), "PNG", optimize=True)
    print("og.png gerada")

if __name__ == "__main__":
    main()
