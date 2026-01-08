# ROTA KAPASİTE AÇIKLAMASI

## Sorun: Bir Araç Neden Sadece 6-10 Konteyner Alıyor?

### Gerçek Dünya Analizi:

**Konteyner Tipleri ve Kapasiteler:**
- Plastic: 240L (küçük)
- 400lt: 400L (orta)
- 770lt: 770L (büyük)
- **Underground: 5000L (ÇOK BÜYÜK!)**

**Araç Kapasiteleri:**
- Küçük Kamyon: 1000L (1 ton)
- Orta Kamyon: 3000L (3 ton)
- Büyük Kamyon: 8000L (8 ton)

###  Matemat ik:

Eğer konteynerlerin %77.7 dolu olduğunu varsayarsak:
- 1 Underground = 5000L × 0.777 = **3,885L**
- 1 Büyük (770lt) = 770L × 0.777 = **598L**
- 1 Orta (400lt) = 400L × 0.777 = **311L**

**8 tonluk (8000L) kamyon için:**
- Underground: 8000L / 3885L = **2 konteyner maksimum**
- 770lt: 8000L / 598L = **13 konteyner maksimum**
- 400lt: 8000L / 311L = **25 konteyner maksimum**
- Plastic: 8000L / 186L = **43 konteyner maksimum**

### Sistem Durumu:

Veritabanında:
- 313 Underground (%27)
- 831 Normal konteyner (%73)

**Sonuç:** Araçlar karışık yük aldığı için (underground + normal), ortalama 6-10 konteyner gerçekçi!

### Çözüm Önerileri:

1. **AYRI ROTALAR**: Underground için özel kamyonlar (ŞU ANDA UYGULANMIŞ - capacity_multiplier=5x)
2. **DAHA FAZLA ARAÇ**: 45 araç 1144 konteyner için yeterli (25 konteyner/araç olsa bile)
3. **ESNEKLİK**: capacity_multiplier ile gerçekçi kapasite aşımına izin verildi

### Güncel Sonuçlar:

✅ Ortalama: 6.4 konteyner/araç  
✅ Maksimum: 10 konteyner (underground varsa mantıklı)  
✅ Toplam atanan: ~290 konteyner (45 araç)  
⚠️  Kalan: ~850 konteyner (daha fazla tur gerekli)

**NOT:** Gerçek hayatta araçlar günde 3-4 tur atar. Sistem tek tur için optimize edilmiş.
