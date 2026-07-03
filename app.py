import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# --- SAYFA GENİŞLİK VE TEMA AYARI ---
st.set_page_config(page_title="FreedomOS - %1 Pro Finans Yönetimi", layout="wide", page_icon="👑")

# --- GOOGLE SHEETS AYARLARI ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BIYr-AaryZp7cisYJZP6lilqdNfaBezcGIAJUkJLf80/edit?usp=sharing"

gider_cols = ["Dönem/Ay", "Net Gelir", "Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler", "Toplam Gider", "Net Tasarruf"]
varlik_cols = ["Dönem/Ay", "Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Toplam Varlık"]

def get_gspread_client():
    if "gcp_service_account" not in st.secrets:
        return None
    try:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.sidebar.error(f"Kimlik Doğrulama Hatası: {e}")
        return None

def load_data_from_google(worksheet_name, default_cols):
    client = get_gspread_client()
    if client is None:
        return pd.DataFrame(columns=default_cols)
    try:
        sh = client.open_by_url(GOOGLE_SHEET_URL)
        wks = sh.worksheet(worksheet_name)
        records = wks.get_all_records()
        if not records:
            return pd.DataFrame(columns=default_cols)
        df = pd.DataFrame(records)
        for col in default_cols:
            if col not in df.columns: df[col] = 0
        return df[default_cols]
    except Exception:
        return pd.DataFrame(columns=default_cols)

if "income_expense_history" not in st.session_state:
    st.session_state.income_expense_history = load_data_from_google("Giderler", gider_cols)
if "investment_history" not in st.session_state:
    st.session_state.investment_history = load_data_from_google("Varlıklar", varlik_cols)

# --- CANLI PIYASA VERILERI ---
@st.cache_data(ttl="15m")
def get_live_prices():
    prices = {"BIST100": 0.0, "Bitcoin ($)": 0.0, "Ons Altın ($)": 0.0}
    try:
        bist_df = yf.Ticker("XU100.IS").history(period="1d")
        if not bist_df.empty: prices["BIST100"] = bist_df['Close'].iloc[-1]
    except: pass
    try:
        btc_df = yf.Ticker("BTC-USD").history(period="1d")
        if not btc_df.empty: prices["Bitcoin ($)"] = btc_df['Close'].iloc[-1]
    except: pass
    try:
        gold_df = yf.Ticker("GC=F").history(period="1d")
        if not gold_df.empty: prices["Ons Altın ($)"] = gold_df['Close'].iloc[-1]
    except: pass
    return prices

live_market = get_live_prices()

# --- ROZET VE OYUNLAŞTIRMA HESAPLAMASI (GLOBAL) ---
def calculate_badge():
    tasarruf_orani = 0
    toplam_varlik = 0
    if not st.session_state.income_expense_history.empty:
        last_m = st.session_state.income_expense_history.iloc[-1]
        try: tasarruf_orani = (float(last_m['Net Tasarruf']) / float(last_m['Net Gelir'])) * 100
        except: tasarruf_orani = 0
    if not st.session_state.investment_history.empty:
        last_v = st.session_state.investment_history.iloc[-1]
        toplam_varlik = float(last_v['Toplam Varlık'])
        
    if toplam_varlik >= 1000000 and tasarruf_orani >= 50: return "👑 %1 Kulübü Lideri", "success"
    elif toplam_varlik >= 100000 and tasarruf_orani >= 30: return "💼 Sermaye Sahibi", "info"
    elif tasarruf_orani >= 20: return "⚔️ Maaşlı Asker", "warning"
    else: return "🛒 Tüketim Kölesi", "error"

# --- SOL PANEL ---
st.sidebar.title("👑 FreedomOS v5.0")
st.sidebar.markdown("*Mark Tilbury %1 Mentorluk Sistemi*")

# Oyunlaştırma Rozeti Gösterimi
badge_name, badge_type = calculate_badge()
st.sidebar.markdown(f"### Mevcut Rütbeniz: \n**{badge_name}**")
st.sidebar.divider()

