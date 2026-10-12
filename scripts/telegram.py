#!/usr/bin/env python3
"""Envia ao canal do Telegram as manchetes novas (roda no GitHub Actions).
Só envia nos horários de TELEGRAM_HORAS (Brasília) e se o secret TELEGRAM_BOT_TOKEN existir."""
import json, os, html, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

CANAL = os.environ.get("TELEGRAM_CANAL", "@plantaodenoticias")
SITE = "https://marcosaraujo123443-ship-it.github.io/plantao-noticias/"
BRT = timezone(timedelta(hours=-3))

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Sem TELEGRAM_BOT_TOKEN; envio desligado."); return
    agora = datetime.now(BRT)
    horas = {int(h) for h in os.environ.get("TELEGRAM_HORAS", "1,5,9,13,17,21").split(",") if h.strip()}
    if agora.hour not in horas and not os.environ.get("TELEGRAM_FORCAR"):
        print(f"{agora:%H}h não é horário de envio."); return
    try: enviados = set(json.load(open("telegram_enviados.json", encoding="utf-8")))
    except Exception: enviados = set()
    itens = json.load(open("noticias.json", encoding="utf-8"))["itens"]
    novos = sorted((i for i in itens if i["link"] not in enviados), key=lambda i: i["data"], reverse=True)[:10]
    if not novos:
        print("Sem manchetes novas."); return
    linhas = [f"<b>📰 Plantão de Notícias · {agora:%d/%m %H:%M}</b>", ""]
    for i in novos:
        linhas.append(f'• <a href="{html.escape(i["link"])}">{html.escape(i["titulo"])}</a> — <i>{html.escape(i["secao"])} · {html.escape(i["fonte"])}</i>')
    linhas += ["", f'<a href="{SITE}">Site completo, com cotações</a>']
    msg = "\n".join(linhas)[:4000]
    dados = urllib.parse.urlencode({"chat_id": CANAL, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=dados, timeout=30) as r:
        ok = json.loads(r.read().decode()).get("ok")
    if not ok: raise SystemExit("Telegram recusou a mensagem")
    enviados |= {i["link"] for i in itens}
    json.dump(sorted(enviados)[-2000:], open("telegram_enviados.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"Enviadas {len(novos)} manchetes.")

if __name__ == "__main__":
    main()
