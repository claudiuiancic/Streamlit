import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import bcrypt

# --- Define User Credentials ---
usernames = ["admin"]
plain_passwords = ["password123"]  # Change this to a secure password
emails = ["admin@example.com"]

# --- Hash Passwords Manually Using bcrypt ---
hashed_passwords = [bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode() for p in plain_passwords]

# --- Create Authentication Config ---
config = {
    'credentials': {
        'usernames': {
            usernames[0]: {
                'email': emails[0],
                'name': "Admin",
                'password': hashed_passwords[0]  # Store hashed password
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'some_random_key',
        'name': 'auth_cookie'
    },
    'preauthorized': [emails[0]]
}

# Save config to a YAML file
with open('config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)

# --- Load Config for Authentication ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# --- Login Form ---
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    st.title(f"Welcome, {name}!")
    st.write("You have successfully logged in to your Streamlit dashboard.")

    # --- Dashboard Content ---
    st.metric("Example Metric", "123", "+10%")
    st.line_chart({"data": [1, 3, 2, 4, 7, 5, 9]})

    authenticator.logout("Logout", "sidebar")

elif authentication_status is False:
    st.error("Username or password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")