import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression
import yfinance as yf

# Sayfa Genişlik ve Tema Ayarı
st.set_page_config(page_title="FreedomOS - %1 Pro Finans Yönetimi", layout="wide", page_icon="👑")

# --- BULUT VERİ TABANI (GOOGLE SHEETS) BAĞLANTISI ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BIYr-AaryZp7cisYJZP6lilqdNfaBezcGIAJUkJLf80/edit?usp=sharing"

# Hafıza alanlarını güvenli bir şekilde ilklendirelim (Fallback Mekanizması)
if "income_expense_history" not in st.session_state:
    st.session_state.income_expense_history = pd.DataFrame(columns=[
        "Dönem/Ay", "Net Gelir", "Kira/Mutfak", "Faturalar", "Kredi/Borç", 
        "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler", "Toplam Gider", "Net Tasarruf"
    ])
if "investment_history" not in st.session_state:
    st.session_state.investment_history = pd.DataFrame(columns=[
        "Dönem/Ay", "Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Toplam Varlık"
    ])

# Google Sheets'ten verileri çek
try:
    conn = st.connection("gsheets", type="sheets")
    sheets_gider = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Giderler", ttl="0m")
    sheets_varlik = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Varlıklar", ttl="0m")
    
    # Gelen veriler boş değilse ve sütunlar eşleşiyorsa session_state'e eşitle
    if sheets_gider is not None and not sheets_gider.empty: 
        st.session_state.income_expense_history = sheets_gider.dropna(how='all')
    if sheets_varlik is not None and not sheets_varlik.empty: 
        st.session_state.investment_history = sheets_varlik.dropna(how='all')
except Exception as e:
    st.sidebar.warning("⚠️ Canlı e-tablo senkronizasyonu şu an lokal modda.")

# --- CANLI PIYASA VERILERI (YFINANCE) ---
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

# --- SOL PANEL (NAVİGASYON) ---
st.sidebar.title("👑 FreedomOS v4.6")
st.sidebar.markdown("*Mark Tilbury %1 Mentorluk Sistemi*")
st.sidebar.divider()

# Canlı Fiyatlar
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
        "🔮 Maaşlı Çalışmadan Kurtulma Motoru"
    ]
)
st.sidebar.divider()

# --- SAYFA 1: GENEL DURUM & ÖZET PANELİ ---
if page == "🏠 Genel Durum & Özet Paneli":
    st.header("🏠 Finansal Komuta Merkezi")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 FreedomOS'a Hoş Geldiniz! Sistemde henüz geçmiş veri kaydı bulunmuyor veya Google Sheets senkronizasyonu bekleniyor. Başlamak için lütfen sol menüden **'Gelir / Detaylı Gider Kaydı'** sayfasına giderek ilk verinizi ekleyin.")
    else:
        last_mali = st.session_state.income_expense_history.iloc[-1]
        last_varlik = st.session_state.investment_history.iloc[-1]
        
        try:
            tasarruf_orani = (float(last_mali['Net Tasarruf']) / float(last_mali['Net Gelir'])) * 100
        except:
            tasarruf_orani = 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Son Ay Net Gelir", f"{float(last_mali['Net Gelir']):,.0f} TL")
        col2.metric("📉 Son Ay Toplam Gider", f"{float(last_mali['Toplam Gider']):,.0f} TL")
        col3.metric("🚀 Aylık Tasarruf Gücü", f"{float(last_mali['Net Tasarruf']):,.0f} TL")
        col4.metric("👑 Toplam Varlık Büyüklüğü", f"{float(last_varlik['Toplam Varlık']):,.0f} TL")
        
        st.divider()
        st.subheader("🧠 Mark Tilbury Finansal Sağlık Analizi")
        if tasarruf_orani >= 50:
            st.success(f"🔥 **Mükemmel!** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Parayı %1'lik kesim gibi yönetiyorsunuz.")
        elif tasarruf_orani >= 20:
            st.info(f"👍 **İyi Durumdasınız:** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Mark Tilbury'nin minimum %20 altın kuralını geçtiniz.")
        else:
            st.warning(f"⚠️ **Geliştirilmeli:** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Mark Tilbury diyor ki: 'Önce kendine öde!' Giderleri kısıp yatırıma bütçe ayırmalısınız.")

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Gider Dağılım Analizi (Son Ay)**")
            gider_labels = ["Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler"]
            gider_values = [float(last_mali[l]) for l in gider_labels if l in last_mali]
            st.plotly_chart(px.pie(names=gider_labels, values=gider_values, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu), use_container_width=True)
        with g2:
            st.markdown("**Yatırım Portföyü Dağılımı (Son Ay)**")
            varlik_labels = ["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"]
            varlik_values = [float(last_varlik[l]) for l in varlik_labels if l in last_varlik]
            st.plotly_chart(px.pie(names=varlik_labels, values=varlik_values, hole=0.4, color_discrete_sequence=px.colors.sequential.Mint), use_container_width=True)

