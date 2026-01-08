"""
CSV Verilerini Veritabanına Yükleme Script'i
Nilüfer Belediyesi Akıllı Atık Yönetim Sistemi
"""

import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import random
import numpy as np

# Veritabanı bağlantı ayarları
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # BURAYA ŞİFRENİZİ YAZIN
    'database': 'nilufer_waste_db'
}

def connect_db():
    """Veritabanına bağlan"""
    return mysql.connector.connect(**DB_CONFIG)

def load_neighborhoods(conn):
    """Mahalle verilerini yükle"""
    print("\n📍 Mahalle verileri yükleniyor...")
    
    # CSV'yi oku
    df = pd.read_csv('data/mahalle_nufus.csv', sep=';', encoding='utf-8-sig')
    
    cursor = conn.cursor()
    
    inserted = 0
    for _, row in df.iterrows():
        mahalle_adi = row['mahalle'].strip()
        nufus = int(float(str(row['nufus']).replace('.', '').replace(',', '.')))
        
        # Alan tahmini (örnek değer)
        alan_km2 = round(random.uniform(0.5, 5.0), 2)
        nufus_yogunlugu = round(nufus / alan_km2, 2)
        
        try:
            cursor.execute("""
                INSERT INTO neighborhoods (neighborhood_name, population, area_km2, population_density)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    population = %s,
                    area_km2 = %s,
                    population_density = %s
            """, (mahalle_adi, nufus, alan_km2, nufus_yogunlugu, nufus, alan_km2, nufus_yogunlugu))
            inserted += 1
        except Exception as e:
            print(f"Hata: {mahalle_adi} - {e}")
    
    conn.commit()
    print(f"✓ {inserted} mahalle kaydedildi")
    return cursor.lastrowid

def load_vehicle_types(conn):
    """Araç tiplerini yükle"""
    print("\n🚛 Araç tipleri yükleniyor...")
    
    cursor = conn.cursor()
    
    vehicle_types = [
        ('Small Garbage Truck', 9.0, 4.8, 0.25, 0.65, 150.00),
        ('Large Garbage Truck', 16.5, 8.0, 0.40, 1.05, 250.00),
        ('Crane Vehicle', 23.0, 11.5, 0.50, 1.30, 300.00)
    ]
    
    for vtype in vehicle_types:
        cursor.execute("""
            INSERT INTO vehicle_types 
            (type_name, capacity_m3, capacity_ton, fuel_consumption_per_km, 
             co2_emission_per_km, hourly_operating_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                capacity_m3 = %s,
                capacity_ton = %s
        """, (*vtype, vtype[1], vtype[2]))
    
    conn.commit()
    print(f"✓ {len(vehicle_types)} araç tipi kaydedildi")

def load_fleet(conn):
    """Filo verilerini yükle"""
    print("\n🚙 Filo verileri yükleniyor...")
    
    df = pd.read_csv('data/fleet.csv', encoding='utf-8-sig')
    
    cursor = conn.cursor()
    
    # Önce tip ID'lerini al
    cursor.execute("SELECT type_id, type_name FROM vehicle_types")
    type_map = {name: tid for tid, name in cursor.fetchall()}
    
    inserted = 0
    for _, row in df.iterrows():
        vehicle_id = int(row['vehicle_id'])
        vehicle_name = row['vehicle_name']
        vehicle_type = row['vehicle_type']
        
        type_id = type_map.get(vehicle_type)
        
        if type_id:
            cursor.execute("""
                INSERT INTO vehicles (vehicle_id, vehicle_name, vehicle_type_id, status)
                VALUES (%s, %s, %s, 'available')
                ON DUPLICATE KEY UPDATE 
                    vehicle_name = %s,
                    vehicle_type_id = %s
            """, (vehicle_id, vehicle_name, type_id, vehicle_name, type_id))
            inserted += 1
    
    conn.commit()
    print(f"✓ {inserted} araç kaydedildi")

def load_containers(conn):
    """Konteyner verilerini yükle"""
    print("\n🗑️ Konteyner verileri yükleniyor...")
    
    df = pd.read_csv('data/container_counts.csv', sep=';', encoding='utf-8-sig')
    
    cursor = conn.cursor()
    
    # Mahalle ID'lerini al
    cursor.execute("SELECT neighborhood_id, neighborhood_name FROM neighborhoods")
    neighborhood_map = {}
    for nid, name in cursor.fetchall():
        # Normalize et
        normalized = name.upper().replace('MAHALLESİ', '').strip()
        neighborhood_map[normalized] = nid
    
    total_containers = 0
    
    for _, row in df.iterrows():
        mahalle = str(row['MAHALLE']).strip().upper()
        
        # Mahalle ID bul
        neighborhood_id = None
        for key, value in neighborhood_map.items():
            if key in mahalle or mahalle in key:
                neighborhood_id = value
                break
        
        if not neighborhood_id:
            continue
        
        # Her konteyner tipini ekle
        container_types = [
            ('underground', int(row.get('YERALTI KONTEYNER', 0) or 0), 1100),
            ('770lt', int(row.get('770 LT KONTEYNER', 0) or 0), 770),
            ('400lt', int(row.get('400 LT KONTEYNER', 0) or 0), 400),
            ('plastic', int(row.get('PLASTİK', 0) or 0), 240)
        ]
        
        for ctype, count, capacity in container_types:
            if count > 0:
                for i in range(count):
                    container_code = f"NIL-{neighborhood_id}-{ctype.upper()}-{i+1:03d}"
                    
                    # Rastgele son toplama tarihi (son 1-7 gün içinde)
                    days_ago = random.randint(1, 7)
                    last_collection = datetime.now() - timedelta(days=days_ago)
                    
                    # Rastgele doluluk seviyesi
                    fill_level = round(random.uniform(0.1, 0.9), 2)
                    
                    try:
                        cursor.execute("""
                            INSERT INTO containers 
                            (container_code, neighborhood_id, container_type, capacity_liters,
                             last_collection_date, current_fill_level)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                current_fill_level = %s
                        """, (container_code, neighborhood_id, ctype, capacity, 
                              last_collection, fill_level, fill_level))
                        total_containers += 1
                    except Exception as e:
                        pass  # Duplicate
    
    conn.commit()
    print(f"✓ {total_containers} konteyner kaydedildi")

