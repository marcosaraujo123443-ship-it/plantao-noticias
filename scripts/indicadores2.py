#!/usr/bin/env python3
"""Indicadores adicionais (um card para cada divulgação), gravados em indicadores2.json:
Caged, inadimplência das famílias, contas externas, INCC-M, produção industrial, varejo, Boletim Focus,
juros nos EUA (Fed) e na zona do euro (BCE) e payroll dos EUA.
Fontes: Banco Central (SGS e Olinda/Focus), IBGE (SIDRA) e FRED (Federal Reserve Bank of St. Louis)."""
import csv, io, json, sys, time, urllib.request
from datetime import date, datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (compatible; PlantaoInforma/1.0)"}
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()
MESES_EXT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
# Reuniões de política monetária (o card sai no dia seguinte, quando a nova taxa já consta no FRED). Atualizar a cada ano.
FOMC = ["2026-12-09"]
BCE = ["2026-12-17"]

def get(url, tentativas=3):
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: return r.read().decode("utf-8", "replace")
        except Exception:
            if t == tentativas - 1: raise
            time.sleep(5 * (t + 1))

def sgs(cod, desde=None, n=20):
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados?formato=json&dataInicial={desde}" if desde
           else f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados/ultimos/{n}?formato=json")
    return [(f"{x['data'][6:10]}-{x['data'][3:5]}", float(x["valor"])) for x in json.loads(get(url))]

def sidra(tab, vars_, classif, n=13):
    url = f"https://apisidra.ibge.gov.br/values/t/{tab}/n1/all/v/{','.join(map(str, vars_))}/p/last%20{n}/{classif}"
    out = {}
    for r in json.loads(get(url))[1:]:
        try: out.setdefault(int(r["D2C"]), []).append((f"{r['D3C'][:4]}-{r['D3C'][4:]}", float(r["V"])))
        except ValueError: pass
    return {k: sorted(v) for k, v in out.items()}

