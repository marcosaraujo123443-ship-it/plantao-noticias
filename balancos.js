/* Balanços das empresas listadas na B3 (Plantão Informa). Dados: /balancos.json (CVM, ITR e DFP). */
(function(){
  var raiz=document.querySelector('[data-balancos]'); if(!raiz) return;
  var css='.quadros>.bl{grid-column:1/-1}.bl{--bi:var(--ink-2,#4a5873);--br:var(--rule,#d9e0ea);--bc:var(--card,#fff);--bt:var(--ink,#0a1d3d);--bp:var(--paper,#f5f7fa);background:var(--bc);border:1px solid var(--br);color:var(--bt);min-width:0}'+
  '.bl-h{padding:16px 16px 12px;border-bottom:1px solid var(--br);display:grid;gap:10px}.bl-h h3{margin:0;font:700 19px Georgia,serif}.bl-h p{margin:0;font-size:13.5px;color:var(--bi)}'+
  '.bl-c{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.bl-c input,.bl-c select{font:600 14px system-ui;color:var(--bt);background:var(--bp);border:1px solid var(--br);border-radius:8px;padding:7px 9px;min-width:0}.bl-c input{flex:1 1 180px}'+
  '.bl-sg{display:inline-flex;border:1px solid var(--br);border-radius:8px;overflow:hidden}.bl-sg button{font:600 13px system-ui;padding:7px 10px;border:0;background:var(--bp);color:var(--bi);cursor:pointer}.bl-sg button.on{background:var(--bt);color:var(--bc)}'+
  '.bl-ul{font-size:13px;color:var(--bi);display:flex;flex-wrap:wrap;gap:6px;align-items:center}.bl-ul button{font:600 12.5px system-ui;border:1px solid var(--br);background:var(--bp);color:var(--bt);border-radius:999px;padding:3px 9px;cursor:pointer}'+
  '.bl-t{width:100%;border-collapse:collapse;font-size:14px;table-layout:fixed}.bl-t th{font:600 12px system-ui;color:var(--bi);text-align:left;padding:8px 10px;border-bottom:1px solid var(--br);text-transform:uppercase;letter-spacing:.03em}'+
  '.bl-t td{padding:9px 10px;border-bottom:1px solid var(--br);vertical-align:top;overflow:hidden;text-overflow:ellipsis}.bl-t .n{text-align:right;white-space:nowrap}.bl-t tr.ln{cursor:pointer}.bl-t tr.ln:hover td{background:var(--bp)}.bl-t tr.ab td{background:var(--bp)}'+
  '.bl-t b.bl-tk{font:800 14px system-ui}.bl-t small{display:block;font-size:12px;color:var(--bi);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.bl .up{color:#0a7d3b}.bl .down{color:#c0262d}'+
  '.bl-t col.c1{width:34%}.bl-t col.c2{width:11%}.bl-t col.c5{width:12%}@media(max-width:620px){.bl-t .mg,.bl-t .pd{display:none}.bl-t col.c1{width:36%}.bl-t td,.bl-t th{padding-inline:6px}.bl-t{font-size:13px}.bl-t{table-layout:auto}.bl-t colgroup{display:none}.bl-t .ea{display:none}}.bl-t .pm{display:none}@media(max-width:620px){.bl-t .pm{display:inline}}'+
  '.bl-d td{padding:4px 12px 16px!important;background:var(--bp)}.bl-dg{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}.bl-k{background:var(--bc);border:1px solid var(--br);border-radius:10px;padding:9px 11px;min-width:0}'+
  '.bl-k span{display:block;font-size:12px;color:var(--bi)}.bl-k b{display:block;font:800 17px system-ui;margin:2px 0}.bl-k small{font-size:12px;color:var(--bi)}.bl-d h4{margin:12px 0 8px;font:700 13px system-ui;color:var(--bi);text-transform:uppercase;letter-spacing:.04em}'+
  '.bl-d small{white-space:normal}.bl-d a{font-weight:700;color:var(--brand,#0b5cd5)}.bl-d p{margin:10px 0 0;font-size:12.5px;color:var(--bi)}.bl-mais{display:block;margin:0 auto;font:700 14px system-ui;padding:10px 18px;border:1px solid var(--br);border-radius:8px;background:var(--bp);color:var(--bt);cursor:pointer}'+
  '.bl-f{padding:12px 16px 16px;display:grid;gap:10px}.bl-f .nota{margin:0;font-size:12.5px;color:var(--bi)}.bl-tw{overflow-x:auto}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  raiz.className='bl'; raiz.setAttribute('aria-label','Balanços das empresas');
  raiz.innerHTML='<header class="bl-h"><h3>Balanços das empresas</h3><p data-bp>Carregando os resultados entregues à CVM…</p>'+
    '<div class="bl-c"><input type="search" data-bq placeholder="Buscar empresa ou código (ex.: PETR4)" aria-label="Buscar empresa">'+
    '<div class="bl-sg" role="group" aria-label="Quais empresas"><button class="on" data-bu="ibov" aria-pressed="true">Ibovespa</button><button data-bu="todas" aria-pressed="false">Todas</button></div>'+
    '<div class="bl-sg" role="group" aria-label="Período"><button class="on" data-bx="tri" aria-pressed="true">Trimestre</button><button data-bx="ano" aria-pressed="false">No ano</button></div>'+
    '<select data-bo aria-label="Ordenar"><option value="rec">Divulgados por último</option><option value="receita">Maior receita</option><option value="lucro">Maior lucro</option><option value="cresc">Lucro que mais cresceu</option><option value="queda">Lucro que mais caiu</option></select></div>'+
    '<div class="bl-ul" data-bl></div></header>'+
    '<div class="bl-tw"><table class="bl-t"><colgroup><col class="c1"><col class="c2 pd"><col><col><col class="c5 mg"></colgroup>'+
    '<thead><tr><th>Empresa</th><th class="pd">Período</th><th class="n">Receita</th><th class="n">Lucro líquido</th><th class="n mg">Margem</th></tr></thead><tbody data-bb></tbody></table></div>'+
    '<div class="bl-f"><button class="bl-mais" data-bm hidden>Mostrar mais empresas</button><p class="nota" data-bn></p></div>';
  function q(s){return raiz.querySelector(s)}
  var D=null, UNI='ibov', PER='tri', ORD='rec', BUSCA='', LIM=15, ABERTA=null;
  function brl(v){ if(v==null) return '–'; var a=Math.abs(v), s=v<0?'−':'', t;
    if(a>=1e12) t=(a/1e12).toFixed(2)+' tri'; else if(a>=1e9) t=(a/1e9).toFixed(a>=1e11?0:a>=1e10?1:2)+' bi'; else if(a>=1e6) t=(a/1e6).toFixed(a>=1e8?0:1)+' mi'; else t=Math.round(a/1e3)+' mil';
    return s+'R$ '+t.replace('.',','); }
  function vr(a,b){ if(a==null||b==null||b===0) return null; if(b<0&&a>=0) return 'virou'; if(b>0&&a<0) return 'perdeu'; return (a-b)/Math.abs(b)*100; }
  function vtx(a,b){ var x=vr(a,b); if(x==null) return '';
    if(a<0&&b<0) return '<small class="'+(a<b?'down':'up')+'">prejuízo '+(a<b?'maior':'menor')+' que há 1 ano</small>';
    if(x==='virou') return '<small class="up">saiu do prejuízo</small>'; if(x==='perdeu') return '<small class="down">teve prejuízo</small>';
    return '<small class="'+(x>0?'up':x<0?'down':'')+'">'+(x>0?'+':'')+(Math.abs(x)>=1000?'>999':x.toFixed(1).replace('.',','))+'%<span class="ea"> em 1 ano</span></small>'; }
  function blk(r){ return (PER==='tri'&&r.tri&&r.tri.receita!=null)?r.tri:r.ano; }
  function data(s){ return s?s.slice(8,10)+'/'+s.slice(5,7):''; }
  function nper(r,b){ var m=r.tipo==='ITR'&&{'2':'6M','3':'9M'}[r.periodo[0]]; return b===r.ano&&r.tipo==='ITR'&&m?m+r.periodo.slice(2):r.periodo; }
  function lista(){
    var L=D.empresas.filter(function(r){ if(BUSCA){ var t=(r.tickers.join(' ')+' '+r.curto+' '+r.nome).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,''); return t.indexOf(BUSCA)>=0 } return UNI==='todas'||r.ibov; });
    var k=function(r){ var b=blk(r); return {receita:b.receita, lucro:b.lucro, cresc:vr(b.lucro,b.lucro_ant)}; };
    if(ORD==='rec') L.sort(function(a,b){ return a.recebido<b.recebido?1:a.recebido>b.recebido?-1:(blk(b).receita||0)-(blk(a).receita||0) });
    else if(ORD==='receita'||ORD==='lucro') L.sort(function(a,b){ return (k(b)[ORD]||-1e18)-(k(a)[ORD]||-1e18) });
    else { var num=function(r){ var x=k(r).cresc; return typeof x==='number'?x:null }; L=L.filter(function(r){ return num(r)!=null && Math.abs(blk(r).lucro_ant||0)>=5e7 });
      L.sort(function(a,b){ return ORD==='cresc'?num(b)-num(a):num(a)-num(b) }); }
    return L;
  }
  function k(rot,val,sub){ return '<div class="bl-k"><span>'+rot+'</span><b>'+val+'</b>'+(sub||'')+'</div>'; }
  function detalhe(r){
    var t=r.tri&&r.tri.receita!=null?r.tri:null, a=r.ano, h='';
    function bloco(b,tit){ if(!b) return ''; var mg=b.receita?(b.lucro/b.receita*100):null;
      return '<h4>'+tit+'</h4><div class="bl-dg">'+k(r.rotulo_receita&&/Intermedia/.test(r.rotulo_receita)?'Receita de intermediação':'Receita líquida',brl(b.receita),vtx(b.receita,b.receita_ant))+
        (b.bruto!=null?k(/Intermedia/.test(r.rotulo_receita||'')?'Resultado bruto da intermediação':'Lucro bruto',brl(b.bruto),b.receita?'<small>margem de '+(b.bruto/b.receita*100).toFixed(1).replace('.',',')+'%</small>':''):'')+
        (b.ebit!=null?k('Resultado operacional (Ebit)',brl(b.ebit),b.receita?'<small>margem de '+(b.ebit/b.receita*100).toFixed(1).replace('.',',')+'%</small>':''):'')+
        k('Lucro líquido',brl(b.lucro),vtx(b.lucro,b.lucro_ant)||(mg!=null?'<small>margem de '+mg.toFixed(1).replace('.',',')+'%</small>':''))+'</div>'; }
    if(t && r.periodo[0]!=='1') h+=bloco(t,'No '+r.periodo.replace('T','º trimestre de 20'));
    h+=bloco(a, r.tipo==='DFP'?'No ano de '+r.ref.slice(0,4):'No acumulado de '+r.ref.slice(0,4)+' (até '+data(r.ref)+')');
    var dl=(r.divida!=null&&r.caixa!=null)?r.divida-r.caixa:null;
    h+='<h4>Balanço em '+data(r.ref)+'/'+r.ref.slice(0,4)+'</h4><div class="bl-dg">'+k('Ativo total',brl(r.ativo))+k('Patrimônio líquido',brl(r.pl))+k('Caixa e aplicações',brl(r.caixa))+
      (r.divida!=null?k('Empréstimos e financiamentos',brl(r.divida),dl!=null?'<small>dívida líquida: '+brl(dl)+'</small>':''):'')+'</div>';
    h+='<p>'+r.nome+' · '+r.tickers.join(', ')+' · '+(r.tipo==='DFP'?'demonstrações anuais':'informações trimestrais')+(r.consolidado?' consolidadas':' individuais')+', entregues à CVM em '+data(r.recebido)+'/'+r.recebido.slice(0,4)+'. '+
      (r.link?'<a href="'+r.link.replace(/^http:/,'https:')+'" target="_blank" rel="noopener">Ver o documento completo na CVM →</a>':'')+'</p>';
    return h;
  }
  function desenhar(){
    var L=lista(), h='';
    L.slice(0,LIM).forEach(function(r){ var b=blk(r), mg=b.receita&&b.lucro!=null?b.lucro/b.receita*100:null, ab=ABERTA===r.cnpj;
      h+='<tr class="ln'+(ab?' ab':'')+'" data-bc="'+r.cnpj+'" tabindex="0" aria-expanded="'+ab+'"><td><b class="bl-tk">'+r.tickers[0]+'</b><small>'+r.curto+'<span class="pm"> · '+nper(r,b)+'</span></small></td><td class="pd">'+nper(r,b)+'<small>'+data(r.recebido)+'</small></td>'+
        '<td class="n">'+brl(b.receita)+vtx(b.receita,b.receita_ant)+'</td><td class="n '+((b.lucro||0)<0?'down':'')+'">'+brl(b.lucro)+vtx(b.lucro,b.lucro_ant)+'</td>'+
        '<td class="n mg">'+(mg==null?'–':mg.toFixed(1).replace('.',',')+'%')+'</td></tr>';
      if(ab) h+='<tr class="bl-d"><td colspan="5">'+detalhe(r)+'</td></tr>';
    });
    q('[data-bb]').innerHTML=h||'<tr><td colspan="5">Nenhuma empresa encontrada.</td></tr>';
    var m=q('[data-bm]'); m.hidden=L.length<=LIM; m.textContent='Mostrar mais empresas ('+(L.length-LIM)+')';
  }
  function topo(){
    var E=D.empresas, rec=E.slice().sort(function(a,b){return a.recebido<b.recebido?1:-1});
    var per={}; E.forEach(function(r){per[r.periodo]=(per[r.periodo]||0)+1}); var top=Object.keys(per).sort(function(a,b){return per[b]-per[a]})[0];
    q('[data-bp]').textContent=E.length+' empresas com ações na B3. Toque numa linha para ver o balanço completo. Comparação sempre com o mesmo período do ano anterior.';
    q('[data-bl]').innerHTML='<span>Últimos a divulgar:</span>'+rec.slice(0,6).map(function(r){return '<button data-bj="'+r.cnpj+'">'+r.tickers[0]+' · '+data(r.recebido)+'</button>'}).join('');
    q('[data-bn]').textContent='Fonte: CVM (dados abertos, formulários ITR e DFP), atualizado duas vezes por dia. Valores consolidados quando disponíveis; lucro atribuído aos controladores. Bancos e seguradoras usam outro plano de contas, então a "receita" deles não é comparável à das demais empresas.';
  }
  function abrir(c){ ABERTA=ABERTA===c?null:c; desenhar(); }
  raiz.addEventListener('click',function(ev){ var t;
    if(t=ev.target.closest('[data-bu]')){ UNI=t.getAttribute('data-bu'); seg(t); LIM=15; desenhar(); }
    else if(t=ev.target.closest('[data-bx]')){ PER=t.getAttribute('data-bx'); seg(t); desenhar(); }
    else if(t=ev.target.closest('[data-bm]')){ LIM+=30; desenhar(); }
    else if(t=ev.target.closest('[data-bj]')){ var c=t.getAttribute('data-bj'); BUSCA=''; q('[data-bq]').value=''; ORD='rec'; q('[data-bo]').value='rec'; UNI='todas'; seg(q('[data-bu="todas"]')); ABERTA=null; var L=lista(); LIM=Math.max(15,L.findIndex(function(r){return r.cnpj===c})+1); abrir(c); var tr=q('[data-bc="'+c+'"]'); if(tr) tr.scrollIntoView({block:'nearest',behavior:'smooth'}); }
    else if(ev.target.closest('a')) return;
    else if(t=ev.target.closest('tr.ln')) abrir(t.getAttribute('data-bc'));
  });
  raiz.addEventListener('keydown',function(ev){ var t=ev.target.closest('tr.ln'); if(t&&(ev.key==='Enter'||ev.key===' ')){ ev.preventDefault(); abrir(t.getAttribute('data-bc')); } });
  function seg(b){ [].forEach.call(b.parentNode.children,function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)}); }
  q('[data-bo]').addEventListener('change',function(ev){ ORD=ev.target.value; LIM=15; desenhar(); });
  q('[data-bq]').addEventListener('input',function(ev){ BUSCA=ev.target.value.trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,''); LIM=15; desenhar(); });
  function carregar(){ if(D) return; D={empresas:[]};
    fetch('/balancos.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(j){ D=j; topo(); desenhar(); })
      .catch(function(){ q('[data-bp]').textContent='Não foi possível carregar os balanços agora.'; D=null; });
  }
  if('IntersectionObserver' in window){ var io=new IntersectionObserver(function(e){ if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()} },{rootMargin:'300px'}); io.observe(raiz); } else carregar();
})();
