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
# 2. AI BAĞLANTISI (GARANTİ SÜRÜM)
# ==========================================
try:
    if "GEMINI_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=API_KEY)
        
        # 404 hatasını önlemek için alternatif isimleri deniyoruz
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Test isteği
            model.generate_content("test")
            target_model = 'gemini-1.5-flash'
        except:
            model = genai.GenerativeModel('gemini-pro')
            target_model = 'gemini-pro'
            
        ai_aktif = True
        st.sidebar.success(f"✅ Bağlandı: {target_model}")
    else:
        st.sidebar.error("❌ Secrets: GEMINI_KEY bulunamadı!")
        ai_aktif = False
except Exception as e:
    st.sidebar.error(f"⚠️ Teknik Hata: {str(e)}")
    ai_aktif = False
# ==========================================
# 3. AI FONKSİYONLARI (DİNAMİK DİL DESTEKLİ)
# ==========================================

def ai_cumle_uret(dil, seviye):
    """Hata payını azaltan güvenli cümle üretme fonksiyonu"""
    prompt = f"Sen bir dil öğretmenisin. Bana {dil} dilinde, {seviye} seviyesinde bir cümle ve Türkçesini ver. YALNIZCA şu formatı kullan: 'cümle|türkçe'. Örnek: 'I love coding|Kodlamayı seviyorum'."
    try:
        res = model.generate_content(prompt)
        # Gelen yanıttaki gereksiz karakterleri temizle
        raw = res.text.strip().replace('"', '').replace("*", "")
        
        if "|" in raw:
            parts = raw.split("|")
            return {"hedef": parts[0].strip(), "tr": parts[1].strip()}
        else:
            # Format hatalı gelirse varsayılan bir cümle döndür ki uygulama hata vermesin
            return {"hedef": "Error: AI sent wrong format", "tr": "Hata: AI yanlış format gönderdi"}
    except Exception as e:
        st.error(f"AI Hatası: {str(e)}")
        return {"hedef": "Hata", "tr": "Bağlantı sorunu"}
        
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
    
    if st.button("Yeni Soru Üret ✨"):
        with st.spinner("AI hazırlanıyor..."):
            st.session_state.soru = ai_cumle_uret(dil_secimi, seviye_secimi)
            st.session_state.cevap_verildi = False
            st.rerun()
    
    if st.session_state.soru:
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
