import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.data_loader import load_data
from utils.filters import global_filters
from utils.layout import page_header
from streamlit_plotly_events import plotly_events

# ====================================
# FUNÇÕES PT-BR
# ====================================

def formatar_moeda(valor):
    return f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    return f"{valor:.1%}".replace(".", ",")

# ====================================
# DADOS
# ====================================

df, ultima_atualizacao = load_data()
df = global_filters(df)

page_header("Histórico Financeiro", ultima_atualizacao)

if df.empty:
    st.stop()


# ====================================
# TOGGLE RECEITAS DE INVESTIMENTO
# ====================================

col_titulo, col_toggle = st.columns([6,1])

with col_toggle:
    incluir_investimentos = st.toggle(
        "Com receitas de investimentos",
        value=False
    )

# aplica filtro
if not incluir_investimentos:
    df = df[
        ~(
            (df["Receita/Despesa"] == "Receita") &
            (df["Categoria"] == "Investimentos")
        )
    ]

if df.empty:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
    st.stop()

# ====================================
# GARANTIR ANOMES FINANCEIRO
# ====================================

df["AnoMes"] = pd.to_datetime(dict(year=df["Ano"], month=df["Mês"], day=1))

st.markdown("### Análise por Categoria")

# ====================================
# NOVO RADIO: RECEITA OU DESPESA
# ====================================

tipo = st.radio(
    "Tipo:",
    ["Despesas", "Receitas"],
    horizontal=True
)

df_tipo = df[df["Receita/Despesa"] == tipo[:-1] if tipo.endswith("s") else tipo]

# ====================================
# FILTRO DE CATEGORIA
# ====================================

categorias = sorted(df_tipo["Categoria"].unique())
categorias = ["Selecionar tudo"] + categorias

categoria_selecionada = st.selectbox(
    "Selecione a Categoria",
    categorias
)

if categoria_selecionada == "Selecionar tudo":
    df_categoria = df_tipo.copy()
else:
    df_categoria = df_tipo[df_tipo["Categoria"] == categoria_selecionada]

# ====================================
# FILTRO SUBCATEGORIA (APENAS DESPESA)
# ====================================

subcategoria_selecionada = "Todas"

if tipo == "Despesas":

    subcats_raw = df_categoria["Subcategoria"].fillna("Sem subcategoria")
    subcats_raw = subcats_raw.replace("", "Sem subcategoria")

    subcategorias = sorted(subcats_raw.unique())
    subcategorias = ["Selecionar tudo"] + subcategorias

    subcategoria_selecionada = st.selectbox(
        "Selecione a Subcategoria",
        subcategorias
    )

    df_categoria = df_categoria.copy()
    df_categoria["Subcategoria"] = (
        df_categoria["Subcategoria"]
        .fillna("Sem subcategoria")
        .replace("", "Sem subcategoria")
    )

    if subcategoria_selecionada != "Selecionar tudo":
        df_categoria = df_categoria[
            df_categoria["Subcategoria"] == subcategoria_selecionada
        ]

# ====================================
# MODO VISUALIZAÇÃO (APENAS DESPESAS)
# ====================================

modo_visualizacao = "Valor Absoluto"

if tipo == "Despesas":

    modo_visualizacao = st.radio(
        "Visualizar por:",
        ["Valor Absoluto", "% da Renda Comprometida"],
        horizontal=True
    )

# ====================================
# AGREGAÇÃO
# ====================================

mensal_categoria = (
    df_categoria
    .groupby("AnoMes", as_index=False)["Valor"]
    .sum()
    .rename(columns={"Valor": "Valor_Categoria"})
)

mensal_receita = (
    df[df["Receita/Despesa"] == "Receita"]
    .groupby("AnoMes", as_index=False)["Valor"]
    .sum()
    .rename(columns={"Valor": "Receita_Mensal"})
)

mensal_despesa_total = (
    df[df["Receita/Despesa"] == "Despesa"]
    .groupby("AnoMes", as_index=False)["Valor"]
    .sum()
    .rename(columns={"Valor": "Despesa_Total"})
)

mensal = (
    mensal_categoria
    .merge(mensal_receita, on="AnoMes", how="left")
    .merge(mensal_despesa_total, on="AnoMes", how="left")
    .fillna(0)
)

mensal = mensal.fillna(0)

mensal["Perc_Mensal"] = mensal["Valor_Categoria"] / mensal["Receita_Mensal"]
mensal["Perc_Mensal"] = mensal["Perc_Mensal"].replace([float("inf"), -float("inf")], pd.NA)

mensal = mensal.reset_index().sort_values("AnoMes")

# ====================================
# KPIs
# ====================================

total_categoria = df_categoria["Valor"].sum()
media_mensal = mensal["Valor_Categoria"].mean()

