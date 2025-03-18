import streamlit as st

import modules.ask_mongo as ask_mongo

# Define constants -----------------------------------------------------------
PUB_LOG = ("THB", "DVZ", "DVZT", "THBT", "DVZMG", "DVZM", "DVZ-Brief")
PUB_MAR = ("THB", "THBT", "SHF", "SHIOF", "SPI", "NSH")
PUB_RAIL = ("EI", "SD", "BM", "BAMA")
PUB_OEPNV = ("RABUS", "NAHV", "NANA", "DNV")
PUB_PI = ("pi_AuD", "pi_PuA", "pi_EuE", "pi_E20", "pi_Industry_Forward", "pi_Industrial_Solutions", "pi_Next_Technology", "pi_")
MARKTBEREICHE = {"Alle": (), "Logistik": PUB_LOG, "Maritim": PUB_MAR, "Rail": PUB_RAIL, "ÖPNV": PUB_OEPNV, "Industrie": PUB_PI}
MARKTBEREICHE_LISTE = list(MARKTBEREICHE.keys())
LLM = "gpt-4o"

# Query database -------------------------------------------------------------
num_documents = ask_mongo.collection.count_documents({})
num_abstracts = ask_mongo.collection.count_documents({'ki_abstract': {'$ne': ''}})
num_embeddings = ask_mongo.collection.count_documents({'embeddings': {'$ne': []}})
num_schlagworte = ask_mongo.collection.count_documents({'schlagworte': {'$ne': []}})

# Output statistics ----------------------------------------------------------
st.write(f"Anzahl Artikel: {num_documents:,}".replace(",", "."))
st.write(f"mit Abstracts: {num_abstracts:,}".replace(",", "."))
st.write(f"ohne Embeddings: {num_documents - num_embeddings:,}".replace(",", "."))
st.write(f"ohne Schlagworte: {num_documents - num_schlagworte:,}".replace(",", "."))

st.divider()

st.write("Anzahl Artikel pro Marktbereich:")
for item in [PUB_LOG, PUB_MAR, PUB_RAIL, PUB_OEPNV, PUB_PI]:
    st.write(f"{item}: {ask_mongo.collection.count_documents({'quelle_id': {'$in': item}}):,}".replace(",", "."))