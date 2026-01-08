# Kurumsal Tasarım Sistemi - Hızlı Referans

## 🎨 Renk Paleti (Hex Kodları)

### Ana Kurumsal Renkler
```
#1e3a5f  Municipal Navy (Belediye Lacivert) - Ana marka rengi
#334155  Slate Primary (Birincil Koyu Gri) - Başlıklar
#475569  Slate Secondary (İkincil Koyu Gri) - Alt başlıklar
#64748b  Slate Light (Açık Gri) - Yardımcı metinler
```

### Durum Renkleri (Muted)
```
#16a34a  Success (Başarı Yeşili) - Pozitif durumlar
#ca8a04  Warning (Uyarı Sarısı) - Dikkat gerektiren
#dc2626  Critical (Kritik Kırmızısı) - Acil durumlar
```

### Yüzey Renkleri
```
#f1f5f9  Background Base (Ana Arka Plan)
#ffffff  Surface White (Kart Yüzeyleri)
#e2e8f0  Border Light (Kenarlıklar)
#0f172a  Text Primary (Ana Metin)
```

---

## 📏 Boyut Sistemi

### Border Radius
```
2px   - Kartlar, düğmeler, input'lar
4px   - Bento grid items
9999px - Sadece badge/rozetler için
```

### Gölgeler (Box Shadow)
```
0 1px 2px rgba(0,0,0,0.05)  - Varsayılan (kartlar)
0 2px 4px rgba(0,0,0,0.08)  - Hover durumu
0 1px 3px rgba(0,0,0,0.1)   - Düğme hover
```

### Padding/Margin
```
0.5rem   - Mini boşluklar
0.875rem - Küçük padding
1rem     - Standart padding
1.5rem   - Kart padding
2rem     - Sayfa padding
```

---

## 🔤 Tipografi Ölçüleri

| Element | Boyut | Ağırlık | Transform |
|---------|-------|---------|-----------|
| Sayfa Başlığı | 1.125rem (18px) | 600 | UPPERCASE |
| Bölüm Başlığı | 0.875rem (14px) | 500 | UPPERCASE |
| KPI Değeri | 2.25rem (36px) | 600 | - |
| KPI Etiketi | 0.6875rem (11px) | 600 | UPPERCASE |
| Gövde Metni | 0.875rem (14px) | 400 | - |
| Detay Metni | 0.75rem (12px) | 400 | - |
| Mini Etiket | 0.6875rem (11px) | 500 | - |

**Letter Spacing:** 0.5px - 0.8px (UPPERCASE başlıklarda)

---

## 🧩 Bileşen Şablonları

### Minimal Card
```css
background: #ffffff;
border: 1px solid #e2e8f0;
border-radius: 4px;
padding: 1.5rem;
box-shadow: 0 1px 2px rgba(0,0,0,0.05);
```

### Primary Button
```css
background: #1e3a5f;
color: white;
padding: 0.625rem 1.5rem;
border: none;
border-radius: 2px;
font-size: 0.875rem;
font-weight: 500;
```

### Input/Select
```css
padding: 0.625rem 0.875rem;
border: 1px solid #e2e8f0;
border-radius: 2px;
font-size: 0.875rem;
```

### Badge (Rozet)
```css
padding: 0.25rem 0.75rem;
border-radius: 9999px;
font-size: 0.75rem;
font-weight: 600;
border: 1px solid;

/* Success */
background: #f0fdf4;
color: #15803d;
border-color: #bbf7d0;

/* Warning */
background: #fefce8;
color: #a16207;
border-color: #fde047;

/* Info */
background: #f0f9ff;
color: #075985;
border-color: #bae6fd;
```

---

## ✅ Yapılması Gerekenler

- ✅ Düz renkler kullan (gradyan YOK)
- ✅ UPPERCASE başlıklar (text-transform)
- ✅ Minimal border-radius (2-4px)
- ✅ Hafif gölgeler (0-2px blur)
- ✅ Profesyonel font (IBM Plex Sans)
- ✅ Yüksek kontrast (okunabilirlik)
- ✅ Resmi Türkçe dil
- ✅ Letter-spacing (başlıklarda)

## ❌ Yapılmaması Gerekenler

- ❌ Emoji kullanma
- ❌ Gradyan arka planlar
- ❌ Ağır glassmorphism efektleri
- ❌ Aşırı yuvarlatılmış köşeler (>10px)
- ❌ Ağır gölgeler (>4px blur)
- ❌ Transform animasyonları (translateY, scale)
- ❌ Parlak/neon renkler
- ❌ Pazarlama dili
- ❌ İngilizce terimler (mümkünse)

---

## 🎯 Kullanım Senaryoları

### Yeni Bir KPI Kartı Eklerken:
1. `bento-item bento-kpi` sınıfını kullan
2. Emoji YOK - boş `.kpi-icon` div
3. UPPERCASE başlık (0.6875rem, 600)
4. Büyük sayı (2.25rem, 600)
5. Küçük açıklama (0.75rem, 400)

### Yeni Bir Analiz Bölümü Eklerken:
1. Başlık: UPPERCASE, 0.875rem, 500
2. İçerik kartları: `insight-item` sınıfı
3. Border-left: 3px solid #1e3a5f
4. Arka plan: #f1f5f9
5. Metin: Resmi Türkçe, pasif cümleler

### Yeni Bir Durum Göstergesi Eklerken:
1. Badge bileşeni kullan
2. Muted renk paleti (success/warning/info)
3. 1px border ekle
4. Font-size: 0.75rem, font-weight: 600

---

## 🔗 Referans Linkler

**Tasarım Felsefesi:**
- Smart City Control Room
- Government Analytics Dashboard
- Municipal Operations Center

**Benzer Sistemler:**
- Microsoft Azure Portal
- AWS CloudWatch
- IBM Cloud Dashboard
- Grafana (Operasyonel)

---

**Not:** Bu tasarım sistemi, "playful startup" → "serious government-grade" dönüşümü için oluşturulmuştur. Tüm değişiklikler sadece görseldir - hiçbir işlevsellik değiştirilmemiştir.
