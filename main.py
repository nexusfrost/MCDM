import streamlit as st

st.markdown("<h1 style='text-align: center;'>Multi Creteria Desicion Making</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; '>Choosing the best supplier for Rumah Atsiri</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/vikorGPT.py", label="vikor", icon="📊")

with col2:
    st.page_link("pages/promethee.py", label="Promethee", icon="📈")
