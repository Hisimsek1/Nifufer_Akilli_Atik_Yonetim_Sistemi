"""
Nilüfer Belediyesi - Profesyonel Veri Hazırlama ve Analiz Modülü
Gerçek verilerden AI modelleri için kaliteli dataset oluşturur
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import json

class DataProcessor:
    def __init__(self):
        self.db_conn = sqlite3.connect('nilufer_waste.db')
        
    def load_raw_data(self):
        """Gerçek CSV verilerini yükle ve temizle"""
        print("📊 Veri yükleniyor...")
        
        # 1. Konteyner sayıları (mahalle bazlı)
        container_counts = pd.read_csv('data/container_counts.csv', sep=';', encoding='utf-8')
        container_counts.columns = ['SIRA_NO', 'MAHALLE', 'YERALTI', 'LT770', 'LT400', 'PLASTIK', 'TOPLAM']
        print(f"✓ Konteyner sayıları: {len(container_counts)} mahalle")
        
        # 2. Tonaj verileri (aylık)
        tonnages = pd.read_csv('data/tonnages.csv', encoding='utf-8')
        print(f"✓ Tonaj verileri: {len(tonnages)} ay")
        
        # 3. Mahalle toplama rotasyonları
        rotations_raw = pd.read_csv('data/neighbor_days_rotations.csv', sep=';', encoding='utf-8')
        rotations_raw.columns = ['MAHALLE', 'TRUCK_TYPE', 'DAYS_PER_WEEK', 'FREQUENCY', 'CRANE_USED', 'CRANE_DAYS']
        rotations_raw['MAHALLE'] = rotations_raw['MAHALLE'].str.strip()
        print(f"✓ Rotasyon verileri: {len(rotations_raw)} mahalle")
        
        # 4. Araç GPS verileri (634,297 kayıt!)
        vehicle_logs = pd.read_csv('data/all_merged_data.csv', encoding='utf-8', on_bad_lines='skip')
        print(f"✓ GPS verileri: {len(vehicle_logs):,} kayıt")
        
        # 5. Mahalle nüfus verileri
        population = pd.read_csv('data/mahalle_nufus.csv', encoding='utf-8')
        print(f"✓ Nüfus verileri: {len(population)} mahalle")
        
        return {
            'container_counts': container_counts,
            'tonnages': tonnages,
            'rotations': rotations_raw,
            'vehicle_logs': vehicle_logs,
            'population': population
        }
    
    def extract_container_locations(self, vehicle_logs):
        """GPS verilerinden konteyner konumlarını çıkar"""
        print("\n🗺️ Konteyner konumları çıkarılıyor...")
        
        # Duraklama süresini dakikaya çevir (HH:MM:SS formatından)
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
        
        vehicle_logs['duration_minutes'] = vehicle_logs['Duraklama Süresi'].apply(parse_duration)
        
        # Duraklamalar (konteyner toplama noktaları olabilir) - 5 dakikadan uzun duraklamalar
        stops = vehicle_logs[vehicle_logs['duration_minutes'] > 5].copy()
        
        # Mahalle bazlı gruplama
        location_clusters = stops.groupby('Mahalle').agg({
            'Enlem': 'mean',
            'Boylam': 'mean',
            'duration_minutes': 'mean',
            '#': 'count'
        }).reset_index()
        
        location_clusters.columns = ['Mahalle', 'Lat', 'Lng', 'Avg_Stop_Duration', 'Stop_Count']
        
        print(f"✓ {len(location_clusters)} mahallede konum bilgisi bulundu")
        return location_clusters
    
    def create_container_features(self, raw_data):
        """Konteynerler için zengin özellikler oluştur"""
        print("\n🔧 Feature Engineering başlıyor...")
        
        # Database'den mevcut konteynerleri al
        containers = pd.read_sql_query("""
            SELECT c.container_id as id, c.neighborhood_id, c.container_type, c.capacity_liters,
                   c.latitude, c.longitude, c.current_fill_level, c.last_collection_date,
                   n.neighborhood_name, n.population
            FROM containers c
            JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
        """, self.db_conn)
        
        print(f"✓ Database'den {len(containers)} konteyner alındı")
        
        # 1. Zaman özellikleri
        containers['last_collection_date'] = pd.to_datetime(containers['last_collection_date'], format='%Y-%m-%d', errors='coerce')
        containers['days_since_collection'] = (datetime.now() - containers['last_collection_date']).dt.days
        containers['day_of_week'] = containers['last_collection_date'].dt.dayofweek
        containers['month'] = containers['last_collection_date'].dt.month
        containers['is_weekend'] = containers['day_of_week'].isin([5, 6]).astype(int)
        
        # 2. Mahalle özellikleri ekle
        # Rotasyon bilgileri
        rotations = raw_data['rotations']
        rot_dict = {}
        for _, row in rotations.iterrows():
            mahalle = row['MAHALLE'].upper().strip()
            try:
                days = int(row['DAYS_PER_WEEK']) if pd.notna(row['DAYS_PER_WEEK']) else 3
            except:
                days = 3
            rot_dict[mahalle] = days
        
        containers['collection_days_per_week'] = containers['neighborhood_name'].str.upper().map(rot_dict).fillna(3)
        
        # Tonaj ortalamaları (son aylar)
        tonnages = raw_data['tonnages']
        avg_daily_tonnage = tonnages['Ortalama Günlük Tonaj (TON)'].mean()
        
        # 3. Konteyner tipi özellikleri
        type_encoding = {
            'plastic': 1,
            '400lt': 2,
            '770lt': 3,
            'underground': 4,
            '5000lt': 5
        }
        containers['type_encoded'] = containers['container_type'].map(type_encoding).fillna(1)
        
        # 4. Kapasite özellikleri
        containers['capacity_category'] = pd.cut(containers['capacity_liters'], 
                                                   bins=[0, 300, 500, 1000, 6000],
                                                   labels=['small', 'medium', 'large', 'xlarge'])
        
        # 5. Nüfus yoğunluğu (proxy)
        containers['population_density'] = containers['population'] / 1000  # normalize
        
        # 6. Beklenen doluluk oranı (günlük artış modeli)
        daily_fill_rate = 0.08  # Ortalama %8 günlük doluluk artışı
        containers['expected_fill_level'] = np.minimum(
            0.95,
            containers['current_fill_level'] + (containers['days_since_collection'] * daily_fill_rate)
        )
        
        # 7. Toplama önceliği
        containers['collection_priority'] = (
            containers['expected_fill_level'] * 0.5 +  # Doluluk
            (containers['days_since_collection'] / 10) * 0.3 +  # Gün sayısı
            (containers['population_density'] / containers['population_density'].max()) * 0.2  # Nüfus
        )
        
        print(f"✓ {len(containers.columns)} özellik oluşturuldu")
        print(f"  - Zaman: days_since_collection, day_of_week, month, is_weekend")
        print(f"  - Mahalle: collection_days_per_week, population_density")
        print(f"  - Konteyner: type_encoded, capacity_category")
        print(f"  - Hedef: expected_fill_level, collection_priority")
        
        return containers
    
    def save_processed_data(self, containers, output_file='data/processed_containers.csv'):
        """İşlenmiş veriyi kaydet"""
        containers.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n💾 Veri kaydedildi: {output_file}")
        return output_file

def main():
    print("="*80)
    print("🚀 NİLÜFER BELEDİYESİ - PROFESYONEL VERİ HAZIRLAMA")
    print("="*80)
    
    processor = DataProcessor()
    
    # Adım 1: Ham veriyi yükle
    raw_data = processor.load_raw_data()
    
    # Adım 2: Konteyner konumları
    locations = processor.extract_container_locations(raw_data['vehicle_logs'])
    
    # Adım 3: Feature engineering
    processed_containers = processor.create_container_features(raw_data)
    
    # Adım 4: Kaydet
    output_file = processor.save_processed_data(processed_containers)
    
    # Özet istatistikler
    print("\n📊 ÖZET İSTATİSTİKLER:")
    print(f"Toplam Konteyner: {len(processed_containers)}")
    print(f"Ortalama Doluluk: {processed_containers['current_fill_level'].mean():.2%}")
    print(f"Yüksek Öncelikli (>0.7): {len(processed_containers[processed_containers['collection_priority'] > 0.7])}")
    print(f"Son 3 Gün İçinde Toplanmış: {len(processed_containers[processed_containers['days_since_collection'] <= 3])}")
    
    print("\n✅ Veri hazırlama tamamlandı!")
    print(f"📁 Çıktı dosyası: {output_file}")
    
    processor.db_conn.close()

if __name__ == '__main__':
    main()
