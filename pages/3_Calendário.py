import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar

from utils.data_loader import load_data
from utils.layout import page_header
from utils.filters import global_filters


def check_password():

    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:

        st.text_input(
            "Senha", type="password", on_change=password_entered, key="password"
        )
        return False

    elif not st.session_state["password_correct"]:

        st.text_input(
            "Senha", type="password", on_change=password_entered, key="password"
        )
        st.error("Senha incorreta")
        return False

    else:
        return True


if not check_password():
    st.stop()

# ====================================
# FUNÇÕES PT-BR
# ====================================

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


meses_pt = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

# ====================================
# DADOS
# ====================================

df, ultima_atualizacao = load_data()

df = global_filters(df, default_ultimo_mes=True)

page_header("Calendário de Transações", ultima_atualizacao)

if df.empty:
    st.stop()

df["Data"] = pd.to_datetime(df["Data"])

# data real da transação (para posicionamento no calendário)
df["Ano_transacao"] = df["Data"].dt.year
df["Mes_transacao"] = df["Data"].dt.month
df["Dia"] = df["Data"].dt.day

# ====================================
# FILTROS
# ====================================

st.markdown("### Filtros")

# Receita / Despesa
tipo = st.selectbox(
    "Receita/Despesa",
    ["Todos"] + sorted(df["Receita/Despesa"].unique())
)

# ====================================
# FILTROS DESPESA
# ====================================

credito_debito = "Selecionar tudo"
bancos_sel = []

if tipo == "Despesa":

    col1, col2 = st.columns(2)

    with col1:
        credito_debito = st.radio(
            "Crédito ou débito?",
            ["Selecionar tudo", "Cartão de Crédito", "Débito/Pix"]
        )

    with col2:
        bancos = sorted(df["Banco"].dropna().unique())

        bancos_sel = st.multiselect(
            "Banco",
            bancos,
            default=bancos
        )

# ====================================
# CATEGORIA / SUBCATEGORIA
# ====================================

col3, col4 = st.columns(2)

categorias = ["Todas"] + sorted(df["Categoria"].dropna().unique())

with col3:
    categorias_sel = st.multiselect(
        "Categoria",
        categorias,
        default=["Todas"]
    )

if "Todas" in categorias_sel:
    categorias_filtrar = df["Categoria"].unique()
else:
    categorias_filtrar = categorias_sel

subcats_disponiveis = (
    df[df["Categoria"].isin(categorias_filtrar)]["Subcategoria"]
    .dropna()
    .unique()
)

subcategorias = ["Todas"] + sorted(subcats_disponiveis)

with col4:
    subcategorias_sel = st.multiselect(
        "Subcategoria",
        subcategorias,
        default=["Todas"]
    )

if "Todas" in subcategorias_sel:
    subcats_filtrar = subcats_disponiveis
else:
    subcats_filtrar = subcategorias_sel

# ====================================
# APLICAR FILTROS
# ====================================

df_filtrado = df.copy()

if tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Receita/Despesa"] == tipo]

if tipo == "Despesa":

    if credito_debito == "Cartão de Crédito":
        df_filtrado = df_filtrado[df_filtrado["Cartão de Crédito?"] == "Sim"]

    elif credito_debito == "Débito/Pix":
        df_filtrado = df_filtrado[df_filtrado["Cartão de Crédito?"] == "Não"]

    if bancos_sel:
        df_filtrado = df_filtrado[df_filtrado["Banco"].isin(bancos_sel)]

df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(categorias_filtrar)]

df_filtrado = df_filtrado[
    (df_filtrado["Subcategoria"].isin(subcats_filtrar)) |
    (df_filtrado["Subcategoria"].isna())
]

soma_transacoes = df_filtrado["Valor"].sum()

# ====================================
# TÍTULO DINÂMICO
# ====================================

# ====================================
# TÍTULO DINÂMICO
# ====================================

anos_sel = sorted(df_filtrado["Ano"].unique())
meses_sel = sorted(df_filtrado["Mês"].unique())

if len(meses_sel) == 0:
    st.warning("Nenhuma transação a ser mostrada")
    st.stop()

ano_inicio = min(anos_sel)
ano_fim = max(anos_sel)

mes_inicio = min(meses_sel)
mes_fim = max(meses_sel)

# 1 mês
if len(meses_sel) == 1 and len(anos_sel) == 1:
    titulo = f"Transações pagas em {meses_pt[mes_inicio]} de {ano_inicio}"

# exatamente 2 meses
elif len(meses_sel) == 2 and len(anos_sel) >= 1:
    if ano_inicio == ano_fim:
        titulo = f"Transações pagas em {meses_pt[mes_inicio]} e {meses_pt[mes_fim]} de {ano_inicio}"
    else:
        titulo = f"Transações pagas em {meses_pt[mes_inicio]} de {ano_inicio} e {meses_pt[mes_fim]} de {ano_fim}"

