import pandas as pd
import streamlit as st

# =========================================
# URLs DAS ABAS
# =========================================

DADOS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOc4RezkY8EO1i8RLAuvb0EMgyPuAOrSUZW4VFo5FSWuf8nCqh9eBOxqUzJ_nD5tH-SryQZNpBOk4Z/pub?gid=0&single=true&output=csv"

DATAHORA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQOc4RezkY8EO1i8RLAuvb0EMgyPuAOrSUZW4VFo5FSWuf8nCqh9eBOxqUzJ_nD5tH-SryQZNpBOk4Z/pub?gid=1847361200&single=true&output=csv"

# =========================================
# CARREGAMENTO
# =========================================

@st.cache_data(ttl=120)
def load_data():

    # ----- Carrega dados principais -----
    df = pd.read_csv(DADOS_URL)

    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)

    df["Valor"] = (
        df["Valor"]
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

    # ----- Carrega aba Data/Hora -----
    df_datahora = pd.read_csv(DATAHORA_URL, header=None)

    ultima_atualizacao = df_datahora.iloc[1, 0]

    return df, ultima_atualizacao