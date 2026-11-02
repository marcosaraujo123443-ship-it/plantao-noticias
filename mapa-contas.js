/* Mapa das contas públicas por estado (Plantão Informa).
   Uso: <div data-mapa-contas></div> e <script src="/mapa-contas.js" defer></script>.
   Dados: /estados.json (Tesouro Nacional, SICONFI/RREO) e /mapa_ufs.json (contornos dos estados). */
(function(){
  var raiz=document.querySelector('[data-mapa-contas]'); if(!raiz) return;
  var css='.mc{--mi:var(--ink-2,var(--ink2,#4a5873));--mr:var(--rule,#d9e0ea);--mc:var(--card,#fff);--mt:var(--ink,#0a1d3d);--mp:var(--paper,#f5f7fa);background:var(--mc);border:1px solid var(--mr);color:var(--mt);margin:18px 0}'+
  '.mc-h{padding:16px 16px 10px;border-bottom:1px solid var(--mr);display:grid;gap:10px}.mc-h h3{margin:0;font:700 19px Georgia,serif}'+
  '.mc-f{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}.mc-f label{display:flex;gap:6px;align-items:center;font:600 13px system-ui;color:var(--mi)}'+
  '.mc-f select{font:600 14.5px system-ui;color:var(--mt);background:var(--mp);border:1px solid var(--mr);border-radius:8px;padding:6px 8px;max-width:100%}'+
  '.mc-seg{display:flex;flex-wrap:wrap;gap:6px}.mc-seg button{font:600 13px system-ui;border:1px solid var(--mr);background:var(--mp);color:var(--mi);border-radius:999px;padding:6px 11px;cursor:pointer}.mc-seg button.on{background:var(--mt);border-color:var(--mt);color:var(--mc)}'+
  '.mc-b{display:grid;gap:14px;padding:12px 16px 16px}@media(min-width:900px){.mc-b{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr)}}'+
  '.mc svg{width:100%;height:auto;display:block}.mc-uf{stroke:var(--mc);stroke-width:1.2;cursor:pointer;transition:fill .25s}.mc-uf:hover{stroke:var(--mt);stroke-width:1.6}.mc-uf.on{stroke:var(--mt);stroke-width:2.6}'+
  '.mc-leg{display:flex;flex-wrap:wrap;gap:4px 12px;font:12px system-ui;color:var(--mi);margin-top:6px}.mc-leg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:4px;vertical-align:-2px}'+
  '.mc-card{overflow:hidden;border:1px solid var(--mr);border-radius:10px;padding:12px 14px;background:var(--mp)}.mc-card b.v{display:block;font:800 24px system-ui;margin:2px 0}.mc-card small{color:var(--mi);font-size:12.5px}'+
  '.mc-cmp{width:100%;table-layout:fixed;border-collapse:collapse;font-size:13.5px;margin-top:10px}.mc-cmp th:first-child{width:36%}.mc-cmp th,.mc-cmp td{padding:6px 4px;overflow:hidden;text-overflow:ellipsis;border-bottom:1px solid var(--mr);text-align:right;white-space:nowrap}.mc-cmp th:first-child,.mc-cmp td:first-child{text-align:left;white-space:normal}.mc-cmp th{font-size:11.5px;text-transform:uppercase;color:var(--mi)}'+
  '.mc-rk{list-style:none;margin:10px 0 0;padding:0;max-height:430px;overflow:auto}.mc-rk li{display:grid;grid-template-columns:2em 2.6em 1fr auto;gap:6px;align-items:center;padding:3px 0;font-size:13px;cursor:pointer}.mc-rk li.on{font-weight:800}'+
  '.mc-rk .bar{height:10px;border-radius:5px;background:var(--mr);overflow:hidden}.mc-rk .bar i{display:block;height:100%}.mc-rk span:first-child{color:var(--mi);text-align:right}'+
  '.mc-n{margin:0;padding:0 16px 14px;font-size:12.5px;color:var(--mi)}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  var AREAS=['Educação','Saúde','Segurança Pública','Previdência Social','Transporte','Assistência Social','Saneamento','Habitação','Urbanismo','Agricultura','Gestão Ambiental','Ciência e Tecnologia','Cultura','Desporto e Lazer','Judiciária','Legislativa','Administração'];
  var IND=[['saldo','Saldo (arrecadado − gasto)'],['receita','Arrecadação total'],['impostos','Impostos arrecadados'],['transf','Repasses da União'],['gasto','Gasto total'],['pessoal','Gasto com pessoal'],['invest','Investimentos']];
  raiz.innerHTML='<section class="mc" aria-label="Mapa das contas públicas por estado"><div class="mc-h"><h3>Mapa das contas por estado</h3>'+
    '<div class="mc-f"><label>Mostrar <select data-mi><optgroup label="Contas">'+IND.map(function(x){return '<option value="'+x[0]+'">'+x[1]+'</option>'}).join('')+'</optgroup><optgroup label="Gasto por área">'+AREAS.map(function(a){return '<option value="f:'+a+'">'+a+'</option>'}).join('')+'</optgroup></select></label>'+
    '<div class="mc-seg" data-mm role="group" aria-label="Medida"><button data-m="pc" class="on">Por habitante</button><button data-m="tot">Total</button><button data-m="pct">% do gasto</button></div>'+
    '<div class="mc-seg" data-ma role="group" aria-label="Período"><button data-a="atual" class="on">Ano atual</button><button data-a="anterior">Ano passado</button></div></div>'+
    '<p style="margin:0;font-size:13.5px;color:var(--mi)" data-mt>Carregando dados do Tesouro Nacional…</p></div>'+
    '<div class="mc-b"><div><svg data-ms role="img" aria-label="Mapa do Brasil por estado"></svg><div class="mc-leg" data-ml></div></div>'+
    '<div><div class="mc-card" data-mcard></div><ol class="mc-rk" data-mrk></ol></div></div>'+
    '<p class="mc-n">Fonte: Tesouro Nacional, SICONFI (Relatório Resumido da Execução Orçamentária enviado por cada estado a cada bimestre). Valores acumulados no ano; gasto = despesa liquidada. Antes do fim do ano é comum o saldo aparecer positivo, porque parte das despesas só é liquidada nos últimos meses. Toque em um estado para ver os números e comparar.</p></section>';
  var EST=null, MAPA=null, IN='saldo', ME='pc', AN='atual', SEL=null, CMP='UF';
  function q(s){return raiz.querySelector(s)}
  function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function lin(L,n){for(var i=0;i<(L||[]).length;i++) if(L[i].n===n) return L[i]; return {}}
  function bruto(b,ind){
    if(!b) return null; var R=b.receitas, D=b.despesas;
    var rt=lin(R,'Total arrecadado').realizado, dt=lin(D,'Total').liquidado;
    if(ind==='saldo') return rt!=null&&dt!=null?rt-dt:null;
    if(ind==='receita') return rt; if(ind==='impostos') return lin(R,'Impostos, taxas e contribuições de melhoria').realizado;
    if(ind==='transf') return lin(R,'das quais, da União').realizado;
    if(ind==='gasto') return dt; if(ind==='pessoal') return lin(D,'Pessoal e encargos').liquidado; if(ind==='invest') return lin(D,'Investimentos').liquidado;
    if(ind.indexOf('f:')===0) return lin(b.funcoes,ind.slice(2)).liquidado||0;
    return null;
  }
  function valor(uf,ind){
    var x=EST.estados[uf]; if(!x) return null; var b=x[AN]; var v=bruto(b,ind); if(v==null) return null;
    if(ME==='pc') return b.populacao?v/b.populacao:null;
    if(ME==='pct'){ var dt=lin(b.despesas,'Total').liquidado; var rt=lin(b.receitas,'Total arrecadado').realizado;
      var base=(ind==='receita'||ind==='impostos'||ind==='transf')?rt:dt; return base?v/base*100:null; }
    return v;
  }
  function fmt(v){ if(v==null) return '–'; if(ME==='pct') return v.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
    var a=Math.abs(v), s=v<0?'−':'';
    if(ME==='pc') return s+'R$ '+a.toLocaleString('pt-BR',{maximumFractionDigits:0});
    if(a>=1e9) return s+'R$ '+(a/1e9).toLocaleString('pt-BR',{maximumFractionDigits:1})+' bi'; if(a>=1e6) return s+'R$ '+(a/1e6).toLocaleString('pt-BR',{maximumFractionDigits:0})+' mi';
    return s+'R$ '+a.toLocaleString('pt-BR',{maximumFractionDigits:0}); }
  var SEQ=['#dbeafe','#93c5fd','#3b82f6','#1d4ed8','#1e3a8a'], POS=['#bbf7d0','#4ade80','#15803d'], NEG=['#fecaca','#f87171','#b91c1c'];
  function cores(vals){
    var v=vals.filter(function(x){return x!=null}).sort(function(a,b){return a-b});
    if(IN==='saldo'&&ME!=='pct'){
      // tons pela posição entre os estados do mesmo sinal (um estado fora da curva não apaga os outros)
      var p=v.filter(function(x){return x>=0}), n=v.filter(function(x){return x<0}).map(Math.abs).sort(function(a,b){return a-b});
      function nivel(lst,x){ if(lst.length<3) return 1; var t1=lst[Math.floor(lst.length/3)], t2=lst[Math.floor(lst.length*2/3)]; return x<=t1?0:x<=t2?1:2; }
      return {f:function(x){ if(x==null) return 'var(--mr)'; return x>=0?POS[nivel(p,x)]:NEG[nivel(n,Math.abs(x))]; },
        leg:[['Déficit maior',NEG[2]],['Déficit',NEG[0]],['Superávit',POS[0]],['Superávit maior',POS[2]]]}; }
    var qs=[0.2,0.4,0.6,0.8].map(function(p){return v[Math.floor(p*(v.length-1))]});
    return {f:function(x){ if(x==null) return 'var(--mr)'; var i=0; while(i<4&&x>qs[i]) i++; return SEQ[i]; },
      leg:SEQ.map(function(c,i){return [(i===0?'até ':'')+fmt(i===0?qs[0]:qs[i-1])+(i===0?'':i===4?' ou mais':' a '+fmt(qs[i])),c]})};
  }
  var NOME={};
  function desenhar(){
    if(!EST||!MAPA) return;
    var ufs=Object.keys(MAPA.ufs), vals={}, lista=[];
    ufs.forEach(function(u){vals[u]=valor(u,IN); if(vals[u]!=null) lista.push(u)});
    var c=cores(ufs.map(function(u){return vals[u]}));
    q('[data-ms]').innerHTML=ufs.map(function(u){var x=EST.estados[u]||{}; return '<path class="mc-uf'+(u===SEL?' on':'')+'" data-u="'+u+'" d="'+MAPA.ufs[u]+'" fill="'+c.f(vals[u])+'"><title>'+esc((x.nome||u)+': '+fmt(vals[u]))+'</title></path>'}).join('');
    q('[data-ml]').innerHTML=c.leg.map(function(l){return '<span><i style="background:'+l[1]+'"></i>'+esc(l[0])+'</span>'}).join('');
    var rotulo=q('[data-mi]').selectedOptions[0].textContent, b=(EST.estados.SP||{})[AN]||{};
    var mes=b.periodo? (b.periodo>=6?'dezembro':['','fevereiro','abril','junho','agosto','outubro'][b.periodo]):'';
    q('[data-mt]').textContent=rotulo+' · '+(ME==='pc'?'por habitante':ME==='pct'?(IN==='receita'||IN==='impostos'||IN==='transf'?'% da arrecadação':'% do gasto total'):'valor total')+' · '+(b.ano||'')+(mes?', acumulado até '+mes:'');
    lista.sort(function(a,b){return vals[b]-vals[a]});
    var mx=Math.max.apply(0,lista.map(function(u){return Math.abs(vals[u])}))||1;
    q('[data-mrk]').innerHTML=lista.map(function(u,i){var v=vals[u];
      return '<li data-u="'+u+'" class="'+(u===SEL?'on':'')+'"><span>'+(i+1)+'º</span><b>'+u+'</b><span class="bar"><i style="width:'+Math.round(Math.abs(v)/mx*100)+'%;background:'+c.f(v)+'"></i></span><span>'+fmt(v)+'</span></li>'}).join('');
    cartao(vals,lista);
  }
  function cartao(vals,lista){
    var el=q('[data-mcard]'), u=SEL||lista[0]; if(!u){el.innerHTML='';return}
    var x=EST.estados[u], pos=lista.indexOf(u)+1, br=valor('UF',IN);
    var linhas=[['saldo','Saldo'],['receita','Arrecadado'],['gasto','Gasto'],['f:Educação','Educação'],['f:Saúde','Saúde'],['f:Segurança Pública','Segurança'],['invest','Invest.']];
    if(IN.indexOf('f:')===0&&['f:Educação','f:Saúde','f:Segurança Pública'].indexOf(IN)<0) linhas.splice(3,0,[IN,IN.slice(2)]);
    var opts=Object.keys(EST.estados).filter(function(k){return k!=='BR'&&k!==u}).sort(function(a,b){return a==='UF'?-1:b==='UF'?1:EST.estados[a].nome.localeCompare(EST.estados[b].nome)});
    var y=EST.estados[CMP]?CMP:'UF';
    el.innerHTML='<small>'+(SEL?'Estado selecionado':'Primeiro do ranking')+'</small><div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline;flex-wrap:wrap"><b style="font-size:17px">'+esc(x.nome)+'</b><small>'+pos+'º de '+lista.length+'</small></div>'+
      '<b class="v">'+fmt(vals[u])+'</b><small>Média dos estados: '+fmt(br)+'</small>'+
      '<table class="mc-cmp"><thead><tr><th>'+(ME==='pc'?'Por habitante':ME==='pct'?'% do total':'Total')+'</th><th>'+u+'</th><th><select data-mc aria-label="Comparar com" style="font:600 12px system-ui;width:8.5em;max-width:100%">'+
      opts.map(function(k){return '<option value="'+k+'"'+(k===y?' selected':'')+'>'+(k==='UF'?'Média dos estados':esc(EST.estados[k].nome))+'</option>'}).join('')+'</select></th></tr></thead><tbody>'+
      linhas.map(function(l){var a=valor(u,l[0]), c2=valor(y,l[0]); return '<tr'+(l[0]===IN?' style="font-weight:800"':'')+'><td>'+esc(l[1])+'</td><td>'+fmt(a)+'</td><td>'+fmt(c2)+'</td></tr>'}).join('')+'</tbody></table>';
  }
  raiz.addEventListener('click',function(ev){
    var t=ev.target.closest('[data-u]'); if(t){SEL=t.getAttribute('data-u'); desenhar(); return}
    var m=ev.target.closest('[data-m]'); if(m){ME=m.dataset.m; raiz.querySelectorAll('[data-m]').forEach(function(b){b.classList.toggle('on',b===m)}); desenhar(); return}
    var a=ev.target.closest('[data-a]'); if(a){AN=a.dataset.a; raiz.querySelectorAll('[data-a]').forEach(function(b){b.classList.toggle('on',b===a)}); desenhar(); return}
  });
  raiz.addEventListener('change',function(ev){
    if(ev.target.matches('[data-mi]')){IN=ev.target.value; if(IN==='saldo'&&ME==='pct'){ME='pc'; raiz.querySelectorAll('[data-m]').forEach(function(b){b.classList.toggle('on',b.dataset.m==='pc')})} desenhar()}
    if(ev.target.matches('[data-mc]')){CMP=ev.target.value; desenhar()}
  });
  function carregar(){
    if(EST) return; EST={};
    var base=(document.querySelector('base')||{}).href||'/';
    Promise.all([fetch('/estados.json',{cache:'no-cache'}).then(function(r){return r.json()}),fetch('/mapa_ufs.json',{cache:'force-cache'}).then(function(r){return r.json()})])
      .then(function(r){EST=r[0];MAPA=r[1]; q('[data-ms]').setAttribute('viewBox','0 0 '+MAPA.w+' '+MAPA.h); desenhar()})
      .catch(function(){q('[data-mt]').textContent='Não foi possível carregar o mapa agora.';EST=null});
  }
  // carrega quando o mapa aparece na tela (na capa ele fica na aba Política)
  if('IntersectionObserver' in window){ var io=new IntersectionObserver(function(e){ if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()} }); io.observe(raiz); }
  else carregar();
})();
