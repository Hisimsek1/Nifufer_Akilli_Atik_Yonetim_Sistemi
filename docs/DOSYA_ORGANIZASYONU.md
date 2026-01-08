# 🚀 Proje Dosya Organizasyonu

Bu dokümantasyon projenin dosya yapısını ve organizasyonunu açıklar.

## 📂 Ana Dizin Yapısı

### Çalışma Dosyaları (Root)
```
├── app_ai.py                    # Ana Flask API (Production)
├── route_optimizer.py           # TSP/VRP Rota Optimizasyonu
├── data_preparation.py          # Feature Engineering Pipeline
├── train_fill_prediction.py    # AI Model Eğitimi
├── train_model.py              # Alternatif Model Eğitimi
├── train_sqlite.py             # SQLite ile Model Eğitimi
├── init_database.py            # Veritabanı Kurulumu
├── load_data_sqlite.py         # Veri Yükleme (SQLite)
├── load_data.py                # Veri Yükleme (Genel)
├── setup.py                    # Otomatik Kurulum Scripti
├── baslat.bat                  # Windows Başlatıcı
├── requirements.txt            # Python Bağımlılıkları
├── .gitignore                  # Git Ignore Kuralları
├── LICENSE                     # MIT Lisansı
└── README.md                   # Ana Dokümantasyon
```

### Klasörler

#### 📂 data/
Gerçek veri dosyaları (634K+ GPS kaydı)
```
├── all_merged_data.csv         # 634,297 GPS lokasyon kaydı
├── container_counts.csv        # Mahalle konteyner sayıları
├── tonnages.csv                # Aylık tonaj verileri
├── neighbor_days_rotations.csv # Toplama programları
├── mahalle_nufus.csv           # Nüfus bilgileri
├── fleet.csv                   # Araç filosu
├── truck_types.csv             # Araç tipleri
└── processed_containers.csv    # İşlenmiş özellikler (ML ready)
```

#### 📂 models/
Eğitilmiş AI modelleri ve metadata
```
├── fill_prediction_model.pkl   # GradientBoosting Model (827 KB)
├── fill_scaler.pkl             # StandardScaler (1.3 KB)
├── fill_model_metadata.json    # Model metrikleri ve info
├── container_location_stats.json # Konum istatistikleri
└── optimized_routes.json       # Optimize edilmiş rotalar
```

#### 📂 public/
Frontend dosyaları (HTML/CSS/JS)
```
├── index.html                  # Ana Sayfa - Rota Dashboard
├── admin.html                  # Admin Paneli
├── admin-script.js             # Admin Panel Logic
├── api-client.js               # API İstemci
├── script.js                   # Ana Sayfa Logic
├── styles.css                  # Global Styles
└── test.html                   # API Test Sayfası
```

#### 📂 docs/
Proje dokümantasyonu
```
├── AI_README.md                # AI/ML Detaylı Dokümantasyon
├── ARCHITECTURE.md             # Sistem Mimarisi
├── DATABASE_SCHEMA.md          # Veritabanı Şeması
├── HIZLI_BASLANGIC.md         # Hızlı Başlangıç Rehberi
├── PROJECT_SUMMARY.md          # Proje Özeti
├── OPTIMIZATION_REPORT.md      # Optimizasyon Raporu
├── TEST_RESULTS.md             # Test Sonuçları
├── IMPROVEMENTS.md             # Yapılan İyileştirmeler
└── ... (diğer dokümantasyon dosyaları)
```

#### 📂 tests/
Test dosyaları ve doğrulama scriptleri
```
├── test_api.py                 # Ana API Testleri (22 test)
├── check_setup.py              # Kurulum Kontrolü
├── check_db.py                 # Veritabanı Kontrolü
├── verify_ml_predictions.py    # ML Tahmin Doğrulama
├── test_route_capacity.py      # Rota Kapasite Testi
└── ... (diğer test dosyaları)
```

#### 📂 scripts/
Yardımcı ve geliştirme scriptleri
```
├── app.py                      # Eski Flask App
├── app_sqlite.py               # SQLite Tabanlı App
├── explore_data.py             # Veri Keşif Scripti
├── predict_container_locations.py # Konum Tahmini
└── ... (diğer yardımcı scriptler)
```

---

## 🔄 Dosya İlişkileri

### Veri Akışı
```
1. data/*.csv → data_preparation.py → data/processed_containers.csv
2. processed_containers.csv → train_fill_prediction.py → models/*.pkl
3. models/*.pkl + data → app_ai.py → API Endpoints
4. API → public/*.html → Kullanıcı Arayüzü
```

### Bağımlılıklar
```
app_ai.py
├── route_optimizer.py
├── models/fill_prediction_model.pkl
├── models/fill_scaler.pkl
└── nilufer_waste.db

route_optimizer.py
└── nilufer_waste.db

train_fill_prediction.py
├── data/processed_containers.csv
└── models/ (output)
```

---

## 📋 Kullanım Önceliği

### Geliştirme İçin
1. `README.md` - Başlangıç için
2. `docs/` - Detaylı dokümantasyon
3. `tests/check_setup.py` - Kurulum kontrolü
4. `app_ai.py` - Ana uygulama

### Deployment İçin
1. `requirements.txt`
2. `init_database.py` + `load_data_sqlite.py`
3. `train_fill_prediction.py`
4. `app_ai.py`
5. `baslat.bat` veya manuel başlatma

### Test İçin
1. `tests/test_api.py` - Ana testler
2. `tests/check_setup.py` - Sistem kontrolü
3. `tests/verify_ml_predictions.py` - Model doğrulama

---

## 🗑️ Temizlenebilir Dosyalar

Geliştirme tamamlandıktan sonra:
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python files
- `scripts/` - Yardımcı scriptler (isteğe bağlı)
- `docs/` klasöründeki eski raporlar

---

## 📝 Notlar

- **Ana çalışma dosyası**: `app_ai.py`
- **Veritabanı**: `nilufer_waste.db` (SQLite)
- **Frontend**: `public/index.html` ve `public/admin.html`
- **Model dosyaları**: Repo'ya dahil (827 KB, küçük)
- **Büyük veri**: `data/all_merged_data.csv` (113 MB) - .gitignore'a eklenebilir

---

Bu organizasyon ile proje GitHub'da profesyonel ve düzenli görünür. 🎯