# --- SAYFA 2: GELİR / DETAYLI GİDER KAYDI ---
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
            
        submit_mali = st.form_submit_button("💰 Verileri Google Sheets'e Gönder")
        
    if submit_mali:
        toplam_gider = g_kira + g_fatura + g_kredi + g_ulasim + g_sosyal + g_diger
        net_tasarruf = gelir - toplam_gider
        
        yeni_satir = pd.DataFrame([{
            "Dönem/Ay": period, "Net Gelir": gelir, "Kira/Mutfak": g_kira, "Faturalar": g_fatura, 
            "Kredi/Borç": g_kredi, "Ulaşım/Araç": g_ulasim, "Sosyal/Eğlence": g_sosyal, 
            "Diğer Giderler": g_diger, "Toplam Gider": toplam_gider, "Net Tasarruf": net_tasarruf
        }])
        
        st.session_state.income_expense_history = pd.concat([st.session_state.income_expense_history, yeni_satir], ignore_index=True)
        try:
            # Buluta tam üzerine yazma parametreleriyle (indekssiz) zorlayarak gönderiyoruz
            conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Giderler", data=st.session_state.income_expense_history, index=False)
            st.success(f"✔️ {period} verileri Google E-Tablonuza kalıcı olarak işlendi!")
        except Exception as e:
            st.error(f"Veri yerel hafızaya yazıldı fakat buluta gönderilemedi. Lütfen 2. Adımı uygulayın. Hata: {e}")
        st.rerun()

    if not st.session_state.income_expense_history.empty:
        st.subheader("📚 Sistemde Kayıtlı Zaman Günlükleri")
        st.dataframe(st.session_state.income_expense_history, use_container_width=True)

