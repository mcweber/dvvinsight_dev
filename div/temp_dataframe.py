import chatdvv_module as chatdvv
import pandas as pd
import streamlit as st

@st.experimental_dialog("Show document")
def show_document(doc_id) -> None:
    document = chatdvv.get_document(doc_id)
    if document:
        st.write("gefunden")


results, results_count = chatdvv.text_search(search_text="blg", limit=50)

df = pd.DataFrame(results)
# st.dataframe(df)

# st.dataframe(output)
col1, col2, col3, col4 = st.columns([1, 1, 4, 1])
for index in range(0, len(df) if len(df) < 10 else 10):
    col1.write(df.iloc[index, 1])
    col2.write(df.iloc[index, 2])
    col3.write(df.iloc[index, 5])
    col4.button("DOC", key=index, on_click=show_document(), ARGS=df.iloc[index, 0])