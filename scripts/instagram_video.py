#!/usr/bin/env python3
"""Monta o reel do Resumo do Plantão (MP4 vertical 1080x1920) a partir dos cards do carrossel.
    python3 scripts/instagram_video.py [pasta_saida]"""
import os, subprocess, sys
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

def reel_resumo(saida):
    os.makedirs(saida, exist_ok=True)
    tmp = os.path.join(saida, "_reel")
    os.makedirs(tmp, exist_ok=True)
    slides = cards.cards_resumo(tmp, video=True)            # resumo-1.png ... resumo-N.png
    n = len(slides)
    duracoes = []
    quadros = []
    for i, caminho in enumerate(slides):
        if i == 0: topo, dur = "RESUMO DO PLANTÃO", 4.5
        elif i == n - 1: topo, dur = "NOTÍCIAS DE HORA EM HORA", 4.5
        else: topo, dur = "RESUMO DO PLANTÃO", 7.0   # tempo de leitura das editorias
        q = os.path.join(tmp, f"q{i}.png")
        quadro(Image.open(caminho).convert("RGB"), topo, "Link na bio").save(q)
        quadros.append(q); duracoes.append(dur)

    # Cada imagem vira um trecho; os trechos se encadeiam com transição (xfade)
    cmd = [ffmpeg(), "-y", "-loglevel", "error"]
    for q, dur in zip(quadros, duracoes):
        cmd += ["-loop", "1", "-t", f"{dur}", "-framerate", "30", "-i", q]
    total = sum(duracoes) - FADE * (n - 1)
    trilha = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trilha.m4a")
    if os.path.exists(trilha):   # trilha original (scripts/gerar_trilha.py); repete se o vídeo for mais longo
        cmd += ["-stream_loop", "-1", "-t", f"{total:.2f}", "-i", trilha]
    else:
        cmd += ["-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    filtros, anterior, deslocamento = [], "[0:v]", 0.0
    for i in range(1, n):
        deslocamento += duracoes[i - 1] - FADE
        saida_i = f"[v{i}]"
        filtros.append(f"{anterior}[{i}:v]xfade=transition=fade:duration={FADE}:offset={deslocamento:.2f}{saida_i}")
        anterior = saida_i
    filtros.append(f"{anterior}format=yuv420p[v]")
    filtros.append(f"[{n}:a]volume=0.85,afade=t=in:d=1,afade=t=out:st={total - 2.5:.2f}:d=2.5[a]")
    destino = os.path.join(saida, "reel-1.mp4")
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-r", "30",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", destino]
    subprocess.run(cmd, check=True)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return [destino]

if __name__ == "__main__":
    print(reel_resumo(sys.argv[1] if len(sys.argv) > 1 else os.path.join(cards.RAIZ, "instagram")))
