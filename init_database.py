"""
SQLite Veritabanı Kurulum Script'i
Nilüfer Belediyesi Akıllı Atık Yönetim Sistemi
"""

import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = 'nilufer_waste.db'

def create_tables():
    """Tabloları oluştur"""
    print("\n📊 Veritabanı tabloları oluşturuluyor...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Neighborhoods tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS neighborhoods (
        neighborhood_id INTEGER PRIMARY KEY AUTOINCREMENT,
        neighborhood_name TEXT NOT NULL UNIQUE,
        population INTEGER,
        population_density REAL,
        area_km2 REAL
    )
    """)
    
    # Vehicle types tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL UNIQUE,
        capacity_tons REAL NOT NULL,
        hourly_cost REAL NOT NULL
    )
    """)
    
    # Vehicles tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL UNIQUE,
        type_id INTEGER,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (type_id) REFERENCES vehicle_types(type_id)
    )
    """)
    
    # Containers tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS containers (
        container_id INTEGER PRIMARY KEY AUTOINCREMENT,
        neighborhood_id INTEGER,
        container_type TEXT NOT NULL,
        capacity_liters INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        last_collection_date TEXT,
        current_fill_level REAL DEFAULT 0.5,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods(neighborhood_id)
    )
    """)
    
    # Users tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        tc_number TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        phone TEXT,
        role TEXT DEFAULT 'citizen',
        trust_score REAL DEFAULT 0.5,
        total_reports INTEGER DEFAULT 0,
        accurate_reports INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Citizen reports tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS citizen_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        container_id INTEGER,
        fill_level_estimate REAL NOT NULL,
        photo_url TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        notes TEXT,
        prediction_diff REAL,
        is_verified INTEGER DEFAULT 0,
        verified_at TEXT,
        actual_full INTEGER,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (container_id) REFERENCES containers(container_id)
    )
    """)
    
    # Collection events tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collection_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER,
        vehicle_id INTEGER,
        collection_date TEXT NOT NULL,
        tonnage_collected REAL NOT NULL,
        fill_level_before REAL,
        collection_duration_minutes INTEGER,
        FOREIGN KEY (container_id) REFERENCES containers(container_id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
    )
    """)
    
    # Tonnage statistics tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tonnage_statistics (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT NOT NULL,
        surface_tonnage REAL,
        underground_tonnage REAL,
        total_tonnage REAL
    )
    """)
    
    # Predictions tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER,
        model_version TEXT NOT NULL,
        predicted_fill_level REAL NOT NULL,
        confidence_score REAL NOT NULL,
        is_full INTEGER NOT NULL,
        predicted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (container_id) REFERENCES containers(container_id)
    )
    """)
    
    # Simulation runs tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_runs (
        simulation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_user_id INTEGER,
        scenario_params TEXT NOT NULL,
        estimated_cost REAL,
        estimated_time_hours REAL,
        run_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_user_id) REFERENCES users(user_id)
    )
    """)
    
    # İndeksler
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_containers_neighborhood ON containers(neighborhood_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_containers_fill ON containers(current_fill_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user ON citizen_reports(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_container ON citizen_reports(container_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_trust ON users(trust_score)")
    
    conn.commit()
    print("✓ Tablolar oluşturuldu")
    
    return conn

def insert_test_users(conn):
    """Test kullanıcıları ekle"""
    print("\n👥 Test kullanıcıları ekleniyor...")
    
    cursor = conn.cursor()
    
    users = [
        ('Ahmet Yılmaz', 'ahmet@test.com', '12345678901', 'test123', '0532 111 1111', 'citizen', 0.85, 45, 38),
        ('Ayşe Demir', 'ayse@test.com', '12345678902', 'test123', '0532 222 2222', 'citizen', 0.92, 67, 62),
        ('Mehmet Kaya', 'mehmet@test.com', '12345678903', 'test123', '0532 333 3333', 'citizen', 0.45, 28, 13),
        ('Admin User', 'admin@nilufer.gov.tr', '99999999999', 'admin123', '0224 444 4444', 'admin', 1.00, 0, 0)
    ]
    
    for name, email, tc, password, phone, role, trust, total, accurate in users:
        password_hash = generate_password_hash(password)
        try:
            cursor.execute("""
                INSERT INTO users (name, email, tc_number, password_hash, phone, role, trust_score, total_reports, accurate_reports)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, email, tc, password_hash, phone, role, trust, total, accurate))
        except:
            pass  # Zaten varsa geç
    
    conn.commit()
    print(f"✓ {len(users)} test kullanıcısı eklendi")

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("NİLÜFER BELEDİYESİ - VERİTABANI KURULUMU")
    print("SQLite (Kolay Başlangıç)")
    print("=" * 60)
    
    conn = create_tables()
    insert_test_users(conn)
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ VERİTABANI HAZIR!")
    print("=" * 60)
    print(f"\n📁 Veritabanı dosyası: {DB_PATH}")
    print("\n📋 Sıradaki adım: python load_data_sqlite.py")

if __name__ == "__main__":
    main()
