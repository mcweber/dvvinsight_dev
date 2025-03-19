import streamlit as st
import datetime

import modules.ask_mongo as ask_mongo

# PUBS = {
#     "Alle": (),
#     "Logistik": ("THB", "DVZ", "DVZT", "THBT", "DVZMG", "DVZM", "DVZ-Brief"),
#     "Maritim": ("THB", "THBT", "SHF", "SHIOF", "SPI", "NSH"),
#     "Rail": ("EI", "SD", "BM", "BAMA"),
#     "OEPNV": ("RABUS", "NAHV", "NANA", "DNV"),
#     "Industrie": ("pi_AuD", "pi_PuA", "pi_EuE", "pi_E20", "pi_Industry_Forward", "pi_Industrial_Solutions", "pi_Next_Technology", "pi_")
# }
# MARKTBEREICHE = list(PUBS.keys())

if "feld_liste" not in st.session_state:
    st.session_state.feld_liste: list = list(ask_mongo.group_by_field().keys())

st.title("DVV Insight - Ausgaben")

with st.form(key="ausgabe"):
    col = st.columns(3)
    with col[0]: quelle = st.selectbox(label="Publikation", options=st.session_state.feld_liste)
    with col[1]: jahrgang = st.number_input(label="Jahrgang", format="%d", value=datetime.datetime.now().year)
    with col[2]: ausgabe = st.number_input(label="Ausgabe", format="%d", min_value=1)
    # question = st.text_input("Suchbegriff", key="question")
    if st.form_submit_button("Ausführen"):
        st.session_state.search_status = True

results = ask_mongo.collect_ausgaben(quelle=quelle, jahrgang=jahrgang, ausgabe=ausgabe)

for result in results:
    st.write(f"[{result["seite_start"]} - {result["seite_ende"]}] {result["titel"]}")

st.session_state.search_status = False