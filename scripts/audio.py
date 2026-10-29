#!/usr/bin/env python3
"""'Ouça o Plantão': narra o Resumo do Plantão com a voz do Gemini (mesma chave gratuita do resumo).
Só gera quando há um resumo novo. Saída: plantao.mp3 (publicado à parte, no ramo 'audio') e audio.json."""
import base64, json, os, subprocess, sys, urllib.error, urllib.request, wave
from datetime import datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
MODELOS = [m.strip() for m in os.environ.get("AUDIO_MODELOS", "gemini-3.8-flash-tts,gemini-2.5-flash-preview-tts").split(",") if m.strip()]
VOZ = os.environ.get("AUDIO_VOZ", "Charon")
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
SECOES = {"Política": "Na política", "IA": "Em inteligência artificial", "Futebol": "No futebol", "Agro": "No agro",
          "Mercado": "No mercado"}

def roteiro(r):
    q = datetime.strptime(r["gerado_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(BRT)
    partes = [f"Plantão Informa. Resumo das {q.hour} horas desta {DIAS[q.weekday()]}, {q.day} de {MESES[q.month - 1]}.",
              r["abertura"]]
    for s in r["secoes"]:
        partes.append(f"{SECOES.get(s['secao'], s['secao'])}. {s['texto']}")
    partes.append("Esse foi o resumo do Plantão Informa. Notícias, cotações e tabelas atualizadas de hora em hora "
                  "em plantão informa ponto com ponto b r.")
    return "\n\n".join(partes), q

def falar(texto, chave):
    pedido = ("Leia em português do Brasil, como um locutor de rádio jornalístico: tom neutro, claro e em ritmo natural, "
              "com pausas curtas entre os assuntos.\n\n" + texto)
    corpo = {"contents": [{"parts": [{"text": pedido}]}],
             "generationConfig": {"responseModalities": ["AUDIO"],
                                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOZ}}}}}
    erros = []
    for modelo in MODELOS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={chave}"
        req = urllib.request.Request(url, data=json.dumps(corpo).encode(), method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r: res = json.loads(r.read().decode())
            p = res["candidates"][0]["content"]["parts"][0]["inlineData"]
            return base64.b64decode(p["data"]), p.get("mimeType", ""), modelo
        except urllib.error.HTTPError as e:
            erros.append(f"{modelo}: {e.code} {e.read().decode('utf-8', 'replace')[:200]}")
        except Exception as e:
            erros.append(f"{modelo}: {e!r}")
    raise SystemExit("Voz indisponível: " + " | ".join(erros))

def ffmpeg():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"

def main():
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not chave: print("Sem GEMINI_API_KEY; áudio desligado."); return
    r = json.load(open("resumo.json", encoding="utf-8"))
    try: atual = json.load(open("audio.json", encoding="utf-8"))
    except Exception: atual = {}
    if atual.get("resumo") == r["gerado_utc"] and not os.environ.get("AUDIO_FORCAR"):
        print("Áudio já gerado para este resumo."); return
    texto, q = roteiro(r)
    dados, mime, modelo = falar(texto, chave)
    bruto = "plantao_bruto.wav"
    if "wav" in mime:
        open(bruto, "wb").write(dados)
    else:   # PCM 16 bits mono 24 kHz (audio/L16)
        taxa = int((mime.split("rate=")[-1].split(";")[0]) if "rate=" in mime else 24000)
        with wave.open(bruto, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(dados)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", bruto, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "64k", "plantao.mp3"], check=True)
    os.remove(bruto)
    out = subprocess.run([ffmpeg(), "-i", "plantao.mp3", "-f", "null", "-"], capture_output=True, text=True).stderr
    try:
        h, m, s = out.split("Duration:")[1].split(",")[0].strip().split(":"); dur = int(h) * 3600 + int(m) * 60 + float(s)
    except Exception: dur = None
    json.dump({"resumo": r["gerado_utc"], "gerado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "hora": f"{q:%H}h", "duracao": round(dur) if dur else None, "modelo": modelo, "voz": VOZ},
              open("audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Áudio gerado com {modelo}: {round(dur or 0)} s, {os.path.getsize('plantao.mp3') // 1024} KB")
    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a") as f: f.write("novo=1\n")

if __name__ == "__main__":
    main()
