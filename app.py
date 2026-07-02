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

try:
    # Bağlantıyı 'gsheets' olarak açıkça tetikliyoruz (st-gsheets-connection kütüphanesi şarttır)
    conn = st.connection("gsheets", type="sheets")
except Exception as e:
    st.error(f"Bağlantı motoru başlatılamadı! Lütfen requirements.txt dosyanıza 'st-gsheets-connection' eklediğinizden emin olun. Detay: {e}")

def load_data(sheet_name):
    try:
        return conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet=sheet_name, ttl="0m")
    except Exception as e:
        if sheet_name == "Giderler":
            return pd.DataFrame(columns=[
                "Dönem/Ay", "Net Gelir", "Kira/Mutfak", "Faturalar", "Kredi/Borç", 
                "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler", "Toplam Gider", "Net Tasarruf"
            ])
        else:
            return pd.DataFrame(columns=[
                "Dönem/Ay", "Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Toplam Varlık"
            ])

st.session_state.income_expense_history = load_data("Giderler")
st.session_state.investment_history = load_data("Varlıklar")

# --- CANLI PIYASA VERILERI (YFINANCE) ---
@st.cache_data(ttl="15m")  # Her 15 dakikada bir verileri yeniler, sistemi yormaz
def get_live_prices():
    try:
        # Örnek olarak küresel ve yerel takip mekanizmaları
        bist = yf.Ticker("XU100.IS").history(period="1d")['Close'].iloc[-1]
        ons_altin = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        return {"BIST100": bist, "Ons Altın ($)": ons_altin, "Bitcoin ($)": btc}
    except:
        return {"BIST100": 0, "Ons Altın ($)": 0, "Bitcoin ($)": 0}

live_market = get_live_prices()

# --- SOL PANEL ---
st.sidebar.title("👑 FreedomOS v4.0")
st.sidebar.markdown("*Mark Tilbury %1 Mentorluk Sistemiyle Entegre*")
st.sidebar.divider()

# Canlı Ticker Gösterimi sidebar'da şık duracaktır
st.sidebar.subheader("🌍 Canlı Piyasa Takibi")
st.sidebar.metric("📊 BIST 100", f"{live_market['BIST100']:,.2f}")
st.sidebar.metric("🪙 Bitcoin", f"${live_market['Bitcoin']:,.0f}")
st.sidebar.metric("🏆 Ons Altın", f"${live_market['Ons Altın ($)']:,.1f}")
st.sidebar.divider()

page = st.sidebar.radio(
    "Stratejik Alan Seçin:",
    ["🏠 Genel Durum & Özet Paneli", "📊 Gelir / Detaylı Gider Kaydı", "📈 Varlık & Portföy Rebalancing", "🔮 %1 Kesim İleri Öngörü & Yapay Zeka"]
)
st.sidebar.divider()

# --- SAYFA 1: GENEL DURUM ---
if page == "🏠 Genel Durum & Özet Paneli":
    st.header("🏠 Finansal Komuta Merkezi")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 FreedomOS'a Hoş Geldiniz! Lütfen önce yan menüden veri girişlerini tamamlayın.")
    else:
        last_month_mali = st.session_state.income_expense_history.iloc[-1]
        last_month_varlik = st.session_state.investment_history.iloc[-1]
        
        tasarruf_orani = (float(last_month_mali['Net Tasarruf']) / float(last_month_mali['Net Gelir'])) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Net Gelir", f"{float(last_month_mali['Net Gelir']):,.0f} TL")
        col2.metric("📉 Toplam Gider", f"{float(last_month_mali['Toplam Gider']):,.0f} TL")
        col3.metric("🚀 Tasarruf Gücü (Aylık)", f"{float(last_month_mali['Net Tasarruf']):,.0f} TL")
        col4.metric("👑 Toplam Net Değer", f"{float(last_month_varlik['Toplam Varlık']):,.0f} TL")
        
        st.divider()
        
        st.subheader("🧠 Mark Tilbury Finansal Sağlık Raporu")
        if tasarruf_orani >= 50:
            st.success(f"🔥 **Mükemmel!** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Parayı %1'lik kesim gibi yönetiyorsunuz. Bu hızla finansal özgürlük çok yakın!")
        elif tasarruf_orani >= 20:
            st.info(f"👍 **İyi Durumdasınız:** Tasarruf oranınız **%{tasarruf_orani:.1f}**. %1'lik kesimin altın kuralı olan minimum %20 barajını geçtiniz.")
        else:
            st.warning(f"⚠️ **Geliştirilmeli:** Tasarruf oranınız **%{tasarruf_orani:.1f}**. Mark Tilbury diyor ki: 'Önce kendine öde!' Giderleri kısıp yatırıma bütçe ayırmalısınız.")

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Gider Dağılımı**")
            gider_labels = ["Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler"]
            gider_values = [float(last_month_mali[l]) for l in gider_labels]
            st.plotly_chart(px.pie(names=gider_labels, values=gider_values, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu), use_container_width=True)
        with g2:
            st.markdown("**Mevcut Varlık Dağılımı**")
            varlik_labels = ["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"]
            varlik_values = [float(last_month_varlik[l]) for l in varlik_labels]
            st.plotly_chart(px.pie(names=varlik_labels, values=varlik_values, hole=0.4, color_discrete_sequence=px.colors.sequential.Mint), use_container_width=True)

