#!/usr/bin/env python3
"""Explica Plantão: transforma mudanças em leis, tributos e direitos em guias práticos de perguntas e respostas.
Monitora o Diário Oficial da União (seção 1: leis, medidas provisórias, decretos, instruções normativas), a Receita
Federal, o Planalto, o STF, o STJ e a Câmara; escolhe a mudança de maior impacto prático do dia, lê o texto da fonte
e pede ao Gemini um guia escrito só com o que está nele. Uma trava confere se cada número do guia aparece na fonte.
Grava explica/AAAA-MM-DD-slug.md (mesmo formato das análises) e explica_registro.json.
    python3 scripts/explicador.py           (EXPLICA_FORCAR=1 ignora o limite de um guia por dia)"""
import html, json, os, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resumo import perguntar
from materias import slug
from noticias import data_iso, limpa

BRT = timezone(timedelta(hours=-3))
UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoNoticias/1.0)"}
PASTA = "explica"
FEEDS = [("Receita Federal", "https://www.gov.br/receitafederal/pt-br/assuntos/noticias/ultimas-noticias/RSS"),
         ("Planalto", "https://www.gov.br/planalto/pt-br/acompanhe-o-planalto/noticias/RSS"),
         ("STF", "https://noticias.stf.jus.br/feed/"),
         ("STJ", "https://res.stj.jus.br/hrestp-c-portalp/RSS.xml"),
         ("Agência Câmara", "https://www.camara.leg.br/noticias/rss/dinamico/DIREITO-E-JUSTICA"),
         ("Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/justica/feed.xml")]
DOU_TIPOS = {"Lei", "Lei Complementar", "Medida Provisória", "Decreto", "Emenda Constitucional", "Instrução Normativa", "Resolução", "Portaria"}
DOU_ORGAOS = re.compile(r"Presidência da República|Receita Federal|Previdência|INSS|Trabalho e Emprego|Fazenda|Conselho Monetário|Banco Central|Defesa do Consumidor|Saúde Suplementar|ANS|Aneel|Anatel", re.I)

def baixar(url, n=2_000_000):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read(n).decode("utf-8", "ignore")
    except Exception:   # alguns portais (como o do DOU) recusam o urllib e aceitam o curl
        import subprocess
        r = subprocess.run(["curl", "-sfL", "-m", "60", "-A", UA["User-Agent"], url], capture_output=True)
        if r.returncode != 0: raise
        return r.stdout[:n].decode("utf-8", "ignore")

def texto_pagina(url):
    h = baixar(url)
    m = re.search(r'<div class="texto-dou">(.*?)</div>\s*</div>', h, re.S)   # ato do DOU
    if m: h = m.group(1)
    else:
        h = re.sub(r"(?is)<(script|style|nav|header|footer|aside|form)[^>]*>.*?</\1>", " ", h)
        m = re.search(r"(?is)<article[^>]*>(.*?)</article>", h) or re.search(r'(?is)<div[^>]+(?:id|class)="[^"]*(?:content-core|conteudo|entry-content|texto)[^"]*"[^>]*>(.*)', h)
        if m: h = m.group(1)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"\s+", " ", t).strip()[:16000]

def dou(agora):
    """Atos de alto impacto da seção 1 do DOU de hoje (e de ontem, se hoje ainda não saiu)."""
    out = []
    for d in (agora, agora - timedelta(days=1)):
        try: h = baixar(f"https://www.in.gov.br/leiturajornal?data={d:%d-%m-%Y}&secao=do1", 8_000_000)
        except Exception as ex: print("DOU:", ex); continue
        m = re.search(r'<script id="params" type="application/json">\s*(\{.*?\})\s*</script>', h, re.S)
        if not m: continue
        for a in json.loads(m.group(1)).get("jsonArray", []):
            tipo, org = a.get("artType", ""), a.get("hierarchyStr", "")
            if tipo not in DOU_TIPOS: continue
            if tipo in ("Resolução", "Portaria", "Instrução Normativa") and not DOU_ORGAOS.search(org): continue
            if tipo == "Portaria" and not re.search(r"Ministro|Interministerial", a.get("content", "") + org, re.I): continue
            out.append({"fonte": "Diário Oficial da União", "titulo": a.get("title", ""), "resumo": (a.get("content") or "")[:400],
                        "link": f"https://www.in.gov.br/web/dou/-/{a.get('urlTitle')}", "orgao": org})
        if out: break
    return out

