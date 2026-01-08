# 🚀 NİLÜFER BELEDİYESİ AI ATIK YÖNETİM SİSTEMİ

## 📋 HIZLI BAŞLANGIÇ REHBERİ

### ✅ Sistem Gereksinimleri

- **Python**: 3.9 veya üzeri ✓
- **İşletim Sistemi**: Windows/Linux/Mac
- **RAM**: Minimum 4GB (8GB önerilir)
- **Disk**: Minimum 500MB boş alan

---

## 🎯 ADIM ADIM ÇALIŞTIRMA

### ADIM 1: Proje Kontrolü

Önce tüm dosyaların hazır olduğundan emin olun:

```bash
python check_setup.py
```

**Beklenen Çıktı:**
```
✅ Python Versiyonu
✅ Python Paketleri
✅ Veritabanı
✅ CSV Veri Dosyaları
✅ İşlenmiş Veri
✅ AI Modelleri
✅ Frontend Dosyaları
✅ Backend Dosyası

📊 Sonuç: 8/8 kontrol başarılı
```

---

### ADIM 2: Flask Sunucusunu Başlat

```bash
python app_ai.py
```

**Beklenen Çıktı:**
```
✅ AI Modelleri başarıyla yüklendi!
   Model: GradientBoosting
   R² Score: 1.0000
   MAE: 0.0004

================================================================================
🚀 NİLÜFER BELEDİYESİ - AI-POWERED ATIK YÖNETİM SİSTEMİ
================================================================================

📊 AI Durum: ✅ Aktif
   Model: GradientBoosting
   Performans: R²=1.0000

🌐 Sunucu Başlatılıyor...
   Admin Panel: http://localhost:5000/admin
   Ana Sayfa: http://localhost:5000/
================================================================================

 * Running on http://127.0.0.1:5000
 * Running on http://10.50.31.13:5000
```

✅ **Sunucu başarıyla başladı!**

---

### ADIM 3: Admin Panelini Aç

Tarayıcınızda aşağıdaki adreslerden birini açın:

- **Lokal**: http://localhost:5000/admin
- **Ağ**: http://127.0.0.1:5000/admin

---

### ADIM 4: Rota Optimizasyonu Yap

1. **Admin panelde** sağ taraftaki **"Rota Optimizasyonu"** sekmesine tıklayın
2. **"Rotaları Optimize Et"** butonuna basın
3. AI modeli çalışacak ve sonuçları gösterecek:
   - Optimize edilmiş rotalar haritada görünür
   - Her araç için detaylı metrikler
   - Toplam mesafe, kapasite kullanımı

**Beklenen Sonuçlar:**
```
• Toplam Araç: 45
• Toplam Konteyner: 140
• Toplam Mesafe: ~370 km
• Ortalama Kapasite: %72+
```

---

## 🛠️ SORUN GİDERME

### Sorun 1: "Modül bulunamadı" Hatası

**Çözüm:**
```bash
pip install -r requirements.txt
```

### Sorun 2: Port 5000 Kullanımda

**Çözüm:**
```bash
# Çalışan sunucuyu durdur
taskkill /F /IM python.exe

# Veya farklı port kullan (app_ai.py'de değiştir)
app.run(debug=True, port=5001, host='0.0.0.0')
```

### Sorun 3: Veritabanı Hatası

**Çözüm:**
```bash
python load_data_sqlite.py
```

### Sorun 4: Model Hatası

**Çözüm:**
```bash
# Veriyi işle
python data_preparation.py

# Modeli yeniden eğit
python train_fill_prediction.py
```

---

## 📊 SİSTEM BİLEŞENLERİ

### 1. Backend (Flask API)
- **Dosya**: `app_ai.py`
- **Port**: 5000
- **AI**: GradientBoosting modeli yüklü

### 2. Frontend (Web UI)
- **Admin Panel**: `public/admin.html`
- **Ana Sayfa**: `public/index.html`
- **Harita**: Leaflet.js + OSRM routing

### 3. AI Modeli
- **Dosya**: `models/fill_prediction_model.pkl`
- **Performans**: R²=1.0000, MAE=0.04%
- **Özellikler**: 9 adet (zaman, mahalle, konteyner)

### 4. Rota Optimizasyonu
- **Dosya**: `route_optimizer.py`
- **Algoritma**: Nearest Neighbor TSP + VRP
- **Mesafe**: Haversine formülü

