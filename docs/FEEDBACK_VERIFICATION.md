# User Feedback Verification Algorithm

## Overview
This document describes the algorithmic approach to validate citizen-submitted waste container reports using AI Model #1 (Fill-Level Prediction). The system prevents abuse and maintains data integrity by cross-checking user claims against ML predictions.

---

## Core Principle

**Verification Philosophy**: 
User feedback is valuable, but must be validated against statistical likelihood before accepting. This prevents:
- Malicious reports (spam, trolling)
- Honest mistakes (misidentification of containers)
- System gaming (attempting to manipulate leaderboard)

---

## Algorithm Flow

### Step 1: Receive User Report
```
INPUT:
- user_id
- container_id
- reported_status: "EMPTY" | "HALF_FULL" | "FULL" | "OVERFLOWING"
- photo_url (optional, required for low-trust users)
- gps_location (optional, required for low-trust users)
- timestamp
```

### Step 2: Check User Trust Score
```python
def check_user_requirements(user_id):
    """
    Determine if additional verification is needed
    """
    user = db.query(User).get(user_id)
    
    # Trust levels
    if user.trust_score < 50:
        return {
            'requires_photo': True,
            'requires_gps': True,
            'manual_review_probability': 0.3  # 30% of reports go to admin review
        }
    elif user.trust_score < 80:
        return {
            'requires_photo': False,
            'requires_gps': True,
            'manual_review_probability': 0.1
        }
    else:  # Trust score >= 80
        return {
            'requires_photo': False,
            'requires_gps': False,
            'manual_review_probability': 0.02  # Only 2% spot-checked
        }
```

### Step 3: Verify Photo (If Required)
```python
def verify_photo(photo_url, container_id, gps_location):
    """
    Optional: Use Computer Vision to validate photo
    """
    # Phase 1: Basic checks
    if not photo_url:
        return {'valid': False, 'reason': 'Photo required but not provided'}
    
    # Phase 2: Metadata verification
    photo_metadata = get_exif_data(photo_url)
    
    # Check if photo was taken recently (within 1 hour)
    if photo_metadata.timestamp < (now() - timedelta(hours=1)):
        return {'valid': False, 'reason': 'Photo too old'}
    
    # Check if GPS in photo matches reported location (within 100m)
    if photo_metadata.gps_coords:
        distance = calculate_distance(photo_metadata.gps_coords, gps_location)
        if distance > 100:  # meters
            return {'valid': False, 'reason': 'Photo location mismatch'}
    
    # Phase 3: Advanced - Image recognition (future enhancement)
    # - Detect if image contains a waste container
    # - Estimate fill level from image
    # - Compare with user's claim
    
    return {'valid': True, 'confidence': 0.85}
```

### Step 4: Get AI Model Prediction
```python
def get_fill_prediction(container_id):
    """
    Call Model #1 to get current fill level prediction
    """
    container = db.query(Container).get(container_id)
    
    # Feature engineering
    features = {
        'hours_since_last_collection': (now() - container.last_collection_date).total_seconds() / 3600,
        'container_capacity': container.capacity_liters,
        'population_density': container.neighborhood.population_density,
        'day_of_week': now().weekday(),
        'is_weekend': now().weekday() >= 5,
        'season': get_season(now()),
        'avg_tonnage_last_month': get_avg_tonnage(container_id, days=30),
        'container_type': container.container_type,
        'historical_fill_rate': calculate_fill_rate(container_id)
    }
    
    # Load trained model
    model = load_model('fill_predictor_v1.pkl')
    
    # Predict probability that container is full
    prediction = model.predict_proba([features])[0]
    
    return {
        'fill_probability': prediction[1],  # Probability of being full
        'confidence': max(prediction),
        'model_version': 'v1.2.3'
    }
```

### Step 5: Validation Logic (Core Algorithm)
```python
def validate_report(user_report, model_prediction):
    """
    CRITICAL FUNCTION: Determine if user report is plausible
    
    Returns:
        - validation_result: 'ACCEPTED', 'REJECTED', 'NEEDS_REVIEW'
        - confidence_score: 0.0 to 1.0
        - reason: Explanation for decision
    """
    
    reported_status = user_report['reported_status']
    fill_probability = model_prediction['fill_probability']
    
    # Define threshold ranges for each status
    thresholds = {
        'EMPTY': {'min': 0.0, 'max': 0.25},
        'HALF_FULL': {'min': 0.25, 'max': 0.75},
        'FULL': {'min': 0.75, 'max': 0.90},
        'OVERFLOWING': {'min': 0.90, 'max': 1.0}
    }
    
    # Get expected range for reported status
    expected_range = thresholds[reported_status]
    
    # Calculate how far off the report is from model prediction
    if expected_range['min'] <= fill_probability <= expected_range['max']:
        # Report aligns with model - ACCEPT
        deviation = 0
        result = 'ACCEPTED'
        confidence = model_prediction['confidence']
        reason = f"Report matches model prediction (fill level: {fill_probability:.2%})"
        
    else:
        # Calculate deviation
        if fill_probability < expected_range['min']:
            deviation = expected_range['min'] - fill_probability
        else:
            deviation = fill_probability - expected_range['max']
        
        # Decision based on deviation severity
        if deviation < 0.20:  # Within 20% tolerance
            result = 'NEEDS_REVIEW'
            confidence = 0.5
            reason = f"Minor deviation from model ({deviation:.2%}). Flagged for review."
            
        elif deviation < 0.40:  # 20-40% deviation
            result = 'REJECTED'
            confidence = 0.7
            reason = f"Moderate deviation from model ({deviation:.2%}). Report rejected."
            
        else:  # > 40% deviation
            result = 'REJECTED'
            confidence = 0.95
            reason = f"Significant deviation from model ({deviation:.2%}). Report highly implausible."
    
    return {
        'validation_result': result,
        'confidence_score': confidence,
        'reason': reason,
        'model_prediction': fill_probability,
        'user_claim': reported_status,
        'deviation': deviation if deviation else 0
    }
```

