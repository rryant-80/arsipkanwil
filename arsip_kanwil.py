import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)

# Ambil string URL langsung dari secrets.toml
sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

# Masukkan URL ke parameter 'spreadsheet'
df = conn.read(spreadsheet=sheet_url, ttl="5m")

st.dataframe(df)
