import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Sayfa Genişlik ve Tema Ayarı
st.set_page_config(page_title="Gelişmiş Finansal Özgürlük Asistanı", layout="wide")

st.title("💰 Mark Tilbury & Kişiselleştirilmiş Varlık Yönetimi Asistanı")
st.markdown("*Önceki planlama kriterleriniz ve enflasyon canavarı hesaba katılarak güncellenmiş dinamik simülatör.*")

# --- SOL PANEL: GELİR VE GİDER DETAYLARI ---
st.sidebar.header("📊 1. Gelir & Gider Girişi")
monthly_income = st.sidebar.number_input("Aylık Net Maaş / Geliriniz (TL):", min_value=1000, value=60000, step=1000)
monthly_expense = st.sidebar.number_input("Aylık Toplam Zorunlu Giderleriniz (TL):", min_value=0, value=30000, step=1000)

# Kalan tasarruf miktarı otomatik hesaplanır
potential_savings = monthly_income - monthly_expense
st.sidebar.info(f"💵 Şu Anki Aylık Net Tasarruf Potansiyeliniz: **{potential_savings:,.0f} TL**")

st.sidebar.header("🛡️ 2. Mevcut Varlıklar")
current_savings = st.sidebar.number_input("Mevcut Birikim / Nakit (TL):", min_value=0, value=50000)
current_investments = st.sidebar.number_input("Mevcut Yatırım Portföyü (Hisse, Kripto vb.) (TL):", min_value=0, value=150000)

st.sidebar.header("📈 3. Enflasyon & Ekonomik Tahminler")
annual_inflation = st.sidebar.slider("Yıllık Beklenen Ortalama Enflasyon (%):", 0, 100, 35)
annual_salary_growth = st.sidebar.slider("Yıllık Maaş Artış Oranınız (%):", 0, 100, 40)
annual_investment_roi = st.sidebar.slider("Yıllık Brüt Yatırım Getiri Beklentisi (%):", 0, 150, 60)

st.sidebar.header("🎯 4. Özgürlük Hedefi")
desired_passive_income_today = st.sidebar.number_input("Maaşlı Çalışmadan Kurtulmak İçin Gereken Aylık Gelir (Bugünün Parasıyla TL):", min_value=1000, value=45000)

# --- MATEMATİKSEL PLANLAMA & SİMÜLASYON ---
# Mark Tilbury İdeal Dağılım Hesaplama (Maaş üzerinden)
tilbury_growth = monthly_income * 0.25
tilbury_stability = monthly_income * 0.15
tilbury_essentials = monthly_income * 0.50
tilbury_rewards = monthly_income * 0.10

st.subheader("📌 Mark Tilbury Kuralına Göre Mevcut Durum Analiziniz")
c1, c2, c3, c4 = st.columns(4)
c1.metric("🚀 %25 Büyüme (Yatırım Hedefi)", f"{tilbury_growth:,.0f} TL", f"Mevcut Tasarruf: {potential_savings:,.0f} TL")
c2.metric("🛡️ %15 İstikrar (Acil Durum)", f"{tilbury_stability:,.0f} TL")
c3.metric("🏠 %50 Temel İhtiyaç Sınırı", f"{tilbury_essentials:,.0f} TL", f"Mevcut Gider: {monthly_expense:,.0f} TL", delta_color="inverse")
c4.metric("🎉 %10 Ödül Bütçesi", f"{tilbury_rewards:,.0f} TL")

st.divider()

# --- GELECEĞE YÖNELİK 30 YILLIK REEL SİMÜLASYON ---
years = 30
months = years * 12

portfolio = current_investments + current_savings
current_income = monthly_income
current_expense = monthly_expense
target_passive = desired_passive_income_today

freedom_month = -1
sim_records = []

