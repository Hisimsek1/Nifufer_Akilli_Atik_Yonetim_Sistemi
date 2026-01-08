# Nilüfer Belediyesi Atık Yönetim Sistemi - Kurumsal Tasarım Sistemi

## 🎯 Tasarım Vizyonu

Bu sistem, **oyunsu/startup estetiğinden** → **profesyonel/kurumsal/devlet standardına** dönüştürülmüştür.

**Hedef Kullanıcı Profili:**
- Belediye yöneticileri
- Operasyon müdürleri
- Kent yönetimi yetkilileri
- Stratejik karar alıcılar

**Tasarım Felsefesi:**
- Ciddi, güvenilir, sakin
- Veri odaklı
- Yönetici sunumlarına hazır
- Belediye ve akıllı kent operasyon merkezlerine uygun

---

## 🎨 Renk Paleti

### Birincil Renkler
```css
--municipal-navy: #1e3a5f        /* Ana kurumsal renk */
--slate-primary: #334155          /* Birincil koyu gri */
--slate-secondary: #475569        /* İkincil koyu gri */
--slate-light: #64748b            /* Açık gri (metinler için) */
```

### Durum Renkleri (Muted/Sakin Tonlar)
```css
--success-muted: #16a34a          /* Başarı - yeşil */
--warning-muted: #ca8a04          /* Uyarı - sarı */
--critical-muted: #dc2626         /* Kritik - kırmızı */
```

### Yüzey ve Arka Plan Renkleri
```css
--bg-base: #f1f5f9                /* Ana arka plan */
--surface-white: #ffffff          /* Kartlar ve yüzeyler */
--border-light: #e2e8f0           /* Kenarlıklar */
--text-primary: #0f172a           /* Ana metin */
--text-secondary: #64748b         /* İkincil metin */
```

### Renk Kullanım Prensipleri
- ❌ Gradyan kullanımı YOK
- ❌ Neon veya canlı renkler YOK
- ✅ Düz, tek ton renkler
- ✅ Yüksek kontrast (okunabilirlik)
- ✅ Minimal vurgu renkleri

---

## 📝 Tipografi Sistemi

### Font Ailesi
**IBM Plex Sans** - Profesyonel, kurumsal, okunaklı sans-serif

```css
font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Yazı Tipi Hiyerarşisi

| Element | Boyut | Ağırlık | Kullanım |
|---------|-------|---------|----------|
| **Sayfa Başlığı** | 1.125rem | 600 | Üst başlık (UPPERCASE) |
| **Bölüm Başlıkları** | 0.875rem | 500 | Panel başlıkları (UPPERCASE) |
| **KPI Değerleri** | 2.25rem | 600 | Büyük metrikler |
| **KPI Etiketleri** | 0.6875rem | 600 | Üst açıklamalar (UPPERCASE) |
| **Gövde Metni** | 0.875rem | 400 | Normal içerik |
| **Detay Metni** | 0.75rem | 400 | Yardımcı bilgiler |
| **Mini Etiketler** | 0.6875rem | 500 | Badge ve etiketler |

### Tipografi Prensipleri
- ✅ Küçük harfler → UPPERCASE dönüşümü (başlıklarda)
- ✅ Letter-spacing: 0.5px - 0.8px (okunabilirlik)
- ✅ Line-height: 1.5 - 1.6 (rahat okuma)
- ❌ Aşırı büyük başlıklar YOK
- ❌ İtalik veya dekoratif fontlar YOK

---

## 🧱 Bileşen Tasarım Sistemi

### Kartlar (Cards)
```css
background: var(--surface-white);
border: 1px solid var(--border-light);
border-radius: 4px;  /* Minimal yuvarlatma */
padding: 1.5rem;
box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);  /* Çok hafif gölge */
```

**Hover Durumu:**
```css
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);  /* Hafif derinlik */
```

### Düğmeler (Primary Button)
```css
background: var(--municipal-navy);
color: white;
padding: 0.625rem 1.5rem;
border: none;
border-radius: 2px;
font-weight: 500;
font-size: 0.875rem;
box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
```

**Hover Durumu:**
```css
background: var(--slate-primary);
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
```

### Form Elemanları (Input/Select)
```css
padding: 0.625rem 0.875rem;
border: 1px solid var(--border-light);
border-radius: 2px;
font-size: 0.875rem;
font-weight: 400;
background: white;
```

**Focus Durumu:**
```css
border-color: var(--municipal-navy);
box-shadow: 0 0 0 2px rgba(30, 58, 95, 0.1);
```

### Rozetler (Badges)
```css
padding: 0.25rem 0.75rem;
border-radius: 9999px;  /* Yuvarlak kenarlar rozetler için OK */
font-size: 0.75rem;
font-weight: 600;
border: 1px solid;
```

**Varyantlar:**
- **Başarı:** `background: #f0fdf4; color: #15803d; border-color: #bbf7d0`
- **Uyarı:** `background: #fefce8; color: #a16207; border-color: #fde047`
- **Bilgi:** `background: #f0f9ff; color: #075985; border-color: #bae6fd`

