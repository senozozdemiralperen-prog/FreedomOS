import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
import gspread
from google.oauth2.service_account import Credentials

# Sayfa Genişlik ve Tema Ayarı
st.set_page_config(page_title="FreedomOS - Pro Finans & Varlık Yönetimi", layout="wide", page_icon="👑")

# --- GOOGLE SHEETS AYARLARI ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BIYr-AaryZp7cisYJZP6lilqdNfaBezcGIAJUkJLf80/edit?usp=sharing"

# Standart Sütun Yapıları
gider_cols = ["Dönem/Ay", "Net Gelir", "Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler", "Toplam Gider", "Net Tasarruf"]
varlik_cols = ["Dönem/Ay", "Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Toplam Varlık"]
envanter_cols = ["Varlık Adı", "Varlık Tipi", "Miktar/Adet", "Alış Fiyatı (TL/$)", "Güncel Birim Fiyat (TL/$)", "Toplam Maliyet", "Güncel Toplam Değer", "Kâr / Zarar"]

# Google Cloud Service Account Bağlantı Motoru
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

# Google Sheets'ten geçmiş verileri çekme ve Sayfa Yoksa Otomatik Oluşturma Fonksiyonu
def load_data_from_google(worksheet_name, default_cols):
    client = get_gspread_client()
    if client is None:
        return pd.DataFrame(columns=default_cols)
    try:
        sh = client.open_by_url(GOOGLE_SHEET_URL)
        try:
            wks = sh.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Eğer Google Sheets'te sayfa yoksa otomatik olarak oluşturur ve başlıkları yazar
            wks = sh.add_worksheet(title=worksheet_name, rows="100", cols="20")
            wks.append_row(default_cols)
            
        records = wks.get_all_records()
        if not records:
            return pd.DataFrame(columns=default_cols)
        df = pd.DataFrame(records)
        for col in default_cols:
            if col not in df.columns: df[col] = 0
        return df[default_cols]
    except Exception as e:
        return pd.DataFrame(columns=default_cols)

# Verileri Google'dan çekip hafızaya kilitleyelim
if "income_expense_history" not in st.session_state:
    st.session_state.income_expense_history = load_data_from_google("Giderler", gider_cols)
if "investment_history" not in st.session_state:
    st.session_state.investment_history = load_data_from_google("Varlıklar", varlik_cols)
if "asset_inventory" not in st.session_state:
    st.session_state.asset_inventory = load_data_from_google("Varlık_Envanteri", envanter_cols)

# --- CANLI PIYASA VERILERI & S&P 500 MOTORU ---
@st.cache_data(ttl="15m")
def get_live_prices_and_sp500():
    prices = {"BIST100": 0.0, "Bitcoin ($)": 0.0, "Ons Altın ($)": 0.0, "S&P 500": 0.0}
    sp500_history = pd.DataFrame()
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
    try:
        sp_ticker = yf.Ticker("^GSPC")
        sp500_df = sp_ticker.history(period="1d")
        if not sp500_df.empty: prices["S&P 500"] = sp500_df['Close'].iloc[-1]
        # Grafikler için 6 aylık geçmiş veri çekimi
        sp500_history = sp_ticker.history(period="6m").reset_index()
    except: pass
    return prices, sp500_history

live_market, sp500_hist_data = get_live_prices_and_sp500()

# --- SOL PANEL ---
st.sidebar.title("👑 FreedomOS v6.0")
st.sidebar.markdown("*Alpi Pro Yönetim Sistemi*")
st.sidebar.divider()

st.sidebar.subheader("🌍 Canlı Piyasa Takibi")
if live_market["BIST100"] > 0: st.sidebar.metric("📊 BIST 100", f"{live_market['BIST100']:,.2f}")
if live_market["S&P 500"] > 0: st.sidebar.metric("🇺🇸 S&P 500 Index", f"{live_market['S&P 500']:,.2f}")
if live_market["Bitcoin ($)"] > 0: st.sidebar.metric("🪙 Bitcoin", f"${live_market['Bitcoin ($)']:,.0f}")
if live_market["Ons Altın ($)"] > 0: st.sidebar.metric("🏆 Ons Altın", f"${live_market['Ons Altın ($)']:,.1f}")
st.sidebar.divider()

