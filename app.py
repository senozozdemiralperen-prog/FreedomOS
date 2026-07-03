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
envanter_cols = ["Varlık Adı", "Kategori", "Alış Fiyatı", "Güncel Değer", "Notlar"]

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
    try:
        sp500_df = yf.Ticker("^GSPC").history(period="1d")
        if not sp500_df.empty: prices["S&P 500"] = sp500_df['Close'].iloc[-1]
    except: pass
    return prices

live_market = get_live_prices()

# --- ROZET VE OYUNLAŞTIRMA (25/50/15/10 MANTIĞI) ---
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
        
    if toplam_varlik >= 1000000 and tasarruf_orani >= 40: return "👑 %1 Kulübü Lideri", "success"
    elif toplam_varlik >= 100000 and tasarruf_orani >= 25: return "📈 Bileşik Getiri Avcısı", "info"
    elif tasarruf_orani >= 15: return "🛡️ %15 Güvenlik Savaşçısı", "warning"
    else: return "🛒 Tüketim Kölesi", "error"

# --- SOL PANEL ---
st.sidebar.title("👑 FreedomOS v6.0")
st.sidebar.markdown("*25/50/15/10 - %1 Yönetim Sistemi*")

badge_name, badge_type = calculate_badge()
st.sidebar.markdown(f"### Mevcut Rütbeniz: \n**{badge_name}**")
st.sidebar.divider()

st.sidebar.subheader("🌍 Canlı Piyasa Takibi")
if live_market["BIST100"] > 0: st.sidebar.metric("📊 BIST 100", f"{live_market['BIST100']:,.2f}")
if live_market["Bitcoin ($)"] > 0: st.sidebar.metric("🪙 Bitcoin", f"${live_market['Bitcoin ($)']:,.0f}")
if live_market["Ons Altın ($)"] > 0: st.sidebar.metric("🏆 Ons Altın", f"${live_market['Ons Altın ($)']:,.1f}")
if live_market.get("S&P 500", 0) > 0: st.sidebar.metric("📈 S&P 500", f"${live_market['S&P 500']:,.0f}")
st.sidebar.divider()

page = st.sidebar.radio(
    "Gitmek İstediğiniz Sayfa:",
    [
        "🏠 Komuta Merkezi: 25-50-15-10 Analizi", 
        "📊 Gelir / Gider Kaydı", 
        "🎯 İlk 1 Milyon TL (Bileşik Kırılma)",
        "📦 Varlık Envanteri",
        "📈 Varlık & Portföy Rebalancing", 
        "☕ Vampir Harcama (Latte Faktörü)",
        "🛡️ Kıyamet Senaryosu (%15 Güvenlik)",
        "❄️ Pasif Gelir Kar Topu",
        "🔮 Maaşlı Çalışmadan Kurtulma Motoru"
    ]
)
st.sidebar.divider()

