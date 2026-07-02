import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Sayfa Genişlik ve Tema Ayarı
st.set_page_config(page_title="Mark Tilbury Finansal Özgürlük Asistanı", layout="wide")

st.title("💰 Mark Tilbury Tarzı Varlık Yönetimi ve Özgürlük Simülatörü")
st.markdown("*"99% insan finansal sistemin kölesi olur çünkü geleceği planlamaz. Bugün bunu değiştiriyoruz!*")

# --- SOL PANEL: GİRDİLER ---
st.sidebar.header("📋 Finansal Verileriniz")
income = st.sidebar.number_input("Aylık Net Geliriniz (TL):", min_value=1000, value=50000, step=1000)
current_assets = st.sidebar.number_input("Mevcut Yatırım Varlıklarınız Toplamı (TL):", min_value=0, value=100000, step=5000)

st.sidebar.subheader("📈 Gelecek ve Enflasyon Tahminleri")
inflation_rate = st.sidebar.slider("Yıllık Ortalama Enflasyon Beklentisi (%):", 0, 100, 35)
salary_increase = st.sidebar.slider("Yıllık Maaş Artış Beklentiniz (%):", 0, 100, 40)
investment_return = st.sidebar.slider("Yıllık Ortalama Yatırım Getirisi (%):", 0, 150, 55)

st.sidebar.subheader("🎯 Hedef")
target_monthly_passive_income = st.sidebar.number_input("İşten Ayrılmak İçin Gereken Aylık Pasif Gelir (Bugünün Parasıyla TL):", min_value=1000, value=40000)

# --- MATEMATİKSEL HESAPLAMALAR (Mark Tilbury 25/15/50/10 Kuralı) ---
growth_pot = income * 0.25      # %25 Büyüme (Yatırım)
stability_pot = income * 0.15   # %15 İstikrar (Acil Durum Fonu)
essentials_pot = income * 0.50  # %50 İhtiyaçlar
rewards_pot = income * 0.10     # %10 Ödüller / Eğlence

# KPI Göstergeleri
col1, col2, col3, col4 = st.columns(4)
col1.metric("🚀 %25 Büyüme (Aylık Yatırım)", f"{growth_pot:,.0f} TL")
col2.metric("🛡️ %15 İstikrar (Güvenlik)", f"{stability_pot:,.0f} TL")
col3.metric("🏠 %50 Temel İhtiyaç Sınırı", f"{essentials_pot:,.0f} TL")
col4.metric("🎉 %10 Ödül (Suçluluk Duymadan Harca)", f"{rewards_pot:,.0f} TL")

st.divider()

# --- 30 YILLIK GELECEK ÖNGÖRÜ SİMÜLASYONU ---
years = 30
months = years * 12

sim_data = []
current_portfolio = current_assets
current_monthly_income = income
current_monthly_growth_investment = growth_pot
current_target_passive = target_monthly_passive_income

freedom_month = -1

for month in range(1, months + 1):
    # Her yıl başında enflasyon ve maaş zamları uygulanır
    if month > 1 and month % 12 == 1:
        current_monthly_income *= (1 + salary_increase / 100)
        current_monthly_growth_investment = current_monthly_income * 0.25
        current_target_passive *= (1 + inflation_rate / 100)
    
    # Aylık yatırım getirisi eklenir (Yıllık getirinin aylık bileşiği)
    monthly_return_rate = (1 + investment_return / 100) ** (1/12) - 1
    current_portfolio = current_portfolio * (1 + monthly_return_rate) + current_monthly_growth_investment
    
    # Mevcut portföyün üretebileceği GÜVENLİ AYLIK PASİF GELİR (%4 kuralı baz alınmıştır)
    # Portföyün yıllık %4'ünün enflasyondan arındırılmış aylık getirisi
    safe_monthly_passive_income = (current_portfolio * 0.04) / 12
    
    # Özgürlük kontrolü: Pasif gelir, enflasyonla büyütülmüş hedefi geçiyor mu?
    if safe_monthly_passive_income >= current_target_passive and freedom_month == -1:
        freedom_month = month
        
    sim_data.append({
        "Ay": month,
        "Yıl": round(month / 12, 1),
        "Toplam Varlık (TL)": current_portfolio,
        "Üretilen Aylık Pasif Gelir (TL)": safe_monthly_passive_income,
        "Gereken Hedef Pasif Gelir (TL)": current_target_passive
    })

df_sim = pd.DataFrame(sim_data)

# --- ÖNGÖRÜ VE RAPORLAMA ---
st.subheader("🔮 Finansal Özgürlük Analiziniz")

if freedom_month != -1:
    freedom_years = freedom_month // 12
    freedom_remaining_months = freedom_month % 12
    st.success(f"🥳 **Müjde dostum! Maaşlı çalışmaktan tam {freedom_years} yıl {freedom_remaining_months} ay sonra kurtulabilirsin!**")
    st.info(f"O tarihte toplam varlığınız yaklaşık **{df_sim.loc[freedom_month-1, 'Toplam Varlık (TL)']:,.0f} TL** seviyesine ulaşacak ve size sürdürülebilir bir özgürlük sunacaktır.")
else:
    st.warning("⚠️ Mevcut yatırım oranınız ve getiri tahminlerinizle 30 yıl içinde tam özgürlüğe ulaşılamıyor. Ya getirinizi artırmalı ya da giderlerinizi kısmalısınız!")

# Grafik Çizimi
st.subheader("📈 Varlıklarınızın Zaman İçindeki Değişimi")
fig = px.line(df_sim, x="Yıl", y=["Toplam Varlık (TL)"], 
              title="Enflasyon ve Getiri Odaklı Gelecek Varlık Projeksiyonu",
              labels={"value": "Tutar (TL)", "variable": "Gösterge"})
st.plotly_chart(fig, use_container_width=True)

# İleriye Dönük Stratejik Öneriler Paneli
st.subheader("💡 Mark Tilbury'den İleriye Dönük Tavsiyeler")
st.markdown(f"""
1. **Acil Durum Fonunu Kilitle:** Aylık temel giderin olan **{essentials_pot:,.0f} TL** baz alındığında, seni en az 5 ay mermisiz bırakmayacak **{(essentials_pot * 5):,.0f} TL** istikrar fonunu nakit benzeri risksiz bir hesapta biriktirene kadar yatırımlarında agresifleşme.
2. **Enflasyon Canavarına Dikkat Et:** Yıllık %{inflation_rate} enflasyon tahminine karşı yatırımlarının (BIST, Amerikan Borsası veya Emtia) mutlaka bu oranın üzerinde getiri sağlaması gerekiyor. Paran vadeli hesapta erimemeli!
3. **Gelirini Artır, Harcamayı Sabitle:** Maaşına %{salary_increase} zam geldiğinde yaşam standardını hemen yükseltme (Lifestyle Creep). O ekstra parayı doğrudan %25'lik Büyüme potuna aktar ki yukarıdaki özgürlük süren daha da kısalsın!
""")
