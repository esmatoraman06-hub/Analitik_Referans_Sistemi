import streamlit as st

st.set_page_config(page_title="Akıllı Analitik Referans Sistemi", layout="wide")

st.title("Akıllı Analitik Referans Sistemi")
st.markdown("### Uygulama Modüllerini Seçin:")

st.info("""
Sol taraftaki menüden iki ana analitik modülden birini seçin:

1. **Veritabanı Analizi:** Mevcut literatür verilerine dayalı enstrüman önerisi.
2. **Fizikokimyasal Analiz:** Molekül özelliklerine (MW, Çözünürlük, Uçuculuk) dayalı teorik öneri.
""")