# ==========================================
# SAYFA 1: KOMUTA MERKEZİ & 25/50/15/10 ANALİZİ
# ==========================================
if page == "🏠 Komuta Merkezi: 25-50-15-10 Analizi":
    st.header("🏠 Finansal Komuta Merkezi")
    st.markdown("Mark Tilbury'nin zenginlik formülü: Gelirinizin **%50'si İhtiyaçlara, %25'i Yatırıma (Büyüme), %15'i Güvenliğe (Acil Durum/Borç), %10'u Ödüllere (Eğlence)** gitmelidir.")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 FreedomOS'a Hoş Geldiniz! Başlamak için lütfen yan menüden **'Gelir / Detaylı Gider Kaydı'** sayfasına gidin.")
    else:
        last_mali = st.session_state.income_expense_history.iloc[-1]
        last_varlik = st.session_state.investment_history.iloc[-1]
        
        net_gelir = float(last_mali['Net Gelir']) if float(last_mali['Net Gelir']) > 0 else 1
        
        # 25/50/15/10 Kategorizasyonu
        actual_essentials = float(last_mali["Kira/Mutfak"]) + float(last_mali["Faturalar"]) + float(last_mali["Ulaşım/Araç"])
        actual_rewards = float(last_mali["Sosyal/Eğlence"]) + float(last_mali["Diğer Giderler"])
        
        net_tasarruf = float(last_mali["Net Tasarruf"])
        if net_tasarruf > 0:
            tas_stab = net_tasarruf * (15.0 / 40.0) # Toplam %40 tasarrufun %15'lik kısmı
            tas_grow = net_tasarruf * (25.0 / 40.0) # Toplam %40 tasarrufun %25'lik kısmı
        else:
            tas_stab = 0
            tas_grow = 0
            
        actual_stability = float(last_mali["Kredi/Borç"]) + tas_stab
        actual_growth = tas_grow
        
        perc_essentials = (actual_essentials / net_gelir) * 100
        perc_rewards = (actual_rewards / net_gelir) * 100
        perc_stability = (actual_stability / net_gelir) * 100
        perc_growth = (actual_growth / net_gelir) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Son Ay Net Gelir", f"{net_gelir:,.0f} TL")
        col2.metric("📉 Son Ay Toplam Gider", f"{float(last_mali['Toplam Gider']):,.0f} TL")
        col3.metric("🚀 Aylık Yatırım (Büyüme)", f"{actual_growth:,.0f} TL")
        col4.metric("👑 Toplam Varlık", f"{float(last_varlik['Toplam Varlık']):,.0f} TL")
        
        st.divider()
        st.subheader("⚖️ 25-50-15-10 Uyumluluk Analizi (Bu Ay)")
        
        # Karşılaştırma Grafiği
        df_kural = pd.DataFrame({
            "Kategori": ["%50 İhtiyaçlar (Essentials)", "%15 Güvenlik & Borç (Stability)", "%25 Büyüme & Yatırım (Growth)", "%10 Ödül & Zevk (Rewards)"],
            "Senin Oranın (%)": [perc_essentials, perc_stability, perc_growth, perc_rewards],
            "Hedeflenen Oran (%)": [50, 15, 25, 10]
        })
        
        fig = px.bar(df_kural, x="Kategori", y=["Senin Oranın (%)", "Hedeflenen Oran (%)"], barmode='group', 
                     title="İdeal Zenginlik Formülü vs Senin Harcamaların",
                     color_discrete_map={"Senin Oranın (%)": "#FF4B4B", "Hedeflenen Oran (%)": "#00CC96"})
        st.plotly_chart(fig, use_container_width=True)
        
        if perc_growth >= 25: st.success("🔥 Mükemmel! Gelirinizin en az %25'ini geleceğinizi satın almak (Büyüme) için kullanıyorsunuz.")
        else: st.warning(f"⚠️ Büyüme (Yatırım) oranınız %{perc_growth:.1f}. Zenginliğe giden yolda Mark Tilbury bu oranın %25 olmasını şart koşar. Harcamaları kısmalısınız.")

# ==========================================
# SAYFA 2: GELİR / GİDER KAYDI
# ==========================================
elif page == "📊 Gelir / Gider Kaydı":
    st.header("📊 25/50/15/10 Gider Kayıt Defteri")
    
    with st.form("gider_formu", clear_on_submit=True):
        period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
        gelir = st.number_input("Aylık Toplam Net Gelir (TL):", min_value=0, value=60000, step=1000)
        
        st.markdown("---")
        st.markdown("### 🏠 %50 İhtiyaçlar (Essentials)")
        col1, col2 = st.columns(2)
        with col1: g_kira = st.number_input("Kira, Ev ve Mutfak (TL):", min_value=0, value=20000, step=500)
        with col2: g_fatura = st.number_input("Faturalar (TL):", min_value=0, value=4000, step=100)
        g_ulasim = st.number_input("Ulaşım ve Araç (TL):", min_value=0, value=3000, step=100)
        
        st.markdown("---")
        st.markdown("### 🛡️ %15 Güvenlik & 🎢 %10 Ödül")
        col3, col4 = st.columns(2)
        with col3: g_kredi = st.number_input("Kredi Kartları / Borç Ödemeleri (TL):", min_value=0, value=5000, step=500)
        with col4: g_sosyal = st.number_input("Sosyal Hayat ve Eğlence (TL):", min_value=0, value=4000, step=100)
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

