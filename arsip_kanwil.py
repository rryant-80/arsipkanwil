import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Dashboard Monitoring Arsip")

# Menginisialisasi koneksi gsheets dari secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Baca data langsung tanpa menulis URL sama sekali
df = conn.read(ttl="5m")

st.dataframe(df)
