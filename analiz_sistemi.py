import pandas as pd

# --- ADIM 1: Veriyi Yükleme ---
# VS Code'da dosya yolları genellikle Jupyter'daki gibi basit çalışır.
# Eğer Excel dosyanız VS Code'da açtığınız klasördeyse, bu kod çalışacaktır.
try:
    df = pd.read_excel('analitik_veri.xlsx') 
    print("Veri Başarıyla Yüklendi. İlk 3 Satır:")
    print(df.head(3))
   
except FileNotFoundError:
    print("HATA: Excel dosyası bulunamadı. Lütfen 'analitik_veri.xlsx' dosyasının adını ve konumunu kontrol edin.")
    exit() # Hata varsa programı durdur
# --- ADIM 2: Akıllı Sorgulama Fonksiyonunu Tanımlama ---
def analitik_oner(matriks_girdi, amac_girdi, veritabani):
    
    # 1. LİTERATÜR VERİSİNİ KONTROL ET
    filtrelenmis_data = veritabani[
        (veritabani['Analiz Matriksi'].str.contains(matriks_girdi, case=False)) & 
        (veritabani['Analiz Amacı (ICH Eşdeğeri)'].str.contains(amac_girdi, case=False))
    ]
    
    toplam_calisma = len(filtrelenmis_data)
    
    # 2. LİTERATÜR YANITINI DEĞERLENDİR (2 veya daha fazla çalışma varsa yeterlidir)
    if toplam_calisma >= 2: 
        en_sik_enstruman = filtrelenmis_data['Kullanılan Enstrüman Kategorisi'].mode().iloc[0]
        kullanım_sayisi = filtrelenmis_data[filtrelenmis_data['Kullanılan Enstrüman Kategorisi'] == en_sik_enstruman].shape[0]
        yuzde = (kullanım_sayisi / toplam_calisma) * 100
        
        return (f"\n--- ANALİTİK ÖNERİ (Literatür Odaklı) ---\n"
                f"Bulunan {toplam_calisma} benzer çalışmaya göre, en çok önerilen enstrüman: **{en_sik_enstruman}** "
                f"({yuzde:.1f}% kullanım).\n"
                f"DEĞERLENDİRME: Literatür kanıtı yeterli ve endüstri eğilimini yansıtır.")

    # 3. ICH KURAL SETİNİ UYGULA (Literatür Verisi Yetersizse VEYA Hiç Yoksa)
    else:
        
        matriks_l = matriks_girdi.lower()
        amac_l = amac_girdi.lower()
        
        # KURAL 1: Biyolojik Bütünlük ve Yapısal Zorluklar (Biyofarmasötikler, Peptitler, Aşılar)
        if "protein" in amac_l or "peptit" in amac_l or "aşı" in matriks_l or \
           "yük varyantı" in amac_l or "agregat" in amac_l or "bütünlük" in amac_l:
            onerilen_cihaz = "CEX-HPLC, SEC-HPLC veya Kılcal Elektroforez (CE)"
            gerekce = "ICH Q6B gereğince, biyolojik ürünlerin kritik kalite özelliklerinin (CQA), yapısal bütünlüğünün ve varyantlarının analiz edilmesi zorunludur."
        
        # KURAL 2: Biyolojik Matriks ve Yüksek Hassasiyet (PK, TDM)
        elif "plazma" in matriks_l or "serum" in matriks_l or "idrar" in matriks_l:
            onerilen_cihaz = "LC-MS/MS"
            gerekce = "ICH Q2 (Bioanalitik) gereğince biyolojik matriks karmaşıktır. Farmakokinetik/TDM için ultra yüksek hassasiyet zorunludur."
            
        # KURAL 3: İnorganik/Metal Tespiti (Klinik Kimya ve Kalıntı Kontrolü)
        elif "iyon" in amac_l or "metal" in amac_l or "kantitasyon" in amac_l:
            onerilen_cihaz = "İyon Seçici Elektrot (ISE) veya ICP-MS"
            gerekce = "Klinik veya kalıntı kontrolünde inorganik iyonların hassas ve spesifik ölçümü için bu dedektörler esastır."
            
        # KURAL 4: Safsızlık / Yapı Belirleme (Kimyasal Bilgi)
        elif "safsızlık" in amac_l or "tanımlama" in amac_l or "metabolit" in amac_l:
            onerilen_cihaz = "LC-MS veya GC-MS"
            gerekce = "ICH Q3A/B gereğince safsızlıkların/metabolitlerin kimyasal yapısının belirlenmesi için kütle spektrometrik dedektörler esastır."
        
        # KURAL 5: Fitokimyasal/İzomer Ayrımı
        elif "ekstrakt" in matriks_l or "izomer" in amac_l:
            onerilen_cihaz = "UPLC-MS veya HPLC-DAD"
            gerekce = "Doğal ürünlerde ve bitki matrikslerinde çok sayıda yapısal olarak benzer bileşiğin (izomer) ayrılması ve kesin kimlik doğrulaması gerekir."
            
        # KURAL 6: Farmasötik Rutin Analiz (Miktar Tayini/Çözünme)
        elif "miktar tayini" in amac_l or "çözünme" in amac_l or "assay" in amac_l:
            onerilen_cihaz = "HPLC-UV / HPLC-DAD"
            gerekce = "ICH Q6A gereğince, bitmiş üründe Assay ve Çözünme testleri için yüksek doğruluk ve tekrarlanabilirlik yeterlidir. HPLC-UV/DAD maliyet-etkin ve rutin kullanıma uygundur."
            
        else:
            onerilen_cihaz = "Analiz amacınızı veya matriksinizi daha spesifik belirtin."
            gerekce = "Sistemin içindeki spesifik bir ICH kuralı uygulanmadı."

        return (f"\n--- ANALİTİK ÖNERİ (ICH Kural Seti Odaklı) ---\n"
                f"Literatürde sadece {toplam_calisma} benzer çalışma bulundu (Veri Yetersizliği).\n"
                f"TEORİK ÖNERİ: **{onerilen_cihaz}**\n"
                f"GEREKÇE: {gerekce}")
   # --- ADIM 3: YENİ VE GENİŞLETİLMİŞ SİSTEM TESTİ BAŞLIYOR ---