### 5. Veritabanı
- **Dosya**: `nilufer_waste.db`
- **Tip**: SQLite
- **Tablolar**: containers, neighborhoods, vehicles, vehicle_types

---

## 🎯 ÖNEMLİ API ENDPOINT'LERİ

### Dashboard
```
GET /dashboard/stats
```
Genel istatistikler (toplam konteyner, araç, doluluk ortalaması)

### Konteynerler
```
GET /api/containers
GET /containers/all
```
Tüm konteynerleri listele

### Doluluk Tahmini
```
GET /api/predict_fill/<container_id>
```
Bir konteyner için AI tahmini

### Rota Optimizasyonu
```
POST /api/optimize_routes
Body: {"min_priority": 0.6}
```
AI ile rota optimizasyonu

### Model Bilgisi
```
GET /api/model_info
```
AI model performans metrikleri

---

## 📈 PERFORMANS BEKLENTİLERİ

### AI Tahmin Modeli
- ✅ R² Score: **1.0000** (Mükemmel)
- ✅ MAE: **0.0004** (%0.04 hata)
- ✅ Tahmin süresi: <10ms
- ✅ Güven skoru: %99.96

### Rota Optimizasyonu
- ✅ 45 araç için optimize
- ✅ ~140 yüksek öncelikli konteyner
- ✅ ~370 km toplam mesafe
- ✅ %70+ kapasite kullanımı
- ✅ Optimizasyon süresi: <5 saniye

### Web Arayüzü
- ✅ Harita yükleme: <2 saniye
- ✅ API yanıt: <500ms
- ✅ OSRM routing: <1 saniye

---

## 🔐 GÜVENLİK NOTLARI

- ⚠️ Bu geliştirme sunucusudur (Flask debug mode)
- ⚠️ Production'da Gunicorn/uWSGI kullanın
- ⚠️ CORS tüm domainlere açık
- ⚠️ Authentication yok (eklenebilir)

---

## 📝 EK KOMUTLAR

### Veriyi Yeniden İşle
```bash
python data_preparation.py
```

### Modeli Yeniden Eğit
```bash
python train_fill_prediction.py
```

### Rota Testi
```bash
python route_optimizer.py
```

### Veri Analizi
```bash
python explore_data.py
```

---

## 🎓 KULLANIM SENARYOLARı

### Senaryo 1: Günlük Rota Planlama
1. Admin paneli aç
2. "Rotaları Optimize Et" tıkla
3. Araç seç (dropdown)
4. Haritada gerçek sokak rotasını gör
5. Raporu PDF olarak kaydet

### Senaryo 2: Konteyner Doluluk İzleme
1. Ana sayfayı aç
2. Haritada konteynerleri gör
3. Renkler doluluk seviyesini gösterir
4. Konteynere tıkla → AI tahmini gör

### Senaryo 3: Filo Yönetimi
1. Admin panel → Fleet Management
2. Araç listesini gör
3. Kapasite kullanımını analiz et
4. Araç ekleme/çıkarma simülasyonu

---

## 📞 DESTEK

**Proje Dosyaları:**
- 📖 `AI_README.md` - Detaylı teknik dokümantasyon
- 🏗️ `ARCHITECTURE.md` - Sistem mimarisi
- 📊 `DATABASE_SCHEMA.md` - Veritabanı şeması

**Test Komutları:**
```bash
python check_setup.py      # Sistem kontrolü
python check_db.py          # Veritabanı kontrolü
python test_api.py          # API testi (varsa)
```

---

## ✨ SONUÇ

Sisteminiz **tam otomatik AI-powered** bir atık yönetim platformu!

**Özellikler:**
- ✅ Gerçek GPS verisiyle çalışır (634K kayıt)
- ✅ Machine Learning tahminleri
- ✅ TSP/VRP rota optimizasyonu
- ✅ OSRM gerçek sokak navigasyonu
- ✅ Real-time harita görselleştirmesi
- ✅ Profesyonel admin paneli

**Başlatmak için sadece:**
```bash
python app_ai.py
```

**Ardından:**
http://localhost:5000/admin

---

**🎉 İyi kullanımlar!**

*Son Güncelleme: 28 Aralık 2025*
*Versiyon: 2.0.0 (AI Edition)*
