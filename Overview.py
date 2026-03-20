import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.data_loader import load_data
from utils.filters import global_filters
from utils.layout import page_header
from streamlit_plotly_events import plotly_events


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
# CONFIGURAÇÃO DA PÁGINA
# ====================================

st.set_page_config(
    page_title="Controle Financeiro",
    layout="wide"
)

# ----------------------------------
# FUNÇÃO FORMATAÇÃO PT-BR
# ----------------------------------

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_numero(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ----------------------------------
# CARREGAR DADOS
# ----------------------------------

df, ultima_atualizacao = load_data()
df = global_filters(df)

# === SESSION STATE ===
if "mes_selecionado" not in st.session_state:
    st.session_state["mes_selecionado"] = None

page_header("Overview Financeiro", ultima_atualizacao)

# ====================================
# TOGGLE RECEITAS DE INVESTIMENTO
# ====================================

col_toggle_left, col_toggle_right = st.columns([6,1])

with col_toggle_right:
    incluir_investimentos = st.toggle(
        "com receitas de investimentos",
        value=False
    )

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

# ==============================
# AGREGAÇÃO MENSAL (ANTES DO FILTRO)
# ==============================

df["AnoMes_dt"] = pd.to_datetime(dict(year=df["Ano"], month=df["Mês"], day=1))

monthly = (
    df.groupby(["AnoMes_dt", "Receita/Despesa"])["Valor"]
    .sum()
    .unstack()
    .fillna(0)
    .sort_index()
)

monthly["Saldo"] = monthly.get("Receita", 0) - monthly.get("Despesa", 0)

receita_segura = monthly.get("Receita", 0).replace(0, pd.NA)
monthly["Perc_Economizado"] = monthly["Saldo"] / receita_segura

# ==============================================
# SELETOR
# ==============================================

metrica = st.radio(
    "Selecione a métrica:",
    ["Saldo", "% Economizada"],
    horizontal=True
)

# ==============================================
# GRÁFICO (HISTÓRICO)
# ==============================================

fig = go.Figure()

if metrica == "Saldo":

    media = monthly["Saldo"].mean()

    cores = ["#B91C1C" if v < 0 else "#1D4ED8" for v in monthly["Saldo"]]

    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly["Saldo"],
            mode="lines+markers+text",
            line=dict(color="#1D4ED8", width=3),
            marker=dict(size=7, color=cores),
            text=[f"<b>{v:,.1f}</b>".replace(",", "X").replace(".", ",").replace("X", ".") for v in monthly["Saldo"]],
            textposition="top center",
            textfont=dict(
                size=18,
                color=["#B91C1C" if v < 0 else "#1E3A8A" for v in monthly["Saldo"]]
            ),
            fill="tozeroy",
            fillcolor="rgba(29,78,216,0.06)"
        )
    )

    fig.add_hline(
        y=media,
        line_dash="dash",
        line_color="#D1D5DB",
        layer="below",
        annotation_text=f"Média: {formatar_numero(media)}",
        annotation_position="top right",
        annotation_font_size=16
    )

else:

    media = monthly["Perc_Economizado"].mean(skipna=True)

    cores = [
    "#B91C1C" if (pd.notna(v) and v < 0) else "#15803D"
    for v in monthly["Perc_Economizado"]
    ]

    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly["Perc_Economizado"],
            mode="lines+markers+text",
            line=dict(color="#15803D", width=3),
            marker=dict(size=7, color=cores),
            text=[f"<b>{v*100:.1f}</b>" if pd.notna(v) else "" for v in monthly["Perc_Economizado"]],
            textposition="top center",
            textfont=dict(size=20, color=cores)
        )
    )

    fig.add_hline(
        y=media,
        line_dash="dash",
        line_color="#D1D5DB",
        layer="below",
        annotation_text=f"Média: {media:.1%}",
        annotation_position="top right",
        annotation_font_size=16
    )

fig.update_layout(
    title=f"{metrica} Mensal",
    hoverlabel=dict(font_size=18),
    xaxis=dict(
        tickformat="%m %y",
        tickmode="array",
        tickvals=monthly.index,
        tickfont=dict(size=16),
        showgrid=False,
        title=None,
        range=[
            monthly.index.min() - pd.Timedelta(days=25),
            monthly.index.max() + pd.Timedelta(days=25)
        ]
    ),
    yaxis=dict(showgrid=False, showticklabels=False, title=None),
    showlegend=False,
    margin=dict(l=40, r=40, t=60, b=40)
)

# === CLIQUE ===
event = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    key="overview"
)

if event:
    x_clicado = pd.to_datetime(event[0]["x"])
    st.session_state["mes_selecionado"] = x_clicado

# ==============================================
# FILTRO POR MÊS (SÓ PARA KPIs E GRÁFICOS)
# ==============================================

df_filtrado = df.copy()

if st.session_state["mes_selecionado"] is not None:
    df_filtrado = df_filtrado[
        df_filtrado["AnoMes_dt"] == st.session_state["mes_selecionado"]
    ]

# ==============================
# KPIs
# ==============================

receita_total = df_filtrado[df_filtrado["Receita/Despesa"] == "Receita"]["Valor"].sum()
despesa_total = df_filtrado[df_filtrado["Receita/Despesa"] == "Despesa"]["Valor"].sum()
saldo_total = receita_total - despesa_total

perc_comprometido = despesa_total / receita_total if receita_total > 0 else 0

if perc_comprometido > 1:
    cor_comprometido = "#B91C1C"
elif perc_comprometido >= 0.5:
    cor_comprometido = "#CA8A04"
else:
    cor_comprometido = "#15803D"

cor_saldo = "#15803D" if saldo_total >= 0 else "#B91C1C"

col1, col2, col3, col4 = st.columns([1, 1, 1.3, 1])

col1.metric("Receita", formatar_moeda(receita_total))
col2.metric("Despesa", formatar_moeda(despesa_total))

with col3:
    st.markdown(
        f"""
        <div style="text-align:center">
            <div style="font-size:16px;color:#6B7280">Saldo</div>
            <div style="font-size:34px;font-weight:700;color:{cor_saldo}">
                {formatar_moeda(saldo_total)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div style="text-align:center">
            <div style="font-size:16px;color:#6B7280">% da renda comprometida</div>
            <div style="font-size:34px;font-weight:700;color:{cor_comprometido}">
                {perc_comprometido:.2%}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================
# SEÇÃO: COMPOSIÇÃO
# ==============================================

st.markdown("---")
st.subheader("Composição das Despesas e Fluxo Mensal")

col_left, col_right = st.columns(2)

with col_left:
    despesas = df_filtrado[df_filtrado["Receita/Despesa"] == "Despesa"]

    despesas_categoria = (
        despesas.groupby("Categoria")["Valor"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig_donut = go.Figure(
        data=[
            go.Pie(
                labels=despesas_categoria["Categoria"],
                values=despesas_categoria["Valor"],
                hole=0.65
            )
        ]
    )

    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:

    receita_total = df_filtrado[df_filtrado["Receita/Despesa"] == "Receita"]["Valor"].sum()
    despesa_total = df_filtrado[df_filtrado["Receita/Despesa"] == "Despesa"]["Valor"].sum()

    fig_bar = go.Figure()

    fig_bar.add_trace(go.Bar(y=["Receita"], x=[receita_total], orientation="h"))
    fig_bar.add_trace(go.Bar(y=["Despesa"], x=[despesa_total], orientation="h"))

    st.plotly_chart(fig_bar, use_container_width=True)