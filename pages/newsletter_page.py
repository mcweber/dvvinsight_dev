import streamlit as st
import datetime

import modules.ask_llm as ask_llm
import modules.ask_mongo as ask_mongo

PUB_LOG = ("THB", "DVZ", "DVZT", "THBT", "DVZMG", "DVZM", "DVZ-Brief")
PUB_MAR = ("THB", "THBT", "SHF", "SHIOF", "SPI", "NSH")
PUB_RAIL = ("EI", "SD", "BM", "BAMA")
PUB_OEPNV = ("RABUS", "NAHV", "NANA", "DNV")
PUB_PI = ("pi_AuD", "pi_PuA", "pi_EuE", "pi_E20", "pi_Industry_Forward", "pi_Industrial_Solutions", "pi_Next_Technology", "pi_")
MARKTBEREICHE = {"Alle": (), "Logistik": PUB_LOG, "Maritim": PUB_MAR, "Rail": PUB_RAIL, "ÖPNV": PUB_OEPNV, "Industrie": PUB_PI}
MARKTBEREICHE_LISTE = list(MARKTBEREICHE.keys())
LLM = "gemini"

# ---------------------------------------------------
# Functions
# ---------------------------------------------------

@st.cache_resource
def init_llm(llm: str = "gemini", local: bool = False):
    return ask_llm.LLMHandler(llm=llm, local=local)


# ---------------------------------------------------
# Main
# ---------------------------------------------------

if "search_status" not in st.session_state:
    st.session_state.search_status = False

st.title("DVV Insight - Newsletter")

llm = init_llm(llm=LLM, local=False)

with st.form(key="ausgabe"):
    col = st.columns(3)
    with col[0]: quelle = st.text_input("Quelle")
    with col[1]: jahrgang = st.number_input(label="Jahrgang", format="%d", value=datetime.datetime.now().year)
    with col[2]: ausgabe = st.number_input(label="Ausgabe", format="%d", min_value=1)
    # question = st.text_input("Suchbegriff", key="question")
    if st.form_submit_button("Ausführen"):
        st.session_state.search_status = True

if st.session_state.search_status:
    results = ask_mongo.collect_ausgaben(quelle=quelle, jahrgang=jahrgang, ausgabe=ausgabe)

    ausgabe_text = f"{quelle} {jahrgang}/{ausgabe}" + "\n"

    with st.expander(label="Inhaltsverzeichnis"):
        for result in results:
            st.write(f"[{result["seite_start"]} - {result["seite_ende"]}] {result["titel"]}")
            # st.write(result["untertitel"])
            # with st.expander(label="Inhalt"):
            #      st.write(result["text"])
            ausgabe_text += result["titel"] + "\n"
            ausgabe_text += result["untertitel"] + "\n"
            ausgabe_text += result["text"] + "\n"
            ausgabe_text += "\n"

    with st.expander(label="Texte DE"):
        st.write(ausgabe_text)

    ausgabe_text_en = llm.ask_llm(
        question = "Translate the newsletter text to english. Structure each article as follows: ### Title, Summary.",  
        source_doc_str = ausgabe_text
        )
    
    with st.expander(label="Texte EN"):
        st.write(ausgabe_text_en)

    st.session_state.search_status = False