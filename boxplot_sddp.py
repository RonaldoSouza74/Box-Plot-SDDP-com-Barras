"""Box plots horários por mês e por subsistema a partir de um CSV do SDDP.

Lê um arquivo de saída do SDDP (ex.: vergnd_cvarR_Stage-2-13.csv), converte a
hora sequencial do mês (1..744) em hora do dia (1..24) e gera, para cada mês,
box plots com as 24 horas no eixo x para todas as colunas de subsistema.

Mapeamento de estágios: o mês 2 do arquivo corresponde a janeiro de 2030 e o
mês 13 a dezembro de 2030 (mês civil = estágio - 1).

Uso:
    python boxplot_sddp.py [caminho_csv] [pasta_saida]
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

ANO = 2030
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# Estilo: uma única série por gráfico -> uma cor, eixos e grade discretos.
COR = "#2a78d6"
COR_TEXTO = "#0b0b0b"
COR_TEXTO_2 = "#52514e"
COR_GRADE = "#e4e3df"
FUNDO = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": FUNDO,
    "axes.facecolor": FUNDO,
    "axes.edgecolor": COR_GRADE,
    "axes.labelcolor": COR_TEXTO_2,
    "axes.titlecolor": COR_TEXTO,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": COR_TEXTO_2,
    "ytick.color": COR_TEXTO_2,
    "font.size": 9,
})


def ler_csv(caminho):
    """Lê o CSV do SDDP (3 linhas de cabeçalho + linha de colunas)."""
    with open(caminho, encoding="latin-1") as f:
        info = f.readline().split(",")
    unidade = info[3].strip() if len(info) > 3 else ""

    df = pd.read_csv(caminho, skiprows=3, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "Mes", df.columns[1]: "Seq",
                            df.columns[2]: "Hora"})
    df = df.dropna(axis=1, how="all")
    # Hora sequencial no mês (1..744) -> hora do dia (1..24)
    df["HoraDia"] = (df["Hora"] - 1) % 24 + 1
    df["Dia"] = (df["Hora"] - 1) // 24 + 1
    subsistemas = [c for c in df.columns
                   if c not in ("Mes", "Seq", "Hora", "HoraDia", "Dia")]
    return df, subsistemas, unidade


def rotulo_mes(estagio):
    """Estágio 2 -> Janeiro/2030 ... estágio 13 -> Dezembro/2030."""
    m = int(estagio) - 1
    return m, f"{MESES[m - 1]}/{ANO}"


def desenhar_boxplot(ax, dados_mes, subsistema, unidade):
    horas = range(1, 25)
    ax.set_xticks(list(horas))
    ax.set_xticklabels([str(h) for h in horas], fontsize=7)
    ax.set_xlim(0.3, 24.7)
    ax.set_xlabel("Hora do dia")
    if (dados_mes[subsistema] == 0).all():
        ax.text(0.5, 0.5, "Sem valores no mês (todos zero)",
                transform=ax.transAxes, ha="center", va="center",
                color=COR_TEXTO_2, fontsize=10)
        ax.set_yticks([])
        return
    series = [dados_mes.loc[dados_mes["HoraDia"] == h, subsistema].values
              for h in horas]
    ax.boxplot(
        series,
        positions=list(horas),
        widths=0.6,
        patch_artist=True,
        boxprops=dict(facecolor=COR + "40", edgecolor=COR, linewidth=1),
        medianprops=dict(color=COR, linewidth=2),
        whiskerprops=dict(color=COR, linewidth=1),
        capprops=dict(color=COR, linewidth=1),
        flierprops=dict(marker="o", markersize=3, markerfacecolor="none",
                        markeredgecolor=COR, alpha=0.6),
    )
    ax.grid(axis="y", color=COR_GRADE, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylabel(unidade)


def main():
    raiz = Path(__file__).resolve().parent
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        raiz / "dados" / "vergnd_cvarR_Stage-2-13.csv"
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else raiz / "graficos"
    nome_var = csv.stem.split("_")[0]

    df, subsistemas, unidade = ler_csv(csv)
    (saida / "por_mes").mkdir(parents=True, exist_ok=True)

    ncols = 4
    nrows = -(-len(subsistemas) // ncols)

    with PdfPages(saida / f"boxplots_{nome_var}_{ANO}.pdf") as pdf:
        for estagio, dados_mes in df.groupby("Mes"):
            m, rotulo = rotulo_mes(estagio)
            dias = dados_mes["Dia"].max()
            prefixo = f"{ANO}-{m:02d}_{MESES[m - 1]}"

            # Figura com todos os subsistemas do mês
            fig, axes = plt.subplots(nrows, ncols,
                                     figsize=(6 * ncols, 3.6 * nrows))
            for ax, sub in zip(axes.flat, subsistemas):
                desenhar_boxplot(ax, dados_mes, sub, unidade)
                ax.set_title(sub, loc="left", fontweight="bold")
            for ax in list(axes.flat)[len(subsistemas):]:
                ax.set_visible(False)
            fig.suptitle(f"{nome_var} — {rotulo} — distribuição por hora do "
                         f"dia ({dias} dias)", fontsize=15, x=0.01, ha="left",
                         color=COR_TEXTO, fontweight="bold")
            fig.tight_layout(rect=(0, 0, 1, 0.97))
            fig.savefig(saida / "por_mes" / f"{prefixo}.png", dpi=110)
            pdf.savefig(fig)
            plt.close(fig)

            # Um gráfico individual por subsistema
            for sub in subsistemas:
                pasta = saida / "individuais" / sub.replace(" ", "_").replace(".", "")
                pasta.mkdir(parents=True, exist_ok=True)
                fig, ax = plt.subplots(figsize=(10, 4.5))
                desenhar_boxplot(ax, dados_mes, sub, unidade)
                ax.set_title(f"{sub} — {rotulo} ({nome_var})", loc="left",
                             fontweight="bold", fontsize=12)
                fig.tight_layout()
                fig.savefig(pasta / f"{prefixo}.png", dpi=110)
                plt.close(fig)

            print(f"Estágio {estagio:>2} -> {rotulo}: {len(dados_mes)} horas "
                  f"({dias} dias)")

    print(f"Gráficos salvos em: {saida}")


if __name__ == "__main__":
    main()