# ==========================================
# SAYFA 3: YENİ - İLK 1 MİLYON TL MOTORU
# ==========================================
elif page == "🎯 İlk 1 Milyon TL (Bileşik Kırılma)":
    st.header("🎯 İlk 1 Milyon TL ve Bileşik Getirinin Gücü")
    st.markdown("> *\"İlk 100.000 Doları (veya 1 Milyon TL'yi) biriktirmek cehennem gibidir. Ama o barajı aştıktan sonra kar topu o kadar büyür ki, sonraki milyonlar kendiliğinden yuvarlanarak gelir.\"* - Mark Tilbury")
    st.divider()
    
    current_portfolio = float(st.session_state.investment_history.iloc[-1]["Toplam Varlık"]) if not st.session_state.investment_history.empty else 0
    monthly_saving = float(st.session_state.income_expense_history.iloc[-1]["Net Tasarruf"]) if not st.session_state.income_expense_history.empty else 10000
    
    # 25% (Growth) kuralına göre yatırıma giden kısım
    if monthly_saving > 0: monthly_invest = monthly_saving * 0.625 
    else: monthly_invest = 0
    
    st.write(f"**Mevcut Toplam Varlığınız:** {current_portfolio:,.0f} TL")
    
    col1, col2 = st.columns(2)
    with col1: user_invest = st.number_input("Aylık Yatırım Tutarı (Büyüme/Growth) (TL):", min_value=0, value=int(monthly_invest) if monthly_invest>0 else 10000)
    with col2: roi_rate = st.slider("Beklenen Yıllık Getiri (%):", 10, 150, 65)
    
    if st.button("Bileşik Getiri Kırılma Noktasını Hesapla 🚀"):
        m_roi = (1 + roi_rate / 100) ** (1/12) - 1
        port = current_portfolio
        milestones = []
        targets = [1000000, 2000000, 3000000, 4000000, 5000000]
        target_idx = 0
        last_milestone_year = 0
        
        for m in range(1, 1201): # Maksimum 100 yıl projeksiyon
            port = port * (1 + m_roi) + user_invest
            if target_idx < len(targets) and port >= targets[target_idx]:
                current_year = m / 12
                delta_years = current_year - last_milestone_year
                milestones.append({
                    "Hedef Barajı": f"{target_idx + 1}. Milyon TL", 
                    "Sıfırdan Geçecek Süre (Yıl)": current_year,
                    "Gereken Ekstra Zaman (Yıl)": delta_years
                })
                last_milestone_year = current_year
                target_idx += 1
                if target_idx == len(targets): break
                
        if milestones:
            df_mil = pd.DataFrame(milestones)
            st.success("Tebrikler! Bileşik getirinin sihrini grafiksel olarak ispatladık.")
            
            # Ekstra gereken zamanın azaldığını gösteren Çubuk Grafik
            fig = px.bar(df_mil, x="Hedef Barajı", y="Gereken Ekstra Zaman (Yıl)", 
                         text=df_mil["Gereken Ekstra Zaman (Yıl)"].apply(lambda x: f"{x:.1f} Yıl"),
                         title="Her Yeni Milyon İçin Gereken 'Ekstra' Yıl Sayısı (Sürekli Düşüş)",
                         color_discrete_sequence=["#00CC96"])
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **Analiz:** Gördüğünüz gibi ilk milyonu yapmak yıllar alıyor. Ancak paranız sizin için çalışmaya başladığında ikinci, üçüncü ve dördüncü milyonlar arasındaki bekleme süresi dramatik bir şekilde kısalıyor!")
        else:
            st.error("Bu yatırım oranıyla hedeflere ulaşmak çok uzun sürüyor. Aylık yatırımı veya getiriyi artırmalısınız.")

