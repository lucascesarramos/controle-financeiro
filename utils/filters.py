import streamlit as st

def global_filters(df):

    st.sidebar.markdown("## Filtros Globais")

    anos = sorted(df["Ano"].unique())
    meses = sorted(df["Mês"].unique())

    # -------------------------
    # ANO
    # -------------------------

    selecionar_todos_anos = st.sidebar.checkbox(
        "Selecionar todos os anos",
        value=True
    )

    if selecionar_todos_anos:
        anos_selecionados = anos
    else:
        anos_selecionados = st.sidebar.multiselect(
            "Ano",
            anos,
            default=[]
        )

    # -------------------------
    # MÊS
    # -------------------------

    selecionar_todos_meses = st.sidebar.checkbox(
        "Selecionar todos os meses",
        value=True
    )

    if selecionar_todos_meses:
        meses_selecionados = meses
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