### Step 6: Update Database & User Trust Score
```python
def process_validation_result(user_id, report_id, validation):
    """
    Apply validation result and update user trust
    """
    
    if validation['validation_result'] == 'ACCEPTED':
        # Accept the report
        db.execute("""
            UPDATE citizen_reports
            SET report_status = 'validated',
                validation_result = 'plausible',
                model_prediction_score = :pred_score,
                processed_at = NOW()
            WHERE report_id = :report_id
        """, {'pred_score': validation['model_prediction'], 'report_id': report_id})
        
        # Update container fill level
        container_id = get_report_container(report_id)
        db.execute("""
            UPDATE containers
            SET current_fill_level = :fill_level,
                last_prediction_update = NOW()
            WHERE container_id = :container_id
        """, {'fill_level': validation['model_prediction'], 'container_id': container_id})
        
        # INCREASE user trust score
        update_user_trust_score(user_id, report_accepted=True)
        
        # Trigger Model #2: Check if route dispatch needed
        if validation['model_prediction'] >= 0.75:
            trigger_route_optimization(container_id)
        
        return {'status': 'success', 'message': 'Report accepted. Thank you!'}
    
    elif validation['validation_result'] == 'REJECTED':
        # Reject the report
        db.execute("""
            UPDATE citizen_reports
            SET report_status = 'rejected',
                validation_result = 'implausible',
                model_prediction_score = :pred_score,
                processed_at = NOW()
            WHERE report_id = :report_id
        """, {'pred_score': validation['model_prediction'], 'report_id': report_id})
        
        # DECREASE user trust score
        update_user_trust_score(user_id, report_accepted=False)
        
        return {
            'status': 'rejected',
            'message': f"Report could not be validated. {validation['reason']}",
            'suggestion': 'Please verify the container ID and status before resubmitting.'
        }
    
    else:  # NEEDS_REVIEW
        # Flag for manual admin review
        db.execute("""
            UPDATE citizen_reports
            SET report_status = 'pending_review',
                validation_result = 'needs_review',
                model_prediction_score = :pred_score,
                admin_reviewed = FALSE
            WHERE report_id = :report_id
        """, {'pred_score': validation['model_prediction'], 'report_id': report_id})
        
        # Neutral - no trust score change yet
        
        return {
            'status': 'pending',
            'message': 'Your report has been submitted for review. We will verify shortly.',
            'estimated_review_time': '2-4 hours'
        }
```

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  USER SUBMITS REPORT                                            │
│  - Container ID: "NIL-001-A"                                    │
│  - Status: "FULL"                                               │
│  - (Optional) Photo + GPS                                       │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: CHECK USER TRUST SCORE                                 │
│  - Trust Score < 50? → Require Photo + GPS                      │
│  - Trust Score < 80? → Require GPS only                         │
│  - Trust Score >= 80? → No additional requirements              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: VERIFY PHOTO & GPS (if required)                       │
│  - Check EXIF timestamp (< 1 hour old?)                         │
│  - Verify GPS matches reported location (< 100m?)               │
│  - [Future] Run image recognition to detect container           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: CALL AI MODEL #1                                       │
│  - Extract features (time, capacity, population, etc.)          │
│  - model.predict_proba(features)                                │
│  - Output: fill_probability = 0.82 (82% likely full)            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: VALIDATION LOGIC                                       │
│                                                                  │
│  User claims: "FULL" (expected range: 0.75 - 0.90)             │
│  Model predicts: 0.82                                           │
│                                                                  │
│  ✓ Prediction within expected range → ACCEPT                    │
│                                                                  │
│  Alternative scenarios:                                          │
│  - Model predicts 0.65, user claims "FULL"                      │
│    → Deviation = 0.10 (10%) → NEEDS_REVIEW                      │
│  - Model predicts 0.30, user claims "FULL"                      │
│    → Deviation = 0.45 (45%) → REJECTED                          │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  ACCEPTED   │ │ NEEDS_REVIEW│ │  REJECTED   │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Update DB   │ │ Flag for    │ │ Update DB   │
│ Trust +2    │ │ Admin Review│ │ Trust -5    │
│ Trigger     │ │ No trust    │ │ Notify user │
│ Route Opt.  │ │ change yet  │ │ with reason │
└─────────────┘ └─────────────┘ └─────────────┘
```

---

## Trust Score Calculation

### Initial State
- New users start with **trust_score = 0**
- All reports require photo + GPS verification

### Score Updates

| Event | Trust Score Change | Photo Requirement |
|-------|-------------------|-------------------|
| Report ACCEPTED | +2 points | Continue until score >= 80 |
| Report REJECTED | -5 points | Always required |
| Report NEEDS_REVIEW (later accepted) | +1 point | Continue |
| Report NEEDS_REVIEW (later rejected) | -2 points | Continue |

### Trust Levels

| Trust Score | Level | Requirements | Auto-Accept Rate |
|-------------|-------|--------------|------------------|
| 0-49 | Low Trust | Photo + GPS mandatory | 0% (All validated) |
| 50-79 | Medium Trust | GPS mandatory | 50% (Random sampling) |
| 80-100 | High Trust | No requirements | 90% (Spot checks only) |

### Example Progression
```
User joins → Score = 0

