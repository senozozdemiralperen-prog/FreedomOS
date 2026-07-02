import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from sklearn.linear_model import LinearRegression
from streamlit_values_connection import FilesConnection # GSheets bağlantısı için ek kütüphane

# Sayfa Genişlik ve Tema Ayarı
st.set_page_config(page_title="WealthOS - Kalıcı Varlık Yönetim Sistemi", layout="wide", page_icon="💼")

# --- BULUT VERİ TABANI (GOOGLE SHEETS) BAĞLANTISI ---
try:
    conn = st.connection("gsheets", type="sheets")
except:
    st.error("⚠️ Google Sheets Secrets ayarı henüz yapılmamış veya hatalı! Lütfen Streamlit Settings > Secrets alanını kontrol edin.")

# Veritabanından okuma fonksiyonları
def load_data(sheet_name):
    try:
        # Google Sheet üzerindeki ilgili sekmeyi okur
        return conn.read(worksheet=sheet_name, ttl="0m")
    except:
        # Eğer tablo boşsa veya hata verirse şablon döndürür
        if sheet_name == "Giderler":
            return pd.DataFrame(columns=[
                "Dönem/Ay", "Net Gelir", "Kira/Mutfak", "Faturalar", "Kredi/Borç", 
                "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler", "Toplam Gider", "Net Tasarruf"
            ])
        else:
            return pd.DataFrame(columns=[
                "Dönem/Ay", "Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Toplam Varlık"
            ])

# Hafıza alanlarını doğrudan canlı Google E-Tabloya bağlıyoruz
st.session_state.income_expense_history = load_data("Giderler")
st.session_state.investment_history = load_data("Varlıklar")

# --- SOL PANEL: SAYFA SEÇİCİ NAVİGASYON ---
st.sidebar.title("💼 WealthOS v3.0 (Canlı Veri)")
st.sidebar.markdown("*Verileriniz Google Sheets Üzerinde Ömür Boyu Güvende*")
st.sidebar.divider()

page = st.sidebar.radio(
    "Gitmek İstediğiniz Sayfa:",
    ["🏠 Genel Durum & Özet Paneli", "📊 Gelir / Detaylı Gider Kaydı", "📈 Varlık & Yatırım Takibi", "🔮 İleri Yönelik Öngörü & Yapay Zeka"]
)
st.sidebar.divider()

# --- SAYFA 1: GENEL DURUM & ÖZET PANELİ ---
if page == "🏠 Genel Durum & Özet Paneli":
    st.header("🏠 Finansal Durum Özet Paneli")
    st.markdown("Google Sheets bulut veri tabanınızdaki güncel mali verilerin anlık izdüşümü.")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 WealthOS'a Hoş Geldiniz! Sistemde henüz geçmiş veri kaydı bulunmuyor. Başlamak için lütfen sol menüden **'Gelir / Detaylı Gider Kaydı'** ve **'Varlık & Yatırım Takibi'** sayfalarına giderek ilk veri girişlerinizi yapın.")
    else:
        last_month_mali = st.session_state.income_expense_history.iloc[-1]
        last_month_varlik = st.session_state.investment_history.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Son Ay Net Gelir", f"{float(last_month_mali['Net Gelir']):,.0f} TL")
        col2.metric("📉 Son Ay Toplam Gider", f"{float(last_month_mali['Toplam Gider']):,.0f} TL", delta=f"-{float(last_month_mali['Toplam Gider'])/float(last_month_mali['Net Gelir'])*100:.1f}% Gelire Oranı", delta_color="inverse")
        col3.metric("🚀 Aylık Tasarruf Gücü", f"{float(last_month_mali['Net Tasarruf']):,.0f} TL")
        col4.metric("👑 Toplam Varlık Büyüklüğü", f"{float(last_month_varlik['Toplam Varlık']):,.0f} TL")
        
        st.divider()
        st.subheader("📊 Grafiksel Analizler")
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("**Gider Dağılım Analizi (Son Ay)**")
            gider_labels = ["Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler"]
            gider_values = [float(last_month_mali[l]) for l in gider_labels]
            fig_gider = px.pie(names=gider_labels, values=gider_values, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_gider, use_container_width=True)
            
        with g2:
            st.markdown("**Yatırım Portföyü Dağılımı (Son Ay)**")
            varlik_labels = ["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"]
            varlik_values = [float(last_month_varlik[l]) for l in varlik_labels]
            fig_varlik = px.pie(names=varlik_labels, values=varlik_values, hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
            st.plotly_chart(fig_varlik, use_container_width=True)

# --- SAYFA 2: GELİR / DETAYLI GİDER KAYDI ---
elif page == "📊 Gelir / Detaylı Gider Kaydı":
    st.header("📊 Detaylı Gelir ve Gider Kayıt Defteri")
    
    with st.form("gider_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
            gelir = st.number_input("Aylık Toplam Net Gelir (TL):", min_value=0, value=60000, step=1000)
            g_kira = st.number_input("Kira, Ev and Mutfak Harcamaları (TL):", min_value=0, value=20000, step=500)
            g_fatura = st.number_input("Faturalar (TL):", min_value=0, value=4000, step=100)
        with col2:
            g_kredi = st.number_input("Kredi Kartları ve Borçlar (TL):", min_value=0, value=5000, step=500)
            g_ulasim = st.number_input("Ulaşım ve Araç Masrafları (TL):", min_value=0, value=3000, step=100)
            g_sosyal = st.number_input("Sosyal Hayat ve Eğlence (TL):", min_value=0, value=4000, step=100)
            g_diger = st.number_input("Diğer Harcamalar (TL):", min_value=0, value=2000, step=100)
            
        submit_mali = st.form_submit_button("💰 Verileri Canlı Bulut Tabanına Kilitle")
        
    if submit_mali:
        toplam_gider = g_kira + g_fatura + g_kredi + g_ulasim + g_sosyal + g_diger
        net_tasarruf = gelir - toplam_gider
        
        yeni_satir = pd.DataFrame([{
            "Dönem/Ay": period, "Net Gelir": gelir, "Kira/Mutfak": g_kira, "Faturalar": g_fatura, 
            "Kredi/Borç": g_kredi, "Ulaşım/Araç": g_ulasim, "Sosyal/Eğlence": g_sosyal, 
            "Diğer Giderler": g_diger, "Toplam Gider": toplam_gider, "Net Tasarruf": net_tasarruf
        }])
        
        güncel_df = pd.concat([st.session_state.income_expense_history, yeni_satir], ignore_index=True)
        # Google E-Tabloya canlı yazma işlemi
        conn.update(worksheet="Giderler", data=güncel_df)
        st.success(f"✔️ {period} verileri Google E-Tablonuza kalıcı olarak kaydedildi! Sayfayı kapatsanız da silinmeyecek.")
        st.rerun()

    st.divider()
    st.subheader("📚 Buluttan Çekilen Geçmiş Zaman Günlükleri")
    if not st.session_state.income_expense_history.empty:
        st.dataframe(st.session_state.income_expense_history, use_container_width=True)
        fig_trend = px.bar(st.session_state.income_expense_history, x="Dönem/Ay", y=["Net Gelir", "Toplam Gider", "Net Tasarruf"], barmode="group", title="Finansal Trendiniz")
        st.plotly_chart(fig_trend, use_container_width=True)
