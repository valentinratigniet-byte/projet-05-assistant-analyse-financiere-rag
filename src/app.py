"""
Interface Streamlit de l'assistant d'analyse financière RAG.

Lancer : streamlit run src/app.py
La récupération marche sans clé ; la génération nécessite ANTHROPIC_API_KEY.
"""
import os

import streamlit as st

from rag import CHUNKS_JSON, answer, build_index

PETROL, AMBRE = "#137A8B", "#E4A93C"

st.set_page_config(page_title="Assistant d'analyse financière RAG", page_icon="📊")
st.markdown(f"<h1 style='color:{PETROL}'>📊 Assistant d'analyse financière</h1>",
            unsafe_allow_html=True)
st.caption("Pose une question sur les rapports annuels ACME (2023-2024). "
           "Chaque réponse est **sourcée** et l'assistant refuse d'inventer.")

if not CHUNKS_JSON.exists():
    with st.spinner("Construction de l'index vectoriel…"):
        build_index()

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.warning("`ANTHROPIC_API_KEY` non définie : récupération des sources active, "
               "génération de la réponse désactivée.", icon="🔑")

q = st.text_input("Ta question", placeholder="Quel est le résultat net 2024 ?")
examples = ["Quel est le chiffre d'affaires 2024 ?",
            "Compare la marge nette 2023 et 2024.",
            "Quel est le cours de bourse de l'action ?"]
cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    if col.button(ex, use_container_width=True):
        q = ex

if q:
    with st.spinner("Recherche…"):
        res = answer(q)
    st.markdown(f"<div style='border-left:4px solid {AMBRE};padding:.5rem 1rem'>"
                f"{res['answer']}</div>", unsafe_allow_html=True)
    st.subheader("Sources récupérées")
    for i, p in enumerate(res["passages"], 1):
        with st.expander(f"[{i}] {p['doc']} · p.{p['page']} · score {p['score']}"):
            st.write(p["text"])
