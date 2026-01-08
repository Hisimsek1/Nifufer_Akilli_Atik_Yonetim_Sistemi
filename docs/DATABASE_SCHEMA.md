# Database Schema - Smart Waste Management System

## Database Technology
**Primary Database**: PostgreSQL 14+ with PostGIS extension (for geospatial data)

---

## Schema Overview

### Core Tables
1. **containers** - Waste container locations and specifications
2. **vehicles** - Fleet information
3. **vehicle_types** - Truck specifications
4. **neighborhoods** - District and population data
5. **users** - Citizen accounts and trust scores
6. **citizen_reports** - User-submitted feedback
7. **collection_events** - Historical collection records
8. **routes** - Generated collection routes
9. **predictions** - Model outputs (cached)
10. **simulation_runs** - Admin simulation history

---

## Detailed Table Definitions

### 1. containers
```sql
CREATE TABLE containers (
    container_id SERIAL PRIMARY KEY,
    container_code VARCHAR(50) UNIQUE NOT NULL, -- e.g., "NIL-001-A"
    neighborhood_id INTEGER REFERENCES neighborhoods(neighborhood_id),
    street_name VARCHAR(255),
    location GEOGRAPHY(POINT, 4326) NOT NULL, -- PostGIS: lat/lng
    container_type VARCHAR(50) NOT NULL, -- 'plastic', 'glass', 'organic', 'paper'
    capacity_liters INTEGER NOT NULL, -- e.g., 1100, 2400
    last_collection_date TIMESTAMP,
    current_fill_level DECIMAL(3,2), -- 0.00 to 1.00 (predicted)
    last_prediction_update TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'maintenance', 'removed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_containers_neighborhood ON containers(neighborhood_id);
CREATE INDEX idx_containers_location ON containers USING GIST(location);
CREATE INDEX idx_containers_fill_level ON containers(current_fill_level);
CREATE INDEX idx_containers_type ON containers(container_type);
```

### 2. vehicles
```sql
CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    vehicle_plate VARCHAR(20) UNIQUE NOT NULL, -- License plate
    vehicle_type_id INTEGER REFERENCES vehicle_types(type_id),
    status VARCHAR(20) DEFAULT 'available', -- 'available', 'on_route', 'maintenance'
    current_location GEOGRAPHY(POINT, 4326), -- Real-time GPS
    current_capacity_used INTEGER DEFAULT 0, -- Current load in liters
    fuel_type VARCHAR(20), -- 'diesel', 'electric', 'hybrid'
    last_maintenance_date DATE,
    total_km_driven INTEGER DEFAULT 0,
    assigned_route_id INTEGER REFERENCES routes(route_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_location ON vehicles USING GIST(current_location);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type_id);
```

### 3. vehicle_types
```sql
CREATE TABLE vehicle_types (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL, -- 'small_truck', 'large_truck', 'compactor'
    capacity_liters INTEGER NOT NULL,
    fuel_consumption_per_km DECIMAL(5,2), -- liters per km
    co2_emission_per_km DECIMAL(5,2), -- kg CO2 per km
    hourly_operating_cost DECIMAL(8,2), -- TRY per hour
    compatible_container_types TEXT[], -- Array: {'plastic', 'organic'}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sample data
INSERT INTO vehicle_types (type_name, capacity_liters, fuel_consumption_per_km, co2_emission_per_km, hourly_operating_cost, compatible_container_types) VALUES
('small_truck', 5000, 0.25, 0.65, 150.00, ARRAY['plastic', 'glass', 'paper']),
('large_truck', 12000, 0.40, 1.05, 250.00, ARRAY['plastic', 'organic', 'glass', 'paper']),
('compactor', 18000, 0.50, 1.30, 300.00, ARRAY['organic']);
```

### 4. neighborhoods
```sql
CREATE TABLE neighborhoods (
    neighborhood_id SERIAL PRIMARY KEY,
    neighborhood_name VARCHAR(255) UNIQUE NOT NULL,
    district_name VARCHAR(255),
    population INTEGER,
    area_km2 DECIMAL(10,2),
    population_density DECIMAL(10,2), -- calculated: population / area
    boundary GEOGRAPHY(POLYGON, 4326), -- PostGIS: neighborhood boundary
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_neighborhoods_name ON neighborhoods(neighborhood_name);
CREATE INDEX idx_neighborhoods_boundary ON neighborhoods USING GIST(boundary);
```

