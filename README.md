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

- `por_mes/2030-MM_<Mês>.png` – um painel por mês com todos os 14 subsistemas.
- `individuais/<SUBSISTEMA>/2030-MM_<Mês>.png` – um gráfico por subsistema e mês.
- `boxplots_vergnd_2030.pdf` – os 12 painéis mensais em um único PDF.
