import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from sklearn.linear_model import LinearRegression

# Sayfa Genişlik ve Tema Ayarı
st.set_page_config(page_title="WealthOS - Kişisel Varlık Yönetim Sistemi", layout="wide", page_icon="💼")

# --- HAFIZA (SESSION STATE) KURULUMU ---
if "income_expense_history" not in st.session_state:
    st.session_state.income_expense_history = pd.DataFrame(columns=[
        "Dönem/Ay", "Net Gelir", "Kira/Mutfak", "Faturalar", "Kredi/Borç", 
        "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler", "Toplam Gider", "Net Tasarruf"
    ])

if "investment_history" not in st.session_state:
    st.session_state.investment_history = pd.DataFrame(columns=[
        "Dönem/Ay", "Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia", "Toplam Varlık"
    ])

# --- SOL PANEL: SAYFA SEÇİCİ NAVİGASYON ---
st.sidebar.title("💼 WealthOS v2.0")
st.sidebar.markdown("*Alpi Standartlarında Kişiselleştirilmiş Finansal Yönetim Paneli*")
st.sidebar.divider()

page = st.sidebar.radio(
    "Gitmek İstediğiniz Sayfa:",
    ["🏠 Genel Durum & Özet Paneli", "📊 Gelir / Detaylı Gider Kaydı", "📈 Varlık & Yatırım Takibi", "🔮 İleri Yönelik Öngörü & Yapay Zeka"]
)

st.sidebar.divider()

