import streamlit as st
import datetime

import modules.ask_llm as ask_llm
import modules.ask_mongo as ask_mongo

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
    
if "feld_liste" not in st.session_state:
    st.session_state.feld_liste: list = list(ask_mongo.group_by_field().keys())

st.title("DVV Insight - Newsletter")

llm = init_llm(llm=LLM, local=False)

with st.form(key="ausgabe"):
    col = st.columns(3)
    with col[0]: quelle = st.selectbox(label="Publikation", options=st.session_state.feld_liste)
    with col[1]: jahrgang = st.number_input(label="Jahrgang", format="%d", value=datetime.datetime.now().year)
    with col[2]: ausgabe = st.number_input(label="Ausgabe", format="%d", min_value=0, value=0)
    # question = st.text_input("Suchbegriff", key="question")
    if st.form_submit_button("Ausführen"):
        st.session_state.search_status = True

if st.session_state.search_status:
    results = ask_mongo.collect_ausgaben(quelle=quelle, jahrgang=jahrgang, ausgabe=ausgabe)

    if results:
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
            st.warning(ausgabe_text_en)
    else:
        st.write("Keine Ergebnisse gefunden.")

    st.session_state.search_status = False