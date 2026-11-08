/* Contas públicas mês a mês (Plantão Informa). Dados: /contas_mensal.json (Banco Central, NFSP). */
(function(){
  var raiz=document.querySelector('[data-contas-mes]'); if(!raiz) return;
  var css='.cm{--ci:var(--ink-2,#4a5873);--cr:var(--rule,#d9e0ea);--cc:var(--card,#fff);--ct:var(--ink,#0a1d3d);--cp:var(--paper,#f5f7fa);background:var(--cc);border:1px solid var(--cr);color:var(--ct);min-width:0}'+
  '.cm-h{padding:16px 16px 10px;border-bottom:1px solid var(--cr);display:grid;grid-template-columns:minmax(0,1fr);gap:10px}.cm-h h3{margin:0;font:700 19px Georgia,serif}.cm-h p{margin:0;font-size:13.5px;color:var(--ci)}'+
  '.cm-c{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.cm-c>*{min-width:0;max-width:100%}.cm-c select{font:600 14px system-ui;color:var(--ct);background:var(--cp);border:1px solid var(--cr);border-radius:8px;padding:7px 9px}'+
  '.cm-sg{display:flex;flex-wrap:wrap;border:1px solid var(--cr);border-radius:8px;overflow:hidden}.cm-sg button{font:600 13px system-ui;padding:7px 10px;border:0;background:var(--cp);color:var(--ci);cursor:pointer}.cm-sg button.on{background:var(--ct);color:var(--cc)}'+
  '.cm-b{padding:12px 16px 4px;min-width:0}.cm-r{margin:0 0 6px;font-size:14.5px}.cm-r b{font-weight:800}.cm .up{color:#137a3d}.cm .down{color:#c0262d}'+
  '.cm-k{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0 10px}.cm-k div{background:var(--cp);border-radius:10px;padding:8px 11px}.cm-k span{display:block;font-size:12px;color:var(--ci)}.cm-k b{font:800 18px system-ui}'+
  '.cm svg{width:100%;height:auto;display:block}.cm-leg{display:flex;flex-wrap:wrap;gap:4px 14px;font:12.5px system-ui;color:var(--ci);margin:6px 0 0}.cm-leg i{display:inline-block;width:14px;height:4px;border-radius:2px;margin-right:5px;vertical-align:3px}'+
  '.cm-tw{overflow-x:auto;margin-top:10px}.cm-t{width:100%;border-collapse:collapse;font-size:12.5px;min-width:760px}.cm-t th,.cm-t td{padding:5px 6px;border-bottom:1px solid var(--cr);text-align:right;white-space:nowrap}.cm-t th:first-child,.cm-t td:first-child{text-align:left}.cm-t th{font:600 11px system-ui;color:var(--ci);text-transform:uppercase}'+
  '.cm-n{margin:0;padding:8px 16px 14px;font-size:12.5px;color:var(--ci)}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  raiz.className='cm quadro';
  raiz.innerHTML='<header class="cm-h"><h3>Mês a mês: o resultado das contas públicas</h3><p>Quanto sobrou ou faltou a cada mês, segundo o Banco Central. Compare o mesmo mês em anos diferentes.</p>'+
    '<div class="cm-c"><select data-cme aria-label="Escolher a esfera de governo"></select>'+
    '<div class="cm-sg" role="group" aria-label="Indicador"><button class="on" data-cmi="prim" aria-pressed="true">Resultado primário</button><button data-cmi="juros" aria-pressed="false">Gasto com juros</button><button data-cmi="nom" aria-pressed="false">Resultado nominal</button></div>'+
    '<div class="cm-sg" role="group" aria-label="Visão"><button class="on" data-cmv="mes" aria-pressed="true">No mês</button><button data-cmv="acu" aria-pressed="false">Acumulado no ano</button></div></div></header>'+
    '<div class="cm-b"><p class="cm-r" data-cmr>Carregando os dados do Banco Central…</p><div class="cm-k" data-cmk></div><svg data-cmg viewBox="0 0 640 270" role="img" aria-label="Gráfico mês a mês"></svg><div class="cm-leg" data-cml></div>'+
    '<div class="cm-tw"><table class="cm-t" data-cmt></table></div></div><p class="cm-n" data-cmn></p>';
  function q(s){return raiz.querySelector(s)}
  var MES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'], MESX=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];
  var D=null, ES='spc', IN='prim', VIS='mes';
  var marca=getComputedStyle(document.documentElement).getPropertyValue('--brand').trim()||'#8f0922', CORES=['#c9d3e1','#9fb1c9','#5f7ea6',marca];
  function nf(v,s){ if(v==null||isNaN(v)) return '–'; var a=Math.abs(v)*1e6, t=a>=1e12?(a/1e12).toFixed(2)+' tri':a>=1e9?(a/1e9).toFixed(1)+' bi':(a/1e6).toFixed(0)+' mi'; return (s&&v<0?'−':s&&v>0?'+':'')+'R$ '+t.replace('.',','); }
  function bruto(m){ if(!m) return null; var p=m.prim, j=m.juros; if(IN==='prim') return p; if(IN==='juros') return j==null?null:-j; return (p==null||j==null)?null:p+j; }
  function serie(e,ano){ var out=[], ac=0, ok=true;
    for(var i=1;i<=12;i++){ var v=bruto(e.m[ano+'-'+(i<10?'0':'')+i]); if(v==null){out.push(null);ok=false;continue}
      if(VIS==='acu'){ if(!ok){out.push(null);continue} ac+=v; out.push(ac);} else out.push(v); }
    return out; }
  function rotulo(v){ if(IN==='juros') return 'gasto com juros de '+nf(v); if(v>=0) return 'superávit '+(IN==='prim'?'primário':'nominal')+' de '+nf(v); return 'déficit '+(IN==='prim'?'primário':'nominal')+' de '+nf(-v); }
  function desenhar(){
    var e=D.esferas[ES]; if(!e) return;
    var anos=Object.keys(e.m).map(function(k){return k.slice(0,4)}).filter(function(v,i,a){return a.indexOf(v)===i}).sort().slice(-4);
    var S=anos.map(function(a){return serie(e,a)}), tudo=[].concat.apply([],S).filter(function(v){return v!=null});
    var est=raiz.clientWidth<520, W=est?400:640, H=est?250:270, ml=est?46:58, mr=10, mt=12, mb=26, w=W-ml-mr, h=H-mt-mb, g=q('[data-cmg]');
    g.setAttribute('viewBox','0 0 '+W+' '+H);
    var mx=Math.max.apply(null,tudo.concat([0])), mn=Math.min.apply(null,tudo.concat([0])), pad=(mx-mn)*0.08||1; mx+=pad; mn-=pad; var fx=mx-mn;
    var Y=function(v){return mt+h*(mx-v)/fx}, X=function(i){return ml+w*i/11};
    var svg='', b10=Math.pow(10,Math.floor(Math.log10(fx/5))), passo=[1,2,5,10].map(function(k){return k*b10}).filter(function(p){return fx/p<=6})[0]||10*b10;
    for(var t=Math.ceil(mn/passo)*passo;t<=mx;t+=passo){ svg+='<line x1="'+ml+'" x2="'+(W-mr)+'" y1="'+Y(t).toFixed(1)+'" y2="'+Y(t).toFixed(1)+'" stroke="currentColor" stroke-opacity="'+(Math.abs(t)<passo/2?'.45':'.1')+'"/>'+
      '<text x="'+(ml-6)+'" y="'+(Y(t)+4).toFixed(1)+'" text-anchor="end" font-size="'+(est?12:11)+'" fill="currentColor" opacity=".6">'+(t/1000).toFixed(passo<1000?1:0).replace('.',',')+'</text>'; }
    for(var i=0;i<12;i++) svg+='<text x="'+X(i).toFixed(1)+'" y="'+(H-7)+'" text-anchor="middle" font-size="'+(est?12:12)+'" fill="currentColor" opacity=".7">'+MES[i]+'</text>';
    S.forEach(function(s,k){ var cor=CORES[CORES.length-anos.length+k], ult=k===S.length-1, d='', pts='';
      s.forEach(function(v,i){ if(v==null) return; d+=(d?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1); pts+='<circle cx="'+X(i).toFixed(1)+'" cy="'+Y(v).toFixed(1)+'" r="'+(ult?3.6:2.4)+'" fill="'+cor+'"><title>'+MES[i]+'/'+anos[k]+': '+nf(v,true)+'</title></circle>'; });
      svg+='<path d="'+d+'" fill="none" stroke="'+cor+'" stroke-width="'+(ult?3:2)+'" stroke-linejoin="round"/>'+pts; });
    svg+='<text x="'+(ml-6)+'" y="'+(mt-2)+'" text-anchor="end" font-size="10" fill="currentColor" opacity=".55">R$ bi</text>';
    g.innerHTML=svg;
    q('[data-cml]').innerHTML=anos.map(function(a,k){return '<span><i style="background:'+CORES[CORES.length-anos.length+k]+'"></i>'+a+'</span>'}).join('');
    var ua=anos[anos.length-1], us=S[S.length-1], ui=-1; for(var i2=11;i2>=0;i2--) if(us[i2]!=null){ui=i2;break}
    if(ui>=0){ var v=us[ui], ant=S.length>1?S[S.length-2][ui]:null;
      q('[data-cmr]').innerHTML='<b>'+MESX[ui][0].toUpperCase()+MESX[ui].slice(1)+' de '+ua+'</b>'+(VIS==='acu'?' (acumulado no ano)':'')+': '+e.nome.toLowerCase().replace('banco central','Banco Central')+' com <b class="'+(IN==='juros'?'':v>=0?'up':'down')+'">'+rotulo(v)+'</b>'+(ant!=null?'. No mesmo período de '+anos[anos.length-2]+': '+rotulo(ant)+'.':'.'); }
    var P=D.pib||{}, k3=[];
    if(P.prim_pib) k3.push(['Primário em 12 meses', (P.prim_pib.valor>0?'déficit ':'superávit ')+Math.abs(P.prim_pib.valor).toFixed(2).replace('.',',')+'% do PIB']);
    if(P.divida_bruta) k3.push(['Dívida bruta do governo', P.divida_bruta.valor.toFixed(1).replace('.',',')+'% do PIB']);
    if(P.divida_liq) k3.push(['Dívida líquida do setor público', P.divida_liq.valor.toFixed(1).replace('.',',')+'% do PIB']);
    q('[data-cmk]').innerHTML=k3.map(function(x){return '<div><span>'+x[0]+'</span><b>'+x[1]+'</b></div>'}).join('');
    q('[data-cmt]').innerHTML='<thead><tr><th>Ano</th>'+MES.map(function(m){return '<th>'+m+'</th>'}).join('')+'</tr></thead><tbody>'+
      anos.map(function(a,k){return '<tr><td><b>'+a+'</b></td>'+S[k].map(function(v){return '<td>'+(v==null?'–':nf(v,IN!=='juros').replace('R$ ',''))+'</td>'}).join('')+'</tr>'}).reverse().join('')+'</tbody>';
    q('[data-cmn]').textContent='Fonte: Banco Central, estatísticas fiscais (necessidades de financiamento do setor público, sem desvalorização cambial). Resultado primário: receitas menos despesas, sem contar os juros. Resultado nominal: primário menos os juros da dívida. Valores em reais correntes; positivo é superávit. Os indicadores em % do PIB são do setor público consolidado. O Banco Central divulga os dados cerca de um mês depois.';
  }
  function seg(b){[].forEach.call(b.parentNode.children,function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)})}
  raiz.addEventListener('click',function(ev){var t;
    if(t=ev.target.closest('[data-cmi]')){IN=t.getAttribute('data-cmi');seg(t);D&&desenhar()}
    else if(t=ev.target.closest('[data-cmv]')){VIS=t.getAttribute('data-cmv');seg(t);D&&desenhar()} });
  q('[data-cme]').addEventListener('change',function(ev){ES=ev.target.value;D&&desenhar()});
  function carregar(){ if(D) return; D={};
    fetch('/contas_mensal.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(j){D=j;
      q('[data-cme]').innerHTML=Object.keys(j.esferas).map(function(k){return '<option value="'+k+'">'+j.esferas[k].nome+'</option>'}).join(''); q('[data-cme]').value=ES; desenhar()})
      .catch(function(){q('[data-cmr]').textContent='Não foi possível carregar os dados agora.';D=null});
  }
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(e){if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()}},{rootMargin:'300px'});io.observe(raiz)} else carregar();
})();