# --- SAYFA 2: GELİR / GİDER ---
elif page == "📊 Gelir / Detaylı Gider Kaydı":
    st.header("📊 Finansal Akış Kaydı")
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
            
        submit_mali = st.form_submit_button("💰 Verileri Buluta Gönder ve Kilitle")
        
    if submit_mali:
        toplam_gider = g_kira + g_fatura + g_kredi + g_ulasim + g_sosyal + g_diger
        net_tasarruf = gelir - toplam_gider
        yeni_satir = pd.DataFrame([{
            "Dönem/Ay": period, "Net Gelir": gelir, "Kira/Mutfak": g_kira, "Faturalar": g_fatura, 
            "Kredi/Borç": g_kredi, "Ulaşım/Araç": g_ulasim, "Sosyal/Eğlence": g_sosyal, 
            "Diğer Giderler": g_diger, "Toplam Gider": toplam_gider, "Net Tasarruf": net_tasarruf
        }])
        güncel_df = pd.concat([st.session_state.income_expense_history, yeni_satir], ignore_index=True)
        conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Giderler", data=güncel_df)
        st.success("✔️ Veriler bulut tabanına işlendi!")
        st.rerun()

    if not st.session_state.income_expense_history.empty:
        st.dataframe(st.session_state.income_expense_history, use_container_width=True)

