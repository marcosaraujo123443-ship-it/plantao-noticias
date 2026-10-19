#!/usr/bin/env python3
"""Publica no Instagram do Plantão Informa (roda no GitHub Actions).

    python3 scripts/instagram.py gerar    resumo|mercado|agro|reel   -> desenha os cards (ou o vídeo) em instagram/ e a legenda
    python3 scripts/instagram.py publicar resumo|mercado|agro|reel   -> envia à API do Instagram (imagens pela URL do GitHub;
                                                                          o vídeo do reel pela URL do ramo "midia")
    python3 scripts/instagram.py renovar                        -> renova o token (imprime o novo em stdout)

Secrets: IG_TOKEN (obrigatório) e IG_USER_ID (opcional; se faltar, é descoberto pelo token).
As imagens são lidas pelo Instagram a partir de IMAGENS_BASE (URL pública da pasta instagram/ no commit atual).
Não publica de novo o mesmo conteúdo (instagram_publicados.json), a não ser com IG_FORCAR=1."""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as cards

RAIZ = cards.RAIZ
PASTA = os.path.join(RAIZ, "instagram")
REGISTRO = os.path.join(RAIZ, "instagram_publicados.json")
API = "https://graph.instagram.com/v23.0"
BRT = timezone(timedelta(hours=-3))
# 3 a 5 hashtags específicas por post (recomendação atual do Instagram)
TAGS = {"resumo": "#noticias #resumododia #brasil #plantaoinforma",
        "reel": "#noticias #resumododia #brasil #plantaoinforma",
        "mercado": "#ibovespa #dolar #bolsadevalores #plantaoinforma",
        "agro": "#agronegocio #cotacoes #soja #boigordo #plantaoinforma",
        "futebol": "#brasileirao #futebol #tabela #plantaoinforma",
        "contas": "#contaspublicas #transparencia #plantaoinforma"}
# Pergunta no fim da legenda (comentários aumentam a distribuição); neutras, sem tomar lado
PERGUNTAS = {
    "resumo": ["Qual dessas notícias mais te chamou atenção hoje?", "Qual editoria você quer ver primeiro amanhã?",
               "Faltou algum assunto importante? Conta nos comentários.", "De qual dessas notícias você ainda não tinha ouvido falar?"],
    "reel": ["Qual notícia de hoje mais te impactou?", "Você prefere o resumo em vídeo ou em fotos?",
             "Qual assunto merece um resumo só dele?"],
    "mercado": ["Você acompanha o dólar todos os dias?", "Qual ação você está de olho?",
                "O que mais pesou no mercado hoje, na sua opinião?"],
    "economia": ["Isso pesa no seu bolso?", "Você sentiu essa diferença no dia a dia?",
                 "Qual indicador você acompanha de perto?", "Como isso afeta o seu planejamento?"],
    "contas": ["De qual estado você é?", "Você acompanha as contas do seu estado?",
               "Qual área deveria receber mais recursos no seu estado?"],
    "futebol": ["Seu time está onde na tabela?", "Quem leva o título este ano?",
                "Quem você acha que escapa do rebaixamento?"],
    "agro": ["Qual cotação você acompanha todo dia?", "De qual região você é? Conta nos comentários.",
             "Quer que a gente inclua alguma outra cotação?"],
}

def final(tipo):
    """Pergunta do dia (varia conforme a data) + hashtags."""
    lista = PERGUNTAS[tipo]
    return "💬 " + lista[datetime.now(BRT).timetuple().tm_yday % len(lista)] + "\n\n" + TAGS[tipo]