---

## 📊 Veri Görselleştirme

### KPI Kartları
- Minimal ikonlar (emoji YOK)
- Düz renk arka planlar
- Net sayısal değerler
- Küçük, bilgilendirici etiketler
- Destekleyici metrikler (badge formatında)

### İlerleme Çubukları
```css
/* Container */
height: 6px;
background: var(--border-light);
border-radius: 3px;

/* Fill */
background: var(--municipal-navy);  /* Tek renk, gradyan YOK */
```

### Maliyet Karşılaştırma Çubuğu
```css
height: 48px;
background: var(--success-muted);  /* Düz yeşil */
border: 1px solid var(--border-light);
border-radius: 2px;
```

---

## 🗺️ Harita Tasarımı

### Harita Stili
- **Basemap:** CartoDB Dark Mode
- **Route Lines:** Muted colors, minimal glow
- **Konumlandırma:** Border: 1px solid var(--border-light)
- **Border Radius:** 2px (minimal)

### Harita Kılavuzu (Legend)
- Küçük, kompakt tasarım
- Minimal geometrik şekiller (8x8px squares)
- UPPERCASE başlıklar (10px)
- Profesyonel ton

---

## 🚫 Kullanılmayan Öğeler

### Kaldırılanlar
- ❌ **Tüm Emojiler** (🏙️, 💰, 🌱, 🚛, 🤖, vb.)
- ❌ **Glassmorphism efektleri** (backdrop-blur)
- ❌ **Gradyan arka planlar ve metinler**
- ❌ **Aşırı yuvarlatılmış köşeler** (20px+ border-radius)
- ❌ **Ağır gölgeler ve derinlik efektleri**
- ❌ **Renkli animasyonlar ve hover dönüşümleri** (transform: translateY)
- ❌ **Parlak ve neon renkler**
- ❌ **Oyunsu mikro-kopyalar** ("AI Destekli", "Smart", emojiler)

### Değiştirildi
| Öncesi | Sonrası |
|--------|---------|
| 🏙️ Nilüfer Smart Waste Command Center | NİLÜFER BELEDİYESİ ATIK YÖNETİM KOMUTA MERKEZİ |
| AI-Powered Municipal Operations | Entegre Operasyon ve Analiz Platformu |
| 🤖 AI Öngörüleri | KARAR DESTEK ANALİZLERİ |
| 💡 Maliyet Kıyaslaması | Maliyet Kıyaslamaları |
| 🚀 Rota Oluştur | Rota Oluştur |
| AI Destekli: %76 | Optimizasyon Sonrası: %76 |

---

## 📐 Düzen ve Boşluklar

### Grid Sistemi
- 12-sütunlu Bento Grid
- Gap: 1.5rem
- Max-width: 1800px
- Padding: 2rem (yanlar)

### Boşluk Sistemi
```css
/* Kartlar arası */
margin-bottom: 0.5rem - 0.75rem

/* Bölüm başlıkları */
margin-bottom: 1rem

/* Panel padding */
padding: 1.5rem

/* Kontrol paneli */
padding: 1rem
```

---

## 🎯 Kullanıcı Deneyimi Prensipleri

### Görsel Hiyerarşi
1. **Üst Başlık** - Kurumsal kimlik (navy background)
2. **Özet KPI'lar** - Hızlı genel bakış (2 kart)
3. **Detaylı Metrikler** - 4 KPI kartı (grid layout)
4. **Harita ve Kontroller** - Ana operasyonel alan
5. **Canlı Filo** - Gerçek zamanlı takip
6. **Analizler ve Performans** - Karar destek bölümleri

