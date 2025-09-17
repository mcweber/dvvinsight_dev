import pandas as pd
import streamlit as st
import modules.user_management_sql as user_management


# ------------------------------------------
# Main
# ------------------------------------------

def main() -> None:
    st.title("DVV Insight - User-Management")

    if 'init' not in st.session_state:
        st.session_state.init = True
        st.session_state.action = "none"
        
    df = pd.DataFrame(user_management.list_users())
    df["status"] = False 

    edited_df = st.data_editor(
        data=df,
        hide_index=True,
        )
    
    df_selected = edited_df[edited_df["status"]]
#    st.write(df_selected)

    with st.form(key="editForm"):

        if len(df_selected) > 0:
            username_value = df_selected.iat[0,1]
            password_value = df_selected.iat[0,2]
            rolle_index = ["user","admin"].index(df_selected.iat[0,4])
        else:
            username_value = ""
            password_value = ""
            rolle_index = ["user","admin"].index("user")

        username = st.text_input(label="Benutzer:", value=username_value)
        password = st.text_input(label="Passwort:", value=password_value)
        rolle = st.selectbox(label="Rolle:", options=["user","admin"], index=rolle_index) 

        if st.form_submit_button(label="Update"):
            if user_management.update_user(username, password, rolle):
                st.success("User aktualisiert.")
                st.rerun()
            else:
                st.error("Fehler beim Aktualisieren!")

        if st.form_submit_button(label="delete"):
            if user_management.delete_user(username):
                st.success("User gelöscht.")
                st.rerun()
            else:
                st.error("User NICHT gelöscht.")

        if st.form_submit_button(label="add"):
            if user_management.add_user(username, password, rolle):
                st.success("User hinzugefügt.")
                st.rerun()
            else:
                st.error("Fehler beim Hinzufügen.")

# if __name__ == "__main__":
main()

