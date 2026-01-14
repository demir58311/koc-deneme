import streamlit as st
import google.generativeai as genai
import random

# ==========================================
# 1. AYARLAR VE HAFIZA
# ==========================================
st.set_page_config(page_title="Master AI Çok Dilli Koç", layout="wide")

# Hafıza değişkenlerini başlat
for key, val in {
    'skor': 0, 'soru': None, 'cevap_verildi': False, 
    'kelime_bilmece': None
}.items():
    if key not in st.session_state: st.session_state[key] = val
# ==========================================
# 2. AI BAĞLANTISI (KESİN ÇÖZÜM - MODEL FIX)
# ==========================================
if "GEMINI_KEY" not in st.secrets:
    st.sidebar.error("❌ Secrets: GEMINI_KEY bulunamadı!")
    ai_aktif = False
else:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        
        # Google'ın yeni isimlendirme formatını zorluyoruz
        # 'gemini-1.5-flash' yerine 'models/gemini-1.5-flash'
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # Test sorgusu
        test_res = model.generate_content("Merhaba", generation_config={"max_output_tokens": 5})
        ai_aktif = True
        st.sidebar.success("✅ AI Bağlantısı Kuruldu (Flash)")
        
    except Exception as e:
        try:
            # Flash olmazsa Pro'yu da tam isimle dene
            model = genai.GenerativeModel('models/gemini-pro')
            test_res = model.generate_content("Merhaba", generation_config={"max_output_tokens": 5})
            ai_aktif = True
            st.sidebar.warning("⚠️ Pro Modeli Aktif")
        except Exception as e2:
            st.sidebar.error("❌ Bağlantı hala kurulamadı.")
            st.sidebar.info("Lütfen Google AI Studio'dan yeni bir API Key alıp Secrets'ı güncelleyin.")
            ai_aktif = False
# ==========================================
# 3. AI FONKSİYONLARI (DİNAMİK DİL DESTEKLİ)
# ==========================================

def ai_cumle_uret(dil, seviye):
    prompt = f"Sen bir dil öğretmenisin. Bana {dil} dilinde, {seviye} seviyesinde bir cümle ve Türkçesini ver. Format: 'cümle|türkçe'. Örn: 'Ich lerne Deutsch|Almanca öğreniyorum'."
    try:
        # ai_aktif kontrolü ekliyoruz
        if not ai_aktif:
            return {"hedef": "Hata", "tr": "Yapay zeka şu an aktif değil."}
            
        res = model.generate_content(prompt)
        
        if res and res.text:
            raw = res.text.strip().replace('"', '').replace("*", "")
            if "|" in raw:
                parts = raw.split("|")
                return {"hedef": parts[0].strip(), "tr": parts[1].strip()}
        
        return {"hedef": "Hata", "tr": "AI yanıt formatı hatalı."}
    except Exception as e:
        # Hatayı terminale veya ekrana basarak ne olduğunu anlayalım
        print(f"Üretim Hatası: {e}") 
        return {"hedef": "Hata", "tr": f"Cümle kurulamadı: {str(e)}"}
        
def ai_kontrol_esnek(tahmin, dogru, tr, dil):
    """AI ile anlam kontrolü yapar"""
    prompt = f"Türkçe: '{tr}'. {dil} dilinde beklenen: '{dogru}'. Öğrenci: '{tahmin}'. Anlam doğruysa sadece 'OK' yaz. Yanlışsa Türkçe kısa açıklama yap."
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except: return "AI şu an kontrol edemiyor."

def ai_bilmece_uret(dil, seviye):
    """Seçilen dilde kelime bilmecesi üretir"""
    prompt = f"Bana {dil} dilinde {seviye} seviyesinde bir kelime seç. Format: 'kelime|Türkçe|İpucu'. Örn: 'Hund|köpek|Ein Haustier'."
    try:
        res = model.generate_content(prompt)
        return res.text.strip().replace("*", "")
    except: return "Hata|Hata|Hata"

# ==========================================
# 4. YAN PANEL (DİL VE SEVİYE SEÇİMİ)
# ==========================================

st.sidebar.title("🤖 Master AI Koçu")

# DİL SEÇİMİ
dil_secimi = st.sidebar.selectbox("Öğrenilecek Dil:", ["İngilizce", "Almanca"])

# SEVİYE SEÇİMİ (A1'den C2'ye)
seviye_secimi = st.sidebar.select_slider(
    "Seviye Seçin:", 
    options=["A1", "A2", "B1", "B2", "C1", "C2"]
)

st.sidebar.divider()
st.sidebar.metric(f"🏆 {dil_secimi} Skoru", st.session_state.skor)

mod = st.sidebar.radio("Oyun Modu:", ["Çeviri (TR -> Hedef)", "Karışık Kelimeler", "AI Kelime Bilmecesi"])

