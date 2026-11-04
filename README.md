# Box-Plot-SDDP-com-Barras

Box plots horários, por mês e por subsistema, de arquivos de saída do SDDP
(ex.: `vergnd_cvarR_Stage-2-13.csv`).

- A coluna `Hora` é sequencial no mês (1..744); o script a converte em hora do
  dia (1..24), e cada box resume os valores daquela hora em todos os dias do mês.
- Os estágios vêm mapeados para o calendário: estágio 2 = janeiro/2030 … estágio 13 = dezembro/2030.

## Uso

```bash
pip install -r requirements.txt
python boxplot_sddp.py dados/vergnd_cvarR_Stage-2-13.csv graficos
```

## Saídas (`graficos/`)

- `por_mes/2030-MM_<Mês>.png` – um painel por mês com os subsistemas que têm valores (os totalmente zerados são omitidos).
- `individuais/<SUBSISTEMA>/2030-MM_<Mês>.png` – um gráfico por subsistema e mês.
- `boxplots_curtailment_2030.pdf` – os 12 painéis mensais em um único PDF.

## gerter_cvarR a partir dos cenários da vergnd_cvarR

```bash
python calc_gerter_cvarR.py
```

Para cada subsistema (colunas D a Q) e cada hora dos 12 meses:

1. Na `vergnd_Distribuicao` há 10 cenários; os 10% maiores são 1 cenário, o de maior vergnd
   (o máximo confere com a `vergnd_cvarR` em todas as horas).
2. Entram os cenários que atingem esse máximo. Nos empates entram todos, e quando os 10
   valem zero entram os 10.
3. `gerter_cvarR` = média da `gerter_Distribuicao` nesses cenários.

Saídas:

- `dados/gerter_cvarR_Stage-2-13.csv` – mesmo formato da `vergnd_cvarR`.
- `dados/cenarios_selecionados_Stage-2-13.csv` – cenários usados por subsistema e hora.
- `planilhas/calculo_gerter_cvarR_Stage-2-13.xlsx` – passo a passo com fórmulas: abas Leia-me
  (com exemplos), Resumo, gerter_cvarR, Cenarios_selecionados e uma aba por subsistema.