Report 1: ACCEPTED → Score = 2
Report 2: ACCEPTED → Score = 4
Report 3: REJECTED → Score = -1 (max(4-5, 0) = 0, floor at 0)
Report 4: ACCEPTED → Score = 2
...
Report 40: ACCEPTED → Score = 82 → HIGH TRUST UNLOCKED
```

---

## Edge Cases & Handling

### Case 1: Model Confidence is Low
```python
if model_prediction['confidence'] < 0.60:
    # Model is uncertain - be more lenient with user reports
    return {
        'validation_result': 'NEEDS_REVIEW',
        'reason': 'Model confidence low. Human review recommended.'
    }
```

### Case 2: Container Recently Collected
```python
if (now() - container.last_collection_date) < timedelta(hours=6):
    # Too soon after collection - likely empty
    if user_report == "FULL":
        return {
            'validation_result': 'REJECTED',
            'reason': 'Container collected 4 hours ago. Report unlikely.'
        }
```

### Case 3: Multiple Reports on Same Container
```python
def check_duplicate_reports(container_id, time_window_minutes=30):
    recent_reports = db.query("""
        SELECT COUNT(*) FROM citizen_reports
        WHERE container_id = :cid
        AND created_at > NOW() - INTERVAL ':window minutes'
    """, {'cid': container_id, 'window': time_window_minutes})
    
    if recent_reports > 3:
        # Multiple users reporting same container - likely accurate
        return {'boost_confidence': True, 'multiplier': 1.5}
```

### Case 4: Admin Manual Override
```python
# Admin can override validation in special circumstances
def admin_override_validation(report_id, admin_id, decision, notes):
    db.execute("""
        UPDATE citizen_reports
        SET report_status = :decision,
            admin_reviewed = TRUE,
            admin_notes = :notes,
            validation_result = 'admin_override'
        WHERE report_id = :report_id
    """, {'decision': decision, 'notes': notes, 'report_id': report_id})
    
    # Apply trust score change based on admin decision
    user_id = get_report_user(report_id)
    if decision == 'validated':
        update_user_trust_score(user_id, report_accepted=True)
    else:
        update_user_trust_score(user_id, report_accepted=False)
```

---

## Performance Metrics

### Target Metrics
- **False Positive Rate** (Accepting bad reports): < 5%
- **False Negative Rate** (Rejecting good reports): < 3%
- **Average Validation Time**: < 500ms
- **Admin Review Queue**: < 50 pending reports

### Monitoring & Alerts
```python
# Daily monitoring job
def calculate_validation_metrics():
    metrics = db.query("""
        SELECT 
            COUNT(*) AS total_reports,
            SUM(CASE WHEN validation_result = 'plausible' THEN 1 ELSE 0 END) AS accepted,
            SUM(CASE WHEN validation_result = 'implausible' THEN 1 ELSE 0 END) AS rejected,
            SUM(CASE WHEN validation_result = 'needs_review' THEN 1 ELSE 0 END) AS pending,
            AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) AS avg_processing_time_sec
        FROM citizen_reports
        WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
    """).fetchone()
    
    # Alert if pending queue is too large
    if metrics['pending'] > 50:
        send_alert_to_admins("High pending review queue: " + str(metrics['pending']))
    
    return metrics
```

---

## Future Enhancements

1. **Machine Learning Feedback Loop**: Use validated reports to retrain Model #1
2. **Anomaly Detection**: Flag coordinated abuse (multiple fake accounts reporting same containers)
3. **Sentiment Analysis**: Analyze user description text for additional signals
4. **Computer Vision Integration**: Automatic fill-level estimation from photos
5. **Weather Integration**: Adjust validation thresholds based on rain (heavier containers)