if tipo == "Despesas":

    total_receita_periodo = df[df["Receita/Despesa"] == "Receita"]["Valor"].sum()

    percentual_renda = (
        total_categoria / total_receita_periodo
        if total_receita_periodo > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total no Período", f"R$ {formatar_moeda(total_categoria)}")
    col2.metric("% da renda comprometida no período", formatar_percentual(percentual_renda))
    col3.metric("Média Mensal", f"R$ {formatar_moeda(media_mensal)}")

else:

    col1, col2 = st.columns(2)

    col1.metric("Total no Período", f"R$ {formatar_moeda(total_categoria)}")
    col2.metric("Média Mensal", f"R$ {formatar_moeda(media_mensal)}")

# ====================================
# EIXO NUMÉRICO
# ====================================

mensal["Data_dt"] = mensal["AnoMes"]
mensal["Mes"] = mensal["Data_dt"].dt.strftime("%m %y")
mensal["pos"] = range(len(mensal))

# ====================================
# FIGURA
# ====================================

fig = go.Figure()

if modo_visualizacao == "Valor Absoluto":

    fig.add_trace(
        go.Bar(
            x=mensal["pos"],
            y=mensal["Valor_Categoria"],
            marker_color="#7C3AED",
            text=[f"<b>{formatar_moeda(v)}</b>" for v in mensal["Valor_Categoria"]],
            textposition="outside",
            textfont=dict(size=13, color="#4C1D95"),
            cliponaxis=False,
            hovertemplate="Mês: %{customdata}<br>Valor: %{y:,.1f}<extra></extra>",
            customdata=mensal["Mes"]
        )
    )

    media_valor = mensal["Valor_Categoria"].mean()

    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(mensal)-0.5,
        y0=media_valor,
        y1=media_valor,
        line=dict(color="rgba(180,180,180,0.8)", dash="dash", width=2),
        layer="below"
    )

    fig.add_annotation(
        x=len(mensal)-0.5,
        y=media_valor,
        xref="x",
        yref="y",
        text=f"Média: {formatar_moeda(media_valor)}",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=14, color="rgba(120,120,120,1)")
    )

else:

    fig.add_trace(
        go.Scatter(
            x=mensal["pos"],
            y=mensal["Perc_Mensal"],
            mode="lines+markers+text",
            line=dict(color="#F97316", width=3),
            marker=dict(size=7),
            text=[
                "<b>SR</b>" if pd.isna(p)
                else f"<b>{str(round(p*100,1)).replace('.', ',')}</b>"
                for p in mensal["Perc_Mensal"]
            ],
            textposition="top center",
            textfont=dict(color="#C2410C", size=13),
            hovertemplate="Mês: %{customdata}<br>% da renda: %{y:.1%}<extra></extra>",
            customdata=mensal["Mes"]
        )
    )

    media_percentual = mensal["Perc_Mensal"].mean()

    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(mensal)-0.5,
        y0=media_percentual,
        y1=media_percentual,
        line=dict(color="rgba(180,180,180,0.8)", dash="dot", width=2),
        layer="below"
    )

    fig.add_annotation(
        x=len(mensal)-0.5,
        y=media_percentual,
        xref="x",
        yref="y",
        text=f"Média: {str(round(media_percentual*100,1)).replace('.', ',')}",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=14, color="rgba(120,120,120,1)")
    )

# ====================================
# LAYOUT
# ====================================

fig.update_layout(
    uniformtext=dict(mode="show", minsize=13),
    xaxis=dict(
        tickmode="array",
        tickvals=mensal["pos"],
        ticktext=mensal["Mes"],
        showgrid=False,
        showline=False,
        zeroline=False
    ),
    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
    margin=dict(l=40, r=40, t=60, b=120),
    title=f"Evolução - {categoria_selecionada} | {subcategoria_selecionada}",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

# ====================================
# CLIQUE
# ====================================

selected_points = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=520
)

if selected_points:

    pos_clicado = selected_points[0]["x"]

    mes_clicado = mensal.loc[
        mensal["pos"] == pos_clicado, "AnoMes"
    ].values[0]

    df_mes = df_categoria[
        df_categoria["AnoMes"] == mes_clicado
    ].sort_values("Data")

    if not df_mes.empty:

        df_tabela = df_mes[["Data", "Descrição", "Valor"]].copy()
        df_tabela["Data"] = df_tabela["Data"].dt.strftime("%d/%m/%Y")
       

        maior_descricao = df_categoria["Descrição"].astype(str).str.len().max()
        largura_descricao = max(300, maior_descricao * 7)

        col_esq, col_centro, col_dir = st.columns([1,2,1])

        with col_centro:

            st.markdown(
                f"<h3 style='text-align:center; margin-bottom:15px;'>Transações — {pd.to_datetime(mes_clicado).strftime('%m/%Y')}</h3>",
                unsafe_allow_html=True
            )

            st.markdown("""
                <style>
                div[data-testid="stDataFrame"] table {
                    font-size: 15px;
                }
                </style>
            """, unsafe_allow_html=True)

            st.dataframe(
                df_tabela,
                use_container_width=False,
                column_config={
                    "Data": st.column_config.Column(width=100),
                    "Descrição": st.column_config.Column(width=largura_descricao),
                    "Valor": st.column_config.NumberColumn(
                       width=120,
                       format="R$ %.1f"
                    )
                },
                hide_index=True
            )