st.sidebar.subheader("🌍 Canlı Piyasa Takibi")
if live_market["BIST100"] > 0: st.sidebar.metric("📊 BIST 100", f"{live_market['BIST100']:,.2f}")
if live_market["Bitcoin ($)"] > 0: st.sidebar.metric("🪙 Bitcoin", f"${live_market['Bitcoin ($)']:,.0f}")
if live_market["Ons Altın ($)"] > 0: st.sidebar.metric("🏆 Ons Altın", f"${live_market['Ons Altın ($)']:,.1f}")
st.sidebar.divider()

page = st.sidebar.radio(
    "Gitmek İstediğiniz Sayfa:",
    [
        "🏠 Genel Durum & Özet Paneli", 
        "📊 Gelir / Detaylı Gider Kaydı", 
        "📈 Varlık & Portföy Rebalancing", 
        "☕ Vampir Harcama (Latte Faktörü)",
        "🛡️ Kıyamet Senaryosu (Stres Testi)",
        "❄️ Pasif Gelir Kar Topu",
        "🔮 Maaşlı Çalışmadan Kurtulma Motoru"
    ]
)
st.sidebar.divider()

# ==========================================
# SAYFA 1: GENEL DURUM & ÖZET PANELİ
# ==========================================
if page == "🏠 Genel Durum & Özet Paneli":
    st.header("🏠 Finansal Komuta Merkezi")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 FreedomOS'a Hoş Geldiniz! Başlamak için lütfen yan menüden **'Gelir / Detaylı Gider Kaydı'** sayfasına giderek ilk ay verinizi ekleyin.")
    else:
        last_mali = st.session_state.income_expense_history.iloc[-1]
        last_varlik = st.session_state.investment_history.iloc[-1]
        
        try: tasarruf_orani = (float(last_mali['Net Tasarruf']) / float(last_mali['Net Gelir'])) * 100
        except: tasarruf_orani = 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Son Ay Net Gelir", f"{float(last_mali['Net Gelir']):,.0f} TL")
        col2.metric("📉 Son Ay Toplam Gider", f"{float(last_mali['Toplam Gider']):,.0f} TL")
        col3.metric("🚀 Aylık Tasarruf Gücü", f"{float(last_mali['Net Tasarruf']):,.0f} TL")
        col4.metric("👑 Toplam Varlık Büyüklüğü", f"{float(last_varlik['Toplam Varlık']):,.0f} TL")
        
        st.divider()
        st.subheader("🧠 Mark Tilbury Finansal Sağlık Analizi")
        if tasarruf_orani >= 50: st.success(f"🔥 **Mükemmel!** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Parayı %1'lik kesim gibi yönetiyorsunuz.")
        elif tasarruf_orani >= 20: st.info(f"👍 **İyi Durumdasınız:** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Minimum %20 kuralını geçtiniz.")
        else: st.warning(f"⚠️ **Geliştirilmeli:** Tasarruf oranınız **%{tasarruf_orani:.1f}**. 'Önce kendine öde!' Giderleri kısmalısınız.")

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Gider Dağılım Analizi**")
            gider_labels = ["Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler"]
            gider_values = [float(last_mali[l]) for l in gider_labels]
            st.plotly_chart(px.pie(names=gider_labels, values=gider_values, hole=0.4), use_container_width=True)
        with g2:
            st.markdown("**Yatırım Portföyü Dağılımı**")
            varlik_labels = ["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"]
            varlik_values = [float(last_varlik[l]) for l in varlik_labels]
            st.plotly_chart(px.pie(names=varlik_labels, values=varlik_values, hole=0.4, color_discrete_sequence=px.colors.sequential.Mint), use_container_width=True)

