#!/usr/bin/env python3
"""Compõe a trilha de fundo do reel (original, sintetizada aqui, sem direitos de terceiros).
Gera scripts/trilha.wav; o vídeo usa scripts/trilha.m4a (convertida com ffmpeg).
Para usar outra música livre de direitos, basta substituir scripts/trilha.m4a.
    python3 scripts/gerar_trilha.py"""
import os, subprocess, wave
import numpy as np

SR = 44100
BPM = 96
BEAT = 60 / BPM
COMPASSO = 4 * BEAT
DURACAO = 48.0
AQUI = os.path.dirname(os.path.abspath(__file__))

def nota(n):                      # número MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)

# I – V – vi – IV em dó maior, 2 compassos cada acorde (progressão comum, sem autoria)
ACORDES = [[48, 55, 60, 64, 67], [43, 55, 59, 62, 67], [45, 57, 60, 64, 69], [41, 53, 57, 60, 65]]

t_total = np.arange(int(DURACAO * SR)) / SR
mix = np.zeros_like(t_total)

def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e

def soma(sinal, inicio):
    i = int(inicio * SR)
    fim = min(len(mix), i + len(sinal))
    if i < len(mix): mix[i:fim] += sinal[:fim - i]

rng = np.random.default_rng(7)
k = 0
inicio = 0.0
while inicio < DURACAO:
    acorde = ACORDES[k % 4]
    dur = 2 * COMPASSO
    n = int((dur + 1.5) * SR)
    t = np.arange(n) / SR
    # pad: notas do acorde com leve desafinação (efeito coral) e ataque lento
    pad = np.zeros(n)
    for m in acorde[1:]:
        for det in (-0.12, 0.12):
            f = nota(m + det / 12)
            pad += np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    soma(0.035 * pad * env_adsr(n, 1.2, 1.5), inicio)
    # baixo: tônica em semínimas pontuadas, decaimento suave
    for b in range(8):
        tb = np.arange(int(BEAT * 1.4 * SR)) / SR
        f = nota(acorde[0])
        som = (np.sin(2 * np.pi * f * tb) + 0.3 * np.sin(4 * np.pi * f * tb)) * np.exp(-tb * 3.2)
        soma(0.16 * som * env_adsr(len(tb), 0.01, 0.1), inicio + b * BEAT)
    # arpejo em colcheias, tipo "pluck"
    seq = [acorde[2], acorde[3], acorde[4], acorde[3]] * 4
    for j, m in enumerate(seq):
        ta = np.arange(int(BEAT * 0.9 * SR)) / SR
        f = nota(m + 12)
        som = (np.sin(2 * np.pi * f * ta) + 0.25 * np.sin(6 * np.pi * f * ta)) * np.exp(-ta * 7)
        soma(0.05 * som * env_adsr(len(ta), 0.005, 0.05), inicio + j * BEAT / 2)
    # bumbo nos tempos 1 e 3, chimbal discreto nos contratempos
    for bt in range(8):
        if bt % 2 == 0:
            tk = np.arange(int(0.25 * SR)) / SR
            freq = 50 + 80 * np.exp(-tk * 30)
            som = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tk * 14)
            soma(0.22 * som, inicio + bt * BEAT)
        th = np.arange(int(0.06 * SR)) / SR
        ruido = np.diff(rng.standard_normal(len(th) + 1)) * np.exp(-th * 70)
        soma(0.018 * ruido, inicio + bt * BEAT + BEAT / 2)
    inicio += dur
    k += 1

# eco leve para dar ambiência
atraso = int(BEAT * 0.75 * SR)
eco = np.zeros_like(mix); eco[atraso:] = mix[:-atraso] * 0.22
mix += eco
mix *= env_adsr(len(mix), 1.5, 3.0)
mix = mix / np.max(np.abs(mix)) * 0.7
estereo = np.stack([mix, np.roll(mix, int(0.012 * SR))], axis=1)   # leve abertura estéreo

wav = os.path.join(AQUI, "trilha.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((estereo * 32767).astype("<i2").tobytes())
try:
    import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    ff = "ffmpeg"
subprocess.run([ff, "-y", "-loglevel", "error", "-i", wav, "-c:a", "aac", "-b:a", "128k",
                os.path.join(AQUI, "trilha.m4a")], check=True)
os.remove(wav)
print("trilha.m4a gerada")
