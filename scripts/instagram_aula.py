#!/usr/bin/env python3
"""Série 'Economia em 30 dias': um carrossel informativo por dia, com o conteúdo de serie/economia.json.
Usado por scripts/instagram.py (tipo 'aula'); para ver um dia: python3 scripts/instagram_aula.py 3 [pasta]"""
import json, os, sys
from PIL import ImageDraw
import instagram_cards as c

AQUI = os.path.dirname(os.path.abspath(__file__))
SERIE = os.path.join(os.path.dirname(AQUI), "serie", "economia.json")
COR = "#0f766e"; VERDE, VERMELHO, OURO = "#137a3d", "#c0262d", "#b7791f"
W, H, M = c.W, c.H, c.M

def serie(): return json.load(open(SERIE, encoding="utf-8"))

def base(dia, pag, total):
    s = serie()
    img, d = c.tela(f"{s['nome']} · semana {dia['semana']}", COR, f"Dia {dia['n']} de 30",
                    pagina=f"{pag}/{total}  →" if pag < total else f"{pag}/{total}")
    return img, d

def progresso(d, n, y):
    larg = (W - 2 * M - 29 * 6) / 30
    for i in range(30):
        x = M + i * (larg + 6)
        d.rounded_rectangle([x, y, x + larg, y + 12], radius=6, fill=COR if i < n else "#d9e0ea")

def titulo_sec(d, y, txt, cor):
    d.text((M, y), txt.upper(), font=c.fonte("bold", 28), fill=cor)
    return y + 52

def caixa(img, d, y, rot, texto, fundo, cor_rot, altura_max=260):
    f = c.fonte("reg", 34); linhas = c.quebrar(d, texto, f, W - 2 * M - 64)
    tam = 34
    while len(linhas) * int(tam * 1.4) > altura_max and tam > 26:
        tam -= 2; f = c.fonte("reg", tam); linhas = c.quebrar(d, texto, f, W - 2 * M - 64)
    h = 70 + len(linhas) * int(tam * 1.4) + 24
    d.rounded_rectangle([M, y, W - M, y + h], radius=22, fill=fundo)
    d.text((M + 32, y + 26), rot.upper(), font=c.fonte("bold", 24), fill=cor_rot)
    for i, l in enumerate(linhas): d.text((M + 32, y + 66 + i * int(tam * 1.4)), l, font=f, fill=c.TINTA)
    return y + h

def capa(dia, total, extra=None, lista=True):
    s = serie(); img, d = base(dia, 1, total)
    progresso(d, dia["n"], 300)
    y = 360
    y += c.bloco(d, (M, y), dia["titulo"], "serif", 92, c.TINTA, W - 2 * M, 330, 1.12, 60) + 24
    y += c.bloco(d, (M, y), dia["gancho"], "semi", 40, c.TINTA2, W - 2 * M, 200, 1.35, 30) + 40
    if extra: y += c.bloco(d, (M, y), extra, "reg", 32, c.TINTA2, W - 2 * M, 150, 1.4, 26) + 20
    elif lista:
        d.text((M, y), "NESTE POST", font=c.fonte("bold", 24), fill=c.TINTA2); y += 48
        for t, cor in (("O que é e como funciona", COR), ("O lado bom", VERDE), ("Pontos de atenção", VERMELHO), ("O impacto no seu bolso", OURO)):
            d.rounded_rectangle([M, y + 8, M + 26, y + 34], radius=7, fill=cor)
            d.text((M + 44, y), t, font=c.fonte("semi", 34), fill=c.TINTA); y += 56
    yb = H - 108 - 250
    d.rounded_rectangle([M, yb, W - M, yb + 190], radius=24, fill=c.FAIXA)
    d.text((M + 36, yb + 30), "“", font=c.fonte("serif", 90), fill="#f2b84b")
    c.bloco(d, (M + 96, yb + 40), s["frase"], "serif-semi", 38, "#ffffff", W - 2 * M - 140, 120, 1.3, 30)
    return img

def slide_explica(dia, total):
    img, d = base(dia, 2, total)
    y = titulo_sec(d, 300, "O que é", COR)
    y += c.bloco(d, (M, y), dia["explica"], "reg", 40, c.TINTA, W - 2 * M, 520, 1.45, 30) + 36
    caixa(img, d, y, "Na prática", dia["exemplo"], "#e6f2f0", COR, altura_max=H - 108 - y - 140)
    return img

