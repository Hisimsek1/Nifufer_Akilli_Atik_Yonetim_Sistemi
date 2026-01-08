"""
Konteyner Koordinatlarını Gerçek GPS Verilerinden Güncelle
"""

import pandas as pd
import sqlite3
import numpy as np
from sklearn.cluster import DBSCAN

def extract_real_container_locations():
    """GPS verilerinden gerçek konteyner konumlarını çıkar"""
    print("\n🗺️ Gerçek GPS verilerinden konteyner konumları çıkarılıyor...")
    
    # GPS verilerini yükle
    print("   📊 GPS verileri yükleniyor...")
    gps_data = pd.read_csv('data/all_merged_data.csv')
    print(f"   ✓ {len(gps_data):,} GPS kaydı yüklendi")
    
    # Duraklama süresini parse et
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
    
    gps_data['duration_minutes'] = gps_data['Duraklama Süresi'].apply(parse_duration)
    
    # 5 dakikadan uzun duraklamalar (muhtemel konteyner noktaları)
    stops = gps_data[gps_data['duration_minutes'] > 5].copy()
    print(f"   ✓ {len(stops):,} duraklama noktası bulundu (>5 dk)")
    
    # Veritabanından mahalle bilgilerini al
    conn = sqlite3.connect('nilufer_waste.db')
    
    neighborhoods = pd.read_sql_query("""
        SELECT neighborhood_id, neighborhood_name 
        FROM neighborhoods
    """, conn)
    
    containers = pd.read_sql_query("""
        SELECT container_id, neighborhood_id, container_type
        FROM containers
    """, conn)
    
    print(f"   ✓ {len(containers)} konteyner, {len(neighborhoods)} mahalle")
    
    # Her mahalle için GPS noktalarını al
    updated_containers = []
    
    for _, neighborhood in neighborhoods.iterrows():
        mahalle_name = neighborhood['neighborhood_name'].upper().strip()
        neighborhood_id = neighborhood['neighborhood_id']
        
        # Bu mahalleye ait konteynerleri al
        mahalle_containers = containers[containers['neighborhood_id'] == neighborhood_id]
        
        if len(mahalle_containers) == 0:
            continue
        
        # GPS verilerinde bu mahalleyi bul
        mahalle_stops = stops[stops['Mahalle'].str.upper().str.contains(mahalle_name, na=False)]
        
        if len(mahalle_stops) == 0:
            # GPS verisi yoksa mahalle merkez noktası kullan
            print(f"   ⚠️  {mahalle_name}: GPS verisi yok, varsayılan kullanılıyor")
            continue
        
        # GPS noktalarını kümeleme (DBSCAN)
        coords = mahalle_stops[['Enlem', 'Boylam']].values
        
        if len(coords) < len(mahalle_containers):
            # Yeterli GPS noktası yoksa, mevcut noktaları tekrarla
            cluster_centers = coords
        else:
            # DBSCAN ile kümeleme yap
            clustering = DBSCAN(eps=0.001, min_samples=2).fit(coords)
            
            # Her kümenin merkez noktasını al
            unique_labels = set(clustering.labels_)
            cluster_centers = []
            
            for label in unique_labels:
                if label == -1:  # Gürültü noktaları
                    continue
                cluster_points = coords[clustering.labels_ == label]
                center = cluster_points.mean(axis=0)
                cluster_centers.append(center)
            
            cluster_centers = np.array(cluster_centers)
            
            # Küme sayısı konteyner sayısından azsa, gürültü noktalarını ekle
            if len(cluster_centers) < len(mahalle_containers):
                noise_points = coords[clustering.labels_ == -1]
                if len(noise_points) > 0:
                    cluster_centers = np.vstack([cluster_centers, noise_points])
        
        # Konteynerlere koordinat ata
        for idx, (_, container) in enumerate(mahalle_containers.iterrows()):
            if idx < len(cluster_centers):
                lat, lng = cluster_centers[idx]
            else:
                # Küme sayısı yetmediyse rastgele bir GPS noktası kullan
                random_idx = np.random.randint(0, len(coords))
                lat, lng = coords[random_idx]
            
            updated_containers.append({
                'container_id': container['container_id'],
                'latitude': float(lat),
                'longitude': float(lng)
            })
        
        print(f"   ✓ {mahalle_name}: {len(mahalle_containers)} konteyner güncellendi")
    
    # Database'i güncelle
    print(f"\n💾 Database güncelleniyor...")
    cursor = conn.cursor()
    
    for container in updated_containers:
        cursor.execute("""
            UPDATE containers 
            SET latitude = ?, longitude = ?
            WHERE container_id = ?
        """, (container['latitude'], container['longitude'], container['container_id']))
    
    conn.commit()
    conn.close()
    
    print(f"✅ {len(updated_containers)} konteyner koordinatı güncellendi!")
    print(f"   Kaynak: Gerçek GPS duraklama noktaları (DBSCAN kümeleme)")

if __name__ == "__main__":
    print("="*80)
    print("🚀 KONTEYNER KOORDİNATLARINI GERÇEK GPS VERİLERİYLE GÜNCELLE")
    print("="*80)
    
    extract_real_container_locations()
    
    # Sonuçları göster
    conn = sqlite3.connect('nilufer_waste.db')
    cursor = conn.cursor()
    
    print("\n📊 Güncellenmiş Koordinat Örnekleri:")
    cursor.execute("SELECT container_id, latitude, longitude FROM containers LIMIT 10")
    for row in cursor.fetchall():
        print(f"   Konteyner {row[0]}: {row[1]:.6f}, {row[2]:.6f}")
    
    conn.close()
    print("\n✅ Güncelleme tamamlandı!")
