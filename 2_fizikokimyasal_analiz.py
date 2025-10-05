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
        st.error(f"Veri yüklenirken bir hata oluştu: Missing optional dependency 'openpyxl'. Lütfen requirements.txt dosyasını kontrol edin.")
        return None


# --- ANALİZ MANTIĞINI UYGULA ---

def main():
    st.set_page_config(page_title="Akıllı Analitik Referans Sistemi", layout="wide")
    
    st.title("🧪 Akıllı Analitik Referans Sistemi")
    st.markdown("---")
    
    # 1. Veri Yükleme Kontrolü
    df = load_data()
    if df is None:
        return

    st.sidebar.header("1. Veri Kayıtlarına Göre Filtreleme")

    # Mevcut Dört Açılır Menü (Veritabanı Filtresi)
    sorgulanabilir_sutunlar = [
        'Analiz Matriksi',
        'Analiz Amacı (ICH Eşdeğeri)',
        'Molekül Tipi',
        'Kullanılan Enstrüman Kategorisi'
    ]
    sorgu_degerleri = {}
    
    for sutun in sorgulanabilir_sutunlar:
        secenekler = ['Filtreleme Yok'] + [str(x) for x in df[sutun].unique()]
        try:
            secilen_deger = st.sidebar.selectbox(
                f"Sorgulama Parametresi: {sutun}", 
                options=sorted(secenekler),
                key=f"sb_{sutun}" # Her selectbox için benzersiz anahtar
            )
            sorgu_degerleri[sutun] = secilen_deger
        except KeyError:
            # Hata oluşursa (sütun adı yanlışsa), kullanıcıyı uyar
            st.sidebar.error(f"HATA: Excel'de '{sutun}' sütunu bulunamadı. Lütfen başlığı kontrol edin.")
            return

    # --- 2. YENİ FİZİKOKİMYASAL ÖZELLİK SORGULARI ---
    st.sidebar.markdown("---")
    st.sidebar.header("2. Fizikokimyasal Özellikler")

    # Çözünürlük (Radio)
    solubility = st.sidebar.radio(
        "1. Çözünürlük",
        ('Suda', 'Organik çözücülerde', 'Her ikisinde', 'Çok düşük çözünürlük'),
        help="Analitin hangi çözücüde çözündüğünü belirtir."
    )

    # Uçuculuk (Radio)
    volatility = st.sidebar.radio(
        "2. Uçuculuk",
        ('Evet (Buharlaşır)', 'Hayır (Uçucu değil)'),
        help="Analit oda sıcaklığında veya hafif ısıtıldığında buharlaşır mı?"
    )

    # Molekül Ağırlığı (Radio)
    mw_range = st.sidebar.radio(
        "3. Molekül Ağırlığı",
        ('< 500 Da (Küçük)', '500–5000 Da (Orta)', '> 5000 Da (Büyük)'),
        help="Analitin molekül ağırlığı aralığı."
    )
    
    # UV/Floresans Absorpsiyonu (Checkboxes)
    st.sidebar.markdown("---")
    st.sidebar.subheader("4. Optik Özellikler")
    uv_abs = st.sidebar.checkbox("UV Absorpsiyonu Var", help="Analit UV ışıkta absorpsiyon gösterir mi?")
    fluorescence = st.sidebar.checkbox("Floresans Var", help="Analit floresan ışık yayar mı?")
    
    # Konsantrasyon (Radio)
    concentration = st.sidebar.radio(
        "5. Beklenen Konsantrasyon",
        ('< 1 ng/mL (Çok düşük)', '1–100 ng/mL (Düşük)', '> 100 ng/mL (Yüksek)'),
        help="Numunedeki beklenen konsantrasyon aralığı."
    )

    # Buton
    if st.sidebar.button("Analitik Öneri Oluştur", key="main_button"):
        
        # --- VERİTABANI FİLTRESİ ---
        filtre_kosullari = []
        for sutun, deger in sorgu_degerleri.items():
            if deger != 'Filtreleme Yok' and deger != 'Belirtilmemiş':
                filtre_kosullari.append(f"`{sutun}` == '{deger}'")

        if filtre_kosullari:
            filtre_stringi = ' & '.join(filtre_kosullari)
            try:
                filtrelenmis_data = df.query(filtre_stringi, engine='python')
            except Exception:
                st.error("Veritabanı sorgusunda hata oluştu.")
                return
        else:
            filtrelenmis_data = df

        toplam_calisma = len(filtrelenmis_data)

        # --- FİZİKOKİMYASAL MANTIK UYGULAMASI ---
        öneri_puanı = {} 
        
        # Olası cihazları başlangıçta sıfır puanla başlat
        cihazlar = ['LC-MS/MS', 'HPLC-UV/DAD', 'GC-MS', 'SEC/CEX-HPLC', 'ICP-MS', 'CE']
        for cihaz in cihazlar:
            öneri_puanı[cihaz] = 0

        gerekceler = [] # Karar gerekçelerini tutmak için

        
        # KURAL 1: Uçuculuk Kontrolü
        if volatility == 'Evet (Buharlaşır)':
            öneri_puanı['GC-MS'] += 3 # Yüksek puan
            gerekceler.append("• Uçuculuk nedeniyle **GC (Gaz Kromatografisi)** tabanlı yöntemlere yönlendirme.")

        # KURAL 2: Molekül Ağırlığı Kontrolü
        if mw_range == '< 500 Da (Küçük)':
            # Küçük moleküller HPLC-UV/DAD veya GC-MS için uygundur
            öneri_puanı['HPLC-UV/DAD'] += 1
            öneri_puanı['LC-MS/MS'] += 1
        elif mw_range == '> 5000 Da (Büyük)':
            # Büyük moleküller (Biyolojikler) SEC/CEX/CE gerektirir
            öneri_puanı['SEC/CEX-HPLC'] += 3
            öneri_puanı['CE'] += 2
            gerekceler.append("• Büyük molekül ağırlığı (Biyolojik) nedeniyle **SEC/CEX/CE** uygunluğu.")
            
        # KURAL 3: Hassasiyet (Konsantrasyon) Kontrolü
        if concentration == '< 1 ng/mL (Çok düşük)' or concentration == '1–100 ng/mL (Düşük)':
            # Çok düşük konsantrasyonlar en hassas dedektörleri gerektirir
            öneri_puanı['LC-MS/MS'] += 3 # MS en yüksek hassasiyettir
            öneri_puanı['HPLC-UV/DAD'] -= 1 # UV/DAD yetersiz kalabilir
            gerekceler.append("• Düşük konsantrasyon beklentisi nedeniyle **Kütle Spektrometresi (MS)** tercih edildi.")

        # KURAL 4: Optik Özellikler (Dedektör Tipi)
        if uv_abs and not fluorescence:
            öneri_puanı['HPLC-UV/DAD'] += 2
            gerekceler.append("• UV absorbsiyonu nedeniyle **UV/DAD dedektörleri** uygundur.")
        if fluorescence:
            öneri_puanı['HPLC-UV/DAD'] += 3 # DAD genelde floresansı destekler
            gerekceler.append("• Floresans özelliği nedeniyle **FLD dedektörleri** (HPLC ile) uygundur.")
            
        # KURAL 5: Çözünürlük (Numune Hazırlık)
        if solubility == 'Çok düşük çözünürlük':
             gerekceler.append("• Çözünürlük sorunları nedeniyle Numune Hazırlama (Örn: SPE) kritik önem taşır.")


        # --- LİTERATÜR MANTIĞI (VERİ AĞIRLIĞI) ---
        
        öneri_turu = "Fizikokimyasal Özelliklere Dayalı Teorik Öneri"
        
        if toplam_calisma > 0:
            # Enstrüman kategorilerini filtreler
            enstruman_dagilimi = filtrelenmis_data['Kullanılan Enstrüman Kategorisi'].value_counts(normalize=True)
            
            # Veri setindeki en sık kullanılan cihaza ağırlık ekle (en fazla 1 puan)
            if not enstruman_dagilimi.empty:
                en_sik_enstruman = enstruman_dagilimi.index[0]
                öneri_puanı[en_sik_enstruman] += 1
                öneri_turu = "Veritabanı Kanıtı İle Güçlendirilmiş Öneri"
                gerekceler.append(f"• {toplam_calisma} benzer kayıttan gelen literatür kanıtı ile desteklendi.")

        # --- SON KARAR ---
        
        # En yüksek puana sahip cihazı bul
        en_iyi_cihaz = max(öneri_puanı, key=öneri_puanı.get)
        en_yuksek_puan = öneri_puanı[en_iyi_cihaz]
        
        if en_yuksek_puan == 0 and toplam_calisma == 0:
            onerilen_cihaz = "Belirsiz"
            kaynak_bilgisi = "Yetersiz Veri ve Özellik"
            gerekce = "Lütfen daha fazla fizikokimyasal özellik belirtin."
        else:
            onerilen_cihaz = en_iyi_cihaz
            kaynak_bilgisi = öneri_turu
            gerekce = "\n".join(gerekceler)
            
            # Eğer GC önerilmişse ve MW yüksekse, GC'nin MW kuralını geçersiz kıldığını belirt
            if onerilen_cihaz == 'GC-MS' and mw_range == '> 5000 Da (Büyük)':
                 gerekce += "\n• Uçuculuk, büyük MW kuralını geçersiz kıldı, ancak derivatizasyon gerektirebilir."

        # 5. Sonuçları Ekrana Yazma
        st.subheader("💡 Analitik Öneri")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(label="EN İYİ TEORİK/LİTERATÜR ÖNERİ", value=onerilen_cihaz)
        
        with col2:
            st.info(f"**Kaynak Türü:** {kaynak_bilgisi}")
            st.warning(f"**Gerekçeler:** \n{gerekce}")

        st.markdown("---")
        
        # Filtrelenmiş Veriyi Göster
        st.caption(f"Veritabanında bulunan benzer kayıt sayısı: {toplam_calisma}")
        if toplam_calisma > 0:
            st.dataframe(filtrelenmis_data) 
        else:
            st.info("Veritabanında spesifik filtrelemeye uyan kayıt bulunamadı.")
            
        
    
    
if __name__ == "__main__":
    main()