/* Mapa da produção agropecuária por estado (Plantão Informa). Dados: /agro_estados.json (IBGE) e /mapa_ufs.json. */
(function(){
  var raiz=document.querySelector('[data-mapa-agro]'); if(!raiz) return;
  var css='.ma{--mi:var(--ink-2,var(--ink2,#4a5873));--mr:var(--rule,#d9e0ea);--mc:var(--card,#fff);--mt:var(--ink,#0a1d3d);--mp:var(--paper,#f5f7fa);background:var(--mc);border:1px solid var(--mr);color:var(--mt)}'+
  '.ma-h{padding:16px 16px 10px;border-bottom:1px solid var(--mr);display:grid;gap:8px}.ma-h h3{margin:0;font:700 19px Georgia,serif}.ma-h p{margin:0;font-size:13.5px;color:var(--mi)}'+
  '.ma-h label{min-width:0}.ma-h select{min-width:0;width:100%;font:600 14.5px system-ui;color:var(--mt);background:var(--mp);border:1px solid var(--mr);border-radius:8px;padding:6px 8px;max-width:100%}'+
  '.ma-b{display:grid;gap:14px;padding:12px 16px 16px}.ma-b>div{min-width:0}@media(min-width:900px){.ma-b{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr)}}.ma svg{width:100%;height:auto;display:block}.ma-uf{stroke:var(--mc);stroke-width:1.2;cursor:pointer;transition:fill .25s}.ma-uf:hover{stroke:var(--mt)}.ma-uf.on{stroke:var(--mt);stroke-width:2.6}'+
  '.ma-leg{display:flex;flex-wrap:wrap;gap:4px 12px;font:12px system-ui;color:var(--mi);margin-top:6px}.ma-leg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:4px;vertical-align:-2px}'+
  '.ma-card{border:1px solid var(--mr);border-radius:10px;padding:12px 14px;background:var(--mp)}.ma-card b.v{display:block;font:800 24px system-ui;margin:2px 0}.ma-card small{color:var(--mi);font-size:12.5px}'+
  '.ma-t{width:100%;table-layout:fixed;border-collapse:collapse;font-size:13.5px;margin-top:10px}.ma-t td{padding:5px 4px;border-bottom:1px solid var(--mr)}.ma-t td.n{text-align:right;white-space:nowrap;width:9.5em}.ma-t tr.on td{font-weight:800}'+
  '.ma-rk{list-style:none;margin:10px 0 0;padding:0;max-height:300px;overflow:auto}.ma-rk li{display:grid;grid-template-columns:2em 2.6em 1fr auto;gap:6px;align-items:center;padding:3px 0;font-size:13px;cursor:pointer}.ma-rk li.on{font-weight:800}'+
  '.ma-rk .bar{height:10px;border-radius:5px;background:var(--mr);overflow:hidden}.ma-rk .bar i{display:block;height:100%}.ma-rk span:first-child{color:var(--mi);text-align:right}.ma-n{margin:0;padding:0 16px 14px;font-size:12.5px;color:var(--mi)}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  var NOME={AC:'Acre',AL:'Alagoas',AP:'Amapá',AM:'Amazonas',BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MT:'Mato Grosso',MS:'Mato Grosso do Sul',MG:'Minas Gerais',PA:'Pará',PB:'Paraíba',PR:'Paraná',PE:'Pernambuco',PI:'Piauí',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RS:'Rio Grande do Sul',RO:'Rondônia',RR:'Roraima',SC:'Santa Catarina',SP:'São Paulo',SE:'Sergipe',TO:'Tocantins'};
  // [chave, rótulo, tipo de número, período]
  var IND=[['agro_pib_br','Contribuição do agro do estado para o PIB do Brasil','pct','pib'],['part_agro_br','Participação no agro brasileiro','pct','pib'],
    ['agro_no_estado','Peso do agro na economia do estado','pct','pib'],['va_agro','PIB do agro (valor adicionado)','rs','pib'],['vp_agricola','Valor da produção agrícola','rs','vp_agricola'],
    ['soja','Soja','t','safra'],['milho','Milho','t','safra'],['cana','Cana-de-açúcar','t','safra'],['cafe','Café','t','safra'],['algodao','Algodão','t','safra'],
    ['arroz','Arroz','t','safra'],['feijao','Feijão','t','safra'],['trigo','Trigo','t','safra'],['laranja','Laranja','t','safra'],['bovinos','Rebanho bovino','cab','bovinos']];
  raiz.innerHTML='<section class="ma" aria-label="Mapa da produção agropecuária por estado"><div class="ma-h"><h3>Mapa do agro por estado</h3>'+
    '<label style="display:flex;gap:6px;align-items:center;font:600 13px system-ui;color:var(--mi)">Mostrar <select data-ai>'+
    '<optgroup label="Agro no PIB">'+IND.slice(0,4).map(o).join('')+'</optgroup><optgroup label="Produção">'+IND.slice(4).map(o).join('')+'</optgroup></select></label>'+
    '<p data-at>Carregando dados do IBGE…</p></div><div class="ma-b"><div><svg data-as role="img" aria-label="Mapa do Brasil por estado"></svg><div class="ma-leg" data-al></div></div>'+
    '<div><div class="ma-card" data-ac></div><ol class="ma-rk" data-ar></ol></div></div>'+
    '<p class="ma-n">Fonte: IBGE. Produção das lavouras: Levantamento Sistemático da Produção Agrícola (estimativa da safra do ano); valor da produção: Produção Agrícola Municipal; rebanho: Pesquisa da Pecuária Municipal; PIB do agro: Contas Regionais (o detalhe por atividade sai com cerca de 4 anos de atraso). Toque em um estado para ver tudo dele.</p></section>';
  function o(x){return '<option value="'+x[0]+'">'+x[1]+'</option>'}
  function q(s){return raiz.querySelector(s)}
  var D=null, M=null, IN='agro_pib_br', SEL=null;
  function fmt(v,t){ if(v==null) return '–';
    if(t==='pct') return v.toLocaleString('pt-BR',{maximumFractionDigits:v<1?2:1})+'%';
    if(t==='rs') return v>=1e9?'R$ '+(v/1e9).toLocaleString('pt-BR',{maximumFractionDigits:1})+' bi':'R$ '+(v/1e6).toLocaleString('pt-BR',{maximumFractionDigits:0})+' mi';
    var u=t==='cab'?' cabeças':' t'; if(v>=1e6) return (v/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1})+' mi'+u; if(v>=1e3) return (v/1e3).toLocaleString('pt-BR',{maximumFractionDigits:0})+' mil'+u; return v.toLocaleString('pt-BR')+u; }
  var COR=['#ecf7e3','#c1e3a5','#86c665','#4a9d3a','#1f6b27'];
  function ind(k){for(var i=0;i<IND.length;i++) if(IND[i][0]===k) return IND[i]}
  function desenhar(){
    if(!D||!M) return; var I=ind(IN), ufs=Object.keys(M.ufs), v={}, lista=[];
    ufs.forEach(function(u){var x=(D.estados[u]||{})[IN]; v[u]=x==null?null:x; if(x) lista.push(u)});
    var vs=lista.map(function(u){return v[u]}).sort(function(a,b){return a-b});
    var qs=[.2,.4,.6,.8].map(function(p){return vs[Math.floor(p*(vs.length-1))]});
    function cor(x){ if(!x) return 'var(--mr)'; var i=0; while(i<4&&x>qs[i]) i++; return COR[i] }
    q('[data-as]').innerHTML=ufs.map(function(u){return '<path class="ma-uf'+(u===SEL?' on':'')+'" data-u="'+u+'" d="'+M.ufs[u]+'" fill="'+cor(v[u])+'"><title>'+NOME[u]+': '+fmt(v[u],I[2])+'</title></path>'}).join('');
    q('[data-al]').innerHTML=COR.map(function(c,i){return '<span><i style="background:'+c+'"></i>'+(i===0?'até '+fmt(qs[0],I[2]):i===4?fmt(qs[3],I[2])+' ou mais':fmt(qs[i-1],I[2])+' a '+fmt(qs[i],I[2]))+'</span>'}).join('')+'<span><i style="background:var(--mr)"></i>sem produção</span>';
    var per=(D.periodos||{})[I[3]]||'';
    q('[data-at]').textContent=I[1]+' · '+(I[3]==='safra'?'safra estimada em '+per:I[3]==='pib'?'ano de '+per:per);
    lista.sort(function(a,b){return v[b]-v[a]}); var mx=v[lista[0]]||1;
    var tot=lista.reduce(function(s,u){return s+v[u]},0);
    q('[data-ar]').innerHTML=lista.map(function(u,i){return '<li data-u="'+u+'" class="'+(u===SEL?'on':'')+'"><span>'+(i+1)+'º</span><b>'+u+'</b><span class="bar"><i style="width:'+Math.round(v[u]/mx*100)+'%;background:'+cor(v[u])+'"></i></span><span>'+fmt(v[u],I[2])+'</span></li>'}).join('');
    var u=SEL||lista[0], e=D.estados[u]||{};
    var partBR=I[2]!=='pct'&&tot?' · '+(v[u]/tot*100).toLocaleString('pt-BR',{maximumFractionDigits:1})+'% do Brasil':'';
    q('[data-ac]').innerHTML='<small>'+(SEL?'Estado selecionado':'Primeiro do ranking')+'</small><div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:baseline"><b style="font-size:17px">'+NOME[u]+'</b><small>'+(lista.indexOf(u)+1||'–')+'º de '+lista.length+'</small></div>'+
      '<b class="v">'+fmt(v[u],I[2])+'</b><small>'+I[1]+partBR+'</small><table class="ma-t">'+
      IND.filter(function(x){return e[x[0]]!=null}).map(function(x){return '<tr class="'+(x[0]===IN?'on':'')+'"><td>'+x[1]+'</td><td class="n">'+fmt(e[x[0]],x[2])+'</td></tr>'}).join('')+'</table>';
  }
  raiz.addEventListener('click',function(ev){var t=ev.target.closest('[data-u]'); if(t){SEL=t.getAttribute('data-u'); desenhar()}});
  raiz.addEventListener('change',function(ev){if(ev.target.matches('[data-ai]')){IN=ev.target.value; desenhar()}});
  function carregar(){ if(D) return; D={};
    Promise.all([fetch('/agro_estados.json',{cache:'no-cache'}).then(function(r){return r.json()}),fetch('/mapa_ufs.json',{cache:'force-cache'}).then(function(r){return r.json()})])
      .then(function(r){D=r[0];M=r[1]; q('[data-as]').setAttribute('viewBox','0 0 '+M.w+' '+M.h); desenhar()})
      .catch(function(){q('[data-at]').textContent='Não foi possível carregar o mapa agora.';D=null});
  }
  if('IntersectionObserver' in window){ var io=new IntersectionObserver(function(e){ if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()} }); io.observe(raiz); } else carregar();
})();
