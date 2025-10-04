import pandas as pd
import streamlit as st
import os

# --- SADECE VERİYİ YÜKLEME KISMI ---
# Excel dosyasını yüklerken Streamlit'in cache mekanizmasını kullanmak önemlidir.
@st.cache_data
def load_data():
    # Dosyanın aynı klasörde olduğunu varsayıyoruz
    file_path = 'analitik_veri.xlsx'
    if not os.path.exists(file_path):
        st.error(f"HATA: '{file_path}' dosyası bulunamadı. Lütfen dosya adını ve konumunu kontrol edin.")
        return None
    try:
        df = pd.read_excel(file_path)
        # Sütun adlarında boşluk varsa temizleyelim
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Veri yüklenirken bir hata oluştu: {e}")
        return None

# --- ANALİTİK ÖNERİ FONKSİYONU (ICH Mantığı) ---
def analitik_oner(matriks_girdi, amac_girdi, veritabani):
    
    # 1. LİTERATÜR VERİSİNİ KONTROL ET
    filtrelenmis_data = veritabani[
        (veritabani['Analiz Matriksi'].str.contains(matriks_girdi, case=False, na=False)) & 
        (veritabani['Analiz Amacı (ICH Eşdeğeri)'].str.contains(amac_girdi, case=False, na=False))
    ]
    
    toplam_calisma = len(filtrelenmis_data)
    
    # 2. LİTERATÜR YANITINI DEĞERLENDİR
    if toplam_calisma >= 2: 
        en_sik_enstruman = filtrelenmis_data['Kullanılan Enstrüman Kategorisi'].mode().iloc[0]
        kullanım_sayisi = filtrelenmis_data[filtrelenmis_data['Kullanılan Enstrüman Kategorisi'] == en_sik_enstruman].shape[0]
        yuzde = (kullanım_sayisi / toplam_calisma) * 100
        
        return (f"**{en_sik_enstruman}**", 
                f"Literatür Odaklı: {toplam_calisma} benzer çalışmaya göre {yuzde:.1f}% kullanım.",
                "Literatür kanıtı yeterlidir. Bu, endüstriyel bir eğilimi yansıtır.")

    # 3. ICH KURAL SETİNİ UYGULA (Yeni ve Genişletilmiş Mantık)
    else:
        
        matriks_l = matriks_girdi.lower()
        amac_l = amac_girdi.lower()
        
        # KURAL 1: Biyolojik Bütünlük (mAb, Aşı, Peptit)
        if "protein" in amac_l or "peptit" in amac_l or "aşı" in matriks_l or \
           "yük varyantı" in amac_l or "agregat" in amac_l or "bütünlük" in amac_l:
            onerilen_cihaz = "CEX-HPLC, SEC-HPLC veya Kılcal Elektroforez (CE)"
            gerekce = "ICH Q6B gereğince, biyolojik ürünlerin kritik kalite özelliklerinin (CQA), yapısal bütünlüğünün ve varyantlarının analiz edilmesi zorunludur."
        
        # KURAL 2: Biyolojik Matriks ve PK/TDM
        elif "plazma" in matriks_l or "serum" in matriks_l or "idrar" in matriks_l:
            onerilen_cihaz = "LC-MS/MS"
            gerekce = "ICH Q2 (Bioanalitik) gereğince biyolojik matriks karmaşıktır. Farmakokinetik/TDM için ultra yüksek hassasiyet zorunludur."
            
        # KURAL 3: İnorganik/Metal Tespiti
        elif "iyon" in amac_l or "metal" in amac_l or "kantitasyon" in amac_l:
            onerilen_cihaz = "İyon Seçici Elektrot (ISE) veya ICP-MS"
            gerekce = "Klinik veya kalıntı kontrolünde inorganik iyonların hassas ve spesifik ölçümü için bu dedektörler esastır."
            
        # KURAL 4: Safsızlık / Yapı Belirleme
        elif "safsızlık" in amac_l or "tanımlama" in amac_l or "metabolit" in amac_l or "izomer" in amac_l:
            onerilen_cihaz = "LC-MS veya GC-MS"
            gerekce = "ICH Q3A/B gereğince safsızlıkların/metabolitlerin kimyasal yapısının belirlenmesi ve izomer ayrımı için kütle spektrometrik dedektörler esastır."
        
        # KURAL 5: Fitokimyasal/Ekstrakt Analizi
        elif "ekstrakt" in matriks_l or "bitki" in matriks_l:
            onerilen_cihaz = "UPLC-MS veya HPLC-DAD"
            gerekce = "Doğal ürünlerde ve bitki matrikslerinde çok sayıda yapısal olarak benzer bileşiğin ayrılması ve kesin kimlik doğrulaması gerekir."
            
        # KURAL 6: Farmasötik Rutin Analiz
        elif "miktar tayini" in amac_l or "çözünme" in amac_l or "assay" in amac_l:
            onerilen_cihaz = "HPLC-UV / HPLC-DAD"
            gerekce = "ICH Q6A gereğince, bitmiş üründe Assay ve Çözünme testleri için yüksek doğruluk ve tekrarlanabilirlik yeterlidir. HPLC-UV/DAD maliyet-etkin ve rutin kullanıma uygundur."
            
        else:
            onerilen_cihaz = "Analiz amacınızı veya matriksinizi netleştirin."
            kaynak_bilgisi = f"ICH Kural Seti Odaklı: Literatürde sadece {toplam_calisma} çalışma bulundu (Veri Yetersizliği)."
            gerekce = "Sistemin içindeki spesifik bir ICH kuralı uygulanamadı."
            
            return (f"**{onerilen_cihaz}**", 
                    kaynak_bilgisi,
                    gerekce)

        return (f"**{onerilen_cihaz}**", 
                f"ICH Kural Seti Odaklı: Literatürde sadece {toplam_calisma} çalışma bulundu (Veri Yetersizliği).",
                gerekce)


# --- ARABİRİM TASARIMI ---
def main():
    st.set_page_config(page_title="Akıllı Analitik Referans Sistemi", layout="wide")
    
    st.title("🧪 Akıllı Analitik Referans Sistemi")
    st.markdown("---")
    
    # 1. Veri Yükleme Kontrolü
    df = load_data()
    if df is None:
        return

    st.sidebar.header("Sorgulama Parametreleri")

    # Kullanıcıdan Girdi Alma
    matriks_girdi = st.sidebar.text_input("Analiz Matriksi (Örn: Plazma, Tablet, Kök Ekstraktı)", "Plazma")
    amac_girdi = st.sidebar.text_input("Analiz Amacı (Örn: Farmakokinetik, Miktar Tayini, Yük Varyantı)", "Farmakokinetik")
    
    # Buton
    if st.sidebar.button("Analitik Öneri Oluştur"):
        
        # 2. Analiz ve Sonuçları Alma
        onerilen_cihaz, kaynak_bilgisi, gerekce = analitik_oner(matriks_girdi, amac_girdi, df)
        
        st.subheader("💡 Analitik Öneri")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(label="EN ÇOK ÖNERİLEN ENSTRÜMAN", value=onerilen_cihaz.replace('**', ''))
        
        with col2:
            st.info(f"**Kaynak Türü:** {kaynak_bilgisi}")
            st.warning(f"**Gerekçe:** {gerekce}")

        st.markdown("---")
        st.caption(f"Veri Kümesi Boyutu: Toplam {len(df)} kayıt üzerinde analiz yapılmıştır.")
        st.dataframe(df.head(5))


if __name__ == "__main__":
    main()