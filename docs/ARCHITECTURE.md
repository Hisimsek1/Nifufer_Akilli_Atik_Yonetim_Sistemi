# Smart Waste Management System - Architecture Overview

## Executive Summary
This document outlines the architecture for Nilüfer Municipality's Smart Waste Management System, integrating AI-powered predictions with real-time GPS data, citizen feedback, and dynamic fleet routing.

---

## System Components

### 1. Data Layer

#### Data Sources (Existing Files)
- **address_data.csv**: Neighborhood and street information
- **container_counts.csv**: Container locations and types
- **fleet.csv**: Vehicle fleet information
- **mahalle_nufus.csv**: Population density by neighborhood
- **neighbor_days_rotations.csv**: Historical collection schedules
- **tonnages.csv**: Historical waste collection volumes
- **truck_types.csv**: Vehicle specifications and capacities
- **Yol-2025-12-16_13-38-47.json**: Road network graph data

#### Real-Time Data Streams
- **GPS Telemetry**: Vehicle location tracking
- **IoT Sensors**: Container fill-level sensors (if available)
- **Citizen Reports**: User-submitted feedback and reports

---

## AI Model Architecture

### Model #1: Fill-Level Prediction Engine

#### Input Features
```
- Historical tonnage data (tonnages.csv)
- Container type and capacity (container_counts.csv)
- Population density (mahalle_nufus.csv)
- Day of week / seasonality
- Last collection timestamp
- GPS proximity data (vehicles near containers)
- Weather data (optional enhancement)
```

#### Model Type
- **Algorithm**: Gradient Boosting (XGBoost/LightGBM) or Random Forest
- **Output**: Probability score (0-1) that a container is full
- **Threshold**: Configurable (default: 0.75 = 75% confidence)

#### Training Pipeline
1. Feature engineering from historical CSV data
2. Time-series split for validation (prevent data leakage)
3. Hyperparameter tuning via cross-validation
4. Model versioning and A/B testing framework

#### Validation Logic for Citizen Feedback
```python
def validate_citizen_report(container_id, user_report, model):
    """
    Verifies if citizen report is plausible
    """
    # Get model prediction
    prediction_score = model.predict(container_id)
    
    # Define plausibility thresholds
    if user_report == "FULL":
        # User claims full - model must agree (>50% probability)
        is_plausible = prediction_score > 0.50
    elif user_report == "EMPTY":
        # User claims empty - model must agree (<30% probability)
        is_plausible = prediction_score < 0.30
    else:
        # User claims partially full
        is_plausible = 0.20 < prediction_score < 0.80
    
    return is_plausible, prediction_score
```

---

### Model #2: Dynamic Routing & Fleet Dispatch

#### Input Data
```
- Validated full containers (from Model #1)
- Current vehicle locations (GPS stream)
- Vehicle capacity and type (fleet.csv, truck_types.csv)
- Road network graph (Yol-2025-12-16_13-38-47.json)
- Traffic conditions (if available)
- Vehicle current load status
```

#### Algorithm Components

##### A. Vehicle Selection Logic
```
Decision Criteria:
1. Distance to nearest full container
2. Remaining vehicle capacity
3. Vehicle type compatibility with container
4. Current route efficiency
5. Fuel consumption optimization
```

##### B. Route Optimization
- **Algorithm**: Modified Vehicle Routing Problem (VRP)
- **Approach**: 
  - Dijkstra's algorithm for shortest path (road network JSON)
  - Constraint programming for multiple stops
  - Real-time rerouting when new containers become full

##### C. Output
- **Vehicle Assignment**: Which truck to dispatch
- **Optimized Route**: Step-by-step navigation waypoints
- **ETA Calculation**: Estimated completion time
- **Efficiency Metrics**: Expected fuel consumption, CO2 emissions

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├─────────────────────┬───────────────────────────────────────────┤
│  Citizen Dashboard  │         Admin Dashboard                   │
│  - Report Issues    │  - Fleet Management                       │
│  - View Stats       │  - Simulation Sandbox                     │
│  - Leaderboard      │  - Real-time Monitoring                   │
└─────────────────────┴───────────────────────────────────────────┘
                               ▲
                               │ REST API / WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                          │
