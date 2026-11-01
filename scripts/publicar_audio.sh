#!/usr/bin/env bash
# Publica a narração recém-gerada (plantao.mp3): no ramo "audio" (player do site) e como episódio do podcast
# (arquivo guardado nas Releases do GitHub + podcast.json/podcast.xml). Precisa de GH_TOKEN e GITHUB_REPOSITORY.
set -u
[ -f plantao.mp3 ] || exit 0
read TAG ARQ < <(python3 scripts/podcast.py nome)
cp plantao.mp3 "$ARQ"
# 1) episódio do podcast (histórico)
gh release view "$TAG" >/dev/null 2>&1 || gh release create "$TAG" --title "Áudios do Resumo do Plantão ($TAG)" \
   --notes "Narrações do Resumo do Plantão (podcast). Feed: https://plantaoinforma.com.br/podcast.xml" --latest=false >/dev/null
if gh release upload "$TAG" "$ARQ" --clobber >/dev/null; then
  python3 scripts/podcast.py registrar "$TAG" "$ARQ"
else
  echo "::warning::não foi possível guardar o episódio do podcast"
fi
rm -f "$ARQ"
# 2) player do site: só a versão atual no ramo "audio"
d=$(mktemp -d); mv plantao.mp3 "$d/"
if ! (cd "$d" && git init -q -b audio && git add plantao.mp3 \
      && git -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" commit -qm "Ouça o Plantão" \
      && git push -fq "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" audio); then
  git checkout -- audio.json 2>/dev/null || rm -f audio.json   # sem MP3 publicado, sem player novo
  echo "::warning::não foi possível publicar o áudio no site"
fi
