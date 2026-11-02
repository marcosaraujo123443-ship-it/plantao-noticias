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
  '.mc-b{display:grid;gap:14px;padding:12px 16px 16px}.mc-b>div{min-width:0}@media(min-width:900px){.mc-b{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr)}}'+
  '.mc svg{width:100%;height:auto;display:block}.mc-uf{stroke:var(--mc);stroke-width:1.2;cursor:pointer;transition:fill .25s}.mc-uf:hover{stroke:var(--mt);stroke-width:1.6}.mc-uf.on{stroke:var(--mt);stroke-width:2.6}'+
  '.mc-leg{display:flex;flex-wrap:wrap;gap:4px 12px;font:12px system-ui;color:var(--mi);margin-top:6px}.mc-leg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:4px;vertical-align:-2px}'+
  '.mc-card{overflow:hidden;border:1px solid var(--mr);border-radius:10px;padding:12px 14px;background:var(--mp)}.mc-card b.v{display:block;font:800 24px system-ui;margin:2px 0}.mc-card small{color:var(--mi);font-size:12.5px}'+
  '.mc-cmp{width:100%;table-layout:fixed;border-collapse:collapse;font-size:13.5px;margin-top:10px}.mc-cmp th:first-child{width:36%}.mc-cmp th,.mc-cmp td{padding:6px 4px;overflow:hidden;text-overflow:ellipsis;border-bottom:1px solid var(--mr);text-align:right;white-space:nowrap}.mc-cmp th:first-child,.mc-cmp td:first-child{text-align:left;white-space:normal}.mc-cmp th{font-size:11.5px;text-transform:uppercase;color:var(--mi)}'+
  '.mc-rk{list-style:none;margin:10px 0 0;padding:0;max-height:430px;overflow:auto}.mc-rk li{display:grid;grid-template-columns:2em 2.6em 1fr auto;gap:6px;align-items:center;padding:3px 0;font-size:13px;cursor:pointer}.mc-rk li.on{font-weight:800}'+
  '.mc-rk .bar{height:10px;border-radius:5px;background:var(--mr);overflow:hidden}.mc-rk .bar i{display:block;height:100%}.mc-rk span:first-child{color:var(--mi);text-align:right}'+
  '.mc-hist{margin-top:12px}.mc-hist svg{width:100%;height:auto;display:block}.mc-ht{margin:0 0 4px;font:600 12.5px system-ui;color:var(--mi)}'+
  '.mc-n{margin:0;padding:0 16px 14px;font-size:12.5px;color:var(--mi)}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  var AREAS=['Educação','Saúde','Segurança Pública','Previdência Social','Transporte','Assistência Social','Saneamento','Habitação','Urbanismo','Agricultura','Gestão Ambiental','Ciência e Tecnologia','Cultura','Desporto e Lazer','Judiciária','Legislativa','Administração'];
  var IND=[['saldo','Saldo (arrecadado − gasto)'],['saldo_sr','Saldo sem os repasses da União'],['propria','Arrecadação sem os repasses da União'],['receita','Arrecadação total'],['impostos','Impostos arrecadados'],['transf','Repasses da União'],['gasto','Gasto total'],['pessoal','Gasto com pessoal'],['invest','Investimentos']];
  raiz.innerHTML='<section class="mc" aria-label="Mapa das contas públicas por estado"><div class="mc-h"><h3>Mapa das contas por estado</h3>'+
    '<div class="mc-f"><label>Mostrar <select data-mi><optgroup label="Contas">'+IND.map(function(x){return '<option value="'+x[0]+'">'+x[1]+'</option>'}).join('')+'</optgroup><optgroup label="Gasto por área">'+AREAS.map(function(a){return '<option value="f:'+a+'">'+a+'</option>'}).join('')+'</optgroup></select></label>'+
    '<div class="mc-seg" data-mm role="group" aria-label="Medida"><button data-m="pc" class="on">Por habitante</button><button data-m="tot">Total</button><button data-m="pct">% do gasto</button></div>'+
    '<label>Ano <select data-ma aria-label="Ano"><option value="atual">Ano atual</option></select></label>'+
    '<label style="font-weight:500"><input type="checkbox" data-mif checked> Corrigir pela inflação</label></div>'+
    '<p style="margin:0;font-size:13.5px;color:var(--mi)" data-mt>Carregando dados do Tesouro Nacional…</p></div>'+
    '<div class="mc-b"><div><svg data-ms role="img" aria-label="Mapa do Brasil por estado"></svg><div class="mc-leg" data-ml></div></div>'+
    '<div><div class="mc-card" data-mcard></div><div class="mc-hist" data-mh></div><ol class="mc-rk" data-mrk></ol></div></div>'+
    '<p class="mc-n">Fonte: Tesouro Nacional, SICONFI (Relatório Resumido da Execução Orçamentária enviado por cada estado a cada bimestre). "Sem os repasses da União" tira da receita as transferências correntes do governo federal (FPE, SUS, convênios e outras), mostrando quanto o estado se sustenta sozinho; esse dado existe a partir de 2018. Anos anteriores: ano fechado (6º bimestre). Valores corrigidos pelo IPCA quando marcado; gasto = despesa liquidada. Antes do fim do ano é comum o saldo aparecer positivo, porque parte das despesas só é liquidada nos últimos meses. Toque em um estado para ver os números e comparar.</p></section>';
  var EST=null, MAPA=null, HIST=null, IN='saldo', ME='pc', AN='atual', SEL=null, CMP='UF', INF=true;
  function q(s){return raiz.querySelector(s)}
  function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function lin(L,n){for(var i=0;i<(L||[]).length;i++) if(L[i].n===n) return L[i]; return {}}
  function bruto(b,ind){
    if(!b) return null; var R=b.receitas, D=b.despesas;
    var rt=lin(R,'Total arrecadado').realizado, dt=lin(D,'Total').liquidado;
    var tu=lin(R,'das quais, da União').realizado;
    if(ind==='saldo') return rt!=null&&dt!=null?rt-dt:null;
    if(ind==='saldo_sr') return rt!=null&&dt!=null&&tu!=null?rt-tu-dt:null;
    if(ind==='propria') return rt!=null&&tu!=null?rt-tu:null;
    if(ind==='receita') return rt; if(ind==='impostos') return lin(R,'Impostos, taxas e contribuições de melhoria').realizado;
    if(ind==='transf') return lin(R,'das quais, da União').realizado;
    if(ind==='gasto') return dt; if(ind==='pessoal') return lin(D,'Pessoal e encargos').liquidado; if(ind==='invest') return lin(D,'Investimentos').liquidado;
    if(ind.indexOf('f:')===0) return lin(b.funcoes,ind.slice(2)).liquidado||0;
    return null;
  }
  // ano fechado do histórico (estados_historico.json): rt, imp, tu, dt, pes, inv, pop e f (gasto por área)
  function brutoH(a,ind){
    if(!a) return null;
    if(ind==='saldo') return a.rt!=null&&a.dt!=null?a.rt-a.dt:null;
    if(ind==='saldo_sr') return a.rt!=null&&a.dt!=null&&a.tu!=null?a.rt-a.tu-a.dt:null;
    if(ind==='propria') return a.rt!=null&&a.tu!=null?a.rt-a.tu:null;
    var m={receita:'rt',impostos:'imp',transf:'tu',gasto:'dt',pessoal:'pes',invest:'inv'}[ind];
    if(m) return a[m]==null?null:a[m];
    if(ind.indexOf('f:')===0) return (a.f||{})[ind.slice(2)]||0;
    return null;
  }
  function fator(ano){ if(!INF||!HIST||!HIST.ipca) return 1; return HIST.ipca[String(ano)]||1 }
  function valor(uf,ind,ano){
    ano=ano||AN; var v, pop, rt, dt, f=1;
    if(ano==='atual'){
      var x=EST.estados[uf]; if(!x||!x.atual) return null; var b=x.atual; v=bruto(b,ind); pop=b.populacao;
      rt=lin(b.receitas,'Total arrecadado').realizado; dt=lin(b.despesas,'Total').liquidado; f=fator(b.ano);
    } else {
      var h=HIST&&HIST.estados[uf]&&HIST.estados[uf].anos[ano]; if(!h) return null; v=brutoH(h,ind); pop=h.pop; rt=h.rt; dt=h.dt; f=fator(ano);
    }
    if(v==null) return null;
    if(ME==='pc') return pop?v/pop*f:null;
    if(ME==='pct'){ var base=(ind==='receita'||ind==='impostos'||ind==='transf'||ind==='propria')?rt:dt; return base?v/base*100:null; }
    return v*f;
  }
  function anoTxt(ano){ if(ano!=='atual') return ano; var b=(EST.estados.SP||{}).atual||{};
    var mes=b.periodo?(b.periodo>=6?'dezembro':['','fevereiro','abril','junho','agosto','outubro'][b.periodo]):''; return (b.ano||'')+(mes&&b.periodo<6?' (até '+mes+')':''); }
  function historico(u){
    var el=q('[data-mh]'); if(!HIST){ el.innerHTML=''; return }
    var anos=Object.keys((HIST.estados.UF||{}).anos||{}).sort(); anos.push('atual');
    var y=EST.estados[CMP]?CMP:'UF';
    var A=anos.map(function(a){return valor(u,IN,a)}), B=anos.map(function(a){return valor(y,IN,a)});
    var tudo=A.concat(B).filter(function(v){return v!=null}); if(tudo.length<3){ el.innerHTML=''; return }
    var mn=Math.min(0,Math.min.apply(0,tudo)), mx=Math.max.apply(0,tudo)||1, W=340, H=150, L=6, R=6, T=10, Bm=22;
    function X(i){return L+i*(W-L-R)/(anos.length-1)} function Y(v){return T+(mx-v)/(mx-mn||1)*(H-T-Bm)}
    function linha(S,cor,trac){var p=S.map(function(v,i){return v==null?null:X(i).toFixed(1)+','+Y(v).toFixed(1)}).filter(Boolean);
      return '<polyline fill="none" stroke="'+cor+'" stroke-width="2.4"'+(trac?' stroke-dasharray="5 4"':'')+' points="'+p.join(' ')+'"/>'+
        S.map(function(v,i){return v==null?'':'<circle cx="'+X(i).toFixed(1)+'" cy="'+Y(v).toFixed(1)+'" r="3" fill="'+cor+'"><title>'+(anos[i]==='atual'?anoTxt('atual'):anos[i])+': '+fmt(v)+'</title></circle>'}).join('')}
    var eixo=anos.map(function(a,i){return (i%2===0||a==='atual')?'<text x="'+X(i).toFixed(1)+'" y="'+(H-6)+'" text-anchor="middle" font-size="10" fill="currentColor">'+(a==='atual'?'hoje':"'"+a.slice(2))+'</text>':''}).join('');
    var zero=mn<0?'<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(0)+'" y2="'+Y(0)+'" stroke="currentColor" stroke-opacity=".35"/>':'';
    var nomeY=y==='UF'?'Média dos estados':EST.estados[y].nome;
    el.innerHTML='<p class="mc-ht">Evolução desde '+anos[0]+(INF&&ME!=='pct'?' (corrigida pela inflação)':'')+(ME!=='pct'&&anos.length?' · o ano atual é parcial':'')+'</p>'+
      '<svg viewBox="0 0 '+W+' '+H+'" style="color:var(--mi)">'+zero+linha(B,'#94a3b8',true)+linha(A,'#1d4ed8')+eixo+'</svg>'+
      '<div class="mc-leg"><span><i style="background:#1d4ed8"></i>'+esc(EST.estados[u].nome)+'</span><span><i style="background:#94a3b8"></i>'+esc(nomeY)+'</span></div>';
  }
  function fmt(v){ if(v==null) return '–'; if(ME==='pct') return v.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
    var a=Math.abs(v), s=v<0?'−':'';
    if(ME==='pc') return s+'R$ '+a.toLocaleString('pt-BR',{maximumFractionDigits:0});
    if(a>=1e9) return s+'R$ '+(a/1e9).toLocaleString('pt-BR',{maximumFractionDigits:1})+' bi'; if(a>=1e6) return s+'R$ '+(a/1e6).toLocaleString('pt-BR',{maximumFractionDigits:0})+' mi';
    return s+'R$ '+a.toLocaleString('pt-BR',{maximumFractionDigits:0}); }
  var SEQ=['#dbeafe','#93c5fd','#3b82f6','#1d4ed8','#1e3a8a'], POS=['#bbf7d0','#4ade80','#15803d'], NEG=['#fecaca','#f87171','#b91c1c'];
  function cores(vals){
    var v=vals.filter(function(x){return x!=null}).sort(function(a,b){return a-b});
    if((IN==='saldo'||IN==='saldo_sr')&&ME!=='pct'){
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
    var rotulo=q('[data-mi]').selectedOptions[0].textContent;
    q('[data-mt]').textContent=rotulo+' · '+(ME==='pc'?'por habitante':ME==='pct'?(IN==='receita'||IN==='impostos'||IN==='transf'||IN==='propria'?'% da arrecadação':'% do gasto total'):'valor total')+' · '+(AN==='atual'?anoTxt('atual')+', acumulado no ano':AN+', ano fechado')+(INF&&ME!=='pct'&&HIST&&HIST.ipca_ate?' · em valores de '+HIST.ipca_ate:'');
    lista.sort(function(a,b){return vals[b]-vals[a]});
    var mx=Math.max.apply(0,lista.map(function(u){return Math.abs(vals[u])}))||1;
    q('[data-mrk]').innerHTML=lista.map(function(u,i){var v=vals[u];
      return '<li data-u="'+u+'" class="'+(u===SEL?'on':'')+'"><span>'+(i+1)+'º</span><b>'+u+'</b><span class="bar"><i style="width:'+Math.round(Math.abs(v)/mx*100)+'%;background:'+c.f(v)+'"></i></span><span>'+fmt(v)+'</span></li>'}).join('');
    cartao(vals,lista);
  }
  function cartao(vals,lista){
    var el=q('[data-mcard]'), u=SEL||lista[0]; if(!u){el.innerHTML='';return}
    var x=EST.estados[u]||HIST.estados[u], pos=lista.indexOf(u)+1, br=valor('UF',IN);
    var linhas=[['saldo','Saldo'],['saldo_sr','Saldo sem repasses'],['receita','Arrecadado'],['transf','Repasses da União'],['gasto','Gasto'],['f:Educação','Educação'],['f:Saúde','Saúde'],['f:Segurança Pública','Segurança'],['invest','Invest.']];
    if(IN.indexOf('f:')===0&&['f:Educação','f:Saúde','f:Segurança Pública'].indexOf(IN)<0) linhas.splice(3,0,[IN,IN.slice(2)]);
    var opts=Object.keys(EST.estados).filter(function(k){return k!=='BR'&&k!==u}).sort(function(a,b){return a==='UF'?-1:b==='UF'?1:EST.estados[a].nome.localeCompare(EST.estados[b].nome)});
    var y=EST.estados[CMP]?CMP:'UF';
    el.innerHTML='<small>'+(SEL?'Estado selecionado':'Primeiro do ranking')+'</small><div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline;flex-wrap:wrap"><b style="font-size:17px">'+esc(x.nome)+'</b><small>'+pos+'º de '+lista.length+'</small></div>'+
      '<b class="v">'+fmt(vals[u])+'</b><small>Média dos estados: '+fmt(br)+'</small>'+
      '<table class="mc-cmp"><thead><tr><th>'+(ME==='pc'?'Por habitante':ME==='pct'?'% do total':'Total')+'</th><th>'+u+'</th><th><select data-mc aria-label="Comparar com" style="font:600 12px system-ui;width:8.5em;max-width:100%">'+
      opts.map(function(k){return '<option value="'+k+'"'+(k===y?' selected':'')+'>'+(k==='UF'?'Média dos estados':esc(EST.estados[k].nome))+'</option>'}).join('')+'</select></th></tr></thead><tbody>'+
      linhas.map(function(l){var a=valor(u,l[0]), c2=valor(y,l[0]); return '<tr'+(l[0]===IN?' style="font-weight:800"':'')+'><td>'+esc(l[1])+'</td><td>'+fmt(a)+'</td><td>'+fmt(c2)+'</td></tr>'}).join('')+'</tbody></table>';
    historico(u);
  }
  raiz.addEventListener('click',function(ev){
    var t=ev.target.closest('[data-u]'); if(t){SEL=t.getAttribute('data-u'); desenhar(); return}
    var m=ev.target.closest('[data-m]'); if(m){ME=m.dataset.m; raiz.querySelectorAll('[data-m]').forEach(function(b){b.classList.toggle('on',b===m)}); desenhar(); return}

  });
  raiz.addEventListener('change',function(ev){
    if(ev.target.matches('[data-mi]')){IN=ev.target.value; if((IN==='saldo'||IN==='saldo_sr')&&ME==='pct'){ME='pc'; raiz.querySelectorAll('[data-m]').forEach(function(b){b.classList.toggle('on',b.dataset.m==='pc')})} desenhar()}
    if(ev.target.matches('[data-mc]')){CMP=ev.target.value; desenhar()}
    if(ev.target.matches('[data-ma]')){AN=ev.target.value; desenhar()}
    if(ev.target.matches('[data-mif]')){INF=ev.target.checked; desenhar()}
  });
  function carregar(){
    if(EST) return; EST={};
    var base=(document.querySelector('base')||{}).href||'/';
    Promise.all([fetch('/estados.json',{cache:'no-cache'}).then(function(r){return r.json()}),fetch('/mapa_ufs.json',{cache:'force-cache'}).then(function(r){return r.json()})])
      .then(function(r){EST=r[0];MAPA=r[1]; q('[data-ms]').setAttribute('viewBox','0 0 '+MAPA.w+' '+MAPA.h); desenhar();
        fetch('/estados_historico.json',{cache:'no-cache'}).then(function(r){return r.ok?r.json():null}).then(function(h){
          if(!h||!h.estados) return; HIST=h; var anos=Object.keys((h.estados.UF||{}).anos||{}).sort().reverse();
          q('[data-ma]').innerHTML='<option value="atual">'+esc(anoTxt('atual'))+'</option>'+anos.map(function(a){return '<option value="'+a+'">'+a+'</option>'}).join('');
          desenhar(); }).catch(function(){}); })
      .catch(function(){q('[data-mt]').textContent='Não foi possível carregar o mapa agora.';EST=null});
  }
  // carrega quando o mapa aparece na tela (na capa ele fica na aba Política)
  if('IntersectionObserver' in window){ var io=new IntersectionObserver(function(e){ if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()} }); io.observe(raiz); }
  else carregar();
})();
