# ⚙️ Yerel RAG Asistanı (Local RAG Assistant with Foundry Local)

Tamamen çevrimdışı çalışan, doküman tabanlı bir soru-cevap asistanı. **Retrieval-Augmented Generation (RAG)** yaklaşımını kullanır: sorulan sorular önce yerel bir SQLite veritabanında anlamsal (embedding tabanlı) olarak aranır, en alakalı doküman parçaları bulunur ve bu parçalar bağlam olarak yerel bir dil modeline (LLM) verilerek cevap üretilir. Tüm işlem — embedding üretimi, benzerlik araması ve cevap üretimi — internet bağlantısı olmadan, [Microsoft Foundry Local](https://github.com/microsoft/foundry-local) üzerinden cihaz üzerinde çalışır.

## ✨ Özellikler

- 📂 **Doküman yükleme**: PDF, Excel (.xlsx) veya doğrudan yapıştırılan metinlerden bilgi ekleme
- 🔎 **Anlamsal arama**: Sorular embedding vektörleri arasında kosinüs benzerliği ile karşılaştırılır
- 🤖 **Yerel LLM ile cevap üretimi**: Sadece veritabanındaki bilgilere dayanarak, kaynak dışına çıkmadan cevap üretir
- ⚠️ **Alaka eşiği**: Soruyla yeterince ilgili bilgi bulunamazsa, model uydurma cevap vermek yerine bunu açıkça belirtir
- 🗑️ **Veritabanı yönetimi**: Arayüz üzerinden mevcut kayıtları görüntüleme ve silme
- 🔒 **%100 çevrimdışı**: Hiçbir veri veya soru internete gönderilmez

## 🧱 Mimari

```
Kullanıcı Sorusu
      │
      ▼
Embedding Modeli (qwen3-embedding-0.6b) ── sorunun vektörünü üretir
      │
      ▼
SQLite Veritabanı ── kayıtlı doküman parçalarıyla kosinüs benzerliği hesaplanır
      │
      ▼
En alakalı parçalar (Top-K) ── bağlam olarak seçilir
      │
      ▼
Sohbet Modeli (phi-3.5-mini) ── bağlama dayanarak cevabı üretir
      │
      ▼
Streamlit Arayüzü ── cevap ve kaynak metinler gösterilir
```

## 🛠️ Kullanılan Teknolojiler

| Bileşen | Teknoloji |
|---|---|
| Arayüz | [Streamlit](https://streamlit.io/) |
| Yerel model çalıştırma | [Microsoft Foundry Local](https://github.com/microsoft/foundry-local) |
| Embedding modeli | `qwen3-embedding-0.6b` |
| Sohbet modeli | `phi-3.5-mini` |
| Veritabanı | SQLite |
| Doküman okuma | PyPDF2 (PDF), pandas (Excel) |

## 📋 Gereksinimler

- Python 3.9+
- [Foundry Local](https://learn.microsoft.com/en-us/windows/ai/foundry-local/get-started) kurulu olmalı (Windows / macOS / Linux)
- Aşağıdaki Python paketleri:

```
streamlit
PyPDF2
pandas
openpyxl
foundry-local-sdk
```

`requirements.txt` dosyanız yoksa şu şekilde oluşturabilirsiniz:

```bash
pip freeze > requirements.txt
```

## 🚀 Kurulum

1. Bu depoyu klonlayın:
   ```bash
   git clone <repo-linkiniz>
   cd <repo-klasörü>
   ```

2. Sanal ortam oluşturup bağımlılıkları kurun:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux

   pip install -r requirements.txt
   ```

3. Foundry Local'in kurulu ve çalışır durumda olduğundan emin olun. Kurulu değilse [resmi kurulum rehberini](https://learn.microsoft.com/en-us/windows/ai/foundry-local/get-started) takip edin.

## ▶️ Çalıştırma

```bash
python -m streamlit run arayuz.py
```

Uygulama tarayıcınızda otomatik açılmazsa terminalde görünen `http://localhost:8501` adresini elle açabilirsiniz.

> **Not:** İlk çalıştırmada `phi-3.5-mini` ve `qwen3-embedding-0.6b` modelleri cihazınızda kayıtlı değilse otomatik olarak indirilir; bu işlem internet hızınıza göre biraz zaman alabilir.

## 📖 Kullanım

1. **📂 Veritabanı Yönetimi** sekmesinden PDF/Excel dosyası yükleyin veya elle metin ekleyin. Her doküman otomatik olarak parçalara ayrılır, embedding'i hesaplanır ve SQLite veritabanına kaydedilir.
2. **💬 Soru-Cevap** sekmesinden yüklediğiniz dokümanlarla ilgili sorular sorun.
3. Cevabın hangi kaynak metinlerden üretildiğini görmek için "Arka Planda Bulunan Kaynak Metinler" bölümünü açın.

## 📁 Proje Yapısı

```
.
├── arayuz.py              # Streamlit arayüzü ve RAG mantığı
├── rag_veritabani.db      # SQLite veritabanı (metin + embedding vektörleri)
├── requirements.txt       # Python bağımlılıkları
└── README.md
```

## ⚠️ Bilinen Sınırlamalar

- Benzerlik araması, veritabanındaki tüm kayıtlar üzerinde kaba kuvvet (brute-force) yöntemiyle yapılır; bu küçük/orta ölçekli veri kümeleri için yeterlidir ancak çok büyük veritabanlarında yavaşlayabilir.
- Cevap kalitesi, veritabanına eklenen dokümanların kalitesine ve parçalama (chunking) stratejisine doğrudan bağlıdır.

## 📄 Lisans

Bu proje eğitim amaçlı bir yaz okulu projesidir.
