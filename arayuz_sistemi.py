import pandas as pd
import streamlit as st
import os

# --- SADECE VERİYİ YÜKLEME KISMI ---
@st.cache_data
def load_data():
    # Excel dosyasının aynı klasörde olduğunu varsayıyoruz
    file_path = 'analitik_veri.xlsx'
    if not os.path.exists(file_path):
        st.error(f"HATA: '{file_path}' dosyası bulunamadı. Lütfen dosya adını ve konumunu kontrol edin.")
        return None
    try:
        df = pd.read_excel(file_path)
        # Sütun adlarında boşluk varsa temizleyelim
        df.columns = df.columns.str.strip()
        # Veri setindeki NaN (boş) değerleri, açılır menüde sorun yaratmaması için "Belirtilmemiş" ile dolduralım
        df = df.fillna('Belirtilmemiş') 
        return df
    except Exception as e:
        # openpyxl yüklü değilse bu hata alınır.
        st.error(f"Veri yüklenirken bir hata oluştu: Missing optional dependency 'openpyxl'. Lütfen requirements.txt dosyasını kontrol edin.")
        return None


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

    # 1. Excel sütun adlarını al (kullanıcının sorgulayabileceği sütunlar)
    sorgulanabilir_sutunlar = [
        'Analiz Matriksi',
        'Analiz Amacı (ICH Eşdeğeri)',
        'Molekül Adı' , 
        'Molekül Türü' , 
        'Kullanılan Enstrüman Kategorisi'

    ]

    # Tüm sütunlardan seçilen değerleri tutmak için boş bir sözlük oluştur
    sorgu_degerleri = {}
    
    for sutun in sorgulanabilir_sutunlar:
        # Sütundaki benzersiz değerleri al ve başına "Filtreleme Yok" seçeneğini ekle
        secenekler = ['Filtreleme Yok'] + [str(x) for x in df[sutun].unique()]
        
        # Streamlit SelectBox oluştur
        secilen_deger = st.sidebar.selectbox(
            f"Sorgulama Parametresi: {sutun}", 
            options=sorted(secenekler) # Seçenekleri alfabetik sıralıyoruz
        )
        sorgu_degerleri[sutun] = secilen_deger
    
    # Buton
    if st.sidebar.button("Analitik Öneri Oluştur"):
        
        # Filtreleme koşullarını oluştur
        filtre_kosullari = []
        
        # Filtreleme koşullarını döngü ile oluştur
        for sutun, deger in sorgu_degerleri.items():
            if deger != 'Filtreleme Yok' and deger != 'Belirtilmemiş':
                # Pandas Query için filtre koşullarını hazırla
                filtre_kosullari.append(f"`{sutun}` == '{deger}'")

        # Filtreleme yap
        if filtre_kosullari:
            # Tüm koşulları '&' (AND) ile birleştirerek tek bir sorgu stringi oluştur.
            filtre_stringi = ' & '.join(filtre_kosullari)
            
            # Pandas Query ile veriyi filtrele
            try:
                # Engine='python' kullanıldı, çünkü bazen query metodu uzun satırlarda hata verebiliyor.
                filtrelenmis_data = df.query(filtre_stringi, engine='python')
            except Exception as e:
                st.error(f"Sorgu hatası: {e}")
                return
        else:
            # Filtreleme Yoksa, tüm veri setini kullan
            filtrelenmis_data = df

        
        # --- ANALİZ MANTIĞINI UYGULA ---
        
        toplam_calisma = len(filtrelenmis_data)

        # 1. HİÇ SONUÇ YOKSA
        if toplam_calisma == 0:
            st.warning("⚠️ Belirtilen parametrelere uyan hiçbir kayıt bulunamadı. Lütfen filtreleri gevşeterek tekrar deneyin.")
            return

        # 2. LİTERATÜR ODAKLI ÇÖZÜM (Enstrüman filtresi yoksa ve en az 2 kayıt varsa)
        if toplam_calisma >= 2 and sorgu_degerleri.get('Kullanılan Enstrüman Kategorisi') == 'Filtreleme Yok': 
            
            # En sık kullanılan enstrümanı bul
            en_sik_enstruman = filtrelenmis_data['Kullanılan Enstrüman Kategorisi'].mode().iloc[0]
            kullanım_sayisi = filtrelenmis_data[filtrelenmis_data['Kullanılan Enstrüman Kategorisi'] == en_sik_enstruman].shape[0]
            yuzde = (kullanım_sayisi / toplam_calisma) * 100
            
            onerilen_cihaz = f"**{en_sik_enstruman}**"
            kaynak_bilgisi = f"Literatür Odaklı: {toplam_calisma} benzer kayda göre {yuzde:.1f}% kullanım."
            gerekce = "Literatür kanıtı yeterlidir. Bu, endüstriyel bir eğilimi yansıtır."

        # 3. KULLANICI ZATEN ENSTRÜMAN SEÇTİYSE (Filtre sonuçlarını gösterir)
        elif sorgu_degerleri.get('Kullanılan Enstrüman Kategorisi') != 'Filtreleme Yok':
            onerilen_cihaz = sorgu_degerleri['Kullanılan Enstrüman Kategorisi']
            kaynak_bilgisi = f"Kullanıcı Filresi: Belirtilen enstrüman ile ilgili {toplam_calisma} kayıt bulundu."
            gerekce = "Sistem, seçtiğiniz enstrümanı kullanan çalışmaları listeledi."
            
        # 4. ICH KURAL SETİ ODAKLI ÇÖZÜM (Kayıt az veya yetersizse)
        else:
            
            matriks_l = sorgu_degerleri.get('Analiz Matriksi', '').lower()
            amac_l = sorgu_degerleri.get('Analiz Amacı (ICH Eşdeğeri)', '').lower()
            
            # KURAL 1: Biyolojik Bütünlük
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
                gerekce = "Sistemin içindeki spesifik bir ICH kuralı uygulanamadı. Daha fazla kayıt için filtrelenen veriler aşağıdadır."
            
            onerilen_cihaz = f"**{onerilen_cihaz}**"
            kaynak_bilgisi = f"ICH Kural Seti Odaklı: {toplam_calisma} kayıt bulundu, yetersiz olduğu için teorik öneri sunulmuştur."


        # 5. Sonuçları Ekrana Yazma
        st.subheader("💡 Analitik Öneri")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(label="EN ÇOK/TEORİK ÖNERİLEN ENSTRÜMAN", value=onerilen_cihaz.replace('**', ''))
        
        with col2:
            st.info(f"**Kaynak Türü:** {kaynak_bilgisi}")
            st.warning(f"**Gerekçe:** {gerekce}")

        st.markdown("---")
        st.caption(f"Filtreleme sonucunda bulunan kayıt sayısı: {toplam_calisma}")
        
        # Filtrelenmiş Veriyi Göster
        if toplam_calisma > 0:
            # Kullanıcı tüm veri setini görmesin diye ilk 10 kaydı gösteriyoruz
            st.dataframe(filtrelenmis_data.head(10)) 
        else:
            st.info("Filtreleme koşullarınıza uyan kayıt bulunamadı.")
            
        
    
    
if __name__ == "__main__":
    main()