-- Nilüfer Belediyesi Akıllı Atık Yönetim Sistemi
-- Veritabanı Kurulum Script'i

-- Veritabanını oluştur
CREATE DATABASE IF NOT EXISTS nilufer_waste_db;
USE nilufer_waste_db;

-- PostGIS uzantısını etkinleştir (PostgreSQL için)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- ==============================================================
-- TABLO OLUŞTURMA
-- ==============================================================

-- 1. Mahalleler
CREATE TABLE IF NOT EXISTS neighborhoods (
    neighborhood_id INT AUTO_INCREMENT PRIMARY KEY,
    neighborhood_name VARCHAR(255) UNIQUE NOT NULL,
    population INT,
    area_km2 DECIMAL(10,2),
    population_density DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Araç Tipleri
CREATE TABLE IF NOT EXISTS vehicle_types (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL,
    capacity_m3 DECIMAL(10,2),
    capacity_ton DECIMAL(10,2),
    fuel_consumption_per_km DECIMAL(5,2),
    co2_emission_per_km DECIMAL(5,2),
    hourly_operating_cost DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Araçlar
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT PRIMARY KEY,
    vehicle_name VARCHAR(100),
    vehicle_type_id INT,
    status VARCHAR(20) DEFAULT 'available',
    current_capacity_used DECIMAL(10,2) DEFAULT 0,
    fuel_type VARCHAR(20) DEFAULT 'diesel',
    total_km_driven INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicle_types(type_id)
);

-- 4. Konteynerler
CREATE TABLE IF NOT EXISTS containers (
    container_id INT AUTO_INCREMENT PRIMARY KEY,
    container_code VARCHAR(50) UNIQUE NOT NULL,
    neighborhood_id INT,
    container_type VARCHAR(50) NOT NULL,
    capacity_liters INT NOT NULL,
    last_collection_date TIMESTAMP,
    current_fill_level DECIMAL(3,2) DEFAULT 0.00,
    last_prediction_update TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods(neighborhood_id)
);

-- 5. Kullanıcılar
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    trust_score INT DEFAULT 0,
    total_reports_submitted INT DEFAULT 0,
    reports_accepted INT DEFAULT 0,
    reports_rejected INT DEFAULT 0,
    account_status VARCHAR(20) DEFAULT 'active',
    requires_photo BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 6. Vatandaş Bildirimleri
CREATE TABLE IF NOT EXISTS citizen_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    container_id INT,
    report_type VARCHAR(50) NOT NULL,
    reported_fill_level VARCHAR(20),
    photo_url VARCHAR(500),
    description TEXT,
    report_status VARCHAR(20) DEFAULT 'pending',
    model_prediction_score DECIMAL(3,2),
    validation_result VARCHAR(20),
    admin_reviewed BOOLEAN DEFAULT FALSE,
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (container_id) REFERENCES containers(container_id)
);

-- 7. Toplama Olayları
CREATE TABLE IF NOT EXISTS collection_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    container_id INT,
    vehicle_id INT,
    collection_date TIMESTAMP NOT NULL,
    tonnage_collected DECIMAL(10,2),
    fill_level_before DECIMAL(3,2),
    collection_duration_minutes INT,
    fuel_consumed_liters DECIMAL(10,2),
    distance_traveled_km DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (container_id) REFERENCES containers(container_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
);

-- 8. Tonaj İstatistikleri
CREATE TABLE IF NOT EXISTS tonnage_statistics (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    month VARCHAR(20),
    year INT,
    surface_tonnage DECIMAL(10,2),
    underground_tonnage DECIMAL(10,2),
    total_tonnage DECIMAL(10,2),
    average_daily_tonnage DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Tahminler (Cache)
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    container_id INT,
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    predicted_fill_level DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    is_full BOOLEAN,
    next_collection_recommended_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (container_id) REFERENCES containers(container_id)
);

-- 10. Simülasyon Geçmişi
CREATE TABLE IF NOT EXISTS simulation_runs (
    simulation_id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_name VARCHAR(255),
    simulation_parameters JSON,
    baseline_period_start DATE,
    baseline_period_end DATE,
    results JSON,
    km_savings DECIMAL(10,2),
    fuel_savings_liters DECIMAL(10,2),
    cost_impact_try DECIMAL(12,2),
    co2_reduction_kg DECIMAL(10,2),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================
-- İNDEKSLER
-- ==============================================================

CREATE INDEX idx_containers_neighborhood ON containers(neighborhood_id);
CREATE INDEX idx_containers_fill_level ON containers(current_fill_level);
CREATE INDEX idx_containers_type ON containers(container_type);

CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type_id);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_trust_score ON users(trust_score DESC);

