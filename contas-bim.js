/* Contas públicas bimestre a bimestre (Plantão Informa). Dados: /estados_bimestral.json (SICONFI, RREO Anexo 1). */
(function(){
  var raiz=document.querySelector('[data-contas-bim]'); if(!raiz) return;
  var css='.cb{--ci:var(--ink-2,#4a5873);--cr:var(--rule,#d9e0ea);--cc:var(--card,#fff);--ct:var(--ink,#0a1d3d);--cp:var(--paper,#f5f7fa);background:var(--cc);border:1px solid var(--cr);color:var(--ct);min-width:0}'+
  '.cb-h{padding:16px 16px 10px;border-bottom:1px solid var(--cr);display:grid;grid-template-columns:minmax(0,1fr);gap:10px}.cb-c>*{min-width:0;max-width:100%}.cb-b{min-width:0}.cb-h h3{margin:0;font:700 19px Georgia,serif}.cb-h p{margin:0;font-size:13.5px;color:var(--ci)}'+
  '.cb-c{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.cb-c select{font:600 14px system-ui;color:var(--ct);background:var(--cp);border:1px solid var(--cr);border-radius:8px;padding:7px 9px;max-width:100%;min-width:0}'+
  '.cb-sg{display:flex;flex-wrap:wrap;max-width:100%;border:1px solid var(--cr);border-radius:8px;overflow:hidden}.cb-sg button{font:600 13px system-ui;padding:7px 10px;border:0;background:var(--cp);color:var(--ci);cursor:pointer}.cb-sg button.on{background:var(--ct);color:var(--cc)}'+
  '.cb-b{padding:12px 16px 4px}.cb-r{margin:0 0 8px;font-size:14.5px}.cb-r b{font-weight:800}.cb .up{color:#137a3d}.cb .down{color:#c0262d}'+
  '.cb svg{width:100%;height:auto;display:block}.cb-leg{display:flex;flex-wrap:wrap;gap:4px 14px;font:12.5px system-ui;color:var(--ci);margin:6px 0 0}.cb-leg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-2px}'+
  '.cb-tw{overflow-x:auto;margin-top:10px}.cb-t{width:100%;border-collapse:collapse;font-size:13px;min-width:520px}.cb-t th,.cb-t td{padding:6px 8px;border-bottom:1px solid var(--cr);text-align:right;white-space:nowrap}.cb-t th:first-child,.cb-t td:first-child{text-align:left}.cb-t th{font:600 11.5px system-ui;color:var(--ci);text-transform:uppercase}'+
  '.cb-n{margin:0;padding:8px 16px 14px;font-size:12.5px;color:var(--ci)}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  raiz.className='cb quadro';
  raiz.innerHTML='<header class="cb-h"><h3>Bimestre a bimestre</h3><p>Compare o mesmo período em anos diferentes. Os estados enviam as contas ao Tesouro a cada dois meses.</p>'+
    '<div class="cb-c"><select data-cbu aria-label="Escolher o governo"></select>'+
    '<div class="cb-sg" role="group" aria-label="Indicador" data-cbi></div>'+
    '<div class="cb-sg" role="group" aria-label="Visão"><button class="on" data-cbv="bim" aria-pressed="true">Só o bimestre</button><button data-cbv="acu" aria-pressed="false">Acumulado no ano</button></div></div></header>'+
    '<div class="cb-b"><p class="cb-r" data-cbr>Carregando o histórico do Tesouro Nacional…</p><svg data-cbg viewBox="0 0 640 260" role="img" aria-label="Gráfico por bimestre"></svg><div class="cb-leg" data-cbl></div>'+
    '<div class="cb-tw"><table class="cb-t" data-cbt></table></div></div><p class="cb-n" data-cbn></p>';
  function q(s){return raiz.querySelector(s)}
  var IND=[['rt','Receita'],['dt','Despesa'],['saldo','Saldo'],['pes','Pessoal'],['inv','Investimentos'],['tu','Repasses da União']];
  var BIM=['jan–fev','mar–abr','mai–jun','jul–ago','set–out','nov–dez'];
  var CORES=['#c9d3e1','#9fb1c9','#5f7ea6',getComputedStyle(document.documentElement).getPropertyValue('--brand').trim()||'#8f0922'];
  var D=null, UF='BR', IN='rt', VIS='bim';
  try{UF=localStorage.getItem('plantao-uf')||'BR'}catch(e){}
  q('[data-cbi]').innerHTML=IND.map(function(x,i){return '<button data-cbk="'+x[0]+'" class="'+(i?'':'on')+'" aria-pressed="'+!i+'">'+x[1]+'</button>'}).join('');
  function nf(v){ if(v==null||isNaN(v)) return '–'; var a=Math.abs(v), s=v<0?'−':''; var t=a>=1e12?(a/1e12).toFixed(2)+' tri':a>=1e9?(a/1e9).toFixed(a>=1e11?0:1)+' bi':(a/1e6).toFixed(0)+' mi'; return s+'R$ '+t.replace('.',','); }
  function val(b,k){ if(!b) return null; if(k==='saldo') return (b.rt!=null&&b.dt!=null)?b.rt-b.dt:null; return b[k]!=null?b[k]:null; }
  function serie(e,ano){   // valores por bimestre do ano (só o bimestre ou acumulado)
    var out=[];
    for(var p=1;p<=6;p++){
      var a=e.b[ano+'-'+p]; if(!a){out.push(null);continue}
      var v=val(a,IN);
      if(VIS==='bim'&&p>1){ var ant=e.b[ano+'-'+(p-1)]; v=(ant&&v!=null&&val(ant,IN)!=null)?v-val(ant,IN):null; }
      out.push(v);
    }
    return out;
  }
  function desenhar(){
    var e=D.entes[UF]||D.entes.BR; if(!e) return;
    var btu=q('[data-cbk="tu"]'); btu.hidden=UF==='BR'; if(UF==='BR'&&IN==='tu'){IN='rt';seg(q('[data-cbk="rt"]'))}
    var anos=Object.keys(e.b).map(function(k){return k.slice(0,4)}).filter(function(v,i,a){return a.indexOf(v)===i}).sort().slice(-4);
    var S=anos.map(function(a){return serie(e,a)});
    var tudo=[].concat.apply([],S).filter(function(v){return v!=null});
    var g=q('[data-cbg]'), est=raiz.clientWidth<520, W=est?400:640, H=est?250:260, ml=6, mt=14, mb=34, h=H-mt-mb; g.setAttribute('viewBox','0 0 '+W+' '+H);
    if(!tudo.length){ g.innerHTML=''; q('[data-cbr]').textContent='Ainda não há dados para este governo.'; return; }
    var mx=Math.max.apply(null,tudo.concat([0])), mn=Math.min.apply(null,tudo.concat([0])), fx=(mx-mn)||1, zero=mt+h*mx/fx;
    var grupo=(W-ml*2)/6, nb=anos.length, lb=grupo*0.8/nb, svg='<line x1="0" x2="'+W+'" y1="'+zero+'" y2="'+zero+'" stroke="currentColor" stroke-opacity=".25"/>';
    for(var p=0;p<6;p++){
      var gx=ml+grupo*p+grupo*0.1;
      S.forEach(function(s,i){ var v=s[p]; if(v==null) return; var y=zero-v/fx*h, y1=Math.min(y,zero), hh=Math.max(Math.abs(y-zero),1.5);
        var cor=CORES[CORES.length-nb+i];
        svg+='<rect x="'+(gx+lb*i).toFixed(1)+'" y="'+y1.toFixed(1)+'" width="'+(lb-2).toFixed(1)+'" height="'+hh.toFixed(1)+'" rx="2" fill="'+cor+'"><title>'+BIM[p]+'/'+anos[i]+': '+nf(v)+'</title></rect>'; });
      svg+='<text x="'+(ml+grupo*p+grupo/2)+'" y="'+(H-12)+'" text-anchor="middle" font-size="'+(est?15:13)+'" fill="currentColor" opacity=".75">'+(est?(p+1)+'º bim.':(p+1)+'º · '+BIM[p])+'</text>';
    }
    g.innerHTML=svg;
    q('[data-cbl]').innerHTML=anos.map(function(a,i){return '<span><i style="background:'+CORES[CORES.length-nb+i]+'"></i>'+a+'</span>'}).join('');
    // destaque: último bimestre disponível comparado com o mesmo do ano anterior
    var ua=anos[anos.length-1], us=S[S.length-1], up=-1; for(var k=5;k>=0;k--) if(us[k]!=null){up=k;break}
    var nomeI=IND.filter(function(x){return x[0]===IN})[0][1].toLowerCase();
    if(up>=0){
      var ant=S.length>1?S[S.length-2][up]:null, v=us[up], txt='<b>'+(up+1)+'º bimestre de '+ua+'</b> ('+BIM[up]+(VIS==='acu'?', acumulado no ano':'')+'): '+nomeI+' de <b>'+nf(v)+'</b>';
      if(ant!=null&&ant!==0&&IN!=='saldo'){ var pc=(v-ant)/Math.abs(ant)*100; txt+=', <span class="'+(pc>=0?(IN==='dt'||IN==='pes'?'down':'up'):(IN==='dt'||IN==='pes'?'up':'down'))+'">'+(pc>=0?'+':'')+pc.toFixed(1).replace('.',',')+'%</span> em relação a '+anos[anos.length-2]+' (valores sem correção pela inflação).'; }
      else if(ant!=null) txt+=' (em '+anos[anos.length-2]+': '+nf(ant)+').';
      q('[data-cbr]').innerHTML=txt;
    }
    q('[data-cbt]').innerHTML='<thead><tr><th>Ano</th>'+BIM.map(function(b,i){return '<th>'+(i+1)+'º bim.</th>'}).join('')+'</tr></thead><tbody>'+
      anos.map(function(a,i){return '<tr><td><b>'+a+'</b></td>'+S[i].map(function(v){return '<td>'+nf(v)+'</td>'}).join('')+'</tr>'}).slice().reverse().join('')+'</tbody>';
    q('[data-cbn]').textContent='Fonte: Tesouro Nacional, SICONFI (RREO, Anexo 1): receitas realizadas e despesas liquidadas, sem operações intraorçamentárias. Valores nominais. "Só o bimestre" é a diferença entre o acumulado do bimestre e o do anterior. A soma dos estados aparece só quando os 27 já enviaram.'+(UF==='BR'?' Na União, receita e despesa incluem a rolagem da dívida pública (emissão e pagamento de títulos), que oscila bastante de um bimestre para outro.':'');
  }
  function opcoes(){
    var ks=Object.keys(D.entes).sort(function(a,b){var o={BR:0,UF:1};return ((a in o?o[a]:2)-(b in o?o[b]:2))||D.entes[a].nome.localeCompare(D.entes[b].nome,'pt-BR')});
    q('[data-cbu]').innerHTML=ks.map(function(k){return '<option value="'+k+'">'+D.entes[k].nome+(k==='BR'||k==='UF'?'':' ('+k+')')+'</option>'}).join('');
    if(!D.entes[UF]) UF='BR'; q('[data-cbu]').value=UF;
  }
  function seg(b){[].forEach.call(b.parentNode.children,function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)})}
  raiz.addEventListener('click',function(ev){var t;
    if(t=ev.target.closest('[data-cbk]')){IN=t.getAttribute('data-cbk');seg(t);D&&desenhar()}
    else if(t=ev.target.closest('[data-cbv]')){VIS=t.getAttribute('data-cbv');seg(t);D&&desenhar()} });
  q('[data-cbu]').addEventListener('change',function(ev){UF=ev.target.value;D&&desenhar()});
  document.addEventListener('change',function(ev){ if(ev.target.matches&&ev.target.matches('[data-uf]')&&D&&D.entes[ev.target.value]){UF=ev.target.value;q('[data-cbu]').value=UF;desenhar()} });
  function carregar(){ if(D) return; D={};
    fetch('/estados_bimestral.json',{cache:'no-cache'}).then(function(r){return r.json()}).then(function(j){D=j;opcoes();desenhar()})
      .catch(function(){q('[data-cbr]').textContent='Não foi possível carregar o histórico agora.';D=null});
  }
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(e){if(e.some(function(x){return x.isIntersecting})){io.disconnect();carregar()}},{rootMargin:'300px'});io.observe(raiz)} else carregar();
})();
