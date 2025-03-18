import streamlit as st
import modules.user_management as user_management

if "role" not in st.session_state:
    st.session_state.role = ""
    st.session_state.user_name = ""
    st.session_state.user_status: bool = False

ROLES = [None, "user", "admin"]


# Define functions -----------------------------------------------------------
def login():
    with st.form(key="loginForm"):
        st.write(f"Status: {st.session_state.role}")
        user_name = st.text_input("Benutzer")
        user_pw = st.text_input("Passwort", type="password")
        if st.form_submit_button("Login"):
            if user_name and user_pw:
                user = user_management.check_user(user_name, user_pw)
                if user:
                    st.session_state.user_name = user["username"]
                    st.session_state.role = user["rolle"]
                    st.session_state.user_status = True
                    user_management.save_action(user_name=st.session_state.user_name, action_type="login")
            st.rerun()


def logout():
    st.session_state.role = None
    st.session_state.user_name = None
    st.session_state.userStatus = False
    st.rerun()

# Define pages --------------------------------------------------------------
page_logout = st.Page(logout, title="Log out")

page_settings = st.Page("pages/settings.py", title="Settings")

page_chat = st.Page(
    "pages/chat_page.py",
    title="Chat",
    # icon=":material/help:",
    default=False,
)

page_ausgaben = st.Page(
    "pages/ausgaben_page.py",
    title="Ausgaben",
    default=False,
)

page_newsletter = st.Page(
    "pages/newsletter_page.py",
    title="Newsletter",
    # icon=":material/healing:",
    default=False,
)

# Define Main ---------------------------------------------------------------
# st.title("Chat DVV")
# st.logo("images/horizontal_blue.png", icon_image="images/icon_blue.png")

page_dict = {}
if st.session_state.role in ["admin", "user"]:
    page_dict["Module"] = [page_chat, page_ausgaben, page_newsletter]
    page_dict["Admin"] = [page_settings, page_logout]

if len(page_dict) > 0:
    pg = st.navigation(page_dict)
else:
    pg = st.navigation([st.Page(login)])

pg.run()