# vários meses no mesmo ano
elif ano_inicio == ano_fim:
    titulo = f"Transações pagas entre {meses_pt[mes_inicio]} e {meses_pt[mes_fim]} de {ano_inicio}"

# vários anos
else:
    titulo = f"Transações pagas entre {meses_pt[mes_inicio]} de {ano_inicio} e {meses_pt[mes_fim]} de {ano_fim}"

# KPI + título
col_titulo, col_kpi = st.columns([6,2])

with col_titulo:
    st.markdown(f"### {titulo}")

if tipo != "Todos":
    with col_kpi:
        st.metric(
            "💰 Soma das transações",
            formatar_moeda(soma_transacoes)
        )

# ====================================
# MAPA DE CORES
# ====================================

categorias_unicas = sorted(df["Categoria"].dropna().unique())

palette = [
"#1D4ED8","#15803D","#9333EA","#F97316","#0EA5E9","#DC2626",
"#A21CAF","#14B8A6","#F59E0B","#4F46E5","#059669","#B91C1C",
"#7C3AED","#0369A1","#65A30D","#BE123C","#0F766E","#92400E",
"#4338CA","#047857","#9D174D","#0C4A6E","#713F12","#701A75"
]

mapa_cores = {
cat: palette[i]
for i, cat in enumerate(categorias_unicas)
}

# ====================================
# MESES A DESENHAR
# ====================================

meses_transacao = (
    df_filtrado[["Ano_transacao", "Mes_transacao"]]
    .drop_duplicates()
    .sort_values(["Ano_transacao", "Mes_transacao"])
)

# data atual para destaque
hoje = pd.Timestamp.today()

# ====================================
# GERAR CALENDÁRIOS
# ====================================

for _, linha_mes in meses_transacao.iterrows():

    ano = int(linha_mes["Ano_transacao"])
    mes = int(linha_mes["Mes_transacao"])

    df_mes = df_filtrado[
        (df_filtrado["Ano_transacao"] == ano) &
        (df_filtrado["Mes_transacao"] == mes)
    ]

    st.markdown(f"## {meses_pt[mes]} {ano}")

    cal = calendar.Calendar(firstweekday=6)
    dias_mes = cal.monthdayscalendar(ano, mes)

    max_transacoes = 0
    for dia in range(1, 32):
        qtd = len(df_mes[df_mes["Dia"] == dia])
        if qtd > max_transacoes:
            max_transacoes = qtd

    altura_transacao = 0.28
    altura_base = 0.35
    altura_celula = altura_base + (max_transacoes * altura_transacao)

    fig = go.Figure()

    for linha, semana in enumerate(dias_mes):
        for coluna, dia in enumerate(semana):

            if dia == 0:
                continue

            transacoes = df_mes[df_mes["Dia"] == dia]

            y_base = -linha * altura_celula

            # destaque do dia atual
            if ano == hoje.year and mes == hoje.month and dia == hoje.day:
                cor_fundo = "#E5E7EB"
            else:
                cor_fundo = "rgba(0,0,0,0)"

            fig.add_shape(
                type="rect",
                x0=coluna,
                x1=coluna + 1,
                y0=y_base,
                y1=y_base - altura_celula,
                line=dict(color="#9CA3AF", width=1.5),
                fillcolor=cor_fundo,
                layer="below"
            )

            fig.add_annotation(
                x=coluna + 0.02,
                y=y_base - 0.02,
                text=f"<b>{dia}</b>",
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font=dict(color="#374151", size=16)
            )

            offset = 0.25

            for _, row in transacoes.iterrows():

                y0 = y_base - offset
                y1 = y_base - offset - 0.22
                y_centro = (y0 + y1) / 2

                fig.add_shape(
                    type="rect",
                    x0=coluna + 0.05,
                    x1=coluna + 0.95,
                    y0=y0,
                    y1=y1,
                    fillcolor=mapa_cores.get(row["Categoria"], "#999999"),
                    line=dict(width=0),
                    layer="below"
                )

                fig.add_trace(
                    go.Scatter(
                        x=[coluna + 0.5],
                        y=[y_centro],
                        mode="text",
                        text=[row["Descrição"][:18]],
                        textposition="middle center",
                        textfont=dict(color="white", size=20),
                        hovertemplate=(
                            f"{row['Descrição']}<br>"
                            f"{formatar_moeda(row['Valor'])}<br>"
                            f"{row['Banco']}"
                            "<extra></extra>"
                        ),
                        showlegend=False
                    )
                )

                offset += altura_transacao

    fig.update_layout(
        height=altura_celula * len(dias_mes) * 120,
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(7)),
            ticktext=["dom.", "seg.", "ter.", "qua.", "qui.", "sex.", "sáb."],
            showgrid=False
        ),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        hoverlabel=dict(font_size=20)
    )

    st.plotly_chart(fig, use_container_width=True)