def load_tonnage_statistics(conn):
    """Tonaj istatistiklerini yükle"""
    print("\n📊 Tonaj istatistikleri yükleniyor...")
    
    df = pd.read_csv('data/tonnages.csv', encoding='utf-8-sig')
    
    cursor = conn.cursor()
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO tonnage_statistics 
                (month, year, surface_tonnage, underground_tonnage, 
                 total_tonnage, average_daily_tonnage)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['AY'],
                int(row['YIL']),
                float(row['Yer Üstü Tonaj (TON)']),
                float(row['Yer Altı Tonaj (TON)']),
                float(row['Toplam Tonaj (TON)']),
                float(row['Ortalama Günlük Tonaj (TON)'])
            ))
            inserted += 1
        except Exception as e:
            print(f"Hata: {e}")
    
    conn.commit()
    print(f"✓ {inserted} tonaj kaydı eklendi")

def generate_synthetic_collection_events(conn, num_events=500):
    """Sentetik toplama olayları oluştur (model eğitimi için)"""
    print(f"\n📦 {num_events} sentetik toplama olayı oluşturuluyor...")
    
    cursor = conn.cursor()
    
    # Konteynerleri ve araçları al
    cursor.execute("SELECT container_id FROM containers LIMIT 200")
    container_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT vehicle_id FROM vehicles")
    vehicle_ids = [row[0] for row in cursor.fetchall()]
    
    if not container_ids or not vehicle_ids:
        print("⚠️ Yeterli konteyner veya araç yok!")
        return
    
    inserted = 0
    for _ in range(num_events):
        container_id = random.choice(container_ids)
        vehicle_id = random.choice(vehicle_ids)
        
        # Rastgele tarih (son 90 gün)
        days_ago = random.randint(1, 90)
        collection_date = datetime.now() - timedelta(days=days_ago)
        
        # Rastgele metrikler
        tonnage = round(random.uniform(0.1, 2.5), 2)
        fill_before = round(random.uniform(0.6, 1.0), 2)
        duration = random.randint(3, 15)
        fuel = round(random.uniform(0.5, 3.0), 2)
        distance = round(random.uniform(0.5, 5.0), 2)
        
        try:
            cursor.execute("""
                INSERT INTO collection_events
                (container_id, vehicle_id, collection_date, tonnage_collected,
                 fill_level_before, collection_duration_minutes, 
                 fuel_consumed_liters, distance_traveled_km)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (container_id, vehicle_id, collection_date, tonnage,
                  fill_before, duration, fuel, distance))
            inserted += 1
        except:
            pass
    
    conn.commit()
    print(f"✓ {inserted} toplama olayı oluşturuldu")

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("Nilüfer Belediyesi - Veri Yükleme Script'i")
    print("=" * 60)
    
    try:
        # Veritabanına bağlan
        print("\n🔌 Veritabanına bağlanılıyor...")
        conn = connect_db()
        print("✓ Bağlantı başarılı")
        
        # Verileri yükle
        load_neighborhoods(conn)
        load_vehicle_types(conn)
        load_fleet(conn)
        load_containers(conn)
        load_tonnage_statistics(conn)
        generate_synthetic_collection_events(conn)
        
        # İstatistikler
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM neighborhoods")
        print(f"\n📊 Toplam {cursor.fetchone()[0]} mahalle")
        
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        print(f"📊 Toplam {cursor.fetchone()[0]} araç")
        
        cursor.execute("SELECT COUNT(*) FROM containers")
        print(f"📊 Toplam {cursor.fetchone()[0]} konteyner")
        
        cursor.execute("SELECT COUNT(*) FROM collection_events")
        print(f"📊 Toplam {cursor.fetchone()[0]} toplama olayı")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ TÜM VERİLER BAŞARIYLA YÜKLENDİ!")
        print("=" * 60)
        
    except mysql.connector.Error as e:
        print(f"\n❌ Veritabanı hatası: {e}")
        print("\n⚠️ Lütfen şunları kontrol edin:")
        print("  1. MySQL çalışıyor mu?")
        print("  2. database_setup.sql çalıştırıldı mı?")
        print("  3. DB_CONFIG'deki şifre doğru mu?")
    except Exception as e:
        print(f"\n❌ Hata: {e}")

if __name__ == "__main__":
    main()
