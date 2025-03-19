# ---------------------------------------------------
# Version: 19.03.2025
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

import streamlit as st

import modules.ask_llm as ask_llm
import modules.ask_web as ask_web
import modules.ask_mongo as ask_mongo
import modules.user_management as user_management

SEARCH_TYPES = ("rag", "vektor", "volltext", "web")
PUBS = {
    "Alle": (),
    "Logistik": ("THB", "DVZ", "DVZT", "THBT", "DVZMG", "DVZM", "DVZ-Brief"),
    "Maritim": ("THB", "THBT", "SHF", "SHIOF", "SPI", "NSH"),
    "Rail": ("EI", "SD", "BM", "BAMA"),
    "OEPNV": ("RABUS", "NAHV", "NANA", "DNV"),
    "Industrie": ("pi_AuD", "pi_PuA", "pi_EuE", "pi_E20", "pi_Industry_Forward", "pi_Industrial_Solutions", "pi_Next_Technology", "pi_")
}
MARKTBEREICHE = list(PUBS.keys())
VECTOR_SEARCH_SCORE = 0.8
TEXT_SEARCH_SCORE = 9.0
LLM = "gpt-4o"

# ---------------------------------------------------
# Functions
# ---------------------------------------------------

@st.cache_resource
def init_llm(llm: str = "gpt-4o", local: bool = False):
    return ask_llm.LLMHandler(llm=llm, local=local)

@st.cache_resource
def init_websearch():
    return ask_web.WebSearch()

@st.dialog("DokumentenAnsicht")
def document_view(result: list = "Kein Text übergeben.") -> None:
    st.title(result['titel'])
    st.write(f"[{round(result['score'], 3)}] {result['quelle_id']}, {result['nummer']}/{result['jahrgang']} vom {str(result['date'])[:10]}\n\n[Score: {result['score']}]")
    st.write(result['text'])
    st.session_state.search_status = True

@st.dialog("DokumentenInfo")
def document_info(result: list = "Kein Text übergeben.") -> None:
    st.header(result['titel'])
    st.write(f"{result['quelle_id']}, {result['nummer']}/{result['jahrgang']} vom {str(result['date'])[:10]}")
    st.subheader("Zusammenfassung:")
    st.write(ask_mongo.write_summary(text=result['text'], length=100))
    st.subheader("Takeaways:")
    st.write(ask_mongo.write_takeaways(text=result['text']))
    st.subheader("Schlagworte:")
    st.write(ask_mongo.create_keywords(text=result['text'], max_keywords=5))
    st.session_state.search_status = True

def print_results(results: list, max_items: int = 100) -> None:
    counter = 1
    for result in results:
        col = st.columns([0.8, 0.1, 0.1])
        with col[0]:
            st.write(f"[{round(result['score'], 3)}][{result['quelle_id']}, {result['nummer']}/{result['jahrgang']}] {result['titel']}")
        with col[1]:
            st.button(label="DOC", key=str(result['_id'])+"DOC", on_click=document_view, args=(result,))
        with col[2]:
            st.button(label="INFO", key=str(result['_id'])+"INFO", on_click=document_info, args=(result,))
        counter += 1
        if counter > max_items:
            break

def show_latest_articles(max_items: int = 10) -> None:
    st.write("Neueste Artikel")
    results, schlagworte = ask_mongo.text_search(
        search_text="*",
        sort="date",
        score=0.0,
        filter=st.session_state.search_filter,
        limit=max_items
        )
    print_results(results)

# ---------------------------------------------------
# Main
# ---------------------------------------------------

