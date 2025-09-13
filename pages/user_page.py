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
        
    user_list = user_management.list_users()

    print("################################")
    print(f"user_list: {user_list}")
    print("################################")

    selection = st.dataframe(
            data=user_list,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            )

    print("################################")
    print(f"seelction: {selection}")
    print("################################")

    if selection:
        selected_user = user_list[selection["selection"]["rows"][0]]
 
    print(selected_user)

    with st.form(key="editForm"):

        username = st.text_input(label="Benutzer:", value=selected_user)
        cpassword = st.text_input(label="Passwort:")
        rolle = st.selectbox(label="Rolle:", options=["user", "admin"])

        if st.form_submit_button(label="Update"):
            st.session_state.action = "update"
        if st.form_submit_button(label="delete"):
            st.session_state.action = "delete"
        if st.form_submit_button(label="add"):
            st.session_state.action = "add"

# if __name__ == "__main__":
main()