# ==========================================
# SAYFA 2: GELİR / DETAYLI GİDER KAYDI
# ==========================================
elif page == "📊 Gelir / Detaylı Gider Kaydı":
    st.header("📊 Detaylı Gelir ve Gider Kayıt Defteri")
    
    with st.form("gider_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
            gelir = st.number_input("Aylık Toplam Net Gelir (TL):", min_value=0, value=60000, step=1000)
            g_kira = st.number_input("Kira, Ev ve Mutfak Harcamaları (TL):", min_value=0, value=20000, step=500)
            g_fatura = st.number_input("Faturalar (TL):", min_value=0, value=4000, step=100)
        with col2:
            g_kredi = st.number_input("Kredi Kartları ve Borçlar (TL):", min_value=0, value=5000, step=500)
            g_ulasim = st.number_input("Ulaşım ve Araç Masrafları (TL):", min_value=0, value=3000, step=100)
            g_sosyal = st.number_input("Sosyal Hayat ve Eğlence (TL):", min_value=0, value=4000, step=100)
            g_diger = st.number_input("Diğer Harcamalar (TL):", min_value=0, value=2000, step=100)
            
        submit_mali = st.form_submit_button("💰 Verileri Google Sheets'e Güvenli Kaydet")
        
    if submit_mali:
        toplam_gider = g_kira + g_fatura + g_kredi + g_ulasim + g_sosyal + g_diger
        net_tasarruf = gelir - toplam_gider
        
        yeni_satir_dict = {
            "Dönem/Ay": period, "Net Gelir": gelir, "Kira/Mutfak": g_kira, "Faturalar": g_fatura, 
            "Kredi/Borç": g_kredi, "Ulaşım/Araç": g_ulasim, "Sosyal/Eğlence": g_sosyal, 
            "Diğer Giderler": g_diger, "Toplam Gider": toplam_gider, "Net Tasarruf": net_tasarruf
        }
        yeni_satir_df = pd.DataFrame([yeni_satir_dict])
        
        st.session_state.income_expense_history = pd.concat([st.session_state.income_expense_history, yeni_satir_df], ignore_index=True)
        
        client = get_gspread_client()
        if client is not None:
            try:
                sh = client.open_by_url(GOOGLE_SHEET_URL)
                wks = sh.worksheet("Giderler")
                if not wks.get_all_values(): wks.append_row(gider_cols)
                wks.append_row([yeni_satir_dict[col] for col in gider_cols])
                st.success(f"✔️ {period} verileri başarıyla kaydedildi!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ API Hatası: {e}")

    if not st.session_state.income_expense_history.empty:
        st.subheader("📚 Sistemde Kayıtlı Zaman Günlükleri")
        st.dataframe(st.session_state.income_expense_history, use_container_width=True)

# ==========================================
# SAYFA 3: VARLIK & PORTFÖY REBALANCING
# ==========================================
elif page == "📈 Varlık & Portföy Rebalancing":
    st.header("📈 Canlı Varlık Sepeti ve Akıllı Dengeleme")
    
    st.sidebar.subheader("🎯 İdeal Portföy Hedefiniz (%)")
    t_nakit = st.sidebar.slider("Hedef Nakit %", 0, 100, 15)
    t_hisse = st.sidebar.slider("Hedef Hisse %", 0, 100, 45)
    t_kripto = st.sidebar.slider("Hedef Kripto %", 0, 100, 15)
    t_altin = st.sidebar.slider("Hedef Altın %", 0, 100, 25)
    
    with st.form("varlik_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            v_period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
            v_nakit = st.number_input("Banka Mevduatı / Nakit Birikim (TL):", min_value=0, value=30000)
            v_hisse = st.number_input("Borsa / Hisse Senedi Portföy Değeri (TL):", min_value=0, value=80000)
        with col2:
            v_kripto = st.number_input("Kripto Para Portföy Değeri (TL):", min_value=0, value=40000)
            v_altin = st.number_input("Altın, Gümüş ve Fiziki Emtialar (TL):", min_value=0, value=50000)
            
        submit_varlik = st.form_submit_button("📈 Portföyü Google Sheets'e Kalıcı Gönder")
        
    if submit_varlik:
        toplam_varlik = v_nakit + v_hisse + v_kripto + v_altin
        yeni_varlik_dict = {
            "Dönem/Ay": v_period, "Nakit Birikim": v_nakit, "Hisse Senedi": v_hisse, 
            "Kripto Para": v_kripto, "Altın/Emtia": v_altin, "Toplam Varlık": toplam_varlik
        }
        yeni_varlik_df = pd.DataFrame([yeni_varlik_dict])
        
        st.session_state.investment_history = pd.concat([st.session_state.investment_history, yeni_varlik_df], ignore_index=True)
        
        client = get_gspread_client()
        if client is not None:
            try:
                sh = client.open_by_url(GOOGLE_SHEET_URL)
                wks = sh.worksheet("Varlıklar")
                if not wks.get_all_values(): wks.append_row(varlik_cols)
                wks.append_row([yeni_varlik_dict[col] for col in varlik_cols])
                st.success("✔️ Portföy başarıyla kaydedildi!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ API Hatası: {e}")

    if not st.session_state.investment_history.empty:
        last_v = st.session_state.investment_history.iloc[-1]
        tot = float(last_v["Toplam Varlık"]) if float(last_v["Toplam Varlık"]) > 0 else 1
        
        p_nakit = (float(last_v["Nakit Birikim"])/tot)*100
        p_hisse = (float(last_v["Hisse Senedi"])/tot)*100
        p_kripto = (float(last_v["Kripto Para"])/tot)*100
        p_altin = (float(last_v["Altın/Emtia"])/tot)*100
        
        st.subheader("⚖️ Portföy Dengeleme (Rebalancing) Önerileri")
        rebal_df = pd.DataFrame({
            "Varlık Tipi": ["Nakit", "Hisse Senedi", "Kripto Para", "Altın/Emtia"],
            "Mevcut Oran %": [p_nakit, p_hisse, p_kripto, p_altin],
            "Hedef Oran %": [t_nakit, t_hisse, t_kripto, t_altin],
        })
        
        for index, row in rebal_df.iterrows():
            fark_orani = row["Hedef Oran %"] - row["Mevcut Oran %"]
            fark_tl = (fark_orani / 100) * tot
            if fark_tl > 0: st.info(f"➕ **{row['Varlık Tipi']}** geride. Dengelenmek için **{fark_tl:,.0f} TL** alım yapmalısınız.")
            elif fark_tl < 0: st.warning(f"✂️ **{row['Varlık Tipi']}** fazla. **{abs(fark_tl):,.0f} TL** kâr satışı düşünülebilir.")

# ==========================================
# SAYFA 4: VAMPİR HARCAMA (LATTE FAKTÖRÜ)
# ==========================================
elif page == "☕ Vampir Harcama (Latte Faktörü)":
    st.header("🧛‍♂️ Vampir Harcama Yüzleşmesi (Latte Faktörü)")
    st.markdown("Küçük zevklerin aslında gelecekteki milyonlarını nasıl çaldığını kendi gözlerinle gör.")
    
    col1, col2, col3 = st.columns(3)
    with col1: gunluk_kahve = st.number_input("☕ Günlük Dışarıdan Kahve/Atıştırmalık (TL):", 0, 500, 150)
    with col2: haftalik_yemek = st.number_input("🍔 Haftalık Dışarıdan Yemek Siparişi (TL):", 0, 5000, 1200)
    with col3: aylik_abonelik = st.number_input("📺 Aylık Kullanılmayan Abonelikler (TL):", 0, 2000, 300)
    
    roi_rate = st.slider("Eğer bu parayı harcamayıp yatırsaydın yıllık ortalama getirin ne olurdu? (%)", 10, 150, 65)
    
    aylik_vampir = (gunluk_kahve * 30) + (haftalik_yemek * 4) + aylik_abonelik
    
    if aylik_vampir > 0:
        st.error(f"🩸 **Kan Kaybı Tespit Edildi:** Aylık tam **{aylik_vampir:,.0f} TL** çöpe gidiyor.")
        
        vampir_data = []
        birikim = 0
        m_roi = (1 + roi_rate / 100) ** (1/12) - 1
        
        for ay in range(1, 361): # 30 yıl
            birikim = (birikim + aylik_vampir) * (1 + m_roi)
            if ay % 12 == 0:
                vampir_data.append({"Yıl": ay//12, "Kayıp Servet (TL)": birikim})
                
        df_vampir = pd.DataFrame(vampir_data)
        
        st.plotly_chart(px.area(df_vampir, x="Yıl", y="Kayıp Servet (TL)", title=f"%{roi_rate} Getiri İle 30 Yıllık Kayıp Servet Dağı", color_discrete_sequence=["#FF4B4B"]), use_container_width=True)
        
        st.subheader("🎙️ Mark Tilbury Diyor Ki:")
        kayip_10_yil = df_vampir.iloc[9]['Kayıp Servet (TL)']
        st.markdown(f"> *O anlık zevkler için harcadığın para yüzünden sadece 10 yıl sonra cebinde olması gereken **{kayip_10_yil:,.0f} TL**'den vazgeçiyorsun. Sen zenginleri daha da zengin etmek için çalışan bir tüketicisin. Uyan!*")

# ==========================================
# SAYFA 5: KIYAMET SENARYOSU (STRES TESTİ)
# ==========================================
elif page == "🛡️ Kıyamet Senaryosu (Stres Testi)":
    st.header("🛡️ Finansal Kriz ve Hayatta Kalma Stres Testi")
    st.markdown("Yarın işten kovulursan veya sıfır gelirin kalırsa, elindeki nakitle standartlarını bozmadan ne kadar yaşayabilirsin?")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.warning("Bu testi yapabilmek için lütfen önce Gelir/Gider ve Varlık verilerinizi girin.")
    else:
        last_expense = float(st.session_state.income_expense_history.iloc[-1]["Toplam Gider"])
        last_cash = float(st.session_state.investment_history.iloc[-1]["Nakit Birikim"])
        
        st.write(f"**Aylık Sabit Gideriniz:** {last_expense:,.0f} TL")
        st.write(f"**Acil Durum Nakitiniz (Banka Mevduatı):** {last_cash:,.0f} TL")
        
        if last_expense > 0:
            hayatta_kalma_ayi = last_cash / last_expense
        else:
            hayatta_kalma_ayi = 0
            
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = hayatta_kalma_ayi,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Hayatta Kalma Süresi (Ay)"},
            gauge = {
                'axis': {'range': [None, 12]},
                'bar': {'color': "black"},
                'steps' : [
                    {'range': [0, 3], 'color': "#FF4B4B"}, # Kırmızı
                    {'range': [3, 6], 'color': "#FFA500"}, # Turuncu
                    {'range': [6, 12], 'color': "#00CC96"}], # Yeşil
                'threshold' : {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 6}
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        if hayatta_kalma_ayi < 3: st.error("🚨 Kırmızı Alarm! Acil durum fonun çok yetersiz. İlk krizde borç batağına düşebilirsin. Nakit rezervini artır!")
        elif hayatta_kalma_ayi < 6: st.warning("⚠️ Fena değil ama risk altındasın. Mark Tilbury minimum 6 aylık bir acil durum fonu önerir.")
        else: st.success(f"🛡️ Mükemmel! Tam {hayatta_kalma_ayi:.1f} ay boyunca hiç çalışmadan mevcut hayatını yaşayabilirsin. Krizlere karşın bir kurşungeçirmez yeleğin var.")

# ==========================================
# SAYFA 6: PASİF GELİR KAR TOPU
# ==========================================
elif page == "❄️ Pasif Gelir Kar Topu":
    st.header("❄️ Pasif Gelir Kar Topu (Param Bana Ne Alırdı?)")
    st.markdown("Mevcut yatırımlarınızın size *şu an* aylık olarak hangi faturalarınızı bedavaya getirebileceğini görün.")
    
    if st.session_state.investment_history.empty:
        st.warning("Veri yok. Lütfen varlıklarınızı girin.")
    else:
        tot_port = float(st.session_state.investment_history.iloc[-1]["Toplam Varlık"])
        safe_withdrawal_rate = st.slider("Yıllık Pasif Getiri / Temettü Beklentiniz (%)", 1, 20, 10)
        
        aylik_pasif = (tot_port * (safe_withdrawal_rate / 100)) / 12
        st.success(f"💸 **Mevcut Portföy Büyüklüğünüz:** {tot_port:,.0f} TL | **Tahmini Aylık Pasif Geliriniz:** {aylik_pasif:,.0f} TL")
        st.divider()
        
        hedef_kalemler = {
            "📱 Dijital Abonelikler (Netflix, Spotify vs.)": 400,
            "☎️ Telefon Faturası": 600,
            "💪 Spor Salonu Üyeliği": 1500,
            "⚡ Elektrik, Su ve Doğalgaz": 3000,
            "🛒 Market ve Mutfak": 15000,
            "🏠 Ev Kirası": 30000
        }
        
        for isim, tutar in hedef_kalemler.items():
            st.write(f"**{isim}** (Aylık Tahmini {tutar} TL)")
            if aylik_pasif >= tutar:
                st.progress(100)
                st.caption("✅ BEDAVA! (Yatırımlarınız bu gideri sonsuza kadar ödüyor)")
            else:
                yuzde = int((aylik_pasif / tutar) * 100)
                st.progress(yuzde)
                st.caption(f"⏳ Yalnızca %{yuzde}'si karşılanıyor. Daha fazla yatırıma ihtiyaç var.")

# ==========================================
# SAYFA 7: MAAŞLI ÇALIŞMADAN KURTULMA MOTORU
# ==========================================
elif page == "🔮 Maaşlı Çalışmadan Kurtulma Motoru":
    st.header("🔮 9-5 İstifa Sayacı & Finansal Özgürlük Projeksiyonu")
    
    st.subheader("⚙️ Simülasyon Parametreleri")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: inf_rate = st.slider("Yıllık Enflasyon Tahmini (%):", 0, 100, 35)
    with sc2: sal_rate = st.slider("Yıllık Maaş Artış Oranınız (%):", 0, 100, 45)
    with sc3: roi_rate = st.slider("Yatırımların Yıllık Getirisi (%):", 0, 150, 65)
        
    target_p = st.number_input("Maaşlı Çalışmayı Bırakmak İçin İstenen Aylık Pasif Gelir (TL):", min_value=1000, value=50000)
    
    current_portfolio = float(st.session_state.investment_history.iloc[-1]["Toplam Varlık"]) if not st.session_state.investment_history.empty else 200000
    base_income = float(st.session_state.income_expense_history.iloc[-1]["Net Gelir"]) if not st.session_state.income_expense_history.empty else 60000
    base_expense = float(st.session_state.income_expense_history.iloc[-1]["Toplam Gider"]) if not st.session_state.income_expense_history.empty else 38000
    
    sim_months = 360  
    freedom_m = -1
    sim_data = []
    
    for m in range(1, sim_months + 1):
        if m > 1 and m % 12 == 1:
            base_income *= (1 + sal_rate / 100)
            base_expense *= (1 + inf_rate / 100)
            target_p *= (1 + inf_rate / 100)
            
        monthly_saving = base_income - base_expense
        if monthly_saving < 0: monthly_saving = 0
        
        m_roi = (1 + roi_rate / 100) ** (1/12) - 1
        current_portfolio = current_portfolio * (1 + m_roi) + monthly_saving
        passive_gen = (current_portfolio * 0.04) / 12
        
        if passive_gen >= target_p and freedom_m == -1: freedom_m = m
        sim_data.append({"Ay": m, "Yıl": round(m/12, 1), "Varlık": current_portfolio, "Pasif Gelir": passive_gen, "Hedef": target_p})
        
    df_sim = pd.DataFrame(sim_data)
    
    st.divider()
    st.subheader("🏆 İstifa Projeksiyon Sonucu")
    if freedom_m != -1:
        st.balloons()
        st.success(f"🥳 **Hesaplama Tamamlandı!** Tam **{freedom_m // 12} Yıl {freedom_m % 12} Ay** sonra maaşlı çalışmaktan kalıcı olarak kurtuluyorsunuz!")
    else:
        st.error("⚠️ Mevcut oranlara göre 30 yıl içinde istifa etmek mümkün görünmüyor. Tasarruf oranını artırmalısınız.")
        
    st.plotly_chart(px.line(df_sim, x="Yıl", y=["Varlık", "Pasif Gelir", "Hedef"], title="30 Yıllık Finansal Bağımsızlık Matrisi"), use_container_width=True)