### 5. users (Citizen Accounts)
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    trust_score INTEGER DEFAULT 0, -- Starts at 0, increases with valid reports
    total_reports_submitted INTEGER DEFAULT 0,
    reports_accepted INTEGER DEFAULT 0,
    reports_rejected INTEGER DEFAULT 0,
    account_status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'banned'
    requires_photo BOOLEAN DEFAULT TRUE, -- Trusted users can submit without photo
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_trust_score ON users(trust_score DESC);
CREATE INDEX idx_users_status ON users(account_status);
```

### 6. citizen_reports
```sql
CREATE TABLE citizen_reports (
    report_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    container_id INTEGER REFERENCES containers(container_id),
    report_type VARCHAR(50) NOT NULL, -- 'full', 'empty', 'damaged', 'missing'
    reported_fill_level VARCHAR(20), -- 'empty', 'half', 'full', 'overflowing'
    photo_url VARCHAR(500), -- S3/cloud storage URL
    location GEOGRAPHY(POINT, 4326), -- User's GPS location at report time
    description TEXT,
    report_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'validated', 'rejected', 'processed'
    model_prediction_score DECIMAL(3,2), -- Model #1 output for validation
    validation_result VARCHAR(20), -- 'plausible', 'implausible', 'needs_review'
    admin_reviewed BOOLEAN DEFAULT FALSE,
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reports_user ON citizen_reports(user_id);
CREATE INDEX idx_reports_container ON citizen_reports(container_id);
CREATE INDEX idx_reports_status ON citizen_reports(report_status);
CREATE INDEX idx_reports_created ON citizen_reports(created_at DESC);
```

### 7. collection_events
```sql
CREATE TABLE collection_events (
    event_id SERIAL PRIMARY KEY,
    container_id INTEGER REFERENCES containers(container_id),
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    route_id INTEGER REFERENCES routes(route_id),
    collection_date TIMESTAMP NOT NULL,
    tonnage_collected DECIMAL(10,2), -- Weight in kg
    fill_level_before DECIMAL(3,2), -- 0.00 to 1.00
    collection_duration_minutes INTEGER, -- Time spent at this container
    fuel_consumed_liters DECIMAL(10,2),
    distance_traveled_km DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_events_container ON collection_events(container_id);
CREATE INDEX idx_events_vehicle ON collection_events(vehicle_id);
CREATE INDEX idx_events_date ON collection_events(collection_date DESC);
CREATE INDEX idx_events_route ON collection_events(route_id);
```

### 8. routes
```sql
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    route_date DATE NOT NULL,
    route_status VARCHAR(20) DEFAULT 'planned', -- 'planned', 'in_progress', 'completed', 'cancelled'
    total_containers INTEGER,
    total_distance_km DECIMAL(10,2),
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    total_tonnage_collected DECIMAL(10,2),
    fuel_consumed_liters DECIMAL(10,2),
    co2_emissions_kg DECIMAL(10,2),
    route_geometry GEOGRAPHY(LINESTRING, 4326), -- Full route path
    optimization_algorithm VARCHAR(50), -- 'dijkstra', 'genetic', 'greedy'
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_routes_vehicle ON routes(vehicle_id);
CREATE INDEX idx_routes_date ON routes(route_date DESC);
CREATE INDEX idx_routes_status ON routes(route_status);
```

### 9. route_stops (Many-to-Many: Routes and Containers)
```sql
CREATE TABLE route_stops (
    stop_id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(route_id) ON DELETE CASCADE,
    container_id INTEGER REFERENCES containers(container_id),
    stop_sequence INTEGER NOT NULL, -- Order of visit: 1, 2, 3...
    estimated_arrival_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    estimated_fill_level DECIMAL(3,2), -- Predicted when route created
    actual_tonnage_collected DECIMAL(10,2),
    stop_duration_minutes INTEGER,
    stop_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'skipped'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_stops_route ON route_stops(route_id);
CREATE INDEX idx_stops_container ON route_stops(container_id);
CREATE INDEX idx_stops_sequence ON route_stops(route_id, stop_sequence);
```

### 10. predictions (Cached Model Outputs)
```sql
CREATE TABLE predictions (
    prediction_id SERIAL PRIMARY KEY,
    container_id INTEGER REFERENCES containers(container_id),
    prediction_timestamp TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50), -- 'v1.2.3' for model tracking
    predicted_fill_level DECIMAL(3,2), -- 0.00 to 1.00
    confidence_score DECIMAL(3,2), -- Model confidence
    feature_importance JSONB, -- Store important features for explainability
    is_full BOOLEAN, -- Threshold-based decision (e.g., > 0.75)
    next_collection_recommended_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_predictions_container ON predictions(container_id);
CREATE INDEX idx_predictions_timestamp ON predictions(prediction_timestamp DESC);
CREATE INDEX idx_predictions_is_full ON predictions(is_full);

-- Partial index for recent predictions only (performance optimization)
CREATE INDEX idx_predictions_recent ON predictions(container_id, prediction_timestamp DESC) 
WHERE prediction_timestamp > NOW() - INTERVAL '7 days';
```

### 11. simulation_runs
```sql
CREATE TABLE simulation_runs (
    simulation_id SERIAL PRIMARY KEY,
    admin_user_id INTEGER REFERENCES users(user_id),
    simulation_name VARCHAR(255),
    simulation_parameters JSONB NOT NULL, -- Store all input parameters
    -- Example: {"num_vehicles": 15, "vehicle_types": {"small": 5, "large": 10}}
    baseline_period_start DATE,
    baseline_period_end DATE,
    results JSONB, -- Store all calculated metrics
    -- Example: {"fuel_savings": 1200.5, "cost_impact": -5000, "co2_reduction": 320}
    km_savings DECIMAL(10,2),
    fuel_savings_liters DECIMAL(10,2),
    cost_impact_try DECIMAL(12,2), -- Negative = savings, Positive = cost
    co2_reduction_kg DECIMAL(10,2),
    citizen_satisfaction_score DECIMAL(3,2),
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_simulations_admin ON simulation_runs(admin_user_id);
CREATE INDEX idx_simulations_created ON simulation_runs(created_at DESC);
```

### 12. vehicle_gps_logs (Time-Series Data)
**Note**: Consider using TimescaleDB extension for this table
```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE vehicle_gps_logs (
    log_id BIGSERIAL,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    timestamp TIMESTAMP NOT NULL,
    location GEOGRAPHY(POINT, 4326),
    speed_kmh DECIMAL(5,2),
    heading_degrees INTEGER, -- 0-360
    fuel_level_percent DECIMAL(5,2),
    engine_status VARCHAR(20), -- 'on', 'off', 'idle'
    PRIMARY KEY (vehicle_id, timestamp)
);

-- Convert to TimescaleDB hypertable (partitioned by time)
SELECT create_hypertable('vehicle_gps_logs', 'timestamp');

-- Indexes
CREATE INDEX idx_gps_vehicle_time ON vehicle_gps_logs(vehicle_id, timestamp DESC);
CREATE INDEX idx_gps_location ON vehicle_gps_logs USING GIST(location);
```

---

## Views (Pre-computed Queries)

### View: Container Fill Status Dashboard
```sql
CREATE VIEW v_container_status AS
SELECT 
    c.container_id,
    c.container_code,
    c.neighborhood_id,
    n.neighborhood_name,
    c.container_type,
    c.capacity_liters,
    c.current_fill_level,
    c.last_collection_date,
    EXTRACT(EPOCH FROM (NOW() - c.last_collection_date))/3600 AS hours_since_collection,
    p.predicted_fill_level AS latest_prediction,
    p.confidence_score,
    p.is_full AS needs_collection,
    ST_X(c.location::geometry) AS longitude,
    ST_Y(c.location::geometry) AS latitude
FROM containers c
LEFT JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
LEFT JOIN LATERAL (
    SELECT predicted_fill_level, confidence_score, is_full
    FROM predictions
    WHERE container_id = c.container_id
    ORDER BY prediction_timestamp DESC
    LIMIT 1
) p ON TRUE
WHERE c.status = 'active';
```

### View: Fleet Efficiency Metrics
```sql
CREATE VIEW v_fleet_efficiency AS
SELECT 
    v.vehicle_id,
    v.vehicle_plate,
    vt.type_name,
    COUNT(DISTINCT r.route_id) AS total_routes_completed,
    SUM(r.total_distance_km) AS total_km_driven,
    SUM(r.fuel_consumed_liters) AS total_fuel_consumed,
    SUM(r.total_tonnage_collected) AS total_waste_collected,
    AVG(r.actual_duration_minutes) AS avg_route_duration,
    SUM(r.co2_emissions_kg) AS total_co2_emissions,
    (SUM(r.total_tonnage_collected) / NULLIF(SUM(r.fuel_consumed_liters), 0)) AS efficiency_kg_per_liter
FROM vehicles v
JOIN vehicle_types vt ON v.vehicle_type_id = vt.type_id
LEFT JOIN routes r ON v.vehicle_id = r.vehicle_id 
    AND r.route_status = 'completed'
    AND r.route_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY v.vehicle_id, v.vehicle_plate, vt.type_name;
```

### View: User Leaderboard (Top 10 Most Reliable)
```sql
CREATE VIEW v_user_leaderboard AS
SELECT 
    user_id,
    full_name,
    trust_score,
    total_reports_submitted,
    reports_accepted,
    CASE 
        WHEN total_reports_submitted > 0 
        THEN ROUND((reports_accepted::DECIMAL / total_reports_submitted) * 100, 1)
        ELSE 0
    END AS accuracy_percentage,
    RANK() OVER (ORDER BY trust_score DESC, reports_accepted DESC) AS rank
FROM users
WHERE account_status = 'active' 
    AND total_reports_submitted >= 5 -- Minimum reports to qualify
ORDER BY trust_score DESC, reports_accepted DESC
LIMIT 10;
```

---

## Stored Procedures

### Update User Trust Score
```sql
CREATE OR REPLACE FUNCTION update_user_trust_score(
    p_user_id INTEGER,
    p_report_accepted BOOLEAN
) RETURNS VOID AS $$
BEGIN
    IF p_report_accepted THEN
        UPDATE users
        SET trust_score = trust_score + 2,
            reports_accepted = reports_accepted + 1,
            requires_photo = CASE WHEN trust_score + 2 >= 80 THEN FALSE ELSE TRUE END
        WHERE user_id = p_user_id;
    ELSE
        UPDATE users
        SET trust_score = GREATEST(trust_score - 5, 0), -- Don't go below 0
            reports_rejected = reports_rejected + 1,
            requires_photo = TRUE
        WHERE user_id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

### Calculate Distance Between Container and Vehicle
```sql
CREATE OR REPLACE FUNCTION calculate_distance_km(
    container_location GEOGRAPHY,
    vehicle_location GEOGRAPHY
) RETURNS DECIMAL AS $$
BEGIN
    RETURN ST_Distance(container_location, vehicle_location) / 1000.0; -- Convert meters to km
END;
$$ LANGUAGE plpgsql;
```

---

## Data Migration Scripts

### Import from CSV Files
```sql
-- Import neighborhoods
COPY neighborhoods(neighborhood_name, population, area_km2)
FROM '/path/to/mahalle_nufus.csv'
DELIMITER ','
CSV HEADER;

-- Import fleet
COPY vehicles(vehicle_plate, vehicle_type_id, status)
FROM '/path/to/fleet.csv'
DELIMITER ','
CSV HEADER;

-- Import historical tonnage
COPY collection_events(container_id, vehicle_id, collection_date, tonnage_collected)
FROM '/path/to/tonnages.csv'
DELIMITER ','
CSV HEADER;
```

---

## Backup & Maintenance

### Daily Backup Job
```sql
-- Automated backup using pg_dump
pg_dump -U postgres -d nilufer_waste_db -F c -f backup_$(date +%Y%m%d).dump
```

### Archive Old GPS Data (Keep last 90 days)
```sql
DELETE FROM vehicle_gps_logs 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## Performance Optimization Recommendations

1. **Partitioning**: Partition `collection_events` by month
2. **Materialized Views**: Refresh `v_fleet_efficiency` hourly
3. **Connection Pooling**: Use PgBouncer for high-traffic scenarios
4. **Index Maintenance**: Run VACUUM ANALYZE weekly
5. **Query Optimization**: Monitor slow queries with pg_stat_statements