def fred(serie):
    linhas = list(csv.reader(io.StringIO(get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie}"))))[1:]
    return [(a, float(b)) for a, b in linhas if b not in (".", "")]

def rot(m): return f"{MESES[int(m[5:]) - 1]}/{m[2:4]}"
def ext(m): return f"{MESES_EXT[int(m[5:]) - 1]} de {m[:4]}"
def br(v, casas=1): return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(v, casas=1, sinal=False): return ("+" if sinal and v > 0 else "−" if v < 0 else "") + br(abs(v), casas) + "%"
def mil(v): return ("+" if v > 0 else "−" if v < 0 else "") + br(abs(v) / 1000, 0 if abs(v) >= 10000 else 1) + " mil"
def acumula(vs):
    f = 1.0
    for v in vs: f *= 1 + v / 100
    return (f - 1) * 100

# ---------------------------------------------------------------- cada indicador
def caged():
    est = sgs(28763, n=20)
    saldos = [(est[i][0], est[i][1] - est[i - 1][1]) for i in range(1, len(est))]
    m, v = saldos[-1]; ano = m[:4]
    ant = next((x for x in saldos if x[0] == f"{int(ano) - 1}{m[4:]}"), None)
    no_ano = sum(x for mm, x in saldos if mm[:4] == ano)
    selo = None
    if ant: selo = ("▲ ACIMA DE " if v > ant[1] else "▼ ABAIXO DE ") + rot(ant[0]).upper(), "bom" if v > ant[1] else "ruim"
    return {"id": "caged", "tag": "Brasil · Trabalho", "titulo": "Empregos com carteira", "sub": "Saldo do mês · Novo Caged",
            "ref": m, "ref_txt": ext(m), "valor": mil(v), "cor": "bom" if v > 0 else "ruim", "selo": selo,
            "frase": f"{'Vagas criadas' if v >= 0 else 'Vagas fechadas'} em {ext(m)}: contratações {'menos' if v >= 0 else 'mais'} demissões." + (f" Em {rot(ant[0])}, o saldo foi de {mil(ant[1])}." if ant else ""),
            "apoio": [("No ano", mil(no_ano), f"saldo desde janeiro de {ano}"), ("Em 12 meses", mil(sum(x for _, x in saldos[-12:])), "vagas com carteira"),
                      ("Total com carteira", br(est[-1][1] / 1e6, 1) + " mi", "vínculos formais ativos")],
            "graf_tit": "Saldo mês a mês · mil vagas", "graf": [(rot(mm), round(x / 1000, 1)) for mm, x in saldos[-12:]], "graf_fmt": "num1",
            "porque": "O Caged mostra a geração de empregos formais. Mais vagas significam mais renda e consumo.",
            "fonte": "Ministério do Trabalho (Novo Caged), via Banco Central", "tags": "#emprego #caged #carteiraassinada #economia"}

def inadimplencia():
    s = sgs(21112, desde="01/01/2011")
    m, v = s[-1]; ant = s[-2]; um_ano = next((x for x in s if x[0] == f"{int(m[:4]) - 1}{m[4:]}"), None)
    recorde = v >= max(x for _, x in s)
    selo = ("▲ RECORDE DA SÉRIE", "ruim") if recorde else (("▲ ALTA NO MÊS", "ruim") if v > ant[1] else ("▼ QUEDA NO MÊS", "bom") if v < ant[1] else None)
    return {"id": "inadimplencia", "tag": "Brasil · Crédito", "titulo": "Inadimplência das famílias", "sub": "Crédito livre · atrasos acima de 90 dias",
            "ref": m, "ref_txt": ext(m), "valor": pct(v, 1), "cor": "ruim" if v > ant[1] else "bom" if v < ant[1] else "neutro", "selo": selo,
            "frase": f"do valor emprestado às famílias com recursos livres está com atraso de mais de 90 dias." + (" É o maior nível da série, iniciada em 2011." if recorde else ""),
            "apoio": [("Mês anterior", pct(ant[1], 1), rot(ant[0])), ("Um ano antes", pct(um_ano[1], 1) if um_ano else "—", rot(um_ano[0]) if um_ano else ""),
                      ("Em 12 meses", (("+" if v - um_ano[1] > 0 else "−") + br(abs(v - um_ano[1]), 1) + " p.p.") if um_ano else "—", "variação")],
            "graf_tit": "Inadimplência mês a mês · %", "graf": [(rot(mm), x) for mm, x in s[-12:]], "graf_fmt": "num1", "base_zero": False,
            "porque": "Mais famílias atrasando pagamentos fazem os bancos cobrarem juros maiores e emprestarem menos.",
            "fonte": "Banco Central", "tags": "#inadimplencia #credito #endividamento #economia"}

def contas_externas():
    tc = sgs(22701, n=14); pib = sgs(23079, n=12); idp = sgs(22885, n=2); res = sgs(3546, n=3)
    m, v = tc[-1]; ant = next((x for x in tc if x[0] == f"{int(m[:4]) - 1}{m[4:]}"), None)
    r = next((x for x in res if x[0] == m), res[-1])
    selo = None
    if ant: selo = (("▼ DÉFICIT MENOR QUE " if v > ant[1] else "▲ DÉFICIT MAIOR QUE ") + rot(ant[0]).upper(), "bom" if v > ant[1] else "ruim") if v < 0 and ant[1] < 0 else None
    return {"id": "contas_externas", "tag": "Brasil · Setor externo", "titulo": "Contas externas", "sub": "Transações correntes · Banco Central",
            "ref": m, "ref_txt": ext(m), "valor": ("−" if v < 0 else "+") + "US$ " + br(abs(v) / 1000, 1) + " bi", "cor": "ruim" if v < 0 else "bom", "selo": selo,
            "frase": f"de {'déficit' if v < 0 else 'superávit'} nas transações correntes em {ext(m)}: o saldo de tudo o que o país compra, vende, paga e recebe do exterior." + (f" Em {rot(ant[0])}: US$ {br(ant[1] / 1000, 1)} bi." if ant else ""),
            "apoio": [("Em 12 meses", pct(abs(pib[-1][1]), 2) + " do PIB", "déficit acumulado" if pib[-1][1] < 0 else "superávit acumulado"),
                      ("Investimento direto", "US$ " + br(idp[-1][1] / 1000, 1) + " bi", f"no mês ({rot(idp[-1][0])})"),
                      ("Reservas", "US$ " + br(r[1] / 1000, 1) + " bi", f"fim de {rot(r[0])}")],
            "graf_tit": "Saldo em 12 meses · % do PIB", "graf": [(rot(mm), x) for mm, x in pib[-12:]], "graf_fmt": "num2",
            "porque": "Quando o investimento estrangeiro cobre o déficit, o país se financia sem pressão sobre o dólar.",
            "fonte": "Banco Central", "tags": "#setorexterno #dolar #investimentos #economia"}

def incc():
    s = sgs(7456, n=26); m, v = s[-1]; ano = m[:4]
    ant = next((x for x in s if x[0] == f"{int(ano) - 1}{m[4:]}"), None)
    doze = acumula([x for _, x in s[-12:]]); no_ano = acumula([x for mm, x in s if mm[:4] == ano])
    prev = s[-2]
    selo = ("▲ ALTA NO MÊS", "ruim") if v > prev[1] else ("▼ DESACELERA", "bom") if v < prev[1] else None
    return {"id": "incc", "tag": "Brasil · Construção", "titulo": "Custo da construção", "sub": "INCC-M · FGV",
            "ref": m, "ref_txt": ext(m), "valor": pct(v, 2, sinal=True), "cor": "ruim" if v > 0 else "bom", "selo": selo,
            "frase": f"em {ext(m)}, ante {pct(prev[1], 2, sinal=True)} no mês anterior. Mede materiais, equipamentos e mão de obra da construção.",
            "apoio": [("Em 12 meses", pct(doze, 2, sinal=True), "acumulado"), ("No ano", pct(no_ano, 2, sinal=True), f"desde janeiro de {ano}"),
                      (f"{MESES[int(m[5:]) - 1].capitalize()}/{int(ano[2:]) - 1}", pct(ant[1], 2, sinal=True) if ant else "—", "mesmo mês do ano passado")],
            "graf_tit": "Variação mês a mês · %", "graf": [(rot(mm), x) for mm, x in s[-12:]], "graf_fmt": "num2",
            "porque": "O INCC corrige parcelas de imóveis na planta: quando ele sobe, a prestação do comprador sobe junto.",
            "fonte": "FGV Ibre, via Banco Central", "tags": "#incc #construcao #imoveis #economia"}

def pesquisa_ibge(id_, tag, titulo, sub, tab, vars_, classif, porque, tags, fonte):
    d = sidra(tab, vars_, classif)
    mm, a, ac, d12 = (d.get(v, []) for v in vars_)
    m, v = mm[-1]
    seq = 0
    for _, x in reversed(mm):
        if (x < 0) == (v < 0) and x != 0: seq += 1
        else: break
    selo = None
    if v != 0: selo = ((f"▼ {seq}ª QUEDA SEGUIDA" if seq > 1 else "▼ QUEDA NO MÊS") if v < 0 else (f"▲ {seq}ª ALTA SEGUIDA" if seq > 1 else "▲ ALTA NO MÊS"), "ruim" if v < 0 else "bom")
    def ultimo(l): return l[-1][1] if l else None
    return {"id": id_, "tag": tag, "titulo": titulo, "sub": sub, "ref": m, "ref_txt": ext(m), "valor": pct(v, 1, sinal=True),
            "cor": "ruim" if v < 0 else "bom" if v > 0 else "neutro", "selo": selo,
            "frase": f"em {ext(m)} na comparação com o mês anterior, já descontados os efeitos sazonais.",
            "apoio": [("Ante um ano antes", pct(ultimo(a), 1, sinal=True) if a else "—", f"{rot(m)} x {rot(str(int(m[:4]) - 1) + m[4:])}"),
                      ("No ano", pct(ultimo(ac), 1, sinal=True) if ac else "—", "acumulado"), ("Em 12 meses", pct(ultimo(d12), 1, sinal=True) if d12 else "—", "acumulado")],
            "graf_tit": "Mês a mês · % em relação ao mês anterior", "graf": [(rot(x), y) for x, y in mm[-12:]], "graf_fmt": "num1",
            "porque": porque, "fonte": fonte, "tags": tags}

def industria():
    return pesquisa_ibge("industria", "Brasil · Indústria", "Produção industrial", "Indústria geral · PIM-PF · IBGE", 8888, [11601, 11602, 11603, 11604],
                         "c544/129314", "A indústria puxa empregos de maior salário e investimentos; quedas seguidas indicam economia desacelerando.",
                         "#industria #ibge #pib #economia", "IBGE (PIM-PF)")

def varejo():
    return pesquisa_ibge("varejo", "Brasil · Varejo", "Vendas no varejo", "Volume de vendas · PMC · IBGE", 8880, [11708, 11709, 11710, 11711],
                         "c11046/56734", "As vendas do varejo mostram o fôlego do consumo das famílias, o maior componente do PIB.",
                         "#varejo #consumo #ibge #economia", "IBGE (PMC)")

def focus():
    ano = date.today().year
    def serie(ind):
        url = ("https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$top=60&$format=json"
               f"&$filter=Indicador%20eq%20'{urllib.request.quote(ind)}'%20and%20DataReferencia%20eq%20'{ano}'%20and%20baseCalculo%20eq%200&$orderby=Data%20desc&$select=Data,Mediana")
        return {x["Data"]: x["Mediana"] for x in json.loads(get(url))["value"]}
    ip = serie("IPCA")
    sextas = sorted(d for d in ip if date.fromisoformat(d).weekday() == 4)[-6:]
    f = sextas[-1]; v = ip[f]; a = ip[sextas[-2]]
    seq = 0
    for i in range(len(sextas) - 1, 0, -1):
        if (ip[sextas[i]] > ip[sextas[i - 1]]) == (v > a) and ip[sextas[i]] != ip[sextas[i - 1]]: seq += 1
        else: break
    selo = ((f"▲ {seq}ª ALTA SEGUIDA" if seq > 1 else "▲ SOBE NA SEMANA") if v > a else (f"▼ {seq}ª QUEDA SEGUIDA" if seq > 1 else "▼ CAI NA SEMANA"), "ruim" if v > a else "bom") if v != a else ("= ESTÁVEL", "neutro")
    out = {}
    for ind in ("Selic", "PIB Total", "Câmbio"):
        try: s = serie(ind); out[ind] = s.get(f) or s[max(s)]
        except Exception: out[ind] = None
    publ = date.fromisoformat(f) + timedelta(days=3)
    return {"id": "focus", "tag": "Brasil · Expectativas", "titulo": "Boletim Focus", "sub": f"Mercado espera inflação de {ano} de",
            "ref": f, "ref_txt": f"divulgado em {publ.day:02d}/{publ.month:02d}", "valor": pct(v, 2), "cor": "ruim" if v > a else "bom" if v < a else "neutro", "selo": selo,
            "frase": f"para o IPCA de {ano}, ante {pct(a, 2)} na semana anterior. A meta de inflação é de 3%, com tolerância até 4,5%.",
            "apoio": [("Selic no fim do ano", pct(out["Selic"], 2) if out["Selic"] else "—", "mediana"), ("PIB", pct(out["PIB Total"], 2, sinal=True) if out["PIB Total"] else "—", f"crescimento em {ano}"),
                      ("Dólar no fim do ano", "R$ " + br(out["Câmbio"], 2) if out["Câmbio"] else "—", "mediana")],
            "graf_tit": f"IPCA {ano} esperado nas últimas semanas · %", "graf": [(f"{x[8:]}/{x[5:7]}", ip[x]) for x in sextas], "graf_fmt": "num2", "base_zero": False,
            "porque": "O Focus reúne as projeções de cerca de cem instituições e orienta as apostas sobre os próximos passos do Copom.",
            "fonte": "Banco Central (Boletim Focus)", "tags": "#focus #inflacao #selic #economia"}

def juros_externos(id_, tag, titulo, sub, series, datas, porque, tags, fonte, apoio_extra):
    hist = {s: fred(s) for s in series}
    base = hist[series[0]]
    mudancas = [base[0]] + [base[i] for i in range(1, len(base)) if base[i][1] != base[i - 1][1]]
    ult_mud = mudancas[-1][0]
    hoje = date.today().isoformat()
    reun = max([d for d in datas if d < hoje] + [ult_mud])
    taxa = lambda s: hist[s][-1][1]
    if len(series) == 2: valor = br(taxa(series[1]), 2) + "%–" + br(taxa(series[0]), 2) + "%"
    else: valor = br(taxa(series[0]), 2) + "%"
    var = mudancas[-1][1] - mudancas[-2][1] if len(mudancas) > 1 else 0
    mudou = ult_mud >= reun
    acao = ("▼ CORTE DE " if var < 0 else "▲ ALTA DE ") + br(abs(var), 2) + " P.P." if mudou else "= MANTIDOS"
    graf = [(f"{MESES[int(d[5:7]) - 1]}/{d[2:4]}", v) for d, v in mudancas[-10:]]
    return {"id": id_, "tag": tag, "titulo": titulo, "sub": sub, "ref": reun, "ref_txt": f"decisão de {reun[8:]}/{reun[5:7]}/{reun[:4]}",
            "valor": valor, "cor": "neutro", "selo": (acao, "neutro"),
            "frase": "ao ano. " + ("Os juros foram " + ("cortados" if var < 0 else "elevados") + " na última reunião." if mudou else f"A taxa segue no mesmo nível desde {MESES_EXT[int(ult_mud[5:7]) - 1]} de {ult_mud[:4]}."),
            "apoio": apoio_extra(hist, mudancas), "graf_tit": "Taxa a cada mudança · % ao ano", "graf": graf, "graf_fmt": "num2", "base_zero": False,
            "porque": porque, "fonte": fonte, "tags": tags}

def _apoio(rotulo_taxa, datas, terceiro):
    def f(h, m):
        hoje = date.today().isoformat(); prox = next((d for d in datas if d >= hoje), None)
        return [("Última mudança", f"{m[-1][0][8:]}/{m[-1][0][5:7]}/{m[-1][0][2:4]}", rotulo_taxa),
                ("Taxa anterior", br(m[-2][1], 2) + "%" if len(m) > 1 else "—", "antes da última mudança"),
                terceiro() if terceiro else ("Próxima reunião", f"{prox[8:]}/{prox[5:7]}" if prox else "—", "calendário oficial")]
    return f

def fed():
    u = fred("UNRATE")
    return juros_externos("fed", "EUA · Juros", "Juros nos EUA", "Decisão do Fed (Federal Reserve)", ["DFEDTARU", "DFEDTARL"], FOMC,
                          "Juros altos nos EUA atraem dólares para lá e costumam pressionar o câmbio no Brasil.", "#fed #juros #eua #economia",
                          "Federal Reserve, via FRED", _apoio("teto da taxa", FOMC, lambda: ("Desemprego nos EUA", pct(u[-1][1], 1), rot(u[-1][0][:7]))))

def bce():
    return juros_externos("bce", "Zona do euro · Juros", "Juros na zona do euro", "Taxa de depósito do BCE", ["ECBDFR"], BCE,
                          "Os juros europeus influenciam o fluxo de capital para emergentes como o Brasil e o preço do euro.", "#bce #juros #europa #economia",
                          "Banco Central Europeu, via FRED", _apoio("taxa de depósito", BCE, None))

def payroll():
    p = fred("PAYEMS")[-14:]; u = fred("UNRATE")
    var = [(p[i][0][:7], (p[i][1] - p[i - 1][1]) * 1000) for i in range(1, len(p))]
    m, v = var[-1]; ant = var[-2]
    selo = ("▲ ACIMA DE " + rot(ant[0]).upper(), "bom") if v > ant[1] else ("▼ ABAIXO DE " + rot(ant[0]).upper(), "ruim")
    return {"id": "payroll", "tag": "EUA · Emprego", "titulo": "Payroll", "sub": "Vagas criadas fora do campo · EUA",
            "ref": m, "ref_txt": ext(m), "valor": mil(v), "cor": "bom" if v > 0 else "ruim", "selo": selo,
            "frase": f"vagas em {ext(m)} nos Estados Unidos, fora do setor agrícola. No mês anterior, {mil(ant[1])}.",
            "apoio": [("Desemprego", pct(u[-1][1], 1), rot(u[-1][0][:7])), ("Média de 3 meses", mil(sum(x for _, x in var[-3:]) / 3), "vagas por mês"),
                      ("Total empregado", br(p[-1][1] / 1000, 1) + " mi", "fora do campo")],
            "graf_tit": "Vagas criadas por mês · mil", "graf": [(rot(mm), round(x / 1000, 0)) for mm, x in var[-12:]], "graf_fmt": "num0",
            "porque": "Um mercado de trabalho forte nos EUA reduz a chance de corte de juros por lá, o que afeta dólar e bolsa no Brasil.",
            "fonte": "BLS (Departamento do Trabalho dos EUA), via FRED", "tags": "#payroll #eua #emprego #economia"}

COLETORES = [caged, inadimplencia, contas_externas, incc, industria, varejo, focus, fed, bce, payroll]

def main():
    try: anterior = json.load(open("indicadores2.json", encoding="utf-8"))["itens"]
    except Exception: anterior = {}
    itens, erros = {}, []
    for f in COLETORES:
        try: itens[f.__name__] = f()
        except Exception as ex:
            erros.append(f"{f.__name__}: {ex!r}"[:300]); print("::warning::" + erros[-1])
            if f.__name__ in anterior: itens[f.__name__] = anterior[f.__name__]
    json.dump({"atualizado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "itens": itens, "erros": erros},
              open("indicadores2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in itens.items(): print(f"{k:16} {v['ref']:10} {v['valor']:>16}  {(v.get('selo') or ('', ''))[0]}")
    if len(erros) == len(COLETORES): sys.exit(1)

if __name__ == "__main__":
    main()