├─────────────────────┬───────────────────────────────────────────┤
│  Feedback Handler   │     Routing Service                       │
│  - Validate reports │  - Fleet dispatcher                       │
│  - Update trust     │  - Route optimizer                        │
│  - Photo verify     │  - GPS tracker                            │
└─────────────────────┴───────────────────────────────────────────┘
                               ▲
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AI/ML LAYER                              │
├─────────────────────┬───────────────────────────────────────────┤
│  Model #1           │     Model #2                              │
│  Fill Predictor     │  Dynamic Router                           │
│  (Classification)   │  (Optimization)                           │
└─────────────────────┴───────────────────────────────────────────┘
                               ▲
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                               │
├──────────────────┬──────────────────┬───────────────────────────┤
│  PostgreSQL/     │  Redis Cache     │  Time-Series DB          │
│  MySQL           │  (Real-time)     │  (GPS/Sensor data)       │
│  - Containers    │  - Vehicle state │  - InfluxDB/TimescaleDB  │
│  - Users         │  - Active routes │  - Telemetry logs        │
│  - Historical    │  - Predictions   │                          │
└──────────────────┴──────────────────┴───────────────────────────┘
                               ▲
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                         │
│  - CSV Import Pipeline (historical data)                        │
│  - GPS Stream Processor (Apache Kafka/RabbitMQ)                 │
│  - Citizen Report API                                            │
│  - Road Network Graph Builder                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Citizen Report Processing

```
1. Citizen submits report → "Container X is full"
                          ↓
2. Check user trust score → Score < threshold? → Require photo + GPS
                          ↓ (Score sufficient)
3. Call Model #1 → Predict fill level of Container X
                          ↓
4. Validation Logic → Is report plausible?
                          ↓
        ┌─────────────────┴─────────────────┐
        │ PLAUSIBLE                         │ IMPLAUSIBLE
        ↓                                   ↓
5. Accept report                     Reject report
   Update container status           Log for review
   Increase user trust +1            Decrease user trust -1
        ↓                                   ↓
6. Trigger Model #2                  Notify user (soft warning)
   Fleet dispatch decision
        ↓
7. Generate optimized route
   Assign vehicle
        ↓
8. Send route to driver app
```

---

## Data Flow: Admin Simulation

```
1. Admin changes simulation parameters
   - Example: "Add 2 more trucks"
                          ↓
2. Historical data + new parameters → Simulation Engine
                          ↓
3. Run Monte Carlo simulation
   - Replay past 30 days with new fleet
   - Calculate metrics per day
                          ↓
4. Aggregate results:
   - Average fuel consumption change
   - Total kilometers driven change
   - Collection efficiency (containers missed)
   - Cost analysis (operational vs. savings)
   - CO2 emissions delta
                          ↓
5. Display real-time results in dashboard
   - Comparative charts (Before/After)
   - Cost-benefit analysis
   - Recommendation: "Add trucks" or "No change needed"
```

---

## Technology Stack Recommendations

### Backend
- **Framework**: Python FastAPI or Django REST Framework
- **AI/ML**: scikit-learn, XGBoost, TensorFlow (optional for deep learning)
- **Routing**: OR-Tools (Google), GraphHopper, OSRM

### Database
- **Primary DB**: PostgreSQL 14+ (with PostGIS for geospatial queries)
- **Cache**: Redis 7+ (real-time state)
- **Time-Series**: TimescaleDB or InfluxDB (GPS data)

### Frontend
- **Framework**: React or Vue.js (but can be vanilla JS for simpler version)
- **Maps**: Leaflet.js or Mapbox GL
- **Charts**: Chart.js or D3.js

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Message Queue**: RabbitMQ or Apache Kafka (GPS stream)
- **Monitoring**: Prometheus + Grafana

---

## Security & Access Control

### Citizen Dashboard
- **Public Access**: Read-only statistics
- **Authenticated Users**: Submit reports (after email verification)
- **Trusted Users**: Submit without photo (trust score > 80)

### Admin Dashboard
- **Role**: Municipality Operations Manager
- **Authentication**: OAuth 2.0 + MFA (Multi-Factor)
- **Audit Logging**: All simulation runs and parameter changes logged

---

## Scalability Considerations

1. **Horizontal Scaling**: Stateless API servers behind load balancer
2. **Database Sharding**: Partition by neighborhood/district
3. **Caching Strategy**: Cache prediction scores for 15-minute windows
4. **Async Processing**: Use Celery for background tasks (model training, report processing)
5. **CDN**: Static assets (images, CSS) served via CDN

---

## Performance Targets

- **Model #1 Inference**: < 100ms per prediction
- **Model #2 Route Generation**: < 5 seconds for 20 container stops
- **API Response Time**: < 200ms (95th percentile)
- **GPS Update Frequency**: Every 30 seconds
- **Dashboard Load Time**: < 2 seconds

---

## Future Enhancements

1. **Mobile App**: Native iOS/Android driver app
2. **Computer Vision**: Automated container fill-level detection via cameras
3. **Predictive Maintenance**: Forecast vehicle maintenance needs
4. **Integration**: Connect with other municipality systems (311, CRM)
5. **Advanced Analytics**: Citizen satisfaction prediction model