def feeds(agora):
    limite = (agora - timedelta(hours=36)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for fonte, url in FEEDS:
        try: raiz = ET.fromstring(baixar(url).encode())
        except Exception as ex: print(fonte, ex); continue
        for el in raiz.iter():
            if el.tag.rsplit("}", 1)[-1] not in ("item", "entry"): continue
            c = {}
            for x in el:
                n = x.tag.rsplit("}", 1)[-1]
                if n == "link": c.setdefault("link", (x.text or "").strip() or x.get("href", ""))
                elif n in ("title", "description", "summary", "pubDate", "date", "published", "updated"): c.setdefault(n, x.text or "")
            dt = data_iso(c.get("pubDate") or c.get("date") or c.get("published") or c.get("updated"))
            if not dt or dt < limite or not c.get("link"): continue
            out.append({"fonte": fonte, "titulo": limpa(c.get("title")), "resumo": limpa(c.get("description") or c.get("summary"))[:400], "link": c["link"]})
    return out

ESCOLHA = """Você é editor do "Explica Plantão", do site Plantão Informa, que transforma mudanças em leis, tributos, regras
trabalhistas, previdência, benefícios e direitos em guias práticos para o cidadão e para pequenas empresas. Recebe uma
lista numerada de atos oficiais e notícias de órgãos públicos e tribunais. Escolha UM item que cria, muda ou esclarece
uma regra com impacto prático amplo (impostos, salário, FGTS, aposentadoria, benefícios sociais, consumidor, contratos,
trânsito, saúde suplementar etc.). Evite atos internos, nomeações, casos individuais sem efeito geral, eventos e
campanhas. Se nenhum servir, responda {"n": 0}. Responda só com JSON: {"n": 3, "tema": "uma frase"}"""

GUIA = """Você é editor do "Explica Plantão", do site Plantão Informa: guias que explicam a leigos, com profundidade, o
que muda com uma lei, norma, decisão judicial ou regra tributária e quais os impactos prováveis na vida das pessoas,
das empresas e das contas públicas. Escreva em português do Brasil, frases claras, explicando todo termo técnico.
Recebe o texto de uma fonte oficial (ato do Diário Oficial, nota de órgão público ou notícia de tribunal).

Regras rígidas:
- FATOS (o que a regra diz, quem decidiu, datas, valores, prazos, números, nomes): use SOMENTE o que está no texto.
  Não invente nem complete. Se faltar, diga "a fonte não informa".
- IMPACTOS: você pode e deve raciocinar sobre as consequências práticas prováveis, com base no seu conhecimento de
  como o sistema funciona no Brasil (Judiciário, tributos, trabalho, Previdência, consumo), mas:
  * escreva como possibilidade ("tende a", "pode", "deve facilitar"), nunca como fato consumado;
  * NÃO use nenhum número, valor, data, percentual ou nome que não esteja no texto da fonte;
  * mostre os dois lados quando houver (quem ganha, quem perde, riscos, efeitos colaterais).
- Nada de conselho jurídico individual; explique a regra e o que costuma estar em jogo. Tom neutro e apartidário.

Responda só com JSON:
{"titulo": "título objetivo, até 90 caracteres, em forma de pergunta ou 'o que muda com'",
 "subtitulo": "1 ou 2 frases com o essencial e por que importa",
 "tldr": ["4 ou 5 frases curtas: o que mudou, para quem, desde quando, principal impacto"],
 "contexto": "2 a 4 frases: como era antes e qual problema a regra ou decisão resolve (só o que o texto permite afirmar; o resto como explicação geral, sem números)",
 "o_que_muda": ["3 a 6 pontos objetivos do que efetivamente muda, segundo o texto"],
 "impactos": {"pessoas": "2 a 4 frases sobre efeitos prováveis para o cidadão comum",
              "empresas": "2 a 4 frases para empresas, empregadores, bancos ou profissionais (ou 'Efeito pequeno ou indireto para empresas.')",
              "governo": "1 a 3 frases sobre efeitos para o governo, a Justiça ou as contas públicas (ou 'Efeito pequeno ou indireto.')"},
 "exemplo": "um exemplo prático em 2 a 4 frases, com uma pessoa ou empresa fictícia em situação típica, sem números que não estejam no texto",
 "perguntas": [{"p": "pergunta que o leitor faria", "r": "resposta completa de 2 a 4 frases"}],
 "o_que_fazer": ["2 a 4 orientações práticas gerais: o que conferir, onde buscar informação oficial, quando procurar um profissional"],
 "quem": "quem é afetado, em 1 ou 2 frases",
 "quando": "a partir de quando vale, como está no texto, ou 'a fonte não informa'",
 "atencao": "limites: o que ainda depende de regulamentação ou de outras decisões, exceções e o que a fonte não esclarece"}
Escreva de 6 a 9 perguntas, das mais práticas para as mais específicas, sem repetir o que já está em "o_que_muda"."""

NUM = re.compile(r"\d+(?:[.,]\d+)*")
def numeros_ok(guia, fonte):
    """Trava: todo número do guia precisa estar na fonte (ignora os de 1 dígito, que aparecem em ordinais e listas)."""
    fonte_n = {n.replace(".", "").replace(",", "") for n in NUM.findall(fonte)}
    txt = json.dumps(guia, ensure_ascii=False)
    faltam = sorted({n for n in NUM.findall(txt) if len(n.replace(".", "").replace(",", "")) > 1
                     and n.replace(".", "").replace(",", "") not in fonte_n})
    return faltam

def main():
    agora = datetime.now(BRT)
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave: print("Sem GEMINI_API_KEY; Explica Plantão desligado."); return
    try: reg = json.load(open("explica_registro.json", encoding="utf-8"))
    except Exception: reg = {"links": [], "ultimo": ""}
    if reg.get("ultimo") == agora.date().isoformat() and not os.environ.get("EXPLICA_FORCAR"):
        print("Guia de hoje já publicado."); return
    cand = [c for c in dou(agora) + feeds(agora) if c["link"] not in reg["links"] and c["titulo"]]
    print(len(cand), "candidatos")
    if not cand: return
    cand = cand[:80]
    lista = "\n".join(f"{k}. [{c['fonte']}{' · ' + c['orgao'] if c.get('orgao') else ''}] {c['titulo']}. {c['resumo']}" for k, c in enumerate(cand, 1))
    texto, _ = perguntar({"temperature": 0.1, "max_tokens": 512, "messages": [{"role": "system", "content": ESCOLHA}, {"role": "user", "content": lista}]}, chave)
    esc = json.loads(re.search(r"\{.*\}", texto, re.S).group(0))
    k = int(esc.get("n") or 0)
    if not 1 <= k <= len(cand): print("Nenhum item com impacto prático hoje."); return
    c = cand[k - 1]; print("Escolhido:", c["titulo"], "·", c["link"])
    fonte = texto_pagina(c["link"])
    if len(fonte) < 400: raise SystemExit("Texto da fonte curto demais: " + fonte[:200])
    guia, modelo = escrever(c, fonte, chave)
    reg["links"] = (reg["links"] + [c["link"]])[-400:]
    if not guia:
        json.dump(reg, open("explica_registro.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        raise SystemExit("Guia descartado pela trava de números.")
    nome = f"{agora:%Y-%m-%d}-{slug(guia['titulo'])[:70].strip('-')}"
    gravar(nome, guia, c, agora, modelo)
    reg["ultimo"] = agora.date().isoformat()
    json.dump(reg, open("explica_registro.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Guia publicado:", nome)

def escrever(c, fonte, chave):
    """Pede o guia (até 3 tentativas) e só aceita se passar na trava de números."""
    faltam, modelo = [], None
    for tentativa in range(3):
        pedido = f"Fonte: {c['fonte']}\nEndereço: {c['link']}\nTítulo: {c['titulo']}\n\nTexto:\n{fonte}"
        if faltam: pedido += "\n\nATENÇÃO: na versão anterior apareceram números que não estão no texto: " + ", ".join(faltam) + ". Reescreva sem eles."
        texto, modelo = perguntar({"temperature": 0.2, "max_tokens": 9000, "messages": [{"role": "system", "content": GUIA}, {"role": "user", "content": pedido}]}, chave)
        try: g = json.loads(re.search(r"\{.*\}", texto, re.S).group(0))
        except Exception: print("Resposta fora do formato"); continue
        faltam = numeros_ok(g, fonte + " " + c["titulo"])
        if not faltam and g.get("titulo") and len(g.get("perguntas", [])) >= 5 and g.get("impactos"): return g, modelo
        print("Trava de números:", faltam)
    return None, modelo

def gravar(nome, guia, c, quando, modelo):
    os.makedirs(PASTA, exist_ok=True)
    lim = lambda t: str(t or "").strip()
    tl = " | ".join(lim(x).replace("|", "/") for x in guia.get("tldr", []) if lim(x))
    corpo = []
    if lim(guia.get("contexto")): corpo += ["## Entenda o contexto", lim(guia["contexto"])]
    if guia.get("o_que_muda"): corpo += ["## O que muda", "\n".join(f"- {lim(x)}" for x in guia["o_que_muda"] if lim(x))]
    imp = guia.get("impactos") or {}
    if any(lim(v) for v in imp.values()):
        corpo += ["## Os impactos prováveis"]
        for k, rot in (("pessoas", "Para você"), ("empresas", "Para empresas e profissionais"), ("governo", "Para o governo e a Justiça")):
            if lim(imp.get(k)): corpo += [f"**{rot}:** {lim(imp[k])}"]
    if lim(guia.get("exemplo")): corpo += ["## Na prática: um exemplo", lim(guia["exemplo"])]
    for q in guia.get("perguntas", []):
        if lim(q.get("p")) and lim(q.get("r")): corpo += [f"## {lim(q['p'])}", lim(q["r"])]
    if lim(guia.get("quem")): corpo += ["## Quem é afetado?", lim(guia["quem"])]
    if lim(guia.get("quando")): corpo += ["## A partir de quando vale?", lim(guia["quando"])]
    if guia.get("o_que_fazer"): corpo += ["## O que fazer agora", "\n".join(f"- {lim(x)}" for x in guia["o_que_fazer"] if lim(x))]
    if lim(guia.get("atencao")): corpo += ["## Atenção: limites e o que ainda falta saber", lim(guia["atencao"])]
    corpo += [f"Fonte oficial: [{c['titulo']}]({c['link']}) ({c['fonte']}).",
              "Guia escrito com apoio de inteligência artificial a partir do texto da fonte oficial acima, com conferência automática "
              "dos números. Os impactos são uma análise das consequências prováveis, não uma previsão. Não substitui a leitura do texto "
              "oficial nem a orientação de um advogado ou contador."]
    cab = [f"titulo: {lim(guia['titulo'])}", f"subtitulo: {lim(guia.get('subtitulo'))}", f"data: {quando.isoformat(timespec='minutes')}",
           "autor: Redação Plantão Informa", "rotulo: Explica Plantão", f"editoria: {c['fonte']}", f"fonte: {c['link']}",
           f"fonte_titulo: {c['titulo']}", f"tldr: {tl}", f"modelo: {modelo}"]
    open(os.path.join(PASTA, nome + ".md"), "w", encoding="utf-8").write("\n".join(l.replace("\n", " ") for l in cab) + "\n---\n" + "\n\n".join(corpo) + "\n")

def refazer(chave):
    """Reescreve os guias já publicados com o modelo atual (mesmo arquivo e data)."""
    import glob
    for arq in sorted(glob.glob(os.path.join(PASTA, "*.md"))):
        cab = dict(l.split(": ", 1) for l in open(arq, encoding="utf-8").read().split("\n---\n")[0].splitlines() if ": " in l)
        link = cab.get("fonte"); tit = cab.get("fonte_titulo")
        if not tit:
            m = re.search(r"Fonte oficial: \[(.+?)\]\(", open(arq, encoding="utf-8").read()); tit = m.group(1) if m else cab.get("titulo", "")
        c = {"fonte": cab.get("editoria", ""), "link": link, "titulo": tit}
        try: fonte = texto_pagina(link)
        except Exception as ex: print("Sem acesso à fonte:", arq, ex); continue
        guia, modelo = escrever(c, fonte, chave)
        if not guia: print("Mantido (trava):", arq); continue
        gravar(os.path.basename(arq)[:-3], guia, c, datetime.fromisoformat(cab["data"]), modelo)
        print("Refeito:", arq)

if __name__ == "__main__":
    if os.environ.get("EXPLICA_REFAZER"): refazer(os.environ["GEMINI_API_KEY"].strip())
    else: main()