# --- SAYFA 3: VARLIK & PORTFÖY REBALANCING ---
elif page == "📈 Varlık & Portföy Rebalancing":
    st.header("📈 Canlı Varlık Sepeti ve Akıllı Dengeleme (Rebalancing)")
    
    st.sidebar.subheader("🎯 İdeal Portföy Hedefiniz (%)")
    t_nakit = st.sidebar.slider("Hedef Nakit %", 0, 100, 15)
    t_hisse = st.sidebar.slider("Hedef Hisse %", 0, 100, 45)
    t_kripto = st.sidebar.slider("Hedef Kripto %", 0, 100, 15)
    t_altin = st.sidebar.slider("Hedef Altın %", 0, 100, 25)
    
    with St.form("varlik_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            v_period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
            v_nakit = st.number_input("Banka Mevduatı / Nakit Birikim (TL):", min_value=0, value=30000)
            v_hisse = st.number_input("Borsa / Hisse Senedi Portföy Değeri (TL):", min_value=0, value=80000)
        with col2:
            v_kripto = st.number_input("Kripto Para Portföy Değeri (TL):", min_value=0, value=40000)
            v_altin = st.number_input("Altın, Gümüş ve Fiziki Emtialar (TL):", min_value=0, value=50000)
            
        submit_varlik = st.form_submit_button("📈 Portföyü Google Sheets'e Gönder")
        
    if submit_varlik:
        toplam_varlik = v_nakit + v_hisse + v_kripto + v_altin
        yeni_varlik_satir = pd.DataFrame([{
            "Dönem/Ay": v_period, "Nakit Birikim": v_nakit, "Hisse Senedi": v_hisse, 
            "Kripto Para": v_kripto, "Altın/Emtia": v_altin, "Toplam Varlık": toplam_varlik
        }])
        st.session_state.investment_history = pd.concat([st.session_state.investment_history, yeni_varlik_satir], ignore_index=True)
        try:
            conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Varlıklar", data=st.session_state.investment_history, index=False)
            st.success(f"✔️ {v_period} portföy durumu Google Sheets'e kilitlendi!")
        except Exception as e:
            st.error(f"Portföy yerel hafızaya alındı fakat buluta gönderilemedi. Hata: {e}")
        st.rerun()

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
            if fark_tl > 0:
                st.info(f"➕ **{row['Varlık Tipi']}** için hedefinizin gerisindesiniz. Dengelenmek için **{fark_tl:,.0f} TL** alım yapmalısınız.")
            elif fark_tl < 0:
                st.warning(f"✂️ **{row['Varlık Tipi']}** hedefinizden fazla yer kaplıyor. **{abs(fark_tl):,.0f} TL** kâr satışı düşünülebilir.")

# --- SAYFA 4: MAAŞLI ÇALIŞMADAN KURTULMA MOTORU ---
elif page == "🔮 Maaşlı Çalışmadan Kurtulma Motoru":
    st.header("🔮 9-5 İstifa Sayacı & Finansal Özgürlük Projeksiyonu")
    st.markdown("Bu hesaplama motoru, yatırımlarınızın oluşturduğu pasif gelirin ne zaman maaşınızın ve harcamalarınızın üzerine çıkacağını matematiksel olarak simüle eder.")
    
    st.subheader("⚙️ Simülasyon Parametreleri")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: inf_rate = st.slider("Yıllık Ortalama Enflasyon Tahmini (%):", 0, 100, 35)
    with sc2: sal_rate = st.slider("Yıllık Maaş Artış Oranınız (%):", 0, 100, 45)
    with sc3: roi_rate = st.slider("Yatırımların Yıllık Ortalama Getirisi (%):", 0, 150, 65)
        
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
        
        if passive_gen >= target_p and freedom_m == -1:
            freedom_m = m
            
        sim_data.append({"Ay": m, "Yıl": round(m/12, 1), "Varlık": current_portfolio, "Pasif Gelir": passive_gen, "Hedef": target_p})
        
    df_sim = pd.DataFrame(sim_data)
    
    st.divider()
    st.subheader("🏆 İstifa Projeksiyon Sonucu")
    if freedom_m != -1:
        st.balloons()
        st.success(f"🥳 **Yapay Zeka Hesaplaması Tamamlandı!** Tam **{freedom_m // 12} Yıl {freedom_m % 12} Ay** sonra patronunuza istifa mektubunuzu verip maaşlı çalışmaktan kalıcı olarak kurtuluyorsunuz!")
    else:
        st.error("⚠️ Mevcut oranlar ve enflasyon baskısı altındaki simülasyona göre 30 yıl içerisinde istifa etmek mümkün görünmüyor. Tasarruf gücünüzü veya getiri oranınızı artırmalısınız.")
        
    fig_sim = px.line(df_sim, x="Yıl", y=["Varlık", "Pasif Gelir", "Hedef"], title="30 Yıllık Finansal Bağımsızlık ve Varlık Matrisi")
    st.plotly_chart(fig_sim, use_container_width=True)
