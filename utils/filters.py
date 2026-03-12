import streamlit as st

def global_filters(df, default_ultimo_mes=False):

    st.sidebar.markdown("## Filtros Globais")

    anos = sorted(df["Ano"].unique())
    meses = sorted(df["Mês"].unique())

    ultimo_ano = df["Ano"].max()
    ultimo_mes = df[df["Ano"] == ultimo_ano]["Mês"].max()

    # -------------------------
    # ANO
    # -------------------------

    if default_ultimo_mes:
        selecionar_todos_anos = st.sidebar.checkbox(
            "Selecionar todos os anos",
            value=False
        )
    else:
        selecionar_todos_anos = st.sidebar.checkbox(
            "Selecionar todos os anos",
            value=True
        )

    if selecionar_todos_anos:
        anos_selecionados = anos
    else:
        if default_ultimo_mes:
            anos_selecionados = st.sidebar.multiselect(
                "Ano",
                anos,
                default=[ultimo_ano]
            )
        else:
            anos_selecionados = st.sidebar.multiselect(
                "Ano",
                anos,
                default=[]
            )

    # -------------------------
    # MÊS
    # -------------------------

    if default_ultimo_mes:
        selecionar_todos_meses = st.sidebar.checkbox(
            "Selecionar todos os meses",
            value=False
        )
    else:
        selecionar_todos_meses = st.sidebar.checkbox(
            "Selecionar todos os meses",
            value=True
        )

    if selecionar_todos_meses:
        meses_selecionados = meses
    else:
        if default_ultimo_mes:
            meses_selecionados = st.sidebar.multiselect(
                "Mês",
                meses,
                default=[ultimo_mes]
            )
        else:
            meses_selecionados = st.sidebar.multiselect(
                "Mês",
                meses,
                default=[]
            )

    # -------------------------
    # APLICAR FILTROS
    # -------------------------

    df_filtrado = df[
        df["Ano"].isin(anos_selecionados) &
        df["Mês"].isin(meses_selecionados)
    ]

    return df_filtrado