def lista(d, y, itens, cor, simbolo, altura):
    tam = 36
    while True:
        f = c.fonte("semi", tam); passo = int(tam * 1.38); tot = 0; blocos = []
        for it in itens:
            ls = c.quebrar(d, it, f, W - 2 * M - 70); blocos.append(ls); tot += len(ls) * passo + 22
        if tot <= altura or tam <= 26: break
        tam -= 2
    for ls in blocos:
        d.ellipse([M, y + 4, M + 44, y + 48], fill=cor)
        d.text((M + 22 - d.textlength(simbolo, font=c.fonte("bold", 30)) / 2, y + 7), simbolo, font=c.fonte("bold", 30), fill="#fff")
        for i, l in enumerate(ls): d.text((M + 70, y + i * passo), l, font=f, fill=c.TINTA)
        y += len(ls) * passo + 22
    return y

def slide_pros(dia, total):
    img, d = base(dia, 3, total)
    y = titulo_sec(d, 300, "O lado bom", VERDE)
    y = lista(d, y, dia["bons"], VERDE, "+", 380) + 30
    d.line([M, y, W - M, y], fill=c.LINHA, width=3); y += 34
    y = titulo_sec(d, y, "Pontos de atenção", VERMELHO)
    lista(d, y, dia["ruins"], VERMELHO, "−", H - 108 - y - 40)
    return img

def slide_bolso(dia, total, amanha):
    img, d = base(dia, 4, total)
    y = titulo_sec(d, 300, "No seu bolso", COR)
    y += c.bloco(d, (M, y), dia["bolso"], "reg", 40, c.TINTA, W - 2 * M, 330, 1.45, 30) + 36
    y = caixa(img, d, y, "Dica do Plantão", dia["dica"], "#fdf3dc", OURO, altura_max=250) + 40
    if amanha:
        d.text((M, y), "AMANHÃ NA SÉRIE", font=c.fonte("bold", 24), fill=c.TINTA2); y += 40
        y += c.bloco(d, (M, y), amanha, "serif", 46, c.TINTA, W - 2 * M, 120, 1.2, 34) + 24
    d.text((M, H - 108 - 70), "Salve este post e compartilhe com quem precisa saber.", font=c.fonte("semi", 30), fill=COR)
    return img

def slides_quiz(dia):
    P = dia["perguntas"]; total = len(P) + 2; out = [capa(dia, total, "Responda nos comentários e confira as respostas no último card.")]
    for i, q in enumerate(P, 2):
        img, d = base(dia, i, total)
        d.text((M, 300), f"PERGUNTA {i - 1} DE {len(P)}", font=c.fonte("bold", 28), fill=COR)
        y = 360 + c.bloco(d, (M, 360), q["p"], "serif", 54, c.TINTA, W - 2 * M, 300, 1.2, 36) + 40
        for j, o in enumerate(q["op"]):
            f = c.fonte("semi", 36); ls = c.quebrar(d, o, f, W - 2 * M - 130); h = 40 + len(ls) * 48
            d.rounded_rectangle([M, y, W - M, y + h], radius=20, fill="#ffffff", outline=c.LINHA, width=3)
            d.ellipse([M + 24, y + h / 2 - 28, M + 80, y + h / 2 + 28], fill=COR)
            L = "ABC"[j]; d.text((M + 52 - d.textlength(L, font=c.fonte("bold", 32)) / 2, y + h / 2 - 20), L, font=c.fonte("bold", 32), fill="#fff")
            for k, l in enumerate(ls): d.text((M + 104, y + 20 + k * 48), l, font=f, fill=c.TINTA)
            y += h + 22
        out.append(img)
    img, d = base(dia, total, total)
    y = titulo_sec(d, 300, "Respostas", VERDE)
    for i, q in enumerate(P, 1):
        t = f"{i}. {'ABC'[q['certa']]}) {q['op'][q['certa']]}"
        y += c.bloco(d, (M, y), t, "bold", 34, c.TINTA, W - 2 * M, 100, 1.3, 26) + 4
        y += c.bloco(d, (M, y), q["porque"], "reg", 30, c.TINTA2, W - 2 * M, 90, 1.35, 24) + 26
    d.text((M, H - 108 - 70), "Quantas você acertou? Conta nos comentários!", font=c.fonte("semi", 30), fill=COR)
    out.append(img)
    return out

