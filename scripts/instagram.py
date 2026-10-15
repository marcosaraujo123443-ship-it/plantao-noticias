#!/usr/bin/env python3
"""Publica no Instagram do Plantão Informa (roda no GitHub Actions).

    python3 scripts/instagram.py gerar    resumo|mercado|agro   -> desenha os cards em instagram/ e a legenda
    python3 scripts/instagram.py publicar resumo|mercado|agro   -> envia à API do Instagram as imagens já no GitHub
    python3 scripts/instagram.py renovar                        -> renova o token (imprime o novo em stdout)

Secrets: IG_TOKEN (obrigatório) e IG_USER_ID (opcional; se faltar, é descoberto pelo token).
As imagens são lidas pelo Instagram a partir de IMAGENS_BASE (URL pública da pasta instagram/ no commit atual).
Não publica de novo o mesmo conteúdo (instagram_publicados.json), a não ser com IG_FORCAR=1."""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as cards

RAIZ = cards.RAIZ
PASTA = os.path.join(RAIZ, "instagram")
REGISTRO = os.path.join(RAIZ, "instagram_publicados.json")
API = "https://graph.instagram.com/v23.0"
BRT = timezone(timedelta(hours=-3))
TAGS = {"resumo": "#noticias #resumododia #plantaoinforma #brasil #politica #economia #futebol #agro",
        "mercado": "#ibovespa #dolar #bolsadevalores #acoes #mercadofinanceiro #investimentos #plantaoinforma",
        "agro": "#agro #agronegocio #soja #milho #boigordo #cafe #cotacoes #plantaoinforma"}

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
               "Resumo feito com auxílio de inteligência artificial a partir de veículos confiáveis.\n\n" + TAGS[tipo])
        return "resumo " + r["gerado_utc"], leg
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
                   "Cotações com atraso, apenas informativas. Não é recomendação de investimento.", "", TAGS[tipo]]
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
                   "Fonte: Cepea/Esalq, via Notícias Agrícolas. Apenas informativo.", "", TAGS[tipo]]
        return f"agro {data}", "\n".join(linhas)
    raise SystemExit(f"tipo desconhecido: {tipo}")

def registro():
    try:
        with open(REGISTRO, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def gerar(tipo):
    chave, legenda = chave_e_legenda(tipo)
    saida = os.environ.get("GITHUB_OUTPUT")
    def sinal(ok):
        if saida:
            with open(saida, "a") as f: f.write(f"publicar={'1' if ok else '0'}\n")
    if not chave:
        print("Nada a publicar:", legenda); sinal(False); return
    if registro().get(tipo) == chave and not os.environ.get("IG_FORCAR"):
        print("Já publicado:", chave); sinal(False); return
    for antigo in os.listdir(PASTA) if os.path.isdir(PASTA) else []:
        if antigo.startswith(tipo + "-"): os.remove(os.path.join(PASTA, antigo))
    arquivos = cards.GERADORES[tipo](PASTA)
    with open(os.path.join(PASTA, f"{tipo}.json"), "w", encoding="utf-8") as f:
        json.dump({"chave": chave, "legenda": legenda, "imagens": [os.path.basename(a) for a in arquivos]},
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

def esperar(container):
    for _ in range(30):
        st = chamar("GET", container, fields="status_code").get("status_code")
        if st == "FINISHED": return
        if st in ("ERROR", "EXPIRED"): raise SystemExit(f"Instagram não processou a mídia {container}: {st}")
        time.sleep(5)
    raise SystemExit(f"Tempo esgotado esperando a mídia {container}")

def publicar(tipo):
    if not os.environ.get("IG_TOKEN"): raise SystemExit("Secret IG_TOKEN não configurado.")
    base = os.environ["IMAGENS_BASE"].rstrip("/")
    with open(os.path.join(PASTA, f"{tipo}.json"), encoding="utf-8") as f: info = json.load(f)
    uid = conta()
    urls = [f"{base}/{n}" for n in info["imagens"]]
    if len(urls) == 1:
        c = chamar("POST", f"{uid}/media", image_url=urls[0], caption=info["legenda"])["id"]
    else:
        filhos = []
        for u in urls:
            filhos.append(chamar("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"])
        for fid in filhos: esperar(fid)
        c = chamar("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(filhos), caption=info["legenda"])["id"]
    esperar(c)
    post = chamar("POST", f"{uid}/media_publish", creation_id=c)["id"]
    reg = registro(); reg[tipo] = info["chave"]; reg[tipo + "_post"] = post
    reg[tipo + "_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(REGISTRO, "w", encoding="utf-8") as f: json.dump(reg, f, ensure_ascii=False, indent=1)
    print(f"Publicado no Instagram: {info['chave']} (post {post})")

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
    elif acao == "renovar": renovar()
    else: raise SystemExit(__doc__)
  except SystemExit as e:
    if e.code not in (None, 0) and not isinstance(e.code, int): _falha(e.code)
    raise
  except Exception as e:
    _falha(repr(e)); raise
