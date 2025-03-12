from streamlit_authenticator import Hasher
print(Hasher(['password@12345']).generate())