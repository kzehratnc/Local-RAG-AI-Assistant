import sqlite3
import json
import math
import streamlit as st
import PyPDF2
import pandas as pd
from foundry_local_sdk import Configuration, FoundryLocalManager

# --- ARAYÜZ TASARIM AYARLARI ---
st.set_page_config(page_title="RAG Asistanı", page_icon="⚙️", layout="centered")
st.title("⚙️ Yerel RAG Asistanı")

# --- RAG AYARLARI ---
SOHBET_MODELI = "phi-3.5-mini"
EMBEDDING_MODELI = "qwen3-embedding-0.6b"

TOP_K = 3                   
BENZERLIK_ESIGI = 0.35        

# --- MATEMATİKSEL HESAPLAMA ---
def kosinus_benzerligi(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0: return 0.0
    return dot_product / (mag1 * mag2)

# --- SİSTEMİ HAZIRLAMA ---
@st.cache_resource
def sistem_hazirla():
    config = Configuration(app_name="RAG_Projesi")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance
    
    emb_model = manager.catalog.get_model(EMBEDDING_MODELI)
    emb_model.load()
    emb_client = emb_model.get_embedding_client()
    
    chat_model = manager.catalog.get_model(SOHBET_MODELI)
    chat_model.load() 
    chat_client = chat_model.get_chat_client()
    chat_client.settings.temperature = 0.1
    chat_client.settings.max_tokens = 400
    
    return emb_client, chat_client

with st.spinner("Modeller belleğe yükleniyor, lütfen bekleyin..."):
    emb_client, chat_client = sistem_hazirla()

# --- SEKMELER (TABS) ---
tab1, tab2 = st.tabs(["💬 Soru-Cevap", "📂 Veritabanı Yönetimi"])

# ==========================================
# 1. SEKME: SORU-CEVAP
# ==========================================
with tab1:
    st.markdown("Veritabanındaki dokümanlara dayanarak sorularınızı sorun.")
    soru = st.text_input("Dokümanlarda ne aramak istiyorsunuz?", placeholder="Yazınız...")

    if st.button("Soruyu Cevapla", type="primary"):
        if soru:
            with st.spinner("Veritabanı taranıyor ve cevap üretiliyor..."):
                soru_vektor = emb_client.generate_embeddings([soru]).data[0].embedding
                
                conn = sqlite3.connect("rag_veritabani.db", timeout=10)
                cursor = conn.cursor()
                cursor.execute("SELECT metin, vektor FROM belgeler")
                kayitlar = cursor.fetchall()
                conn.close()
                
                # Tüm kayıtlar için skor hesapla, en iyi TOP_K taneyi al
                skorlu_kayitlar = []
                for kayit in kayitlar:
                    metin = kayit[0]
                    db_vektor = json.loads(kayit[1])
                    skor = kosinus_benzerligi(soru_vektor, db_vektor)
                    skorlu_kayitlar.append((skor, metin))
                
                skorlu_kayitlar.sort(key=lambda x: x[0], reverse=True)
                en_iyi_kayitlar = skorlu_kayitlar[:TOP_K]
                en_yuksek_skor = en_iyi_kayitlar[0][0] if en_iyi_kayitlar else -1
                
                if not en_iyi_kayitlar or en_yuksek_skor < BENZERLIK_ESIGI:
                    st.success("İşlem Tamamlandı!")
                    st.markdown("### 🤖 Asistanın Cevabı:")
                    st.warning(
                        "Bu soruyla yeterince ilgili bir bilgi veritabanında bulamadım. "
                        "Lütfen sorunuzu veritabanındaki dokümanlarla ilgili tekrar sorun "
                        "ya da önce ilgili dokümanı yükleyin."
                    )
                else:
                    baglam = "\n\n---\n\n".join(
                        f"[Kaynak {i+1}] {metin}" for i, (skor, metin) in enumerate(en_iyi_kayitlar)
                    )

                    sistem_mesaji = (
                        "Sen bir doküman soru-cevap asistanısın. Sana verilen 'Bağlam' içindeki "
                        "bilgilere dayanarak 'Soru'yu Türkçe olarak, kısa ve net şekilde cevapla. "
                        "Sadece bağlamdaki bilgiyi kullan, bağlamda olmayan hiçbir şey uydurma. "
                        "Eğer cevap bağlamda yoksa, kesinlikle 'Bu bilgi elimdeki dokümanlarda yok.' "
                        "de ve başka bir şey söyleme."
                    )

                    birlestirilmis_istek = f"Bağlam:\n{baglam}\n\nSoru: {soru}"
                    messages = [
                        {"role": "system", "content": sistem_mesaji},
                        {"role": "user", "content": birlestirilmis_istek}
                    ]
                    
                    cevap = chat_client.complete_chat(messages)
                    
                    st.success("İşlem Tamamlandı!")
                    st.markdown("### 🤖 Asistanın Cevabı:")
                    st.info(cevap.choices[0].message.content)
                    
                    with st.expander(f"Arka Planda Bulunan Kaynak Metinler (En yüksek skor: {en_yuksek_skor:.2f})"):
                        for i, (skor, metin) in enumerate(en_iyi_kayitlar):
                            st.markdown(f"**Kaynak {i+1} — skor: {skor:.2f}**")
                            st.write(metin)

# ==========================================
# 2. SEKME: VERİTABANI YÖNETİMİ
# ==========================================
with tab2:
    st.markdown("### 📁 Dosya Yükle (PDF / Excel)")
    yuklenen_dosya = st.file_uploader("Sisteme eklenecek PDF veya Excel dosyasını seçin", type=["pdf", "xlsx"])
    
    if st.button("Dosyayı İşle ve Veritabanına Ekle", type="primary"):
        if yuklenen_dosya is not None:
            with st.spinner("Dosya okunuyor ve yapay zeka için işleniyor..."):
                cikartilan_metinler = []
                
                if yuklenen_dosya.name.endswith('.pdf'):
                    pdf_okuyucu = PyPDF2.PdfReader(yuklenen_dosya)
                    for sayfa in pdf_okuyucu.pages:
                        sayfa_metni = sayfa.extract_text()
                        if sayfa_metni:
                            paragraflar = [p.strip() for p in sayfa_metni.split("\n\n") if len(p.strip()) > 10]
                            cikartilan_metinler.extend(paragraflar)
                
                elif yuklenen_dosya.name.endswith('.xlsx'):
                    df = pd.read_excel(yuklenen_dosya)
                    for index, row in df.iterrows():
                        satir_metni = " - ".join([str(val) for val in row.values if pd.notna(val)])
                        if len(satir_metni.strip()) > 5:
                            cikartilan_metinler.append(satir_metni)
                
                if cikartilan_metinler:
                    conn = sqlite3.connect("rag_veritabani.db", timeout=10)
                    cursor = conn.cursor()
                    
                    for p in cikartilan_metinler:
                        vektor = emb_client.generate_embeddings([p]).data[0].embedding
                        cursor.execute("INSERT INTO belgeler (metin, vektor) VALUES (?, ?)", (p, json.dumps(vektor)))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"Başarılı! Dosyadan {len(cikartilan_metinler)} farklı bilgi çıkarıldı ve sisteme eklendi.")
                else:
                    st.warning("Dosyadan metin çıkarılamadı. Dosyanın boş olmadığından veya taranabilir olduğundan emin olun.")
        else:
            st.warning("Lütfen önce bir dosya seçin.")

    st.divider()
    
    st.markdown("### 📝 Manuel Metin Ekle")
    yeni_metin = st.text_area("Kopyaladığınız bir yazıyı buraya yapıştırabilirsiniz:", height=100)
    if st.button("Metni Kaydet"):
        if yeni_metin.strip():
            with st.spinner("Metin kaydediliyor..."):
                paragraflar = [p.strip() for p in yeni_metin.split("\n\n") if p.strip()]
                conn = sqlite3.connect("rag_veritabani.db", timeout=10)
                cursor = conn.cursor()
                for p in paragraflar:
                    vektor = emb_client.generate_embeddings([p]).data[0].embedding
                    cursor.execute("INSERT INTO belgeler (metin, vektor) VALUES (?, ?)", (p, json.dumps(vektor)))
                conn.commit()
                conn.close()
            st.success("Metin başarıyla eklendi.")
        else:
            st.warning("Lütfen eklenecek bir metin girin.")

    st.divider()
    
    st.markdown("### 🗑️ Mevcut Kayıtları Yönet")
    conn = sqlite3.connect("rag_veritabani.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT id, metin FROM belgeler")
    kayitlar = cursor.fetchall()
    conn.close()
    
    if not kayitlar:
        st.info("Veritabanı şu an boş.")
    else:
        for kayit in kayitlar:
            kayit_id = kayit[0]
            kayit_metni = kayit[1]
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"**ID {kayit_id}:** {kayit_metni[:150]}...")
            with col2:
                if st.button("Sil", key=f"sil_{kayit_id}"):
                    conn = sqlite3.connect("rag_veritabani.db", timeout=10)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM belgeler WHERE id = ?", (kayit_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
