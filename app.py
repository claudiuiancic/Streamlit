import streamlit as st
import streamlit_authenticator as stauth
import os
import yaml
from yaml.loader import SafeLoader

# Load credentials from Streamlit secrets
config = {
    "credentials": {
        "usernames": {
            os.getenv("USER1_NAME"): {
                "email": os.getenv("USER1_EMAIL"),
                "name": os.getenv("USER1_DISPLAY"),
                "password": os.getenv("USER1_PASSWORD")  # Already hashed
            }
        }
    },
    "cookie": {
        "name": "streamlit_auth",
        "key": os.getenv("COOKIE_KEY"),
        "expiry_days": 30
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    st.sidebar.success(f"Welcome {name}!")
    st.title("My Secure Dashboard")
    st.write("This is a secure Streamlit dashboard.")
    authenticator.logout('Logout', 'sidebar')
elif authentication_status is False:
    st.error('Username or password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your credentials')