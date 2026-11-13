/* Forex: moedas contra o real e principais pares do mundo (Plantão Informa). Dados: /forex.json */
(function(){
  var raiz=document.querySelector('[data-forex]'); if(!raiz) return;
  var css='.fx{--fi:var(--ink-2,#4a5873);--fr:var(--rule,#d9e0ea);--fc:var(--card,#fff);--ft:var(--ink,#0a1d3d);--fp:var(--paper,#f5f7fa);background:var(--fc);border:1px solid var(--fr);color:var(--ft);min-width:0}'+
  '.fx-h{padding:16px 16px 10px;border-bottom:1px solid var(--fr);display:grid;grid-template-columns:minmax(0,1fr);gap:10px}.fx-h h3{margin:0;font:700 19px Georgia,serif}.fx-h p{margin:0;font-size:13.5px;color:var(--fi)}'+
  '.fx-sg{display:flex;flex-wrap:wrap;border:1px solid var(--fr);border-radius:8px;overflow:hidden;width:max-content;max-width:100%}.fx-sg button{font:600 13px system-ui;padding:7px 12px;border:0;background:var(--fp);color:var(--fi);cursor:pointer}.fx-sg button.on{background:var(--ft);color:var(--fc)}'+
  '.fx-d{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;padding:10px 16px 0;font-size:13.5px;color:var(--fi)}.fx-d b{font:800 18px system-ui;color:var(--ft)}'+
  '.fx-t{width:100%;border-collapse:collapse;font-size:14px}.fx-t th{font:600 11.5px system-ui;color:var(--fi);text-transform:uppercase;text-align:left;padding:8px 10px;border-bottom:1px solid var(--fr)}'+
  '.fx-t td{padding:8px 10px;border-bottom:1px solid var(--fr);vertical-align:middle}.fx-t .n{text-align:right;white-space:nowrap}.fx-t small{display:block;font-size:12px;color:var(--fi)}.fx-t b{font-weight:800}'+
  '.fx .up{color:#137a3d}.fx .down{color:#c0262d}.fx-sp{width:84px;height:26px}@media(max-width:560px){.fx-t .fx-m,.fx-t .fx-s{display:none}.fx-t td,.fx-t th{padding-inline:6px}}'+
  '.fx-n{margin:0;padding:8px 16px 14px;font-size:12.5px;color:var(--fi)}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  raiz.className='fx quadro';
  raiz.innerHTML='<header class="fx-h"><h3>Câmbio (Forex)</h3><p>O mercado global de moedas: quanto vale cada moeda em reais e os pares mais negociados do mundo.</p>'+
    '<div class="fx-sg" role="group" aria-label="Grupo de moedas"><button class="on" data-fxg="real" aria-pressed="true">Moedas em reais</button><button data-fxg="pares" aria-pressed="false">Principais pares</button></div></header>'+
    '<div class="fx-d" data-fxd></div><div class="tw"><table class="fx-t"><thead><tr><th>Moeda</th><th class="n">Cotação</th><th class="n">Dia</th><th class="n fx-m">30 dias</th><th class="n fx-s">Tendência</th></tr></thead><tbody data-fxb><tr><td colspan="5">Carregando as cotações…</td></tr></tbody></table></div>'+
    '<p class="fx-n" data-fxn></p>';
  function q(s){return raiz.querySelector(s)}
  var D=null, G='real';
  function nf(v,c){return v==null?'–':v.toLocaleString('pt-BR',{minimumFractionDigits:c,maximumFractionDigits:c})}
  function casas(v){return v>=100?2:v>=1?4:v>=0.01?4:6}
  function pv(v){ if(v==null) return '<span>–</span>'; return '<span class="'+(v>0?'up':v<0?'down':'')+'">'+(v>0?'▲ +':v<0?'▼ ':'')+nf(v,2)+'%</span>'; }
  function spark(h){ if(!h||h.length<2) return ''; var mn=Math.min.apply(0,h), mx=Math.max.apply(0,h), r=mx-mn||1;
    var pts=h.map(function(x,i){return (i*84/(h.length-1)).toFixed(1)+','+(24-(x-mn)/r*22).toFixed(1)}).join(' ');
    return '<svg class="fx-sp" viewBox="0 0 84 26" aria-hidden="true"><polyline fill="none" stroke="'+(h[h.length-1]>=h[0]?'#137a3d':'#c0262d')+'" stroke-width="1.6" points="'+pts+'"/></svg>'; }
  function desenhar(){
    var L=D[G]||[];
    q('[data-fxb]').innerHTML=L.map(function(x){return '<tr><td><b>'+x.bandeira+' '+x.par+'</b><small>'+x.nome+'</small></td><td class="n">'+(G==='real'?'R$ ':'')+nf(x.preco,casas(x.preco))+'</td><td class="n">'+pv(x.dia)+'</td><td class="n fx-m">'+pv(x.mes)+'</td><td class="n fx-s">'+spark(x.hist)+'</td></tr>'}).join('')||'<tr><td colspan="5">Sem dados agora.</td></tr>';
    var x=D.dxy; q('[data-fxd]').innerHTML=x?'<span>💵 <b>DXY '+nf(x.preco,2)+'</b></span><span>'+pv(x.dia)+' no dia · '+pv(x.mes)+' em 30 dias</span><span>Índice que mede o dólar contra seis moedas fortes: quando sobe, o dólar está se valorizando no mundo.</span>':'';
    var hr=new Date(D.atualizado_utc).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
    q('[data-fxn]').textContent='Cotações de mercado consultadas em '+hr+' (horário de Brasília), com atraso. Nos pares, o número mostra quanto vale 1 unidade da primeira moeda na segunda (ex.: EUR/USD 1,08 = 1 euro vale US$ 1,08). Fonte: Yahoo Finance. Apenas informativo.';
  }
  raiz.addEventListener('click',function(ev){var b=ev.target.closest('[data-fxg]'); if(!b) return; G=b.getAttribute('data-fxg');
    [].forEach.call(b.parentNode.children,function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)}); D&&desenhar(); });
  function carregar(){ if(D) return; D={};
    fetch('/forex.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(j){D=j;desenhar()})
      .catch(function(){q('[data-fxb]').innerHTML='<tr><td colspan="5">Não foi possível carregar as cotações agora.</td></tr>';D=null});
  }
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(e){if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()}},{rootMargin:'300px'});io.observe(raiz)} else carregar();
})();