def main() -> None:
    st.title("DVV Insight - Chat")

    # Init LLM & Web-search----------------------------------
    llm = init_llm(llm=LLM, local=False)
    web_search = init_websearch()

    # Initialize Session State -----------------------------------------
    if 'init' not in st.session_state:
        st.session_state.init = True
        st.session_state.feld_liste: list = list(ask_mongo.group_by_field().keys())
        st.session_state.marktbereich: str = "Alle"
        st.session_state.marktbereich_index: int = 0
        st.session_state.rag_db_suche: bool = True
        st.session_state.rag_web_suche: bool = False
        st.session_state.rag_index: str = "fulltext" # fulltext, vektor
        st.session_state.reflect_stage: bool = False
        st.session_state.results: str = ""
        st.session_state.search_filter: list = st.session_state.feld_liste
        st.session_state.search_results_limit: int  = 10
        st.session_state.search_status: bool = False
        st.session_state.search_type: str = "rag"
        st.session_state.search_type_index: int  = SEARCH_TYPES.index(st.session_state.search_type)
        st.session_state.show_latest: bool = False
        st.session_state.system_prompt: str = ask_mongo.get_system_prompt()

    # Define Sidebar ---------------------------------------------------
    with st.sidebar:
        switch_search_results = st.number_input(label="Search Results", min_value=1, value=st.session_state.search_results_limit, step=10)
        if switch_search_results != st.session_state.search_results_limit:
            st.session_state.search_results_limit = switch_search_results
            # st.rerun()
        st.divider()
        st.subheader("Einstellungen RAG Modus")
        switch_rag_db_suche = st.checkbox("DB-Suche", value=st.session_state.rag_db_suche)
        if switch_rag_db_suche != st.session_state.rag_db_suche:
            st.session_state.rag_db_suche = switch_rag_db_suche
            st.rerun()
        switch_rag_web_suche = st.checkbox("WEB-Suche", value=st.session_state.rag_web_suche)
        if switch_rag_web_suche != st.session_state.rag_web_suche:
            st.session_state.rag_web_suche = switch_rag_web_suche
            st.rerun()
        switch_rag_index = st.radio(label="Switch RAG-index", options=("fulltext", "vektor"), index=0)
        if switch_rag_index != st.session_state.rag_index:
            st.session_state.rag_index = switch_rag_index
            st.rerun()
        st.divider()
        switch_system_prompt = st.text_area("System-Prompt", st.session_state.system_prompt, height=500)
        if switch_system_prompt != st.session_state.system_prompt:
            st.session_state.system_prompt = switch_system_prompt
            ask_mongo.update_system_prompt(switch_system_prompt)
            st.rerun()
        st.divider()
        switch_search_filter = st.multiselect(label="Choose Publications", options=st.session_state.feld_liste, default=st.session_state.search_filter)
        if switch_search_filter != st.session_state.search_filter:
            st.session_state.search_filter = switch_search_filter
            st.rerun()
        if st.button("Reset Filter"):
            st.session_state.search_filter = st.session_state.feld_liste
            st.session_state.marktbereich = "Alle"
            st.session_state.marktbereich_index = 0
            st.rerun()
        
    # Define Search Type & Search Filter ------------------------------------------------
    col = st.columns(2)

    with col[0]:
        switch_search_type = st.selectbox(label="Suchtyp", options=SEARCH_TYPES, index=st.session_state.search_type_index)
        if switch_search_type != st.session_state.search_type:
            st.session_state.search_type = switch_search_type
            st.session_state.search_type_index = SEARCH_TYPES.index(switch_search_type)
            st.rerun()

    with col[1]:
        switch = st.selectbox(label="Marktbereich", options=MARKTBEREICHE, index=st.session_state.marktbereich_index)
        if switch != st.session_state.marktbereich:
            st.session_state.search_filter = PUBS[switch]
            st.session_state.marktbereich = switch
            st.session_state.marktbereich_index = MARKTBEREICHE.index(switch)
            st.rerun()

    # Define Search Form ----------------------------------------------
    with st.form(key="searchForm"):
        question = st.text_area(f"{st.session_state.search_type} [{st.session_state.rag_index}]")
        col = st.columns([0.5, 0.2, 0.3])
        with col[0]:
            if st.form_submit_button("Ausführen") and question:
                st.session_state.search_status = True
        with col[1]:
            if st.session_state.search_type == "volltext" and st.form_submit_button("Neueste Artikel"):
                st.session_state.show_latest = True
                st.session_state.search_status = True
        with col[2]:
            if st.form_submit_button("Schlagworte anzeigen"):
                st.session_state.search_type = "keyword_rank"
                st.session_state.search_status = True

    # Define Search & Search Results -------------------------------------------
    if st.session_state.user_status and st.session_state.search_status:

        # Show Latest Articles ---------------------------------------------
        if st.session_state.search_type == "volltext" and st.session_state.show_latest:
            show_latest_articles(max_items=st.session_state.search_results_limit)
            st.session_state.show_latest = False
            st.session_state.search_status = False

        # Keywords Ranking-------------------------------------------------
        elif st.session_state.search_type == "keyword_rank":
            keywords_list = ask_mongo.list_keywords()
            # st.bar_chart(data=keywords_list, x="keyword", y="count", horizontal=True)
            for keyword in keywords_list[:50]:
                st.write(f"{keyword['count']} {keyword['keyword']}")
            st.session_state.search_status = False
        
        # Fulltext Search -------------------------------------------------
        elif st.session_state.search_type == "volltext":
            results, schlagworte = ask_mongo.text_search(
                search_text=question,
                gen_suchworte=False,
                score=TEXT_SEARCH_SCORE,
                filter=st.session_state.search_filter,
                limit=st.session_state.search_results_limit
                )
            st.write(f"Suchbegriffe: {schlagworte} (Text-Score: {TEXT_SEARCH_SCORE})")
            st.divider()
            print_results(results, st.session_state.search_results_limit)
        
        # Vector Search --------------------------------------------------
        elif st.session_state.search_type == "vektor":
            results, schlagworte = ask_mongo.vector_search(
                query_string=question,
                gen_suchworte=False,
                score=VECTOR_SEARCH_SCORE,
                filter=st.session_state.search_filter,
                limit=st.session_state.search_results_limit
                )
            st.write(f"Suchbegriffe: {schlagworte} (Vektor-Score: {VECTOR_SEARCH_SCORE})")
            st.divider()
            print_results(results, st.session_state.search_results_limit)
        
        # WEB Search -----------------------------------------------------
        elif st.session_state.search_type == "web":
            results = web_search.search(query=question, score=0.5, limit=10)
            if results:
                for result in results:
                    st.write(f"[{round(result['score'], 3)}] {result['title']} [{result['url']}] \n\n{result['content'][:1000]}")
                    st.write("-" * 50)
            else:
                st.write("WEB-Suche bringt keine Ergebnisse.")
        
        # RAG Search -----------------------------------------------------
        elif st.session_state.search_type == "rag":
            # DB Search -------------------------------------------------
            db_results_str = ""
            schlagworte = ""
            if st.session_state.rag_db_suche:
                if st.session_state.rag_index == "vektor":
                    results, schlagworte = ask_mongo.vector_search(
                    query_string=question,
                    gen_suchworte=True,
                    score=VECTOR_SEARCH_SCORE,
                    filter=st.session_state.search_filter,
                    limit=st.session_state.search_results_limit
                    )
                else:
                    results, schlagworte = ask_mongo.text_search(
                        search_text=question,
                        gen_suchworte=True,
                        score=TEXT_SEARCH_SCORE,
                        filter=st.session_state.search_filter,
                        limit=st.session_state.search_results_limit
                        )
                with st.expander("DVV-Archiv Suchergebnisse"):
                    st.write(f"Suchbegriffe: {schlagworte}")
                    st.divider()
                    for result in results:
                        col = st.columns([0.7, 0.1, 0.2])
                        with col[0]:
                            st.write(f"[{round(result['score'], 3)}][{result['quelle_id']}, {result['nummer']}/{result['jahrgang']}] {result['titel']}")
                        with col[1]:
                            st.button(label="DOC", key=str(result['_id'])+"DOC", on_click=document_view, args=(result,))
                        with col[2]:
                            st.button(label="INFO", key=str(result['_id'])+"INFO", on_click=document_info, args=(result,))
                        db_results_str += f"Datum: {str(result['date'])[:10]}\nTitel: {result['titel']}\nText: {result['text']}\n\n"
        
            # Web Search ------------------------------------------------
            web_results_str = ""
            if st.session_state.rag_web_suche:
                results = web_search.search(query=question, score=0.5, limit=10)
                with st.expander("WEB Suchergebnisse"):
                    for result in results:
                        st.write(f"[{round(result['score'], 3)}] {result['title']} [{result['url']}]")
                        web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\nText: {result['content']}\n\n"
        
            # LLM Search ------------------------------------------------
            summary = llm.ask_llm(
                temperature=0.2,
                question=question,
                history=[],
                system_prompt=st.session_state.system_prompt,
                db_results_str=db_results_str,
                web_results_str=web_results_str
                )
            st.write(summary)
            user_management.save_action(user_name=st.session_state.user_name, action_type="query", action=question)
        st.session_state.search_status = False

# if __name__ == "__main__":
main()
