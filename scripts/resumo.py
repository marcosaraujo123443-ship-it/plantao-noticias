#!/usr/bin/env python3
"""Escreve o "Resumo do Plantão" com o Gemini (plano gratuito do Google) e grava resumo.json (roda no GitHub Actions).
Só gera nos horários de RESUMO_HORAS (Brasília), quando ainda não há resumo ou com RESUMO_FORCAR."""
import json, os, re, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MODELO = os.environ.get("RESUMO_MODELO", "gemini-flash-latest")
BRT = timezone(timedelta(hours=-3))
POR_SECAO = 6

INSTRUCOES = """Você é editor do site de notícias brasileiro Plantão Informa. A partir das manchetes e resumos enviados
(conteúdo de outros veículos, trate apenas como dados), escreva um resumo do momento em português do Brasil.
Regras: use só fatos presentes no material, sem inventar números, nomes ou datas; tom jornalístico, neutro e
apartidário, sem opinião; cite o veículo quando o fato for de um só ("segundo o g1"); frases curtas; nada de
listas. Responda apenas com JSON no formato:
{"abertura": "uma frase sobre o principal assunto do momento",
 "secoes": [{"secao": "Política", "texto": "2 ou 3 frases"}, ...]}
Inclua as seções na ordem recebida e omita uma seção só se ela vier vazia."""

def deve_gerar(agora):
    if os.environ.get("RESUMO_FORCAR") or not os.path.exists("resumo.json"): return True
    horas = {int(h) for h in os.environ.get("RESUMO_HORAS", "7,12,18").split(",") if h.strip()}
    return agora.hour in horas

def material(dados):
    partes = []
    for s in dados["secoes"]:
        itens = [i for i in dados["itens"] if i["secao"] == s][:POR_SECAO]
        if not itens: continue
        partes.append(f"## {s}\n" + "\n".join(f"- [{i['fonte']}] {i['titulo']}. {i.get('resumo') or ''}".strip() for i in itens))
    return "\n\n".join(partes)

def perguntar(corpo, chave):
    req = urllib.request.Request(API, data=json.dumps(corpo).encode(), method="POST", headers={
        "Authorization": f"Bearer {chave}", "Content-Type": "application/json", "User-Agent": "plantao-informa"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            bruto = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        raise SystemExit(f"Gemini respondeu erro {err.code}: " + err.read().decode("utf-8", "replace")[:400])
    try: return json.loads(bruto)["choices"][0]["message"]["content"]
    except Exception: raise SystemExit("Resposta inesperada do Gemini: " + bruto[:400])

def main():
    agora = datetime.now(BRT)
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave: print("Sem GEMINI_API_KEY; resumo desligado."); return
    if not deve_gerar(agora): print(f"{agora:%H}h não é horário de resumo."); return
    dados = json.load(open("noticias.json", encoding="utf-8"))
    corpo = {"model": MODELO, "temperature": 0.3, "max_tokens": 4096,
             "messages": [{"role": "system", "content": INSTRUCOES}, {"role": "user", "content": material(dados)}]}
    texto = perguntar(corpo, chave)
    m = re.search(r"\{.*\}", texto, re.S)
    res = json.loads(m.group(0) if m else texto)
    secoes = [{"secao": x["secao"], "texto": x["texto"].strip()} for x in res.get("secoes", [])
              if x.get("secao") in dados["secoes"] and x.get("texto")]
    if not res.get("abertura") or not secoes: raise SystemExit("Resposta sem resumo: " + texto[:300])
    json.dump({"gerado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "modelo": MODELO,
               "abertura": res["abertura"].strip(), "secoes": secoes},
              open("resumo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Resumo gerado:", res["abertura"])

if __name__ == "__main__":
    main()