print("\n\n--- SİSTEM TESTİ BAŞLIYOR ---")

# TEST 1: Literatür Yoğunluklu Test (Yeterli veri var) - Statinler/Antibiyotikler
# Bu sorgu, EXCEL verisinden en sık kullanılan cihazı bulmalıdır.
sonuc_1 = analitik_oner("Plazma", "Farmakokinetik", df)
print(f"\nSORGULAMA 1: Plazmada Farmakokinetik (Statin/Antibiyotik Senaryosu):")
print(sonuc_1)

# TEST 2: Fitokimyasal Test (Yapısal Ayırma Zorunluluğu) - Fenolikler/Ginsenosides
# Bu sorgu, EXCEL verisinden UPLC/LC-MS gibi karmaşık bir cihazı bulmalıdır.
sonuc_2 = analitik_oner("Kök Ekstraktı", "İzomer Ayrımı", df)
print(f"\nSORGULAMA 2: Kök Ekstraktında İzomer Ayrımı (Ginsenosides/Rosmarinic Asit Senaryosu):")
print(sonuc_2)

# TEST 3: Biyofarmasötik Kritik Kalite Testi (ICH Q6B)
# Bu sorgu için EXCEL'de YÜK VARYANTI verisi AZSA/YOKSA, sistem ICH kuralını tetiklemelidir.
sonuc_3 = analitik_oner("Enjeksiyon Sıvısı", "Yük Varyantı Analizi", df)
print(f"\nSORGULAMA 3: Monoklonal Antikor Yük Varyantı Analizi (ICH Kuralı Testi):")
print(sonuc_3)

# TEST 4: İnorganik İyon Testi (Klinik Kimya Kuralı)
# Bu sorgu için EXCEL'de veri yoksa/azsa, sistem ICH kuralını (ISE/ICP-MS) tetiklemelidir.
sonuc_4 = analitik_oner("Biyolojik Sıvı", "Klinik Kantitasyon", df)
print(f"\nSORGULAMA 4: Biyolojik Sıvıda İnorganik İyon Kantitasyonu (Klinik Kural Testi):")
print(sonuc_4)