# --- SAYFA 1: GENEL DURUM & ÖZET PANELİ ---
if page == "🏠 Genel Durum & Özet Paneli":
    st.header("🏠 Finansal Durum Özet Paneli")
    st.markdown("Sisteminizdeki güncel mali verilerin ve varlık dağılımlarınızın anlık izdüşümü.")
    
    if st.session_state.income_expense_history.empty or st.session_state.investment_history.empty:
        st.info("👋 FreedomOS'a Hoş Geldiniz! Sistemde henüz geçmiş veri kaydı bulunmuyor. Başlamak için lütfen sol menüden **'Gelir / Detaylı Gider Kaydı'** ve **'Varlık & Yatırım Takibi'** sayfalarına giderek ilk veri girişlerinizi yapın.")
    else:
        last_month_mali = st.session_state.income_expense_history.iloc[-1]
        last_month_varlik = st.session_state.investment_history.iloc[-1]
        
        # KPI Kartları
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Son Ay Net Gelir", f"{last_month_mali['Net Gelir']:,.0f} TL")
        col2.metric("📉 Son Ay Toplam Gider", f"{last_month_mali['Toplam Gider']:,.0f} TL", delta=f"-{last_month_mali['Toplam Gider']/last_month_mali['Net Gelir']*100:.1f}% Gelire Oranı", delta_color="inverse")
        col3.metric("🚀 Aylık Tasarruf Gücü", f"{last_month_mali['Net Tasarruf']:,.0f} TL")
        col4.metric("👑 Toplam Varlık Büyüklüğü", f"{last_month_varlik['Toplam Varlık']:,.0f} TL")
        
        st.divider()
        st.subheader("📊 Grafiksel Analizler")
        
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("**Gider Dağılım Analizi (Son Ay)**")
            gider_labels = ["Kira/Mutfak", "Faturalar", "Kredi/Borç", "Ulaşım/Araç", "Sosyal/Eğlence", "Diğer Giderler"]
            gider_values = [last_month_mali[l] for l in gider_labels]
            fig_gider = px.pie(names=gider_labels, values=gider_values, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_gider, use_container_width=True)
            
        with g2:
            st.markdown("**Yatırım Portföyü Dağılımı (Son Ay)**")
            varlik_labels = ["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"]
            varlik_values = [last_month_varlik[l] for l in varlik_labels]
            fig_varlik = px.pie(names=varlik_labels, values=varlik_values, hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
            st.plotly_chart(fig_varlik, use_container_width=True)

# --- SAYFA 2: GELİR / DETAYLI GİDER KAYDI ---
elif page == "📊 Gelir / Detaylı Gider Kaydı":
    st.header("📊 Detaylı Gelir ve Gider Kayıt Defteri")
    st.markdown("Her ay değişen gelir ve kapsamlı gider kalemlerinizi buraya işleyerek tarihsel veri tabanınızı oluşturun.")
    
    with st.form("gider_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            period = st.text_input("Dönem / Ay Seçimi (Örn: Ocak 2026, Şubat 2026):", value=datetime.now().strftime("%B %Y"))
            gelir = st.number_input("Aylık Toplam Net Gelir (TL):", min_value=0, value=60000, step=1000)
            g_kira = st.number_input("Kira, Ev and Mutfak Harcamaları (TL):", min_value=0, value=20000, step=500)
            g_fatura = st.number_input("Faturalar (Elektrik, Su, İnternet, Telefon vb.) (TL):", min_value=0, value=4000, step=100)
        with col2:
            g_kredi = st.number_input("Kredi Kartları, Kredi Ödemeleri ve Borçlar (TL):", min_value=0, value=5000, step=500)
            g_ulasim = st.number_input("Ulaşım, Yakıt ve Araç Masrafları (TL):", min_value=0, value=3000, step=100)
            g_sosyal = st.number_input("Sosyal Hayat, Eğlence ve Dışarıda Yeme-İçme (TL):", min_value=0, value=4000, step=100)
            g_diger = st.number_input("Diğer / Beklenmedik Harcamalar (TL):", min_value=0, value=2000, step=100)
            
        submit_mali = st.form_submit_button("💰 Ay Kaydını Veri Tabanına İşle")
        
    if submit_mali:
        toplam_gider = g_kira + g_fatura + g_kredi + g_ulasim + g_sosyal + g_diger
        net_tasarruf = gelir - toplam_gider
        
        yeni_satir = pd.DataFrame([{
            "Dönem/Ay": period, "Net Gelir": gelir, "Kira/Mutfak": g_kira, "Faturalar": g_fatura, 
            "Kredi/Borç": g_kredi, "Ulaşım/Araç": g_ulasim, "Sosyal/Eğlence": g_sosyal, 
            "Diğer Giderler": g_diger, "Toplam Gider": toplam_gider, "Net Tasarruf": net_tasarruf
        }])
        
        st.session_state.income_expense_history = pd.concat([st.session_state.income_expense_history, yeni_satir], ignore_index=True)
        st.success(f"✔️ {period} dönemi finansal verileri başarıyla sisteme kaydedildi!")

    st.divider()
    st.subheader("📚 Geçmiş Zaman Gelir/Gider Günlükleri")
    if not st.session_state.income_expense_history.empty:
        st.dataframe(st.session_state.income_expense_history, use_container_width=True)
        
        fig_trend = px.bar(st.session_state.income_expense_history, x="Dönem/Ay", y=["Net Gelir", "Toplam Gider", "Net Tasarruf"],
                           barmode="group", title="Aylar Arası Finansal Dönüşüm Trendiniz")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Kayıtlı veri bulunmuyor.")
# --- SAYFA 3: VARLIK & YATIRIM TAKİBİ ---
elif page == "📈 Varlık & Yatırım Takibi":
    st.header("📈 Canlı Varlık ve Yatırım Sepeti Yönetimi")
    st.markdown("Her ay kenara ayırdığınız nakitleri ve büyüyen yatırım portföyünüzü sınıflara ayırarak takip edin.")
    
    with st.form("varlik_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            v_period = st.text_input("Dönem / Ay Seçimi:", value=datetime.now().strftime("%B %Y"))
            v_nakit = st.number_input("Banka Mevduatı / Nakit Birikim (TL):", min_value=0, value=30000)
            v_hisse = st.number_input("Borsa / Hisse Senedi Portföy Değeri (TL):", min_value=0, value=80000)
        with col2:
            v_kripto = st.number_input("Kripto Para Portföy Değeri (TL):", min_value=0, value=40000)
            v_altin = st.number_input("Altın, Gümüş ve Fiziki Emtialar (TL):", min_value=0, value=50000)
            
        submit_varlik = st.form_submit_button("📈 Varlık Durumunu Günlüğe Ekle")
        
    if submit_varlik:
        toplam_varlik = v_nakit + v_hisse + v_kripto + v_altin
        yeni_varlik_satir = pd.DataFrame([{
            "Dönem/Ay": v_period, "Nakit Birikim": v_nakit, "Hisse Senedi": v_hisse, 
            "Kripto Para": v_kripto, "Altın/Emtia": v_altin, "Toplam Varlık": toplam_varlik
        }])
        st.session_state.investment_history = pd.concat([st.session_state.investment_history, yeni_varlik_satir], ignore_index=True)
        st.success(f"✔️ {v_period} dönemi portföy varlık envanteri başarıyla kilitlendi!")

    st.divider()
    st.subheader("⏳ Tarihsel Varlık Büyüme Günlüğü")
    if not st.session_state.investment_history.empty:
        st.dataframe(st.session_state.investment_history, use_container_width=True)
        
        fig_growth = px.area(st.session_state.investment_history, x="Dönem/Ay", y=["Nakit Birikim", "Hisse Senedi", "Kripto Para", "Altın/Emtia"],
                             title="Varlıklarınızın Zamana Göre Kümülant Kartografisi (Büyüme Hızı)")
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.info("Kayıtlı portföy geçmişi bulunmuyor.")

# --- SAYFA 4: İLERİ YÖNELİK ÖNGÖRÜ & YAPAY ZEKA ---
elif page == "🔮 İleri Yönelik Öngörü & Yapay Zeka":
    st.header("🔮 Gelecek Simülasyonu ve Finansal Özgürlük Analizi")
    st.markdown("Bu sayfa, geçmiş verilerinizden makine öğrenmesi ve finansal algoritmalar kullanarak ne zaman istifa edebileceğinizi hesaplar.")
    
    st.subheader("⚙️ Projeksiyon Parametreleri")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        inf_rate = st.slider("Yıllık Ortalama Enflasyon Tahmini (%):", 0, 100, 35)
    with sc2:
        sal_rate = st.slider("Yıllık Maaş / Gelir Artış Kriteriniz (%):", 0, 100, 45)
    with sc3:
        roi_rate = st.slider("Yatırımların Yıllık Ortalama Getiri Potansiyeli (%):", 0, 150, 65)
        
    target_p = st.number_input("Maaşlı Köleliği Bırakmak İçin Hedeflenen Aylık Pasif Gelir (Bugünün Parasıyla TL):", min_value=1000, value=50000)
    st.divider()
    
    if len(st.session_state.income_expense_history) >= 2 and len(st.session_state.investment_history) >= 1:
        st.subheader("🤖 Yapay Zeka Trend Çıkarımı")
        
        df_mali = st.session_state.income_expense_history
        X = np.array(range(len(df_mali))).reshape(-1, 1)
        y = df_mali["Toplam Gider"].values
        model = LinearRegression().fit(X, y)
        artis_egilimi = model.coef_
        
        if artis_egilimi > 0:
            st.warning(f"⚠️ Gider Analizi: Geçmiş kayıtlarınıza göre aylık harcamalarınız her ay ortalama {artis_egilimi:,.2f} TL artma eğiliminde. Tasarruf oranınızı korumak için lüks tüketimi kısmalısınız.")
        else:
            st.success(f"📈 Gider Analizi: Harika! Geçmiş kayıtlarınız harcamalarınızı kontrol altında tuttuğunuzu veya düşürdüğünüzü (Ayda ortalama {abs(artis_egilimi):,.2f} TL düşüş) gösteriyor.")
            
        current_portfolio = st.session_state.investment_history.iloc[-1]["Toplam Varlık"]
        base_income = df_mali.iloc[-1]["Net Gelir"]
        base_expense = df_mali.iloc[-1]["Toplam Gider"]
        
        sim_months = 360  
        freedom_m = -1
        sim_data = []
        
        for m in range(1, sim_months + 1):
            if m > 1 and m % 12 == 1:
                base_income *= (1 + sal_rate / 100)
                base_expense *= (1 + inf_rate / 100)
                target_p *= (1 + inf_rate / 100)
                
            monthly_saving = base_income - base_expense
            if monthly_saving < 0: 
                monthly_saving = 0
            
            m_roi = (1 + roi_rate / 100) ** (1/12) - 1
            current_portfolio = current_portfolio * (1 + m_roi) + monthly_saving
            
            passive_gen = (current_portfolio * 0.04) / 12
            
            if passive_gen >= target_p and freedom_m == -1:
                freedom_m = m
                
            sim_data.append({"Ay": m, "Yıl": round(m/12, 1), "Varlık": current_portfolio, "Pasif Gelir": passive_gen, "Hedef": target_p})
            
        df_sim = pd.DataFrame(sim_data)
        
        st.subheader("🔮 Özgürlük Projeksiyon Sonucu")
        if freedom_m != -1:
            st.balloons()
            st.success(f"🥳 Yapay Zeka Hesaplaması Tamamlandı! Mevcut finansal disiplininiz doğrultusunda tam {freedom_m // 12} Yıl {freedom_m % 12} Ay sonra finansal özgürlüğünüze kavuşuyorsunuz!")
            st.info(f"O tarihteki toplam net korumalı servet büyüklüğünüz: {df_sim.loc[freedom_m-1, 'Varlık']:,.0f} TL olacaktır.")
        else:
            st.error("⚠️ Mevcut oranlar simülasyonu 30 yıl içerisinde hedefinize ulaşmanıza izin vermiyor. Yatırımlarınızın yıllık brüt getiri hedefini büyütmeniz şart.")
            
        fig_sim = px.line(df_sim, x="Yıl", y=["Varlık", "Pasif Gelir", "Hedef"], title="30 Yıllık Gelecek Matrisi Simülasyonu")
        st.plotly_chart(fig_sim, use_container_width=True)
        
    else:
        st.warning("🔮 Yapay zeka tahminleme motorunun çalışabilmesi için 'Gelir/Gider' ve 'Varlık' sayfalarından en az 2 farklı aya ait zaman kaydı girişi yapmanız gerekmektedir.")