page = st.sidebar.radio(
    "Gitmek İstediğiniz Sayfa:",
    [
        "🏠 Genel Durum & Özet Paneli", 
        "📊 Gelir /   Detaylı Gider Kaydı", 
        "💎 Detaylı Mal Varlığı Envanteri",
        "📈 Varlık & Portföy Rebalancing", 
        "🔮 Maaşlı Çalışmadan Kurtulma Motoru"
    ]
)
st.sidebar.divider()

# --- SAYFA 1: GENEL DURUM & ÖZET PANELİ ---
if page == "🏠 Genel Durum & Özet Paneli":
    st.header("🏠 Finansal Komuta Merkezi")
    
    # S&P 500 Canlı Durum Kartı ve Grafik Alanı
    if not sp500_hist_data.empty:
        with st.expander("🇺🇸 Canlı Küresel Piyasa Analizi: S&P 500 Endeksi", expanded=True):
            sc1, sc2, sc3 = st.columns([1, 1, 2])
            current_sp = sp500_hist_data['Close'].iloc[-1]
            six_months_ago_sp = sp500_hist_data['Close'].iloc[0]
            perf = ((current_sp - six_months_ago_sp) / six_months_ago_sp) * 100
            
            sc1.metric("Anlık S&P 500 Değeri", f"{current_sp:,.2f}", f"%{perf:+.2f} (6 Ay)")
            sc2.metric("6 Aylık En Yüksek Seviye", f"{sp500_hist_data['High'].max():,.2f}")
            
            fig_sp = px.line(sp500_hist_data, x="Date", y="Close", title="S&P 500 Son 6 Aylık İnteraktif Trend Grafiği", labels={"Date": "Tarih", "Close": "Kapanış Değeri"})
            fig_sp.update_traces(line_color='#2ca02c')
            st.plotly_chart(fig_sp, use_container_width=True)

    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 FreedomOS'a Hoş Geldiniz! Sistemde henüz geçmiş makro veri kaydı bulunmuyor. Başlamak için lütfen 'Gelir / Detaylı Gider Kaydı' sayfasına gidin.")
    else:
        last_mali = st.session_state.income_expense_history.iloc[-1]
        last_varlik = st.session_state.investment_history.iloc[-1]
        
        try: tasarruf_orani = (float(last_mali['Net Tasarruf']) / float(last_mali['Net Gelir'])) * 100
        except: tasarruf_orani = 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Son Ay Net Gelir", f"{float(last_mali['Net Gelir']):,.0f} TL")
        col2.metric("📉 Son Ay Toplam Gider", f"{float(last_mali['Toplam Gider']):,.0f} TL")
        col3.metric("🚀 Aylık Tasarruf Gücü", f"{float(last_mali['Net Tasarruf']):,.0f} TL")
        col4.metric("👑 Makro Varlık Havuzu", f"{float(last_varlik['Toplam Varlık']):,.0f} TL")
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Aylık Gider Dağılım Analizi**")
            gider_labels = ["Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler"]
            gider_values = [float(last_mali[l]) for l in gider_labels]
            st.plotly_chart(px.pie(names=gider_labels, values=gider_values, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu), use_container_width=True)
        with g2:
            st.markdown("**Genel Varlık Sınıfı Dağılımı**")
            varlik_labels = ["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"]
            varlik_values = [float(last_varlik[l]) for l in varlik_labels]
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
            
        submit_mali = st.form_submit_button("💰 Verileri Google Sheets'e Güvenli Kaydet")
        
    if submit_mali:
        toplam_gider = g_kira + g_fatura + g_kredi + g_ulasim + g_sosyal + g_diger
        net_tasarruf = gelir - toplam_gider
        
        yeni_satir_dict = {
            "Dönem/Ay": period, "Net Gelir": gelir, "Kira/Mutfak": g_kira, "Faturalar": g_fatura, 
            "Kredi/Borç": g_kredi, "Ulaşım/Araç": g_ulasim, "Sosyal/Eğlence": g_sosyal, 
            "Diğer Giderler": g_diger, "Toplam Gider": toplam_gider, "Net Tasarruf": net_tasarruf
        }
        st.session_state.income_expense_history = pd.concat([st.session_state.income_expense_history, pd.DataFrame([yeni_satir_dict])], ignore_index=True)
        
        client = get_gspread_client()
        if client is not None:
            try:
                sh = client.open_by_url(GOOGLE_SHEET_URL)
                wks = sh.worksheet("Giderler")
                wks.append_row([yeni_satir_dict[col] for col in gider_cols])
                st.success(f"✔️ {period} bütçe verileri kaydedildi!")
                st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

    if not st.session_state.income_expense_history.empty:
        st.dataframe(st.session_state.income_expense_history, use_container_width=True)