def slides_glossario(dia):
    T = dia["termos"]; total = 4; out = [capa(dia, total, lista=False)]
    for pag, parte in ((2, T[:5]), (3, T[5:])):
        img, d = base(dia, pag, total); y = 300
        for i, (t, df) in enumerate(parte, (pag - 2) * 5 + 1):
            d.text((M, y), f"{i:02d}", font=c.fonte("bold", 40), fill=COR)
            d.text((M + 90, y - 2), t, font=c.fonte("serif", 46), fill=c.TINTA)
            y += 62 + c.bloco(d, (M + 90, y + 62), df, "reg", 33, c.TINTA2, W - 2 * M - 90, 100, 1.35, 26) + 30
        out.append(img)
    img, d = base(dia, 4, total)
    y = titulo_sec(d, 300, "Fim da série", COR)
    y += c.bloco(d, (M, y), "Foram 30 dias de economia, dos fundamentos aos juros, ao mercado e às tendências. Obrigado por acompanhar!",
                 "reg", 40, c.TINTA, W - 2 * M, 300, 1.45, 30) + 40
    y = caixa(img, d, y, "Continue bem informado", "Notícias, cotações, indicadores e análises atualizados o dia todo em plantaoinforma.com.br.", "#e6f2f0", COR)
    d.text((M, H - 108 - 70), "Salve este post para consultar quando precisar.", font=c.fonte("semi", 30), fill=COR)
    out.append(img)
    return out

def gerar(n, saida):
    s = serie(); dia = s["dias"][n - 1]
    prox = s["dias"][n]["titulo"] if n < len(s["dias"]) else None
    if dia.get("tipo") == "quiz": imgs = slides_quiz(dia)
    elif dia.get("tipo") == "glossario": imgs = slides_glossario(dia)
    else: imgs = [capa(dia, 4), slide_explica(dia, 4), slide_pros(dia, 4), slide_bolso(dia, 4, prox)]
    return [c.salvar(im, saida, f"aula-{i}.png") for i, im in enumerate(imgs, 1)]

def legenda_e_alt(n):
    s = serie(); dia = s["dias"][n - 1]
    prox = s["dias"][n]["titulo"] if n < len(s["dias"]) else None
    cab = f"📚 {s['nome']} · Dia {n}/30\n\n{dia['titulo']}\n{dia['gancho']}\n\n"
    if dia.get("tipo") == "quiz":
        corpo = "🧠 Hora de testar o que você aprendeu nesta semana!\n\n" + "\n".join(f"{i}. {q['p']}" for i, q in enumerate(dia["perguntas"], 1)) + \
                "\n\n➡️ Arraste para ver as alternativas. As respostas estão no último card.\n\n💬 Quantas você acertou? Conta nos comentários!"
        alt = [f"Capa: {s['nome']}, dia {n}: {dia['titulo']}. {dia['gancho']}"] + \
              [f"Pergunta {i}: {q['p']} Alternativas: " + "; ".join(f"{'ABC'[j]}) {o}" for j, o in enumerate(q["op"])) for i, q in enumerate(dia["perguntas"], 1)] + \
              ["Respostas: " + " ".join(f"{i}. {q['op'][q['certa']]}. {q['porque']}" for i, q in enumerate(dia["perguntas"], 1))]
    elif dia.get("tipo") == "glossario":
        corpo = "\n".join(f"🔹 {t}: {df}" for t, df in dia["termos"]) + "\n\n🙏 Obrigado por acompanhar os 30 dias da série!\n\n📌 Salve para consultar sempre que ler uma notícia de economia."
        alt = [f"Capa: {s['nome']}, dia {n}: {dia['titulo']}."] + \
              ["Termos: " + " ".join(f"{t}: {df}" for t, df in dia["termos"][:5]), "Termos: " + " ".join(f"{t}: {df}" for t, df in dia["termos"][5:]),
               "Fim da série Economia em 30 dias. Continue bem informado em plantaoinforma.com.br."]
    else:
        corpo = (dia["explica"] + "\n\n✅ O lado bom\n" + "\n".join("• " + x for x in dia["bons"]) +
                 "\n\n⚠️ Pontos de atenção\n" + "\n".join("• " + x for x in dia["ruins"]) +
                 f"\n\n💰 No seu bolso: {dia['bolso']}\n\n💡 Dica: {dia['dica']}")
        if prox: corpo += f"\n\n🔜 Amanhã: {prox}"
        corpo += "\n\n📌 Salve e compartilhe com quem precisa saber."
        alt = [f"Capa: {s['nome']}, dia {n} de 30: {dia['titulo']}. {dia['gancho']} {s['frase']}",
               f"O que é: {dia['explica']} Na prática: {dia['exemplo']}",
               "O lado bom: " + "; ".join(dia["bons"]) + ". Pontos de atenção: " + "; ".join(dia["ruins"]) + ".",
               f"No seu bolso: {dia['bolso']} Dica: {dia['dica']}" + (f" Amanhã: {prox}." if prox else "")]
    leg = cab + corpo + f"\n\n✨ {s['frase']}\n\n👉 Mais no site: link na bio.\n\n{dia['tags']} #economiaem30dias #plantaoinforma"
    return f"aula {n}", leg, alt

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for a in gerar(n, sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(AQUI), "instagram")): print(a)
    print(legenda_e_alt(n)[1])