for month in range(1, months + 1):
    # Her yıl başında Enflasyon, Maaş Zammı ve Gider Artışları yansıtılır
    if month > 1 and month % 12 == 1:
        current_income *= (1 + annual_salary_growth / 100)
        current_expense *= (1 + annual_inflation / 100)
        target_passive *= (1 + annual_inflation / 100)
    
    # Aylık net tasarruf hesabı (Maaş - Gider)
    monthly_saving = current_income - current_expense
    if monthly_saving < 0:
        monthly_saving = 0 # Gider geliri aşarsa tasarruf sıfırlanır
        
    # Aylık bileşik yatırım getirisi ekleme
    monthly_roi_rate = (1 + annual_investment_roi / 100) ** (1/12) - 1
    portfolio = portfolio * (1 + monthly_roi_rate) + monthly_saving
    
    # Portföyün ürettiği sürdürülebilir aylık pasif gelir (%4 Kuralı)
    generated_passive_income = (portfolio * 0.04) / 12
    
    # Maaşlı çalışmadan kurtulma (Finansal Özgürlük) Kontrolü
    if generated_passive_income >= target_passive and freedom_month == -1:
        freedom_month = month
        
    sim_records.append({
        "Ay": month,
        "Yıl": round(month / 12, 1),
        "Toplam Portföy Büyüklüğü (TL)": portfolio,
        "Sizin Ürettiğiniz Pasif Gelir (TL)": generated_passive_income,
        "Enflasyonlu Hedef Pasif Gelir (TL)": target_passive
    })

df_result = pd.DataFrame(sim_records)

# --- SONUÇ RAPORLAMA ---
st.subheader("🔮 Önceki Konuşma Kriterlerine Göre Özgürlük Öngörüsü")

if freedom_month != -1:
    f_years = freedom_month // 12
    f_months = freedom_month % 12
    st.success(f"🎉 **Plan Başarılı! Maaşlı işinizden tam {f_years} yıl {f_months} ay sonra tamamen kurtulabilirsiniz!**")
    st.info(f"Finansal özgürlük gününüzde toplam birikmiş varlığınız **{df_result.loc[freedom_month-1, 'Toplam Portföy Büyüklüğü (TL)']:,.0f} TL** değerine ulaşmış olacak.")
else:
    st.warning("⚠️ Dikkat! Mevcut gider artış hızınız ve yatırım getiri oranınız, yükselen enflasyon karşısında 30 yıl içinde finansal özgürlüğe ulaşmanıza yetmiyor. Yatırım sepetinizi daha yüksek getirili varlıklarla güçlendirmeniz gerekebilir.")

# Grafik Alanı
st.subheader("📈 Enflasyon Karşısında Varlıklarınızın Büyüme Grafiği")
fig_line = px.line(df_result, x="Yıl", y=["Toplam Portföy Büyüklüğü (TL)", "Sizin Ürettiğiniz Pasif Gelir (TL)", "Enflasyonlu Hedef Pasif Gelir (TL)"],
                   title="Yıllara Göre Portföy ve Pasif Gelir Dengesi",
                   labels={"value": "Tutar (TL)", "variable": "Finansal Göstergeler"})
st.plotly_chart(fig_line, use_container_width=True)

# Asistan Önerileri Paneli
st.subheader("💡 Yapay Zeka Asistanınızdan İleriye Dönük Tavsiyeler")
st.markdown(f"""
* **Reel Getiri Gerçeği:** Yatırım getiri oranınız (%{annual_investment_roi}), enflasyon oranınızdan (%{annual_inflation}) yüksek olduğu sürece paranız değer kazanır. Aradaki fark kapandığı an finansal özgürlük süreniz uzayacaktır.
* **Gider Kontrolü:** Şu anki aylık gideriniz olan **{monthly_expense:,.0f} TL** enflasyon oranında artmaktadır. Eğer harcamalarınızı enflasyonun altında tutmayı başarırsanız, sistemdeki özgürlük süreniz tahmin edilenden çok daha kısa sürecektir.
* **Maaş Artış Kaldıracı:** Maaş artış beklentiniz (%{annual_salary_growth}), enflasyonun üzerinde kaldığı sürece yaşam standardınızı değiştirmeden tasarruf oranınızı agresif şekilde büyütebilirsiniz.
""")
