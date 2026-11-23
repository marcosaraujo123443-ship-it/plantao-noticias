#!/usr/bin/env python3
"""Monta o reel do Resumo do Plantão (MP4 vertical 1080x1920) a partir dos cards do carrossel.
    python3 scripts/instagram_video.py [pasta_saida]"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_cards as cards

W, H = 1080, 1920
FADE = 0.6                     # segundos de transição entre slides

def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

def quadro(card, topo, rodape):
    """Coloca o card 1080x1350 no centro de uma tela vertical, com faixas de texto em cima e embaixo."""
    tela = Image.new("RGB", (W, H), cards.FAIXA)
    d = ImageDraw.Draw(tela)
    y = (H - card.height) // 2
    tela.paste(card, (0, y))
    f = cards.fonte("bold", 46)
    d.text(((W - d.textlength(topo, font=f)) / 2, y - 150), topo, font=f, fill="#ffffff")
    f = cards.fonte("semi", 38)
    d.rounded_rectangle([W / 2 - 300, y + card.height + 70, W / 2 + 300, y + card.height + 160], radius=45, fill=cards.MARCA)
    d.text(((W - d.textlength(rodape, font=f)) / 2, y + card.height + 92), rodape, font=f, fill="#ffffff")
    return tela

def narracao():
    """plantao.mp3 (narração do Resumo, baixada do ramo 'audio') se for deste resumo; senão None."""
    mp3 = os.path.join(cards.RAIZ, "plantao.mp3")
    try:
        a = json.load(open(os.path.join(cards.RAIZ, "audio.json"), encoding="utf-8"))
        r = cards.ler("resumo.json")
    except Exception: return None
    if not os.path.exists(mp3) or a.get("resumo") != r["gerado_utc"]: return None
    return mp3

def duracao(arq):
    out = subprocess.run([ffmpeg(), "-i", arq, "-f", "null", "-"], capture_output=True, text=True).stderr
    h, m, s = out.split("Duration:")[1].split(",")[0].strip().split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

def cortes(mp3, total):
    """Momentos da narração em que cada slide deve entrar: estimados pelo tamanho de cada trecho do roteiro e
    ajustados para a pausa (silêncio) mais próxima entre os parágrafos."""
    import audio
    r = cards.ler("resumo.json")
    texto, _ = audio.roteiro(r)
    partes = texto.split("\n\n")                    # saudação, abertura, editorias..., encerramento
    blocos = [partes[0] + " " + partes[1]] + partes[2:]  # um bloco por slide
    tam = [len(b) for b in blocos]
    est, acc = [], 0
    for t in tam[:-1]:
        acc += t; est.append(total * acc / sum(tam))
    out = subprocess.run([ffmpeg(), "-i", mp3, "-af", "silencedetect=noise=-32dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    pz = list(zip(ini, fim))
    cps = sum(tam) / total                          # caracteres falados por segundo
    # cada editoria começa com uma frase curta ("Na política."): o corte é a pausa seguida de um trecho de fala do
    # tamanho dessa frase e de outra pausa
    res, ant = [], 0.0
    for k, e in enumerate(est):
        intro = blocos[k + 1].split(".")[0] if k + 1 < len(blocos) - 1 else ""
        melhor, nota = None, 1e9
        for a, (s0, e0) in enumerate(pz):
            m = (s0 + e0) / 2
            if abs(m - e) > 5 or m < ant + 1.5: continue
            sc = 0.25 * abs(m - e)
            if intro:
                prox = pz[a + 1][0] - e0 if a + 1 < len(pz) else 99
                sc += abs(prox - len(intro) / cps)
            if sc < nota: melhor, nota = m, sc
        c = melhor if melhor is not None else e
        res.append(c); ant = c
    return res

def reel_resumo(saida):
    os.makedirs(saida, exist_ok=True)
    tmp = os.path.join(saida, "_reel")
    os.makedirs(tmp, exist_ok=True)
    slides = cards.cards_resumo(tmp, video=True)            # resumo-1.png ... resumo-N.png
    n = len(slides)
    duracoes = []
    quadros = []
    mp3 = narracao()
    if mp3:   # narrado: cada slide fica na tela enquanto a voz lê o trecho dele
        total_voz = duracao(mp3)
        cs = cortes(mp3, total_voz)
        if len(cs) != n - 1: mp3 = None
    for i, caminho in enumerate(slides):
        if i == 0: topo, dur = "RESUMO DO PLANTÃO", 4.5
        elif i == n - 1: topo, dur = "NOTÍCIAS DE HORA EM HORA", 4.5
        else: topo, dur = "RESUMO DO PLANTÃO", 7.0   # tempo de leitura das editorias
        if mp3:   # a transição (FADE) fica centrada no corte
            a = 0.0 if i == 0 else cs[i - 1]; b = cs[i] if i < n - 1 else total_voz + 1.8
            dur = b - a + FADE
        q = os.path.join(tmp, f"q{i}.png")
        quadro(Image.open(caminho).convert("RGB"), topo, "Ouça e leia · link na bio" if mp3 else "Link na bio").save(q)
        quadros.append(q); duracoes.append(dur)

    # Cada imagem vira um trecho; os trechos se encadeiam com transição (xfade)
    cmd = [ffmpeg(), "-y", "-loglevel", "error"]
    for q, dur in zip(quadros, duracoes):
        cmd += ["-loop", "1", "-t", f"{dur:.2f}", "-framerate", "30", "-i", q]
    total = sum(duracoes) - FADE * (n - 1)
    trilha = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trilha.m4a")
    if os.path.exists(trilha):   # trilha original (scripts/gerar_trilha.py); repete se o vídeo for mais longo
        cmd += ["-stream_loop", "-1", "-t", f"{total:.2f}", "-i", trilha]
    else:
        cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    if mp3: cmd += ["-i", mp3]
    filtros, anterior, deslocamento = [], "[0:v]", 0.0
    for i in range(1, n):
        deslocamento += duracoes[i - 1] - FADE
        saida_i = f"[v{i}]"
        filtros.append(f"{anterior}[{i}:v]xfade=transition=fade:duration={FADE}:offset={deslocamento:.2f}{saida_i}")
        anterior = saida_i
    filtros.append(f"{anterior}format=yuv420p[v]")
    if mp3:   # voz na frente, trilha bem baixinha ao fundo
        filtros.append(f"[{n}:a]volume=0.10,afade=t=in:d=1,afade=t=out:st={total - 2.5:.2f}:d=2.5[tr]")
        filtros.append(f"[{n + 1}:a]aresample=48000,apad=pad_dur=3[voz]")
        filtros.append("[voz][tr]amix=inputs=2:duration=longest:normalize=0,volume=1.0[a]")
    else:
        filtros.append(f"[{n}:a]volume=0.85,afade=t=in:d=1,afade=t=out:st={total - 2.5:.2f}:d=2.5[a]")
    destino = os.path.join(saida, "reel-1.mp4")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-r", "30",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", f"{total:.2f}", "-movflags", "+faststart", destino]
    subprocess.run(cmd, check=True)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return [destino]

if __name__ == "__main__":
    print(reel_resumo(sys.argv[1] if len(sys.argv) > 1 else os.path.join(cards.RAIZ, "instagram")))
