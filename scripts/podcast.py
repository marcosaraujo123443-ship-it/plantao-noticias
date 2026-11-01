#!/usr/bin/env python3
"""Podcast "Resumo do Plantão" (para Spotify e outros apps): guarda cada narração como episódio e gera podcast.xml.
Os MP3 ficam nas Releases do GitHub (uma por mês: audio-AAAA-MM); a lista fica em podcast.json.
    python3 scripts/podcast.py nome          -> imprime tag e nome do arquivo do episódio atual
    python3 scripts/podcast.py registrar TAG ARQUIVO   -> acrescenta o episódio e refaz o feed
    python3 scripts/podcast.py capa          -> gera podcast-capa.jpg (3000x3000)"""
import html, json, os, sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

BRT = timezone(timedelta(hours=-3))
SITE = "https://plantaoinforma.com.br/"
REPO = os.environ.get("GITHUB_REPOSITORY", "marcosaraujo123443-ship-it/plantao-noticias")
EMAIL = "marquinhosbahia8877@gmail.com"
MAX_FEED = 300   # episódios no feed (os arquivos antigos continuam guardados nas Releases)
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
e = html.escape

def ler(nome, padrao):
    try: return json.load(open(nome, encoding="utf-8"))
    except Exception: return padrao

def quando(r):
    return datetime.strptime(r["gerado_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(BRT)

def nome():
    q = quando(ler("resumo.json", {}))
    print(f"audio-{q:%Y-%m} plantao-{q:%Y%m%d-%H%M}.mp3")

def registrar(tag, arquivo):
    r, a = ler("resumo.json", {}), ler("audio.json", {})
    q = quando(r)
    eps = ler("podcast.json", {"episodios": []})
    guid = f"plantao-{r['gerado_utc']}"
    desc = r["abertura"] + "\n\n" + "\n\n".join(f"{s['secao']}: {s['texto']}" for s in r["secoes"]) + \
           f"\n\nNotícias, cotações e tabelas atualizadas de hora em hora em {SITE}"
    ep = {"guid": guid, "titulo": f"Resumo do Plantão · {DIAS[q.weekday()]}, {q.day} de {MESES[q.month - 1]}, {q:%H}h",
          "descricao": desc, "data": r["gerado_utc"], "duracao": a.get("duracao"),
          "url": f"https://github.com/{REPO}/releases/download/{tag}/{arquivo}", "bytes": os.path.getsize(arquivo)}
    eps["episodios"] = [x for x in eps["episodios"] if x["guid"] != guid] + [ep]
    eps["episodios"].sort(key=lambda x: x["data"])
    json.dump(eps, open("podcast.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    feed(eps["episodios"])
    print("Episódio registrado:", ep["titulo"])

def hms(s):
    s = int(s or 0); return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"

def feed(episodios):
    itens = []
    for x in reversed(episodios[-MAX_FEED:]):
        dt = datetime.strptime(x["data"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        itens.append(f"""  <item>
    <title>{e(x['titulo'])}</title>
    <description>{e(x['descricao'])}</description>
    <itunes:summary>{e(x['descricao'])}</itunes:summary>
    <enclosure url="{e(x['url'])}" length="{x['bytes']}" type="audio/mpeg"/>
    <guid isPermaLink="false">{e(x['guid'])}</guid>
    <pubDate>{format_datetime(dt)}</pubDate>
    <itunes:duration>{hms(x['duracao'])}</itunes:duration>
    <itunes:episodeType>full</itunes:episodeType>
    <itunes:explicit>false</itunes:explicit>
    <link>{SITE}</link>
  </item>""")
    sobre = ("O Resumo do Plantão traz, três vezes por dia, as principais notícias de política, inteligência artificial, "
             "futebol, agro, mercado, concursos, ciência e saúde em poucos minutos. Resumo escrito e narrado por "
             f"inteligência artificial a partir das manchetes do Plantão Informa ({SITE}), com veículos confiáveis.")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>Resumo do Plantão · Plantão Informa</title>
  <link>{SITE}</link>
  <atom:link href="{SITE}podcast.xml" rel="self" type="application/rss+xml"/>
  <language>pt-br</language>
  <description>{e(sobre)}</description>
  <itunes:summary>{e(sobre)}</itunes:summary>
  <itunes:author>Plantão Informa</itunes:author>
  <itunes:owner><itunes:name>Plantão Informa</itunes:name><itunes:email>{EMAIL}</itunes:email></itunes:owner>
  <itunes:image href="{SITE}podcast-capa.jpg"/>
  <image><url>{SITE}podcast-capa.jpg</url><title>Resumo do Plantão · Plantão Informa</title><link>{SITE}</link></image>
  <itunes:category text="News"><itunes:category text="Daily News"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:type>episodic</itunes:type>
  <copyright>Plantão Informa</copyright>
{chr(10).join(itens)}
</channel>
</rss>
"""
    open("podcast.xml", "w", encoding="utf-8").write(xml)

def capa():
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import instagram_cards as c
    W = 3000
    img = Image.new("RGB", (W, W), c.FAIXA); d = ImageDraw.Draw(img)
    d.rectangle([0, W - 260, W, W], fill=c.MARCA)
    logo = Image.open(os.path.join(c.RAIZ, "icon-512.png")).convert("RGBA").resize((1050, 1050), Image.LANCZOS)
    img.paste(logo, ((W - 1050) // 2, 330), logo)
    for txt, f, y, cor in (("Resumo do", c.fonte("serif", 300), 1520, "#ffffff"), ("Plantão", c.fonte("serif", 420), 1830, "#ffffff"),
                           ("As notícias do dia em poucos minutos", c.fonte("semi", 120), 2380, "#c9d3e3"),
                           ("plantaoinforma.com.br", c.fonte("bold", 120), W - 200, "#ffffff")):
        d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=cor)
    img.save("podcast-capa.jpg", quality=88)
    print("podcast-capa.jpg", os.path.getsize("podcast-capa.jpg") // 1024, "KB")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "nome": nome()
    elif cmd == "registrar": registrar(sys.argv[2], sys.argv[3])
    elif cmd == "capa": capa()
    else: print(__doc__)