CREATE INDEX idx_reports_user ON citizen_reports(user_id);
CREATE INDEX idx_reports_container ON citizen_reports(container_id);
CREATE INDEX idx_reports_status ON citizen_reports(report_status);
CREATE INDEX idx_reports_created ON citizen_reports(created_at DESC);

CREATE INDEX idx_events_container ON collection_events(container_id);
CREATE INDEX idx_events_vehicle ON collection_events(vehicle_id);
CREATE INDEX idx_events_date ON collection_events(collection_date DESC);

CREATE INDEX idx_predictions_container ON predictions(container_id);
CREATE INDEX idx_predictions_timestamp ON predictions(prediction_timestamp DESC);

-- ==============================================================
-- VIEW'LAR
-- ==============================================================

-- Konteyner Durum Görünümü
CREATE OR REPLACE VIEW v_container_status AS
SELECT 
    c.container_id,
    c.container_code,
    c.neighborhood_id,
    n.neighborhood_name,
    c.container_type,
    c.capacity_liters,
    c.current_fill_level,
    c.last_collection_date,
    TIMESTAMPDIFF(HOUR, c.last_collection_date, NOW()) AS hours_since_collection,
    p.predicted_fill_level AS latest_prediction,
    p.confidence_score,
    p.is_full AS needs_collection
FROM containers c
LEFT JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
LEFT JOIN (
    SELECT container_id, predicted_fill_level, confidence_score, is_full
    FROM predictions
    WHERE (container_id, prediction_timestamp) IN (
        SELECT container_id, MAX(prediction_timestamp)
        FROM predictions
        GROUP BY container_id
    )
) p ON c.container_id = p.container_id
WHERE c.status = 'active';

-- Kullanıcı Liderlik Tablosu
CREATE OR REPLACE VIEW v_user_leaderboard AS
SELECT 
    user_id,
    full_name,
    trust_score,
    total_reports_submitted,
    reports_accepted,
    CASE 
        WHEN total_reports_submitted > 0 
        THEN ROUND((reports_accepted / total_reports_submitted) * 100, 1)
        ELSE 0
    END AS accuracy_percentage
FROM users
WHERE account_status = 'active' 
    AND total_reports_submitted >= 5
ORDER BY trust_score DESC, reports_accepted DESC
LIMIT 10;

-- ==============================================================
-- STORED PROCEDURE'LER
-- ==============================================================

DELIMITER //

-- Kullanıcı Güven Puanını Güncelle
CREATE PROCEDURE update_user_trust_score(
    IN p_user_id INT,
    IN p_report_accepted BOOLEAN
)
BEGIN
    IF p_report_accepted THEN
        UPDATE users
        SET trust_score = trust_score + 2,
            reports_accepted = reports_accepted + 1,
            requires_photo = CASE WHEN trust_score + 2 >= 80 THEN FALSE ELSE TRUE END,
            total_reports_submitted = total_reports_submitted + 1
        WHERE user_id = p_user_id;
    ELSE
        UPDATE users
        SET trust_score = GREATEST(trust_score - 5, 0),
            reports_rejected = reports_rejected + 1,
            requires_photo = TRUE,
            total_reports_submitted = total_reports_submitted + 1
        WHERE user_id = p_user_id;
    END IF;
END //

DELIMITER ;

-- ==============================================================
-- VERİ EKLİYORUZ (CSV'lerden sonra Python ile doldurulacak)
-- ==============================================================

-- Örnek demo kullanıcılar
INSERT INTO users (email, password_hash, full_name, trust_score, total_reports_submitted, reports_accepted, reports_rejected) VALUES
('ahmet.y@example.com', 'hashed_password_1', 'Ahmet Y.', 98, 156, 153, 3),
('zeynep.k@example.com', 'hashed_password_2', 'Zeynep K.', 96, 143, 139, 4),
('mehmet.a@example.com', 'hashed_password_3', 'Mehmet A.', 94, 128, 123, 5),
('ayse.d@example.com', 'hashed_password_4', 'Ayşe D.', 92, 115, 110, 5),
('can.s@example.com', 'hashed_password_5', 'Can S.', 91, 108, 102, 6),
('elif.t@example.com', 'hashed_password_6', 'Elif T.', 89, 102, 95, 7),
('burak.o@example.com', 'hashed_password_7', 'Burak Ö.', 88, 98, 91, 7),
('selin.m@example.com', 'hashed_password_8', 'Selin M.', 87, 94, 87, 7),
('emre.b@example.com', 'hashed_password_9', 'Emre B.', 86, 89, 81, 8),
('deniz.l@example.com', 'hashed_password_10', 'Deniz L.', 85, 87, 79, 8);

COMMIT;