def utc(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def num(v, casas=2): return cards.num(v, casas)

# ---------------------------------------------------------------- conteúdo
def chave_e_legenda(tipo):
    """Devolve (chave do conteúdo, legenda) ou (None, motivo) quando não há o que publicar."""
    agora = datetime.now(timezone.utc)
    if tipo == "resumo":
        r = cards.ler("resumo.json")
        if agora - utc(r["gerado_utc"]) > timedelta(hours=8): return None, "resumo antigo (mais de 8 h)"
        q = utc(r["gerado_utc"]).astimezone(BRT)
        secoes = ", ".join(s["secao"] for s in r["secoes"])
        leg = (f"📰 Resumo do Plantão · {q:%d/%m}, {q:%H}h\n\n{r['abertura']}\n\n"
               f"➡️ Arraste para ver: {secoes}.\n\n"
               "🔗 Manchetes atualizadas de hora em hora, cotações e tabelas no site: link na bio.\n\n"
               "Resumo feito com auxílio de inteligência artificial a partir de veículos confiáveis.\n\n" + final(tipo))
        return "resumo " + r["gerado_utc"], leg
    if tipo == "reel":
        r = cards.ler("resumo.json")
        if agora - utc(r["gerado_utc"]) > timedelta(hours=8): return None, "resumo antigo (mais de 8 h)"
        q = utc(r["gerado_utc"]).astimezone(BRT)
        leg = (f"▶️ O Resumo do Plantão em 40 segundos · {q:%d/%m}\n\n{r['abertura']}\n\n"
               "🔗 Notícias de hora em hora, cotações e tabelas no site: link na bio.\n\n"
               "Resumo feito com auxílio de inteligência artificial a partir de veículos confiáveis.\n\n" + final(tipo))
        return "reel " + r["gerado_utc"], leg
    if tipo == "mercado":
        m = cards.ler("mercado.json")
        q = utc(m["atualizado_utc"]).astimezone(BRT)
        if agora - utc(m["atualizado_utc"]) > timedelta(hours=4) or q.weekday() >= 5:
            return None, "sem pregão recente (fim de semana, feriado ou dados antigos)"
        ind = {i["nome"]: i for i in m["indicadores"]}
        acoes = {a["ticker"]: a for a in m.get("maiores", []) + m.get("acoes", []) if a.get("var") is not None}
        ordem = sorted(acoes.values(), key=lambda a: a["var"], reverse=True)
        linhas = [f"📈 Como fechou o mercado · {q:%d/%m}", ""]
        if ind.get("Ibovespa", {}).get("var") is not None:
            i = ind["Ibovespa"]; linhas.append(f"Ibovespa: {num(i['valor'], 0)} pts ({cards.var_txt(i['var'])})")
        if ind.get("Dólar", {}).get("var") is not None:
            i = ind["Dólar"]; linhas.append(f"Dólar: R$ {num(i['valor'], 4)} ({cards.var_txt(i['var'])})")
        if ordem:
            linhas.append(f"Maior alta: {ordem[0]['ticker']} ({cards.var_txt(ordem[0]['var'])}) · "
                          f"maior queda: {ordem[-1]['ticker']} ({cards.var_txt(ordem[-1]['var'])})")
        linhas += ["", "🔗 Ações, fundos imobiliários e moedas atualizados no site: link na bio.", "",
                   "Cotações com atraso, apenas informativas. Não é recomendação de investimento.", "", final(tipo)]
        return f"mercado {q:%Y-%m-%d}", "\n".join(linhas)
    if tipo == "agro":
        a = cards.ler("agro.json")
        por = {i["nome"]: i for i in a["indicadores"] if i.get("preco") is not None}
        if "Soja (Paranaguá)" not in por: return None, "cotações do agro indisponíveis"
        data = por["Soja (Paranaguá)"]["data"]
        linhas = [f"🌾 Cotações do agro · fechamento de {data[:5]}", ""]
        for nome, rot in (("Soja (Paranaguá)", "Soja"), ("Milho (Campinas)", "Milho"),
                          ("Boi gordo (SP)", "Boi gordo"), ("Café arábica", "Café arábica")):
            if nome in por:
                i = por[nome]
                linhas.append(f"{rot}: R$ {num(i['preco'])}{i['un'].replace('R$', '').strip()} ({cards.var_txt(i['var'])})")
        linhas += ["", "🔗 Todas as cotações, com bolsas de Chicago e B3: link na bio.", "",
                   "Fonte: Cepea/Esalq, via Notícias Agrícolas. Apenas informativo.", "", final(tipo)]
        return f"agro {data}", "\n".join(linhas)
    if tipo == "futebol":
        f, liga, linhas = cards.tabela_brasileirao()
        if agora - utc(f["atualizado_utc"]) > timedelta(hours=6): return None, "tabela do futebol desatualizada"
        jogos = sum(l["j"] for l in linhas)          # muda a cada jogo: só posta quando a tabela andou
        rodada = cards.rodada_atual(linhas)
        lider, vice = linhas[0], linhas[1]
        z4 = ", ".join(l["time"] for l in linhas[-4:])
        leg = (f"⚽ Classificação do Brasileirão · até a {rodada}ª rodada\n\n"
               f"🥇 {lider['time']} lidera com {lider['pts']} pontos; em 2º, {vice['time']} tem {vice['pts']}.\n"
               f"🔻 Na zona de rebaixamento: {z4}.\n\n"
               "🔗 Tabelas completas do Brasileirão e das maiores ligas do mundo no site: link na bio.\n\n"
               "Fonte: ESPN.\n\n" + final(tipo))
        return f"futebol {jogos}", leg
    raise SystemExit(f"tipo desconhecido: {tipo}")

def textos_alt(tipo, n):
    """Texto alternativo de cada imagem (acessibilidade; também ajuda o Instagram a entender o conteúdo)."""
    if tipo == "resumo":
        r = cards.ler("resumo.json")
        alt = ["Capa do Resumo do Plantão, do Plantão Informa: " + r["abertura"]]
        alt += [f"Resumo de {x['secao']}: {x['texto']}" for x in r["secoes"]]
        alt.append("Chamada para o site plantaoinforma.com.br, com notícias de hora em hora, cotações e tabelas.")
        return [a[:1000] for a in alt][:n]
    if tipo == "mercado":
        return ["Card do Plantão Informa com o fechamento do mercado: Ibovespa, dólar, euro, bitcoin, Selic, "
                "IPCA e as cinco maiores altas e baixas da bolsa no dia."]
    if tipo == "agro":
        return ["Card do Plantão Informa com as cotações do agro: soja, milho, boi gordo, café, trigo, açúcar, "
                "algodão, frango e suíno, com preço e variação do dia (fonte Cepea/Esalq)."]
    if tipo == "futebol":
        _, _, linhas = cards.tabela_brasileirao()
        return [("Tabela de classificação do Brasileirão Série A: " +
                 "; ".join(f"{l['pos']}º {l['time']}, {l['pts']} pontos" for l in linhas))[:1000]]
    return []

def registro():
    try:
        with open(REGISTRO, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

# ---------------------------------------------------------------- série das contas públicas
MIN_ESTADOS = 23     # só começa a série de um bimestre novo quando ~85% dos estados já entregaram o relatório

def proximo_contas():
    """Próximo carrossel da série (uma região por dia, depois o consolidado) ou (None, motivo)."""
    import instagram_contas as ct
    est = cards.ler("estados.json")["estados"]
    (ano, p), n = ct.periodo_modal(est)
    serie = f"contas {ano}-{p}"
    reg = registro()
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    feitos = [k for k in ct.ORDEM if reg.get(k) == serie]
    if n < MIN_ESTADOS and not feitos:
        return None, f"{p}º bimestre de {ano}: só {n} de 27 estados publicaram; aguardando"
    for k in ct.ORDEM:
        fb_ok = not os.environ.get("FB_PAGE_TOKEN") or reg.get("fb_" + k) == serie
        if reg.get(k) == serie and fb_ok: continue
        ultimo = max((reg.get(x + "_em", "") for x in ct.ORDEM), default="")
        if ultimo and utc(ultimo).astimezone(BRT).strftime("%Y-%m-%d") == hoje and reg.get(k) != serie \
                and not os.environ.get("IG_FORCAR"):
            return None, "já saiu um carrossel das contas hoje; o próximo vai amanhã"
        return k, serie
    return None, f"série do {p}º bimestre de {ano} completa"

# ---------------------------------------------------------------- indicadores econômicos
def proximo_economia():
    """Divulgação nova (Copom, IPCA, IPCA-15, IGP-M, INPC, desemprego) ou o painel do mês; um por execução."""
    import instagram_economia as ec
    reg, fb = registro(), bool(os.environ.get("FB_PAGE_TOKEN"))
    pend = lambda k, chave: reg.get("eco_" + k) != chave or (fb and reg.get("fb_eco_" + k) != chave)
    for k in ec.ORDEM:
        try: chave = ec.legenda_e_alt(k)[0]
        except Exception: continue
        if pend(k, chave): return k
    if datetime.now(BRT).weekday() < 5 and pend("painel", ec.legenda_e_alt("painel")[0]):
        return "painel"
    return None

def gerar(tipo):
    saida = os.environ.get("GITHUB_OUTPUT")
    def sinal(ok):
        if saida:
            with open(saida, "a") as f: f.write(f"publicar={'1' if ok else '0'}\n")
    if tipo == "economia":
        import instagram_economia as ec
        sub = os.environ.get("ECO_TIPO") or proximo_economia()
        if not sub:
            print("Nada a publicar: nenhuma divulgação nova de indicadores"); sinal(False); return
        chave, legenda, alt = ec.legenda_e_alt(sub)
        lista = PERGUNTAS["economia"]
        legenda += ("\n\n💬 " + lista[datetime.now(BRT).timetuple().tm_yday % len(lista)] + "\n\n"
                    + ec.TAGS[sub] + " #plantaoinforma")
        for antigo in os.listdir(PASTA) if os.path.isdir(PASTA) else []:
            if antigo.startswith("economia-"): os.remove(os.path.join(PASTA, antigo))
        arquivos = ec.gerar(sub, PASTA)
        with open(os.path.join(PASTA, "economia.json"), "w", encoding="utf-8") as f:
            json.dump({"chave": chave, "registro": "eco_" + sub, "legenda": legenda,
                       "imagens": [os.path.basename(a) for a in arquivos], "alt": alt}, f, ensure_ascii=False, indent=1)
        print(f"{len(arquivos)} card(s) gerado(s) para {sub} ({chave})\n\n{legenda}")
        sinal(True); return
    if tipo == "contas":
        import instagram_contas as ct
        sub, motivo = proximo_contas()
        if not sub:
            print("Nada a publicar:", motivo); sinal(False); return
        chave, legenda, alt = ct.legenda_e_alt(sub)
        legenda += "\n\n" + final("contas")
        for antigo in os.listdir(PASTA) if os.path.isdir(PASTA) else []:
            if antigo.startswith("contas-"): os.remove(os.path.join(PASTA, antigo))
        arquivos = ct.gerar(sub, PASTA)
        tags = {"norte": "#regiaonorte", "nordeste": "#nordeste", "centro_oeste": "#centrooeste",
                "sudeste": "#sudeste", "sul": "#regiaosul", "brasil": "#brasil"}[sub.replace("contas_", "")]
        legenda = legenda.replace(TAGS["contas"], TAGS["contas"].replace("#plantaoinforma", tags + " #plantaoinforma"))
        with open(os.path.join(PASTA, "contas.json"), "w", encoding="utf-8") as f:
            json.dump({"chave": chave, "registro": sub, "legenda": legenda,
                       "imagens": [os.path.basename(a) for a in arquivos], "alt": alt}, f, ensure_ascii=False, indent=1)
        print(f"{len(arquivos)} card(s) gerado(s) para {sub} ({chave})\n\n{legenda}")
        sinal(True); return
    chave, legenda = chave_e_legenda(tipo)
    if not chave:
        print("Nada a publicar:", legenda); sinal(False); return
    reg = registro()
    ja_ig = reg.get(tipo) == chave
    ja_fb = not os.environ.get("FB_PAGE_TOKEN") or reg.get("fb_" + tipo) == chave
    if ja_ig and ja_fb and not os.environ.get("IG_FORCAR"):
        print("Já publicado:", chave); sinal(False); return
    for antigo in os.listdir(PASTA) if os.path.isdir(PASTA) else []:
        if antigo.startswith(tipo + "-"): os.remove(os.path.join(PASTA, antigo))
    if tipo == "reel":
        import instagram_video
        arquivos = instagram_video.reel_resumo(PASTA)
    else:
        arquivos = cards.GERADORES[tipo](PASTA)
    with open(os.path.join(PASTA, f"{tipo}.json"), "w", encoding="utf-8") as f:
        json.dump({"chave": chave, "legenda": legenda, "imagens": [os.path.basename(a) for a in arquivos],
                   "alt": textos_alt(tipo, len(arquivos))},
                  f, ensure_ascii=False, indent=1)
    print(f"{len(arquivos)} card(s) gerado(s) para {chave}\n\n{legenda}")
    sinal(True)

# ---------------------------------------------------------------- API do Instagram
def chamar(metodo, caminho, **params):
    params["access_token"] = os.environ["IG_TOKEN"].strip().strip("\"'")
    dados = urllib.parse.urlencode(params).encode()
    url = f"{API}/{caminho}"
    if metodo == "GET": req = urllib.request.Request(url + "?" + dados.decode())
    else: req = urllib.request.Request(url, data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as err:
        corpo = err.read().decode("utf-8", "replace")
        raise SystemExit(f"Instagram respondeu erro {err.code} em {caminho.split('?')[0]}: {corpo[:600]}")

def conta():
    uid = os.environ.get("IG_USER_ID", "").strip()
    if uid: return uid
    eu = chamar("GET", "me", fields="user_id,username")
    print("Conta:", eu.get("username"))
    return eu.get("user_id") or eu["id"]

def esperar(container, tentativas=30):
    for _ in range(tentativas):
        st = chamar("GET", container, fields="status_code").get("status_code")
        if st == "FINISHED": return
        if st in ("ERROR", "EXPIRED"): raise SystemExit(f"Instagram não processou a mídia {container}: {st}")
        time.sleep(5)
    raise SystemExit(f"Tempo esgotado esperando a mídia {container}")

def publicar(tipo):
    if not os.environ.get("IG_TOKEN"): raise SystemExit("Secret IG_TOKEN não configurado.")
    with open(os.path.join(PASTA, f"{tipo}.json"), encoding="utf-8") as f: info = json.load(f)
    tipo = info.get("registro", tipo)
    if registro().get(tipo) == info["chave"] and not os.environ.get("IG_FORCAR"):
        print("Instagram já tinha este post:", info["chave"]); return
    uid = conta()
    if tipo == "reel":
        url = os.environ["IMAGENS_BASE"].rstrip("/") + "/" + info["imagens"][0]
        c = chamar("POST", f"{uid}/media", media_type="REELS", video_url=url, caption=info["legenda"], share_to_feed="true")["id"]
        esperar(c, tentativas=60)          # vídeo demora mais para processar (até ~5 min)
        return registrar(tipo, info, publicar_container(uid, c))
    base = os.environ["IMAGENS_BASE"].rstrip("/")
    urls = [f"{base}/{n}" for n in info["imagens"]]
    alts = info.get("alt", [])
    def alt(i): return {"alt_text": alts[i]} if i < len(alts) else {}
    if len(urls) == 1:
        c = criar_imagem(uid, alt(0), image_url=urls[0], caption=info["legenda"])
    else:
        filhos = []
        for i, u in enumerate(urls):
            filhos.append(criar_imagem(uid, alt(i), image_url=u, is_carousel_item="true"))
        for fid in filhos: esperar(fid)
        c = chamar("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(filhos), caption=info["legenda"])["id"]
    esperar(c)
    registrar(tipo, info, publicar_container(uid, c))

def criar_imagem(uid, extra, **params):
    """Cria o contêiner da imagem com texto alternativo; se a API recusar o alt_text, tenta sem ele."""
    if extra:
        try: return chamar("POST", f"{uid}/media", **params, **extra)["id"]
        except SystemExit as e:
            if "alt_text" not in str(e) and "(#100)" not in str(e) and "code\":100" not in str(e).replace(" ", ""): raise
            print("Aviso: texto alternativo recusado; publicando sem ele.")
    return chamar("POST", f"{uid}/media", **params)["id"]

def publicar_container(uid, c):
    """media_publish às vezes responde 'mídia ainda não está pronta' (2207027) mesmo após FINISHED; espera e repete."""
    for tentativa in range(6):
        try:
            return chamar("POST", f"{uid}/media_publish", creation_id=c)["id"]
        except SystemExit as e:
            if "2207027" not in str(e) and "not ready" not in str(e) or tentativa == 5: raise
            print(f"Instagram ainda processando a mídia; nova tentativa em 20 s ({tentativa + 1}/5)")
            time.sleep(20)

def registrar(tipo, info, post, rede="Instagram"):
    reg = registro(); reg[tipo] = info["chave"]; reg[tipo + "_post"] = post
    reg[tipo + "_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(REGISTRO, "w", encoding="utf-8") as f: json.dump(reg, f, ensure_ascii=False, indent=1)
    print(f"Publicado no {rede}: {info['chave']} (post {post})")

# ---------------------------------------------------------------- Página do Facebook
FB_API = "https://graph.facebook.com/v23.0"
SITE_FB = "https://plantaoinforma.com.br/?utm_source=facebook&utm_medium=social"

def chamar_fb(caminho, **params):
    params["access_token"] = os.environ["FB_PAGE_TOKEN"].strip().strip("\"'")
    req = urllib.request.Request(f"{FB_API}/{caminho}", data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as err:
        raise SystemExit(f"Facebook respondeu erro {err.code} em {caminho}: " + err.read().decode("utf-8", "replace")[:600])

def legenda_fb(leg):
    """No Facebook o link funciona na própria legenda; troca o 'link na bio' pelo endereço do site."""
    leg = re.sub(r"[Ll]ink na bio", SITE_FB, leg)
    return leg.replace("➡️ Arraste para ver:", "➡️ Nas imagens:")

def publicar_facebook(tipo):
    if not os.environ.get("FB_PAGE_TOKEN") or not os.environ.get("FB_PAGE_ID"):
        print("Página do Facebook não configurada (FB_PAGE_TOKEN / FB_PAGE_ID)."); return
    with open(os.path.join(PASTA, f"{tipo}.json"), encoding="utf-8") as f: info = json.load(f)
    tipo = info.get("registro", tipo)
    if registro().get("fb_" + tipo) == info["chave"] and not os.environ.get("IG_FORCAR"):
        print("Facebook já tinha este post:", info["chave"]); return
    pagina = os.environ["FB_PAGE_ID"].strip()
    base = os.environ["IMAGENS_BASE"].rstrip("/")
    urls = [f"{base}/{n}" for n in info["imagens"]]
    leg = legenda_fb(info["legenda"])
    if tipo == "reel":
        post = chamar_fb(f"{pagina}/videos", file_url=urls[0], description=leg,
                         title="Resumo do Plantão")["id"]
    elif len(urls) == 1:
        post = chamar_fb(f"{pagina}/photos", url=urls[0], caption=leg)["post_id"]
    else:
        fotos = [chamar_fb(f"{pagina}/photos", url=u, published="false")["id"] for u in urls]
        anexos = {f"attached_media[{i}]": json.dumps({"media_fbid": fid}) for i, fid in enumerate(fotos)}
        post = chamar_fb(f"{pagina}/feed", message=leg, **anexos)["id"]
    registrar("fb_" + tipo, info, post, rede="Facebook")

def renovar():
    """Renova o token de longa duração (vale mais 60 dias). O novo token sai em stdout."""
    tok = os.environ["IG_TOKEN"].strip().strip("\"'")
    url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": tok})
    try:
        with urllib.request.urlopen(url, timeout=60) as r: res = json.loads(r.read().decode())
    except urllib.error.HTTPError as err:
        msg = "Falha ao renovar o token: " + err.read().decode("utf-8", "replace")[:400]
        with open(os.environ.get("IG_ERRO", os.devnull), "w") as f: f.write(msg)
        raise SystemExit(msg)
    print(f"Token renovado; vale por mais {res.get('expires_in', 0) // 86400} dias.", file=sys.stderr)
    print(res["access_token"])

def _falha(msg):
    # Mostra o motivo como anotação no resumo da execução do GitHub (sem expor o token)
    print("::error::" + str(msg).replace("\n", " ")[:900], file=sys.stderr, flush=True)

if __name__ == "__main__":
  try:
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "gerar": gerar(sys.argv[2])
    elif acao == "publicar": publicar(sys.argv[2])
    elif acao == "facebook": publicar_facebook(sys.argv[2])
    elif acao == "renovar": renovar()
    else: raise SystemExit(__doc__)
  except SystemExit as e:
    if e.code not in (None, 0) and not isinstance(e.code, int): _falha(e.code)
    raise
  except Exception as e:
    _falha(repr(e)); raise