# --- SAYFA 3: VARLIK VE PORTFÖY REBALANCING ---
elif page == "📈 Varlık & Portföy Rebalancing":
    st.header("📈 Akıllı Portföy Yönetimi & Rebalancing (Dengeleme)")
    
    st.sidebar.subheader("🎯 İdeal Portföy Hedefiniz (%)")
    t_nakit = st.sidebar.slider("Hedef Nakit %", 0, 100, 15)
    t_hisse = st.sidebar.slider("Hedef Hisse %", 0, 100, 45)
    t_kripto = st.sidebar.slider("Hedef Kripto %", 0, 100, 15)
    t_altin = st.sidebar.slider("Hedef Altın %", 0, 100, 25)
    
    if (t_nakit + t_hisse + t_kripto + t_altin) != 100:
        st.sidebar.error("⚠️ Hedef oranların toplamı 100 olmalıdır!")

    with st.form("varlik_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            v_period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
            v_nakit = st.number_input("Banka Mevduatı / Nakit Birikim (TL):", min_value=0, value=30000)
            v_hisse = st.number_input("Borsa / Hisse Senedi (TL):", min_value=0, value=80000)
        with col2:
            v_kripto = st.number_input("Kripto Para Portföyü (TL):", min_value=0, value=40000)
            v_altin = st.number_input("Altın ve Fiziki Emtia (TL):", min_value=0, value=50000)
            
        submit_varlik = st.form_submit_button("📈 Portföy Durumunu Güncelle")
        
    if submit_varlik:
        toplam_varlik = v_nakit + v_hisse + v_kripto + v_altin
        yeni_varlik_satir = pd.DataFrame([{
            "Dönem/Ay": v_period, "Nakit Birikim": v_nakit, "Hisse Senedi": v_hisse, 
            "Kripto Para": v_kripto, "Altın/Emtia": v_altin, "Toplam Varlık": toplam_varlik
        }])
        güncel_v_df = pd.concat([st.session_state.investment_history, yeni_varlik_satir], ignore_index=True)
        conn.update(spreadsheet=GOOGLE_SHEET_URL, worksheet="Varlıklar", data=güncel_v_df)
        st.success("✔️ Portföy buluta kaydedildi.")
        st.rerun()

    if not st.session_state.investment_history.empty:
        last_v = st.session_state.investment_history.iloc[-1]
        tot = float(last_v["Toplam Varlık"])
        
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
                st.info(f"➕ **{row['Varlık Tipi']}** için hedefinizin gerisindesiniz. Dengelenmek için yaklaşık **{fark_tl:,.0f} TL** değerinde alım yapmalısınız.")
            elif fark_tl < 0:
                st.warning(f"✂️ **{row['Varlık Tipi']}** portföyünüzde fazla yer kaplıyor. **{abs(fark_tl):,.0f} TL** değerinde kâr satışı düşünülebilir.")

        fig_compare = go.Figure(data=[
            go.Bar(name='Mevcut Durum %', x=rebal_df["Varlık Tipi"], y=rebal_df["Mevcut Oran %"], marker_color='rgb(55, 83, 109)'),
            go.Bar(name='Hedeflenen %', x=rebal_df["Varlık Tipi"], y=rebal_df["Hedef Oran %"], marker_color='rgb(26, 118, 141)')
        ])
        fig_compare.update_layout(barmode='group', title="Hedef vs Mevcut Varlık Dağılımı")
        st.plotly_chart(fig_compare, use_container_width=True)

# --- SAYFA 4: ÖNGÖRÜ VE YAPAY ZEKA ---
elif page == "🔮 %1 Kesim İleri Öngörü & Yapay Zeka":
    st.header("🔮 İleri Düzey Finansal Projeksiyon Matrisi")
    
    sc1, sc2, sc3 = st.columns(3)
    with sc1: inf_rate = st.slider("Yıllık Ortalama Enflasyon (%):", 0, 100, 35)
    with sc2: sal_rate = st.slider("Yıllık Gelir Artış Hızı (%):", 0, 100, 45)
    with sc3: roi_rate = st.slider("Portföy Ortalama Yıllık Getirisi (%):", 0, 150, 65)
        
    target_p = st.number_input("Hedeflenen Aylık Pasif Gelir (Bugünün Parasıyla TL):", min_value=1000, value=50000)
    
    if len(st.session_state.income_expense_history) >= 2:
        df_mali = st.session_state.income_expense_history
        X = np.array(range(len(df_mali))).reshape(-1, 1)
        y = df_mali["Toplam Gider"].values.astype(float)
        model = LinearRegression().fit(X, y)
        
        current_portfolio = float(st.session_state.investment_history.iloc[-1]["Toplam Varlık"])
        base_income = float(df_mali.iloc[-1]["Net Gelir"])
        base_expense = float(df_mali.iloc[-1]["Toplam Gider"])
        
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
        
        st.subheader("🏆 Finansal Özgürlük Yolculuğu Aşamaları")
        st.markdown(f" Yatırımlarınızın mevcut safe-withdrawal (%4) kapasitesi aylık **{df_sim.iloc[-1]['Pasif Gelir']*0.1:,.0f} TL** pasif akış üretebiliyor.")
        
        if freedom_m != -1:
            st.balloons()
            st.success(f"🥳 **Tebrikler!** Bu finansal akışla **{freedom_m // 12} Yıl {freedom_m % 12} Ay** sonra özgürsünüz.")
        else:
            st.error("⚠️ Mevcut girdilerle 30 yıl içinde hedefe ulaşılamıyor. Tasarruf oranını artırmalısınız.")
            
        st.plotly_chart(px.line(df_sim, x="Yıl", y=["Varlık", "Pasif Gelir", "Hedef"], title="30 Yıllık Özgürlük Matrisi Grafiği"), use_container_width=True)