### Etkileşim Tasarımı
- Minimal animasyonlar (sadece hover ve focus)
- Anlık geri bildirim (button hover)
- Profesyonel transition timing (0.15s - 0.2s)
- Sakin, öngörülebilir davranışlar

### Erişilebilirlik
- Yüksek kontrast oranları
- Okunaklı font boyutları (minimum 0.6875rem)
- Net odak göstergeleri (2px focus ring)
- Anlamlı metin etiketleri

---

## 📋 İçerik Tonu (Microcopy)

### Dil Kuralları
✅ **Kullan:**
- Resmi Türkçe
- Belediye terminolojisi
- Operasyonel dil
- Pasif cümleler ("önerilmektedir", "değerlendirilmelidir")

❌ **Kullanma:**
- Pazarlama dili
- Abartılı ifadeler
- Emoji
- İngilizce terimler (mümkünse)

### Örnek Dönüşümler
| Öncesi | Sonrası |
|--------|---------|
| Bugün Engellenen CO₂ Salınımı | Bugün Azaltılan CO₂ Salınımı |
| AI Öngörüleri | Karar Destek Analizleri |
| Canlı Filo Takibi | CANLI FİLO TAKİBİ |
| Mahalle Geri Dönüşüm Skor Tablosu | MAHALLE BAZINDA GERİ DÖNÜŞÜM PERFORMANSI |

---

## 🔧 Teknik Uygulama

### CSS Değişken Sistemi
Tüm renkler CSS custom properties ile yönetiliyor:
```css
:root {
    --municipal-navy: #1e3a5f;
    --slate-primary: #334155;
    /* ... */
}
```

### Modüler Bileşenler
Her bileşen tutarlı sınıf isimlendirme kullanıyor:
- `.bento-item` - Genel kart konteyneri
- `.kpi-*` - KPI bileşenleri
- `.fleet-*` - Filo elemanları
- `.insight-*` - Analiz kartları
- `.scoreboard-*` - Performans tablosu

### Responsive Tasarım
```css
@media (max-width: 1200px) {
    .bento-kpi, .bento-map, .bento-fleet {
        grid-column: span 12 !important;
    }
}
```

---

## ✅ Öncesi / Sonrası Karşılaştırma

| Özellik | Öncesi | Sonrası |
|---------|--------|---------|
| **Renk Paleti** | Canlı, gradyanlı, 7+ renk | Muted, düz, 3 ana renk |
| **Tipografi** | Inter, playful boyutlar | IBM Plex Sans, profesyonel hiyerarşi |
| **Border Radius** | 12px - 30px | 2px - 4px |
| **Gölgeler** | Ağır (0 8px 32px) | Minimal (0 1px 2px) |
| **İkonlar** | Emojiler | Yok / Minimal geometrik |
| **Animasyonlar** | Transform, pulse, glow | Sadece hover (opacity, background) |
| **Dil Tonu** | Startup, marketing | Resmi, kurumsal |
| **Arka Plan** | Gradyan | Düz, açık gri |
| **Başlık** | Emoji + İngilizce | UPPERCASE Türkçe |

---

## 🎓 Referans Sistemler

Bu tasarım şu sistemlerden ilham alınmıştır:
- **Smart City Control Rooms** (Urban Operations Centers)
- **Government Analytics Dashboards**
- **Municipal Management Systems**
- **Traffic Management Centers**
- **Emergency Operations Centers**

**Hedef Estetik:**
- Microsoft Azure Portal (minimal, profesyonel)
- AWS CloudWatch (veri odaklı, sakin)
- Grafana (operasyonel, anlaşılır)
- IBM Cloud (kurumsal, ciddi)

---

## 📌 Sonuç

Bu tasarım sistemi, Nilüfer Belediyesi Atık Yönetim Sistemini:
- ✅ Belediye yöneticilerine sunulabilir hale getirdi
- ✅ Kurumsal kimliğe uygun profesyonel görünüm kazandırdı
- ✅ Operasyonel bir komuta merkezi estetiğine kavuşturdu
- ✅ Güvenilir, ciddi ve veri odaklı bir platform oluşturdu

**Tüm işlevsellik korundu** - yalnızca görsel dil modernleştirildi ve kurumsallaştırıldı.
