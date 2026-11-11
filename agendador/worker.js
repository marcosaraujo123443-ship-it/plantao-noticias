// Agendador do Plantão Informa: o GitHub atrasa ou pula muitos horários agendados dos workflows,
// então este Worker do Cloudflare (cron a cada 15 min) dispara os workflows por "repository_dispatch".
const REPO = "marcosaraujo123443-ship-it/plantao-noticias";

function tarefas(d) {
  const h = d.getUTCHours(), m = d.getUTCMinutes(), dia = d.getUTCDay(), util = dia >= 1 && dia <= 5, slot = Math.floor(m / 15);
  const t = [];
  if (slot === 0 && [0, 1, 2, 4, 7].concat([...Array(14).keys()].map(x => x + 10)).includes(h)) t.push("noticias");  // 7h–23h, 21h, 22h, 1h de Brasília
  if ((util && h >= 12 && h <= 21) || (slot === 1 && h % 3 === 0)) t.push("mercado");                                 // pregão a cada 15 min
  if (slot === 1) t.push("futebol");
  if (util && h >= 11 && h <= 22 && slot % 2 === 0) t.push("agro");
  if (slot === 2 && ((h >= 9 && h <= 23 && h % 2 === 1) || h === 1)) t.push("tempo");
  return t;
}

async function disparar(env, tipo) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/dispatches`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${env.GH_PAT}`, "Accept": "application/vnd.github+json", "User-Agent": "plantao-agendador",
               "Content-Type": "application/json" },
    body: JSON.stringify({ event_type: tipo }),
  });
  return `${tipo}:${r.status}`;
}

export default {
  async scheduled(evento, env, ctx) {
    const lista = tarefas(new Date(evento.scheduledTime));
    ctx.waitUntil(Promise.all(lista.map(t => disparar(env, t))).then(r => console.log(r.join(" "))));
  },
  async fetch(req, env) {   // conferência manual: GET /?ver=1 mostra o que seria disparado agora (não dispara)
    return new Response(JSON.stringify({ agora: new Date().toISOString(), tarefas: tarefas(new Date()) }), { headers: { "content-type": "application/json" } });
  },
};
