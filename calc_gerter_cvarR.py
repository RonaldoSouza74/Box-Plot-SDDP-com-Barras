"""Constrói a gerter_cvarR_Stage-2-13 a partir dos cenários que geraram a
vergnd_cvarR_Stage-2-13.

Método (para cada subsistema e cada hora dos 12 meses):
  1. Na vergnd_Distribuicao há 10 cenários (Seq. 1..10); 10% de 10 = 1, então
     o "10% maiores" é o cenário de maior vergnd. A vergnd_cvarR é esse máximo.
  2. Os cenários selecionados são todos os que atingem esse máximo (empates
     entram todos; quando os 10 valem zero, entram os 10).
  3. gerter_cvarR = média da gerter_Distribuicao nesses cenários selecionados.

Gera:
  - dados/gerter_cvarR_Stage-2-13.csv (mesmo formato da vergnd_cvarR)
  - dados/cenarios_selecionados_Stage-2-13.csv (cenários por subsistema/hora)
  - planilhas/calculo_gerter_cvarR_Stage-2-13.xlsx (passo a passo, com fórmulas)

Uso:
    python calc_gerter_cvarR.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / "dados"
ARQ_VERGND_DIST = DADOS / "vergnd_Distribuicao_Stage-2-13.csv"
ARQ_GERTER_DIST = DADOS / "gerter_Distribuicao_Stage-2-13.csv"
ARQ_VERGND_CVAR = DADOS / "vergnd_cvarR_Stage-2-13.csv"
ARQ_GERTER_CVAR = DADOS / "gerter_cvarR_Stage-2-13.csv"
ARQ_CENARIOS = DADOS / "cenarios_selecionados_Stage-2-13.csv"
ARQ_XLSX = RAIZ / "planilhas" / "calculo_gerter_cvarR_Stage-2-13.xlsx"

ANO = 2030
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out",
         "Nov", "Dez"]
N_CEN = 10
LIN0 = 5  # primeira linha de dados nas abas de subsistema

FONTE = "Arial"
F_NORMAL = Font(name=FONTE, size=10)
F_INPUT = Font(name=FONTE, size=10, color="0000FF")      # dado copiado do CSV
F_LINK = Font(name=FONTE, size=10, color="008000")       # link p/ outra aba
F_BOLD = Font(name=FONTE, size=10, bold=True)
F_TITULO = Font(name=FONTE, size=14, bold=True)
F_NOTA = Font(name=FONTE, size=9, italic=True, color="52514E")
FILL_CAB = PatternFill("solid", fgColor="DDE7F5")
FILL_RES = PatternFill("solid", fgColor="FFF2CC")
AL_CAB = Alignment(horizontal="center", vertical="center", wrap_text=True)


def ler(caminho):
    d = pd.read_csv(caminho, skiprows=3, encoding="latin-1",
                    skipinitialspace=True)
    d.columns = [c.strip() for c in d.columns]
    d = d.dropna(axis=1, how="all")
    return d.rename(columns={d.columns[0]: "Stag", d.columns[1]: "Seq",
                             d.columns[2]: "Blck"})


def calcular():
    vd, gd, vc = ler(ARQ_VERGND_DIST), ler(ARQ_GERTER_DIST), ler(ARQ_VERGND_CVAR)
    subs = list(vd.columns[3:])
    assert list(gd.columns[3:]) == subs == list(vc.columns[3:])
    assert (vd[["Stag", "Seq", "Blck"]].values ==
            gd[["Stag", "Seq", "Blck"]].values).all()
    assert sorted(vd["Seq"].unique()) == list(range(1, N_CEN + 1))

    chaves = vc[["Stag", "Blck"]].reset_index(drop=True)
    res = {}
    for s in subs:
        V = vd.pivot(index=["Stag", "Blck"], columns="Seq", values=s)
        G = gd.pivot(index=["Stag", "Blck"], columns="Seq", values=s)
        V = V.loc[list(map(tuple, chaves.values))]
        G = G.loc[V.index]
        mx = V.max(axis=1)
        sel = V.eq(mx, axis=0)
        ger = (G.where(sel)).mean(axis=1)
        dif = (mx.values - vc[s].values)
        res[s] = dict(V=V.values, G=G.values, mx=mx.values, sel=sel.values,
                      ger=ger.values, cvar=vc[s].values, dif=dif)
        print(f"{s:12s} máx|vergnd_max - vergnd_cvarR| = {np.abs(dif).max():g}"
              f" | horas c/ empate: {(sel.sum(axis=1) > 1).sum()}")
    return chaves, subs, res


def fmt(x):
    return f"{x:.10g}"


def gravar_csv(chaves, subs, res):
    with open(ARQ_VERGND_CVAR, encoding="latin-1", newline="") as f:
        cab = [f.readline() for _ in range(4)]
    linhas = []
    for i, (stg, blk) in enumerate(chaves.values):
        vals = ",".join(fmt(res[s]["ger"][i]) for s in subs)
        linhas.append(f"{stg},1,{blk},{vals}\r\n")
    with open(ARQ_GERTER_CVAR, "w", encoding="latin-1", newline="") as f:
        f.writelines(cab + linhas)
    print(f"CSV: {ARQ_GERTER_CVAR}")

    # Cenários selecionados (Seq.) por subsistema e hora, separados por espaço
    with open(ARQ_CENARIOS, "w", encoding="latin-1", newline="") as f:
        f.write("Mês,Mês/Ano,Hora," + ",".join(subs) + "\r\n")
        for i, (stg, blk) in enumerate(chaves.values):
            cen = [" ".join(str(k + 1) for k in np.flatnonzero(res[s]["sel"][i]))
                   for s in subs]
            f.write(f"{stg},{MESES[int(stg) - 2]}/{ANO},{blk}," + ",".join(cen)
                    + "\r\n")
    print(f"CSV: {ARQ_CENARIOS}")


def nome_aba(s):
    return s.replace(".", "")


def ref(s):
    return f"'{nome_aba(s)}'"


def cel(ws, valor, fonte=F_NORMAL, fill=None, al=None, fmt_num=None):
    c = WriteOnlyCell(ws, value=valor)
    c.font = fonte
    if fill:
        c.fill = fill
    if al:
        c.alignment = al
    if fmt_num:
        c.number_format = fmt_num
    return c


def aba_subsistema(wb, s, chaves, r):
    ws = wb.create_sheet(nome_aba(s))
    L = get_column_letter
    cV = [L(5 + k) for k in range(N_CEN)]            # E..N  vergnd cen 1..10
    cMax, cN, cSel = "O", "P", "Q"
    cG = [L(18 + k) for k in range(N_CEN)]           # R..AA gerter cen 1..10
    cRes, cOrig, cDif = "AB", "AC", "AD"
    ws.freeze_panes = f"E{LIN0}"
    larg = {"A": 8, "B": 10, "C": 9, "D": 8, cMax: 12, cN: 10, cSel: 16,
            cRes: 14, cOrig: 14, cDif: 11}
    for k in range(N_CEN):
        larg[cV[k]] = 10
        larg[cG[k]] = 10
    for col, w in larg.items():
        ws.column_dimensions[col].width = w

    ws.append([cel(ws, f"{s} — cálculo da gerter_cvarR (passo a passo)",
                   F_TITULO)])
    ws.append([cel(ws, "Azul = valor copiado dos CSVs do SDDP; preto = fórmula."
                       " Passo 1: maior vergnd entre os 10 cenários. Passo 2:"
                       " cenários que atingem esse máximo (empates entram"
                       " todos). Passo 3: média da gerter nesses cenários.",
                   F_NOTA)])
    grupos = [None] * 30
    grupos[0] = "Identificação"
    grupos[4] = "vergnd_Distribuicao — cenário (Seq.)"
    grupos[14] = "Passo 1"
    grupos[15] = "Passo 2"
    grupos[17] = "gerter_Distribuicao — cenário (Seq.)"
    grupos[27] = "Passo 3"
    grupos[28] = "Conferência"
    ws.append([cel(ws, g, F_BOLD, FILL_CAB) if g else cel(ws, None, fill=FILL_CAB)
               for g in grupos])
    cab = (["Estágio (Mês no arquivo)", "Mês/Ano", "Hora seq. no mês",
            "Hora do dia"] + [k + 1 for k in range(N_CEN)] +
           ["Máx. vergnd (= 10% maiores)", "Nº cenários no máximo",
            "Cenário(s) selecionado(s)"] + [k + 1 for k in range(N_CEN)] +
           ["gerter_cvarR (média dos selecionados)",
            "vergnd_cvarR (arquivo original)", "Diferença Máx − original"])
    ws.append([cel(ws, h, F_BOLD, FILL_CAB, AL_CAB) for h in cab])

    for i, (stg, blk) in enumerate(chaves.values):
        n = LIN0 + i
        vV = f"{cV[0]}{n}:{cV[-1]}{n}"
        vG = f"{cG[0]}{n}:{cG[-1]}{n}"
        sel_txt = "&".join(f'IF({cV[k]}{n}={cMax}{n}," {k + 1}","")'
                           for k in range(N_CEN))
        linha = [cel(ws, int(stg), F_INPUT),
                 cel(ws, f"{MESES[int(stg) - 2]}/{ANO}"),
                 cel(ws, int(blk), F_INPUT),
                 cel(ws, f"=MOD(C{n}-1,24)+1")]
        linha += [cel(ws, float(v), F_INPUT) for v in r["V"][i]]
        linha += [cel(ws, f"=MAX({vV})"),
                  cel(ws, f"=COUNTIF({vV},{cMax}{n})"),
                  cel(ws, f"=TRIM({sel_txt})")]
        linha += [cel(ws, float(v), F_INPUT) for v in r["G"][i]]
        linha += [cel(ws, f"=AVERAGEIF({vV},{cMax}{n},{vG})", F_BOLD,
                      FILL_RES),
                  cel(ws, float(r["cvar"][i]), F_INPUT),
                  cel(ws, f"={cMax}{n}-{cOrig}{n}")]
        ws.append(linha)
    return ws


def aba_final(wb, chaves, subs):
    ws = wb.create_sheet("gerter_cvarR")
    ws.freeze_panes = "D3"
    ws.column_dimensions["A"].width = 8
    for k in range(len(subs)):
        ws.column_dimensions[get_column_letter(4 + k)].width = 12
    ws.append([cel(ws, "gerter_cvarR_Stage-2-13 — média da gerter nos cenários"
                       " que geraram a vergnd_cvarR (verde = link para a aba do"
                       " subsistema, coluna AB)", F_BOLD)])
    ws.append([cel(ws, h, F_BOLD, FILL_CAB, AL_CAB)
               for h in ["Mês", "Seq.", "Hora"] + subs])
    for i, (stg, blk) in enumerate(chaves.values):
        n = LIN0 + i
        ws.append([cel(ws, int(stg), F_INPUT), cel(ws, 1, F_INPUT),
                   cel(ws, int(blk), F_INPUT)] +
                  [cel(ws, f"={ref(s)}!AB{n}", F_LINK) for s in subs])


def aba_cenarios(wb, chaves, subs):
    ws = wb.create_sheet("Cenarios_selecionados")
    ws.freeze_panes = "D3"
    for k in range(len(subs)):
        ws.column_dimensions[get_column_letter(4 + k)].width = 14
    ws.append([cel(ws, "Cenários (Seq.) que formam os 10% maiores vergnd em cada"
                       " hora — empates listam todos; '1 2 … 10' = todos os"
                       " cenários com vergnd = 0 (verde = link p/ coluna Q da"
                       " aba do subsistema)", F_BOLD)])
    ws.append([cel(ws, h, F_BOLD, FILL_CAB, AL_CAB)
               for h in ["Mês", "Mês/Ano", "Hora"] + subs])
    for i, (stg, blk) in enumerate(chaves.values):
        n = LIN0 + i
        ws.append([cel(ws, int(stg), F_INPUT),
                   cel(ws, f"{MESES[int(stg) - 2]}/{ANO}"),
                   cel(ws, int(blk), F_INPUT)] +
                  [cel(ws, f"={ref(s)}!Q{n}", F_LINK) for s in subs])


def aba_resumo(wb, subs):
    ws = wb.create_sheet("Resumo")
    last = LIN0 + 8760 - 1
    ws.column_dimensions["A"].width = 14
    for k in range(2, 30):
        ws.column_dimensions[get_column_letter(k)].width = 13
    ws.append([cel(ws, "Resumo por subsistema (todas as células são fórmulas"
                       " sobre as abas de cada subsistema)", F_TITULO)])
    ws.append([])
    ws.append([cel(ws, h, F_BOLD, FILL_CAB, AL_CAB) for h in [
        "Subsistema", "Horas", "Horas com cenário único",
        "Horas com empate (máx. > 0)", "Horas com máx. vergnd = 0 (todos os"
        " cenários entram)", "Maior diferença vs vergnd_cvarR",
        "Menor diferença vs vergnd_cvarR", "Média anual gerter_cvarR (MW)"]])
    for s in subs:
        a = ref(s)
        P = f"{a}!$P${LIN0}:$P${last}"
        O = f"{a}!$O${LIN0}:$O${last}"
        ws.append([cel(ws, s, F_BOLD),
                   cel(ws, f"=COUNT({a}!$C${LIN0}:$C${last})"),
                   cel(ws, f"=COUNTIF({P},1)"),
                   cel(ws, f'=COUNTIFS({P},">1",{O},">0")'),
                   cel(ws, f"=COUNTIF({O},0)"),
                   cel(ws, f"=MAX({a}!$AD${LIN0}:$AD${last})"),
                   cel(ws, f"=MIN({a}!$AD${LIN0}:$AD${last})"),
                   cel(ws, f"=AVERAGE({a}!$AB${LIN0}:$AB${last})",
                       fmt_num="#,##0.00")])
    ws.append([])
    ws.append([cel(ws, "Horas em que cada cenário foi o único de maior vergnd",
                   F_BOLD)])
    ws.append([cel(ws, h, F_BOLD, FILL_CAB, AL_CAB) for h in
               ["Subsistema"] + [f"Cenário {k}" for k in range(1, N_CEN + 1)]
               + ["Total"]])
    lin_freq = 3 + len(subs) + 4  # 1ª linha da tabela de frequência
    for j, s in enumerate(subs):
        a = ref(s)
        O = f"{a}!$O${LIN0}:$O${last}"
        P = f"{a}!$P${LIN0}:$P${last}"
        row = [cel(ws, s, F_BOLD)]
        for k in range(N_CEN):
            c = get_column_letter(5 + k)
            row.append(cel(ws, f"=SUMPRODUCT(({a}!${c}${LIN0}:${c}${last}={O})"
                               f"*({P}=1))"))
        row.append(cel(ws, f"=SUM(B{lin_freq + j}:K{lin_freq + j})"))
        ws.append(row)
    ws.append([])
    ws.append([cel(ws, "Horas em que cada cenário está entre os de maior vergnd"
                       " (inclui empates)", F_BOLD)])
    ws.append([cel(ws, h, F_BOLD, FILL_CAB, AL_CAB) for h in
               ["Subsistema"] + [f"Cenário {k}" for k in range(1, N_CEN + 1)]])
    for s in subs:
        a = ref(s)
        O = f"{a}!$O${LIN0}:$O${last}"
        row = [cel(ws, s, F_BOLD)]
        for k in range(N_CEN):
            c = get_column_letter(5 + k)
            row.append(cel(ws, f"=SUMPRODUCT(--({a}!${c}${LIN0}:${c}${last}"
                               f"={O}))"))
        ws.append(row)


def aba_leiame(wb, subs, chaves, res):
    ws = wb.create_sheet("Leia-me")
    grade = {}
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 30
    for c in "CDEFGHIJKLM":
        ws.column_dimensions[c].width = 12

    def put(r, c, v, f=F_NORMAL, fill=None, fmt_num=None):
        x = cel(ws, v, f, fill, fmt_num=fmt_num)
        grade[(r, c)] = x
        return x

    put(1, 2, "Cálculo da gerter_cvarR_Stage-2-13", F_TITULO)
    texto = [
        "Arquivos de origem (dados do SDDP, sem alteração):",
        "  • vergnd_Distribuicao_Stage-2-13.csv — vergnd por cenário (Seq. 1 a"
        " 10), estágio e hora",
        "  • gerter_Distribuicao_Stage-2-13.csv — gerter por cenário, mesma"
        " estrutura",
        "  • vergnd_cvarR_Stage-2-13.csv — resultado de referência (usado só"
        " para conferência)",
        "",
        "Estágio 2 = Jan/2030 … estágio 13 = Dez/2030. Subsistemas: colunas D"
        " a Q (AC RO a XINGU).",
        "",
        "Passo a passo (cada aba de subsistema, uma linha por hora):",
        "  Passo 1 — coluna O: maior vergnd entre os 10 cenários = MAX(E:N)."
        " Com 10 cenários, 10% = 1 cenário,",
        "            logo a média dos 10% maiores é o próprio máximo (coluna AD"
        " confere com a vergnd_cvarR original).",
        "  Passo 2 — colunas P e Q: quantos e quais cenários atingem o máximo."
        " Empates entram todos; se os 10",
        "            cenários valem zero (sem curtailment), os 10 são"
        " selecionados.",
        "  Passo 3 — coluna AB: média da gerter apenas nos cenários selecionados"
        " = AVERAGEIF(E:N; O; R:AA).",
        "",
        "Aba gerter_cvarR: tabela final no mesmo formato da vergnd_cvarR (links"
        " para a coluna AB de cada aba).",
        "Aba Cenarios_selecionados: quais cenários (Seq.) entraram em cada"
        " hora, para cada subsistema.",
        "Aba Resumo: contagem de horas com cenário único/empate e frequência de"
        " cada cenário.",
        "Cores: azul = dado copiado dos CSVs; preto = fórmula; verde = link"
        " para outra aba; amarelo = resultado.",
    ]
    for i, t in enumerate(texto):
        put(3 + i, 2, t, F_BOLD if t.endswith(":") else F_NORMAL)

    r0 = 3 + len(texto) + 1
    put(r0, 2, "Por que 1 cenário:", F_BOLD)
    put(r0 + 1, 2, "Nº de cenários (Seq.)")
    put(r0 + 1, 3, N_CEN, F_INPUT).comment = Comment(
        "Seq. 1 a 10 nos arquivos *_Distribuicao_Stage-2-13.csv", "Claude")
    put(r0 + 2, 2, "Fração considerada")
    put(r0 + 2, 3, 0.10, F_INPUT, fmt_num="0%").comment = Comment(
        "10% maiores, conforme definido pelo usuário", "Claude")
    put(r0 + 3, 2, "Cenários nos 10% maiores")
    put(r0 + 3, 3, f"=C{r0 + 1}*C{r0 + 2}", F_BOLD, FILL_RES)

    # Exemplos: uma hora com cenário único e uma com empate
    exemplos = []
    r = res["NORDESTE"]
    i = int(np.argmax(r["sel"].sum(axis=1) == 1))
    exemplos.append(("NORDESTE", i, "cenário único"))
    r = res["MAN AP BV"]
    m = (r["sel"].sum(axis=1) > 1) & (r["mx"] > 0)
    m &= np.array([len(set(r["G"][j][r["sel"][j]])) > 1 for j in range(len(m))])
    exemplos.append(("MAN AP BV", int(np.argmax(m)), "empate com máx. > 0"))
    r = res["SUL"]
    exemplos.append(("SUL", int(np.argmax(r["mx"] == 0)),
                     "todos os cenários com vergnd = 0"))

    rr = r0 + 5
    for s, i, desc in exemplos:
        n = LIN0 + i
        a = ref(s)
        stg, blk = chaves.values[i]
        put(rr, 2, f"Exemplo — {s}, {MESES[int(stg) - 2]}/{ANO}, hora seq."
                   f" {blk} (linha {n} da aba) — {desc}", F_BOLD)
        put(rr + 1, 2, "Cenário (Seq.)", F_BOLD, FILL_CAB)
        put(rr + 2, 2, "vergnd", F_BOLD)
        put(rr + 3, 2, "Selecionado? (vergnd = máx.)", F_BOLD)
        put(rr + 4, 2, "gerter", F_BOLD)
        for k in range(N_CEN):
            c = 3 + k
            cv = get_column_letter(5 + k)
            cg = get_column_letter(18 + k)
            put(rr + 1, c, k + 1, F_BOLD, FILL_CAB)
            put(rr + 2, c, f"={a}!{cv}{n}", F_LINK)
            put(rr + 3, c, f'=IF({get_column_letter(c)}{rr + 2}=$C${rr + 5},'
                           f'"sim","")')
            put(rr + 4, c, f"={a}!{cg}{n}", F_LINK)
        put(rr + 5, 2, "Passo 1 — máx. vergnd")
        put(rr + 5, 3, f"=MAX(C{rr + 2}:L{rr + 2})", F_BOLD)
        put(rr + 6, 2, "Passo 2 — nº selecionados")
        put(rr + 6, 3, f'=COUNTIF(C{rr + 3}:L{rr + 3},"sim")', F_BOLD)
        put(rr + 7, 2, "Passo 3 — gerter_cvarR")
        put(rr + 7, 3, f'=AVERAGEIF(C{rr + 3}:L{rr + 3},"sim",'
                       f'C{rr + 4}:L{rr + 4})', F_BOLD, FILL_RES)
        put(rr + 7, 4, f"(confere com {nome_aba(s)}!AB{n})", F_NOTA)
        rr += 9

    for r in range(1, max(k[0] for k in grade) + 1):
        ncol = max([k[1] for k in grade if k[0] == r] or [0])
        ws.append([grade.get((r, c)) for c in range(1, ncol + 1)])


def gravar_xlsx(chaves, subs, res):
    ARQ_XLSX.parent.mkdir(exist_ok=True)
    # Modo write-only: as abas são escritas linha a linha (arquivo grande).
    wb = Workbook(write_only=True)
    aba_leiame(wb, subs, chaves, res)
    aba_resumo(wb, subs)
    aba_final(wb, chaves, subs)
    aba_cenarios(wb, chaves, subs)
    for s in subs:
        aba_subsistema(wb, s, chaves, res[s])
    wb.save(ARQ_XLSX)
    print(f"XLSX: {ARQ_XLSX}")


if __name__ == "__main__":
    ch, ss, rs = calcular()
    gravar_csv(ch, ss, rs)
    gravar_xlsx(ch, ss, rs)
