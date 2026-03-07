import streamlit as st

def page_header(nome_pagina, ultima_atualizacao):

    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown("# Controle Financeiro — Lucas Pereira")
        st.markdown(f"## {nome_pagina}")

    with col2:
        st.markdown(
            f"""
            <div style='text-align:right;'>
                <div style='font-size:13px; color:#6B7280;'>
                    Última atualização
                </div>
                <div style='font-size:16px; font-weight:600; color:#111827;'>
                    {ultima_atualizacao}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )