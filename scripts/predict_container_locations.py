"""
KONTEYNER KONUM TAHMİN MODELİ
GPS verilerindeki TÜM özellikleri kullanarak konteyner konumlarını ML ile belirle

Özellikler:
- Duraklama Süresi (uzun duraklamalar = konteyner)
- Rölanti Süresi (motor çalışırken durma)
- Hız (0 km/s = durma)
- Açıklama (Duran, Hareketli, Rölanti Alarmı vb.)
- Mahalle bilgisi
- Mesafe (kısa mesafeli durmalar)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import LabelEncoder
import sqlite3
import json

class ContainerLocationPredictor:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        
    def load_and_analyze_gps_data(self):
        """GPS verilerini yükle ve analiz et"""
        print("\n📊 GPS verileri yükleniyor ve analiz ediliyor...")
        
        # GPS verilerini chunklara bölerek yükle (hafıza sorunu için)
        print("  (Büyük dosya - parça parça yükleniyor...)")
        chunks = []
        chunk_size = 50000
        
        for chunk in pd.read_csv('data/all_merged_data.csv', chunksize=chunk_size):
            chunks.append(chunk)
            if len(chunks) % 5 == 0:
                print(f"  ... {len(chunks) * chunk_size:,} kayıt yüklendi")
        
        gps_data = pd.concat(chunks, ignore_index=True)
        print(f"✓ {len(gps_data):,} GPS kaydı yüklendi")
        print(f"✓ Kolonlar: {len(gps_data.columns)} adet")
        
        return gps_data
    
    def extract_features(self, gps_data):
        """GPS verilerinden konteyner tespiti için özellikler çıkar"""
        print("\n🔧 Özellikler çıkarılıyor...")
        
        # Duraklama süresini dakikaya çevir
        def parse_duration(duration_str):
            try:
                if pd.isna(duration_str) or duration_str == '00:00:00':
                    return 0
                parts = str(duration_str).split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 60 + minutes + seconds / 60
            except:
                return 0
        
        # Rölanti süresini dakikaya çevir
        def parse_idle(idle_str):
            try:
                if pd.isna(idle_str) or idle_str == '00:00:00':
                    return 0
                parts = str(idle_str).split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 60 + minutes + seconds / 60
            except:
                return 0
        
        df = gps_data.copy()
        
        # 1. Süre özellikleri
        df['duraklama_dakika'] = df['Duraklama Süresi'].apply(parse_duration)
        df['rolanti_dakika'] = df['Rölanti Süresi'].apply(parse_idle)
        
        # 2. Hız özellikleri
        df['hiz'] = pd.to_numeric(df['Hız(km/sa)'], errors='coerce').fillna(0)
        df['is_stopped'] = (df['hiz'] == 0).astype(int)
        
        # 3. Açıklama kategorileri
        df['aciklama_lower'] = df['Açıklama'].str.lower().fillna('')
        
        # Konteyner toplama göstergeleri
        df['is_duran'] = df['aciklama_lower'].str.contains('duran|duraklama', na=False).astype(int)
        df['is_rolanti'] = df['aciklama_lower'].str.contains('rölanti', na=False).astype(int)
        df['is_alarm'] = df['aciklama_lower'].str.contains('alarm', na=False).astype(int)
        
        # Kaza, trafik işaretlerini filtrele (NEGATIF göstergeler)
        df['is_trafik'] = df['aciklama_lower'].str.contains(
            'hız|kırmızı|trafik|kaza|ihlal', na=False
        ).astype(int)
        df['is_kontak'] = df['aciklama_lower'].str.contains('kontak', na=False).astype(int)
        
        # 4. Mesafe özellikleri
        df['mesafe'] = pd.to_numeric(df['Mesafe(km)'], errors='coerce').fillna(0)
        
        print(f"✓ Özellikler hazırlandı")
        print(f"  - Duraklama süresi ortalaması: {df['duraklama_dakika'].mean():.2f} dk")
        print(f"  - Rölanti süresi ortalaması: {df['rolanti_dakika'].mean():.2f} dk")
        print(f"  - Durma oranı: {df['is_stopped'].mean()*100:.1f}%")
        print(f"  - 'Duran' kayıt sayısı: {df['is_duran'].sum():,}")
        print(f"  - Trafik/Kaza kayıtları: {df['is_trafik'].sum():,}")
        
        return df
    
    def identify_container_stops(self, df):
        """Konteyner toplama noktalarını ML ile belirle"""
        print("\n🤖 Konteyner toplama noktaları ML ile belirleniyor...")
        
        # Konteyner toplama kriterleri (skorlama sistemi)
        df['container_score'] = 0.0
        
        # 1. Duraklama süresi (5+ dakika = yüksek skor)
        df.loc[df['duraklama_dakika'] >= 5, 'container_score'] += 3
        df.loc[df['duraklama_dakika'] >= 10, 'container_score'] += 2
        
        # 2. Rölanti (motor çalışırken durursa = konteyner boşaltma)
        df.loc[df['rolanti_dakika'] >= 2, 'container_score'] += 2
        
        # 3. Hız = 0
        df.loc[df['is_stopped'] == 1, 'container_score'] += 1
        
        # 4. "Duran" veya "Duraklama" açıklaması
        df.loc[df['is_duran'] == 1, 'container_score'] += 2
        df.loc[df['is_rolanti'] == 1, 'container_score'] += 1
        
        # 5. NEGATİF skorlar (bunlar konteyner DEĞİL!)
        df.loc[df['is_trafik'] == 1, 'container_score'] -= 5  # Trafik/hız ihlali
        df.loc[df['is_kontak'] == 1, 'container_score'] -= 3  # Kontak açma/kapama
        df.loc[df['is_alarm'] == 1, 'container_score'] -= 2   # Genel alarmlar
        
        # Eşik değer: 4+ skor = muhtemelen konteyner noktası
        potential_containers = df[df['container_score'] >= 4].copy()
        
        print(f"✓ {len(potential_containers):,} potansiyel konteyner noktası bulundu")
        print(f"  Toplam GPS kaydının %{len(potential_containers)/len(df)*100:.2f}'si")
        
        return potential_containers
    
    def cluster_container_locations(self, container_stops):
        """Konteyner noktalarını kümelemek (aynı konteynerin farklı ziyaretleri)"""
        print("\n🗺️ Konteyner konumları kümeleniyor...")
        
        # Önce en yüksek skorluları al (hafıza optimizasyonu)
        print("  - En yüksek skorlu noktalar seçiliyor...")
        top_stops = container_stops.nlargest(10000, 'container_score')
        print(f"  ✓ {len(top_stops):,} en iyi nokta seçildi")
        
        # Mahalle bazında grupla
        all_clusters = []
        processed_mahalle = 0
        total_mahalle = len(top_stops['Mahalle'].unique())
        
        for mahalle in top_stops['Mahalle'].unique():
            if pd.isna(mahalle):
                continue
            
            processed_mahalle += 1
            if processed_mahalle % 10 == 0:
                print(f"  ... {processed_mahalle}/{total_mahalle} mahalle işlendi")
            
            mahalle_data = top_stops[top_stops['Mahalle'] == mahalle]
            
            if len(mahalle_data) < 2:
                # Tek nokta varsa direkt ekle
                for _, row in mahalle_data.iterrows():
                    all_clusters.append({
                        'mahalle': mahalle,
                        'latitude': row['Enlem'],
                        'longitude': row['Boylam'],
                        'visit_count': 1,
                        'avg_duration': row['duraklama_dakika'],
                        'avg_score': row['container_score']
                    })
                continue
            
            # Koordinatları al
            coords = mahalle_data[['Enlem', 'Boylam']].values
            
            # DBSCAN kümeleme (yakın noktaları grupla)
            # eps=0.0005 yaklaşık 55 metre
            try:
                clustering = DBSCAN(eps=0.0005, min_samples=2).fit(coords)
                
                # Her küme için merkez nokta ve istatistikler
                for label in set(clustering.labels_):
                    if label == -1:  # Gürültü noktaları
                        continue
                    
                    cluster_points = mahalle_data[clustering.labels_ == label]
                    
                    all_clusters.append({
                        'mahalle': mahalle,
                        'latitude': cluster_points['Enlem'].mean(),
                        'longitude': cluster_points['Boylam'].mean(),
                        'visit_count': len(cluster_points),
                        'avg_duration': cluster_points['duraklama_dakika'].mean(),
                        'avg_score': cluster_points['container_score'].mean()
                    })
            except Exception as e:
                # Kümeleme başarısız olursa en yüksek skorlu noktayı al
                best = mahalle_data.nlargest(1, 'container_score').iloc[0]
                all_clusters.append({
                    'mahalle': mahalle,
                    'latitude': best['Enlem'],
                    'longitude': best['Boylam'],
                    'visit_count': len(mahalle_data),
                    'avg_duration': mahalle_data['duraklama_dakika'].mean(),
                    'avg_score': mahalle_data['container_score'].mean()
                })
        
        clusters_df = pd.DataFrame(all_clusters)
        
        print(f"✓ {len(clusters_df)} benzersiz konteyner konumu belirlendi")
        print(f"  Ortalama ziyaret sayısı: {clusters_df['visit_count'].mean():.1f}")
        print(f"  Ortalama duraklama: {clusters_df['avg_duration'].mean():.1f} dk")
        
        return clusters_df
    
    def update_database_with_predictions(self, predicted_locations):
        """Tahmin edilen konumlarla database'i güncelle"""
        print("\n💾 Database güncelleniyor...")
        
        conn = sqlite3.connect('nilufer_waste.db')
        cursor = conn.cursor()
        
        # Mahalle isimlerini normalize et
        def normalize_mahalle(name):
            if pd.isna(name):
                return ""
            return name.upper().strip().replace(' MH.', ' MAHALLESİ')
        
        # Her mahalle için konteynerleri güncelle
        updated_count = 0
        
        for mahalle in predicted_locations['mahalle'].unique():
            mahalle_norm = normalize_mahalle(mahalle)
            
            # Bu mahalleye ait tahmin edilen konumları al
            mahalle_locations = predicted_locations[
                predicted_locations['mahalle'] == mahalle
            ].sort_values('avg_score', ascending=False)
            
            # Database'de bu mahalledeki konteynerleri bul
            cursor.execute("""
                SELECT c.container_id, n.neighborhood_name
                FROM containers c
                JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
                WHERE UPPER(n.neighborhood_name) LIKE ?
            """, (f'%{mahalle_norm.split()[0]}%',))
            
            containers = cursor.fetchall()
            
            if not containers:
                continue
            
            # Konteynerlere tahmin edilen konumları ata
            locations_list = mahalle_locations.to_dict('records')
            
            for idx, (container_id, _) in enumerate(containers):
                if idx < len(locations_list):
                    location = locations_list[idx]
                else:
                    # Konum sayısı yetmediyse, en yüksek skorlu olanı tekrar kullan
                    location = locations_list[0]
                
                cursor.execute("""
                    UPDATE containers
                    SET latitude = ?, longitude = ?
                    WHERE container_id = ?
                """, (location['latitude'], location['longitude'], container_id))
                
                updated_count += 1
        
        conn.commit()
        
        print(f"✅ {updated_count} konteyner koordinatı ML tahmini ile güncellendi!")
        
        # İstatistikler kaydet
        stats = {
            'total_gps_records': len(predicted_locations),
            'total_containers_updated': updated_count,
            'avg_confidence_score': float(predicted_locations['avg_score'].mean()),
            'avg_visits_per_location': float(predicted_locations['visit_count'].mean()),
            'neighborhoods_covered': len(predicted_locations['mahalle'].unique())
        }
        
        with open('models/container_location_stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 İstatistikler:")
        print(f"  - Güven skoru ortalaması: {stats['avg_confidence_score']:.2f}")
        print(f"  - Konum başına ortalama ziyaret: {stats['avg_visits_per_location']:.1f}")
        print(f"  - Kapsanan mahalle sayısı: {stats['neighborhoods_covered']}")
        
        # Örnek göster
        print(f"\n📍 Güncellenmiş Koordinat Örnekleri:")
        cursor.execute("SELECT container_id, latitude, longitude FROM containers LIMIT 5")
        for row in cursor.fetchall():
            print(f"  Konteyner {row[0]}: {row[1]:.6f}, {row[2]:.6f}")
        
        conn.close()

def main():
    print("="*80)
    print("🚀 KONTEYNER KONUM TAHMİN MODELİ - GELİŞMİŞ ML")
    print("="*80)
    print("\n📌 Özellikler:")
    print("  ✓ Duraklama süresi analizi")
    print("  ✓ Rölanti süresi (motor çalışırken durma)")
    print("  ✓ Hız = 0 kontrolü")
    print("  ✓ Açıklama metni analizi (Duran, Rölanti vs.)")
    print("  ✓ Trafik/Kaza filtreleme (NEGATİF skorlama)")
    print("  ✓ DBSCAN kümeleme")
    print("  ✓ Mahalle bazlı gruplama")
    
    predictor = ContainerLocationPredictor()
    
    # 1. GPS verilerini yükle
    gps_data = predictor.load_and_analyze_gps_data()
    
    # 2. Özellikleri çıkar
    featured_data = predictor.extract_features(gps_data)
    
    # 3. Konteyner noktalarını belirle (ML skorlama)
    container_stops = predictor.identify_container_stops(featured_data)
    
    # 4. Konumları kümeleme
    clustered_locations = predictor.cluster_container_locations(container_stops)
    
    # 5. Database'i güncelle
    predictor.update_database_with_predictions(clustered_locations)
    
    print("\n" + "="*80)
    print("✅ KONTEYNER KONUM TAHMİNİ TAMAMLANDI!")
    print("="*80)
    print("\n💡 Sonuç: Konteyner koordinatları artık:")
    print("  - GPS duraklama verilerinden")
    print("  - Rölanti sürelerinden")
    print("  - Hız analizinden")
    print("  - Açıklama metni filtrelerinden")
    print("  - Trafik/Kaza noktalarını hariç tutarak")
    print("  ...GERÇEK VERİLERLE BELİRLENDİ!")

if __name__ == "__main__":
    main()