# --- SAYFA 3: DETAYLI MAL VARLIĞI ENVANTERİ (YENİ EKLEME) ---
elif page == "💎 Detaylı Mal Varlığı Envanteri":
    st.header("💎 Detaylı Mal Varlığı, Envanter & Canlı Değer Logu")
    st.markdown("Bu alanda sahip olduğunuz tüm fiziksel ve dijital varlıkları tek tek kırılımlı olarak kayıt altına alabilir, kâr/zarar durumlarını izleyebilirsiniz.")
    
    with st.form("envanter_formu", clear_on_submit=True):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            asset_name = st.text_input("Varlık / Yatırım Adı:", placeholder="Örn: Kadıköy Daire, S&P 500 ETF, Apple Hissesi")
            asset_type = st.selectbox("Varlık Tipi / Kategorisi:", ["Gayrimenkul", "Araç", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Nakit/Mevduat"])
        with ec2:
            asset_qty = st.number_input("Sahip Olunan Miktar / Adet:", min_value=0.0, value=1.0, step=0.1)
            asset_cost = st.number_input("Birim Alış / Maliyet Fiyatı (TL veya $):", min_value=0.0, value=100.0)
        with ec3:
            asset_current = st.number_input("Birim Güncel Değeri (TL veya $):", min_value=0.0, value=120.0)
            
        submit_asset = st.form_submit_button("💎 Varlığı Portföy Envanterine Kilitle")
        
    if submit_asset and asset_name:
        tot_cost = asset_qty * asset_cost
        tot_val = asset_qty * asset_current
        p_l = tot_val - tot_cost
        
        yeni_varlik = {
            "Varlık Adı": asset_name, "Varlık Tipi": asset_type, "Miktar/Adet": asset_qty,
            "Alış Fiyatı (TL/$)": asset_cost, "Güncel Birim Fiyat (TL/$)": asset_current,
            "Toplam Maliyet": tot_cost, "Güncel Toplam Değer": tot_val, "Kâr / Zarar": p_l
        }
        st.session_state.asset_inventory = pd.concat([st.session_state.asset_inventory, pd.DataFrame([yeni_varlik])], ignore_index=True)
        
        client = get_gspread_client()
        if client is not None:
            try:
                sh = client.open_by_url(GOOGLE_SHEET_URL)
                wks = sh.worksheet("Varlık_Envanteri")
                wks.append_row([yeni_varlik[col] for col in envanter_cols])
                st.success(f"✔️ {asset_name} envanter tablonuza başarıyla işlendi!")
                st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

    if not st.session_state.asset_inventory.empty:
        st.subheader("📋 Mevcut Canlı Varlık Listesi")
        
        # Toplam Envanter Özet Kartları
        t_maliyet = st.session_state.asset_inventory["Toplam Maliyet"].sum()
        t_guncel = st.session_state.asset_inventory["Güncel Toplam Değer"].sum()
        t_kar_zarar = t_guncel - t_maliyet
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Portföy Maliyeti", f"{t_maliyet:,.2f}")
        k2.metric("Portföyün Güncel Değeri", f"{t_guncel:,.2f}")
        k3.metric("Net Toplam Kâr / Zarar", f"{t_kar_zarar:,.2f}", f"%{((t_kar_zarar/t_maliyet)*100 if t_maliyet > 0 else 0):+.2f}")
        
        st.divider()
        st.dataframe(st.session_state.asset_inventory, use_container_width=True)
        
        # Envanter Grafik Kırılımı
        fig_env = px.pie(st.session_state.asset_inventory, names="Varlık Adı", values="Güncel Toplam Değer", title="Özel Varlık Dağılım Matrisi", hole=0.3)
        st.plotly_chart(fig_env, use_container_width=True)

# --- SAYFA 4: VARLIK & PORTFÖY REBALANCING ---
elif page == "📈 Varlık & Portföy Rebalancing":
    st.header("📈 Makro Varlık Sepeti ve Akıllı Dengeleme (Rebalancing)")
    
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
        yeni_varlik_dict = {"Dönem/Ay": v_period, "Nakit Birikim": v_nakit, "Hisse Senedi": v_hisse, "Kripto Para": v_kripto, "Altın/Emtia": v_altin, "Toplam Varlık": toplam_varlik}
        st.session_state.investment_history = pd.concat([st.session_state.investment_history, pd.DataFrame([yeni_varlik_dict])], ignore_index=True)
        
        client = get_gspread_client()
        if client is not None:
            try:
                sh = client.open_by_url(GOOGLE_SHEET_URL)
                wks = sh.worksheet("Varlıklar")
                wks.append_row([yeni_varlik_dict[col] for col in varlik_cols])
                st.success(f"✔️ {v_period} makro portföy durumu kilitlendi!")
                st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

    if not st.session_state.investment_history.empty:
        last_v = st.session_state.investment_history.iloc[-1]
        tot = float(last_v["Toplam Varlık"]) if float(last_v["Toplam Varlık"]) > 0 else 1
        
        p_nakit = (float(last_v["Nakit Birikim"])/tot)*100
        p_hisse = (float(last_v["Hisse Senedi"])/tot)*100
        p_kripto = (float(last_v["Kripto Para"])/tot)*100
        p_altin = (float(last_v["Altın/Emtia"])/tot)*100
        
        st.subheader("⚖️ Portföy Dengeleme Önerileri")
        rebal_df = pd.DataFrame({"Varlık Tipi": ["Nakit", "Hisse Senedi", "Kripto Para", "Altın/Emtia"], "Mevcut Oran %": [p_nakit, p_hisse, p_kripto, p_altin], "Hedef Oran %": [t_nakit, t_hisse, t_kripto, t_altin]})
        
        for index, row in rebal_df.iterrows():
            fark_orani = row["Hedef Oran %"] - row["Mevcut Oran %"]
            fark_tl = (fark_orani / 100) * tot
            if fark_tl > 0: st.info(f"➕ **{row['Varlık Tipi']}** için hedefinizin gerisindesiniz. **{fark_tl:,.0f} TL** alım yapılmalı.")
            elif fark_tl < 0: st.warning(f"✂️ **{row['Varlık Tipi']}** hedefinizden fazla. **{abs(fark_tl):,.0f} TL** kâr satışı düşünülebilir.")

# --- SAYFA 5: MAAŞLI ÇALIŞMADAN KURTULMA MOTORU ---
elif page == "🔮 Maaşlı Çalışmadan Kurtulma Motoru":
    st.header("🔮 9-5 İstifa Sayacı & Finansal Özgürlük Projeksiyonu")
    
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
        
        if passive_gen >= target_p and freedom_m == -1: freedom_m = m
        sim_data.append({"Ay": m, "Yıl": round(m/12, 1), "Varlık": current_portfolio, "Pasif Gelir": passive_gen, "Hedef": target_p})
        
    df_sim = pd.DataFrame(sim_data)
    
    st.divider()
    st.subheader("🏆 İstifa Projeksiyon Sonucu")
    if freedom_m != -1:
        st.balloons()
        st.success(f"🥳 **Yapay Zeka Hesaplaması Tamamlandı!** Tam **{freedom_m // 12} Yıl {freedom_m % 12} Ay** sonra finansal özgürlüğünüze kavuşuyorsunuz!")
    else:
        st.error("⚠️ Mevcut oranlara göre 30 yıl içinde istifa etmek mümkün görünmüyor.")
        
    st.plotly_chart(px.line(df_sim, x="Yıl", y=["Varlık", "Pasif Gelir", "Hedef"], title="30 Yıllık Finansal Bağımsızlık Matrisi"), use_container_width=True)