if st.sidebar.button("Verileri Sıfırla"): 
    st.session_state.skor = 0
    st.session_state.soru = None
    st.rerun()

# ==========================================
# 5. OYUN MODLARI
# ==========================================
# --- MOD 1: ÇEVİRİ ---
if mod == "Çeviri (TR -> Hedef)":
    st.header(f"🌐 Türkçe ➔ {dil_secimi} Çeviri ({seviye_secimi})")
    
    # Kullanıcıya ne yapacağını söyleyen bir bilgi kutusu (Hata yazısı yerine bu görünecek)
    if not st.session_state.soru:
        st.info(f"Henüz bir soru üretilmedi. Pratiğe başlamak için aşağıdaki butona basın.")

    if st.button("Yeni Soru Üret ✨"):
        with st.spinner("AI hazırlanıyor..."):
            yeni_soru = ai_cumle_uret(dil_secimi, seviye_secimi)
            # Eğer AI gerçekten bir cümle ürettiyse hafızaya al
            if yeni_soru and "Hata" not in yeni_soru["hedef"]:
                st.session_state.soru = yeni_soru
                st.session_state.cevap_verildi = False
                st.rerun()
            else:
                st.error(f"AI şu an cevap veremiyor: {yeni_soru['tr']}")
    
    # SADECE soru üretildiyse aşağıdaki giriş alanlarını göster
    if st.session_state.soru and "Hata" not in st.session_state.soru["hedef"]:
        s = st.session_state.soru
        st.subheader(f"🇹🇷 {s['tr']}")
        tahmin = st.text_input(f"{dil_secimi} karşılığını yazın:", key="trans_in")
        
        if st.button("Kontrol Et"):
            sonuc = ai_kontrol_esnek(tahmin, s['hedef'], s['tr'], dil_secimi)
            if "OK" in sonuc.upper():
                st.success(f"✅ Tebrikler! Doğru.\nCevap: {s['hedef']}")
                if not st.session_state.cevap_verildi:
                    st.session_state.skor += 20
                    st.session_state.cevap_verildi = True
                    st.balloons()
            else:
                st.error(f"❌ Hata!")
                st.info(f"Öğretmen Notu: {sonuc}")
# --- MOD 2: KARIŞIK KELİMELER ---
elif mod == "Karışık Kelimeler":
    st.header(f"🔀 Kelime Sıralama ({dil_secimi})")
    
    if st.button("Yeni Soru Üret ✨"):
        st.session_state.soru = ai_cumle_uret(dil_secimi, seviye_secimi)
        st.session_state.cevap_verildi = False
        st.rerun()
        
    if st.session_state.soru:
        s = st.session_state.soru
        words = s['hedef'].split()
        random.shuffle(words)
        st.info(f"Kelimeler: {' / '.join(words)}")
        st.write(f"🇹🇷 Anlamı: {s['tr']}")
        
        tahmin = st.text_input("Doğru sıralama:", key="mix_in")
        if st.button("Kontrol Et"):
            if tahmin.lower().strip() == s['hedef'].lower().strip():
                st.success("✅ Mükemmel!")
                if not st.session_state.cevap_verildi: 
                    st.session_state.skor += 10
                    st.session_state.cevap_verildi = True
            else:
                st.error(f"Yanlış! Doğrusu: {s['hedef']}")

# --- MOD 3: AI KELİME BİLMECESİ ---
elif mod == "AI Kelime Bilmecesi":
    st.header(f"🧠 {dil_secimi} Kelime Bilmecesi")
    
    if st.button("Yeni Bilmece ✨"):
        with st.spinner("AI kelime seçiyor..."):
            raw = ai_bilmece_uret(dil_secimi, seviye_secimi)
            if "|" in raw:
                hedef_kelime, tr_karsilik, ipucu = raw.split("|")
                st.session_state.kelime_bilmece = {"eng": hedef_kelime.strip(), "tr": tr_karsilik.strip(), "hint": ipucu.strip()}
                st.session_state.cevap_verildi = False
                st.rerun()

    if st.session_state.kelime_bilmece:
        kb = st.session_state.kelime_bilmece
        st.info(f"💡 İpucu: {kb['hint']}")
        tahmin = st.text_input("Tahmininiz:", key="riddle_in")
        
        if st.button("Tahmin Et"):
            t = tahmin.lower().strip()
            if t == kb['eng'].lower() or t == kb['tr'].lower():
                st.success(f"🎉 Bildin! {kb['eng']} = {kb['tr']}")
                if not st.session_state.cevap_verildi: 
                    st.session_state.skor += 25
                    st.session_state.cevap_verildi = True
            else:
                st.error("❌ Tekrar dene!")
