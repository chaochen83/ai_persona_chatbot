import streamlit as st

def gate_by_invite_code():
    # 1. Define valid invite codes
    VALID_CODES = {"mask", "firefly"}
    # 2. Session state: Check if user is authenticated
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    # 3. Invite code form
    if not st.session_state.authenticated:
        st.title("Enter Invite Code")
        code_input = st.text_input("Invite Code", type="password")
        if st.button("Submit"):
            if code_input in VALID_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid invite code. Try again.")
        st.stop()  # 🚫 Stop here if not authenticated