# ==========================================
# SAYFA 4: VARLIK & PORTFÖY REBALANCING
# ==========================================
elif page == "📈 Varlık & Portföy Rebalancing":
    st.header("📈 Canlı Varlık Sepeti ve Akıllı Dengeleme")
    st.markdown("Toplam varlığınızı dengede tutmak Mark Tilbury'nin '%25 Büyüme ve %15 Güvenlik' felsefesinin kalbidir.")
    
    st.sidebar.subheader("🎯 İdeal Portföy Hedefiniz (%)")
    t_nakit = st.sidebar.slider("Hedef Nakit % (Güvenlik)", 0, 100, 15)
    t_hisse = st.sidebar.slider("Hedef Hisse % (Büyüme)", 0, 100, 45)
    t_kripto = st.sidebar.slider("Hedef Kripto % (Büyüme)", 0, 100, 15)
    t_altin = st.sidebar.slider("Hedef Altın % (Büyüme)", 0, 100, 25)
    
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
# SAYFA 5: VAMPİR HARCAMA (LATTE FAKTÖRÜ)
# ==========================================
elif page == "☕ Vampir Harcama (Latte Faktörü)":
    st.header("🧛‍♂️ Vampir Harcama Yüzleşmesi (Latte Faktörü)")
    st.markdown("Kuralın '%10 Ödül' kısmını aşan ve büyümenizi engelleyen küçük kaçamakların uzun vadedeki yıkımını görün.")
    
    col1, col2, col3 = st.columns(3)
    with col1: gunluk_kahve = st.number_input("☕ Günlük Dışarıdan Kahve/Atıştırmalık (TL):", 0, 500, 150)
    with col2: haftalik_yemek = st.number_input("🍔 Haftalık Dışarıdan Yemek Siparişi (TL):", 0, 5000, 1200)
    with col3: aylik_abonelik = st.number_input("📺 Aylık Kullanılmayan Abonelikler (TL):", 0, 2000, 300)
    
    roi_rate = st.slider("Eğer bu parayı harcamayıp (%25 Büyüme fonuna ekleseydin) yıllık getirin ne olurdu?", 10, 150, 65)
    
    aylik_vampir = (gunluk_kahve * 30) + (haftalik_yemek * 4) + aylik_abonelik
    
    if aylik_vampir > 0:
        st.error(f"🩸 **Kan Kaybı Tespit Edildi:** Aylık tam **{aylik_vampir:,.0f} TL** çöpe gidiyor.")
        vampir_data = []
        birikim = 0
        m_roi = (1 + roi_rate / 100) ** (1/12) - 1
        
        for ay in range(1, 361):
            birikim = (birikim + aylik_vampir) * (1 + m_roi)
            if ay % 12 == 0: vampir_data.append({"Yıl": ay//12, "Kayıp Servet (TL)": birikim})

        # Bilgilendirici Mesaj
if aylik_vampir > 0:
    st.success(f"Eğer bu {aylik_vampir:,.0f} TL'yi her ay harcamak yerine yıllık %{int(yillik_getiri_orani*100)} getiri ile yatırıma yönlendirseydin, 10 yıl sonra cebinde **{fv:,.2f} TL** olacaktı. 📉")
else:
    st.info("Vampir harcaması girerek potansiyel kazancını görebilirsin.")
                
        df_vampir = pd.DataFrame(vampir_data)
        st.plotly_chart(px.area(df_vampir, x="Yıl", y="Kayıp Servet (TL)", title=f"%{roi_rate} Getiri İle 30 Yıllık Kayıp Servet Dağı", color_discrete_sequence=["#FF4B4B"]), use_container_width=True)

# ==========================================
# SAYFA 6: KIYAMET SENARYOSU (STRES TESTİ)
# ==========================================
elif page == "🛡️ Kıyamet Senaryosu (%15 Güvenlik)":
    st.header("🛡️ Finansal Kriz ve Hayatta Kalma Stres Testi")
    st.markdown("25/50/15/10 kuralındaki **%15 Güvenlik Fonu**'nun asıl amacı sizi en az 6 ay hayatta tutacak bir Acil Durum Fonu inşa etmektir.")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.warning("Bu testi yapabilmek için lütfen önce Gelir/Gider ve Varlık verilerinizi girin.")
    else:
        last_mali = st.session_state.income_expense_history.iloc[-1]
        last_cash = float(st.session_state.investment_history.iloc[-1]["Nakit Birikim"])
        
        zorunlu_giderler = float(last_mali["Kira/Mutfak"]) + float(last_mali["Faturalar"]) + float(last_mali["Ulaşım/Araç"]) + float(last_mali["Kredi/Borç"])
        
        st.write(f"**Aylık ZORUNLU Gideriniz (%50 İhtiyaçlar + Borçlar):** {zorunlu_giderler:,.0f} TL")
        st.write(f"**Acil Durum Nakitiniz (Banka Mevduatı):** {last_cash:,.0f} TL")
        
        hayatta_kalma_ayi = last_cash / zorunlu_giderler if zorunlu_giderler > 0 else 0
            
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = hayatta_kalma_ayi,
            domain = {'x': [0, 1], 'y': [0, 1]}, title = {'text': "Hayatta Kalma Süresi (Ay)"},
            gauge = {
                'axis': {'range': [None, 12]}, 'bar': {'color': "black"},
                'steps' : [{'range': [0, 3], 'color': "#FF4B4B"}, {'range': [3, 6], 'color': "#FFA500"}, {'range': [6, 12], 'color': "#00CC96"}],
                'threshold' : {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 6}
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        if hayatta_kalma_ayi < 6: st.warning("⚠️ Mark Tilbury 6 aylık güvenliği sağlayana kadar gelirinizin %15'ini buraya aktarmanızı söyler.")
        else: st.success("🛡️ Mükemmel! %15'lik kural görevini tamamlamış. 6 ayı aştığınız için artık nakite değil, %25'lik Büyüme fonuna daha fazla ağırlık verebilirsiniz.")

# ==========================================
# SAYFA 7: PASİF GELİR KAR TOPU
# ==========================================
elif page == "❄️ Pasif Gelir Kar Topu":
    st.header("❄️ Pasif Gelir Kar Topu")
    if st.session_state.investment_history.empty: st.warning("Veri yok.")
    else:
        tot_port = float(st.session_state.investment_history.iloc[-1]["Toplam Varlık"])
        safe_withdrawal_rate = st.slider("Yıllık Pasif Getiri Beklentiniz (%)", 1, 20, 10)
        aylik_pasif = (tot_port * (safe_withdrawal_rate / 100)) / 12
        st.success(f"💸 **Mevcut Portföy Büyüklüğünüz:** {tot_port:,.0f} TL | **Tahmini Aylık Pasif Geliriniz:** {aylik_pasif:,.0f} TL")
        st.divider()
        hedef_kalemler = {"📱 Abonelikler": 400, "☎️ Telefon Faturası": 600, "💪 Spor Salonu": 1500, "⚡ Elektrik/Su": 3000, "🛒 Market/Mutfak": 15000, "🏠 Ev Kirası": 30000}
        for isim, tutar in hedef_kalemler.items():
            st.write(f"**{isim}** (Aylık Tahmini {tutar} TL)")
            if aylik_pasif >= tutar:
                st.progress(100)
                st.caption("✅ BEDAVA! (Yatırımlarınız bu gideri ödüyor)")
            else:
                st.progress(int((aylik_pasif / tutar) * 100))
                st.caption(f"⏳ Yalnızca %{int((aylik_pasif / tutar) * 100)}'si karşılanıyor.")

# ==========================================
# SAYFA 8: MAAŞLI ÇALIŞMADAN KURTULMA MOTORU
# ==========================================
elif page == "🔮 Maaşlı Çalışmadan Kurtulma Motoru":
    st.header("🔮 9-5 İstifa Sayacı & Finansal Özgürlük Projeksiyonu")
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
    if freedom_m != -1: st.success(f"🥳 **Hesaplama Tamamlandı!** Tam **{freedom_m // 12} Yıl {freedom_m % 12} Ay** sonra maaşlı çalışmaktan kalıcı olarak kurtuluyorsunuz!")
    else: st.error("⚠️ Mevcut oranlara göre 30 yıl içinde istifa etmek mümkün görünmüyor.")
    st.plotly_chart(px.line(df_sim, x="Yıl", y=["Varlık", "Pasif Gelir", "Hedef"], title="30 Yıllık Finansal Bağımsızlık Matrisi"), use_container_width=True)
# ==========================================
# SAYFA: 9 VARLIK ENVANTERİ
# ==========================================
elif page == "📦 Varlık Envanteri":
    st.header("📦 Varlık Envanteri")
    
    # 1. Veri Yükleme
    if "inventory_data" not in st.session_state:
        st.session_state.inventory_data = load_data_from_google("Envanter", envanter_cols)
    
    df_env = st.session_state.inventory_data
    
    # 2. Özet Bilgi (Toplam Değer)
    if not df_env.empty:
        total_val = df_env["Güncel Değer"].sum()
        st.metric("Toplam Varlık Değeri", f"{total_val:,.0f} TL")
        st.dataframe(df_env, use_container_width=True)
    
    st.divider()
    
    # 3. Yeni Varlık Ekleme Formu
    st.subheader("➕ Yeni Varlık Ekle")
    with st.form("yeni_varlik_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            varlik_adi = st.text_input("Varlık Adı")
            kategori = st.selectbox("Kategori", ["Gayrimenkul", "Araç", "Değerli Eşya", "Diğer"])
        with col2:
            alis_fiyati = st.number_input("Alış Fiyatı (TL)", min_value=0.0)
            guncel_deger = st.number_input("Güncel Değer (TL)", min_value=0.0)
        
        notlar = st.text_area("Notlar")
        submit = st.form_submit_button("Envantere Ekle")
        
        if submit:
            client = get_gspread_client()
            if client:
                try:
                    sh = client.open_by_url(GOOGLE_SHEET_URL)
                    wks = sh.worksheet("Envanter")
                    if not wks.get_all_values(): wks.append_row(envanter_cols)
                    wks.append_row([varlik_adi, kategori, alis_fiyati, guncel_deger, notlar])
                    st.success("Varlık başarıyla eklendi!")
                    # Veriyi güncelle
                    st.session_state.inventory_data = load_data_from_google("Envanter", envanter_cols)
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata oluştu: {e}")
