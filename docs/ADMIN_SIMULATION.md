# Admin Simulation Module - Documentation

## Overview
The Admin Simulation Module is a "What-If" analysis tool that allows Nilüfer Municipality operations managers to test different fleet configurations and predict their impact on operational efficiency, costs, and environmental metrics.

---

## Purpose

### Business Goals
1. **Budget Planning**: Determine if adding/removing vehicles is cost-effective
2. **Efficiency Optimization**: Find optimal fleet composition
3. **Carbon Reduction**: Quantify environmental impact of fleet changes
4. **Data-Driven Decisions**: Replace gut instinct with evidence-based planning

---

## Simulation Input Parameters

### Fleet Configuration
```javascript
{
  "simulation_name": "Test: Add 2 Large Trucks",
  "baseline_period": {
    "start_date": "2024-11-01",
    "end_date": "2024-11-30"  // 30 days of historical data
  },
  "fleet_changes": {
    "small_trucks": 0,      // Change from current: +0
    "large_trucks": +2,     // Change from current: +2
    "compactors": -1        // Change from current: -1
  },
  "operational_parameters": {
    "collection_strategy": "dynamic",  // "dynamic" or "scheduled"
    "max_route_duration_hours": 8,
    "fuel_price_per_liter": 35.00,     // TRY
    "electricity_price_per_kwh": 2.50,  // For electric vehicles
    "driver_hourly_wage": 75.00,       // TRY
    "maintenance_cost_per_km": 1.20    // TRY
  }
}
```

---

## Simulation Engine Algorithm

### Step 1: Load Historical Baseline Data
```python
def load_baseline_data(start_date, end_date):
    """
    Retrieve actual performance from the specified period
    """
    baseline = db.query("""
        SELECT 
            COUNT(DISTINCT route_id) AS total_routes,
            SUM(total_distance_km) AS total_km,
            SUM(fuel_consumed_liters) AS total_fuel,
            SUM(total_tonnage_collected) AS total_tonnage,
            SUM(actual_duration_minutes) / 60.0 AS total_hours,
            SUM(co2_emissions_kg) AS total_co2,
            AVG(total_containers) AS avg_containers_per_route
        FROM routes
        WHERE route_date BETWEEN :start AND :end
        AND route_status = 'completed'
    """, {'start': start_date, 'end': end_date}).fetchone()
    
    # Calculate baseline costs
    baseline_cost = calculate_operational_cost(
        fuel_liters=baseline['total_fuel'],
        total_hours=baseline['total_hours'],
        total_km=baseline['total_km']
    )
    
    return {
        'routes': baseline['total_routes'],
        'km_driven': baseline['total_km'],
        'fuel_consumed': baseline['total_fuel'],
        'tonnage_collected': baseline['total_tonnage'],
        'operating_hours': baseline['total_hours'],
        'co2_emissions': baseline['total_co2'],
        'total_cost': baseline_cost,
        'avg_containers_per_route': baseline['avg_containers_per_route']
    }
```

### Step 2: Simulate Modified Fleet Performance
```python
def run_simulation(historical_data, fleet_changes, parameters):
    """
    Monte Carlo simulation: Replay historical demand with modified fleet
    """
    
    # Get modified fleet composition
    current_fleet = get_current_fleet()
    simulated_fleet = apply_fleet_changes(current_fleet, fleet_changes)
    
    # Validate fleet changes
    if simulated_fleet['total_vehicles'] < 1:
        return {'error': 'Cannot simulate with zero vehicles'}
    
    # Initialize simulation results
    results = {
        'total_km': 0,
        'total_fuel': 0,
        'total_tonnage': 0,
        'total_co2': 0,
        'total_routes': 0,
        'missed_collections': 0,
        'daily_results': []
    }
    
    # Load historical collection demand (day by day)
    daily_demand = load_daily_demand(
        start_date=parameters['baseline_period']['start_date'],
        end_date=parameters['baseline_period']['end_date']
    )
    
    # Simulate each day
    for day_data in daily_demand:
        day_result = simulate_single_day(
            containers_needing_collection=day_data['full_containers'],
            available_fleet=simulated_fleet,
            parameters=parameters
        )
        
        results['total_km'] += day_result['km_driven']
        results['total_fuel'] += day_result['fuel_consumed']
        results['total_tonnage'] += day_result['tonnage_collected']
        results['total_co2'] += day_result['co2_emissions']
        results['total_routes'] += day_result['routes_completed']
        results['missed_collections'] += day_result['missed_containers']
        results['daily_results'].append(day_result)
    
    return results
```

### Step 3: Simulate Single Day Operations
```python
def simulate_single_day(containers_needing_collection, available_fleet, parameters):
    """
    Core simulation logic: Assign containers to vehicles and calculate metrics
    """
    
    # Sort containers by priority (fill level, location clustering)
    sorted_containers = prioritize_containers(containers_needing_collection)
    
    # Initialize vehicle states
    vehicle_states = [
        {
            'vehicle_id': v['vehicle_id'],
            'type': v['type'],
            'capacity': v['capacity_liters'],
            'current_load': 0,
            'current_location': v['depot_location'],
            'route_distance': 0,
            'route_duration': 0,
            'containers_collected': []
        }
        for v in available_fleet
    ]
    
    collected_containers = []
    missed_containers = []
    
    # Greedy assignment algorithm
    for container in sorted_containers:
        # Find best available vehicle
        best_vehicle = find_best_vehicle(
            container=container,
            vehicles=vehicle_states,
            max_duration=parameters['max_route_duration_hours'] * 60
        )
        
        if best_vehicle is None:
            # No vehicle available - container missed
            missed_containers.append(container['container_id'])
            continue
        
        # Calculate additional distance
        additional_km = calculate_route_distance(
            from_location=best_vehicle['current_location'],
            to_location=container['location']
        )
        
        # Calculate additional time (includes collection time)
        collection_time_minutes = 5  # Average time to empty one container
        additional_time = (additional_km / 30) * 60 + collection_time_minutes  # Assume 30 km/h avg
        
        # Check if adding this container exceeds constraints
        if (best_vehicle['current_load'] + container['estimated_tonnage'] > best_vehicle['capacity'] or
            best_vehicle['route_duration'] + additional_time > parameters['max_route_duration_hours'] * 60):
            # Vehicle full or time limit reached - mark as unavailable
            best_vehicle['available'] = False
            missed_containers.append(container['container_id'])
            continue
        
        # Assign container to vehicle
        best_vehicle['current_load'] += container['estimated_tonnage']
        best_vehicle['route_distance'] += additional_km
        best_vehicle['route_duration'] += additional_time
        best_vehicle['current_location'] = container['location']
        best_vehicle['containers_collected'].append(container['container_id'])
        collected_containers.append(container)
    
    # Calculate day totals
    total_km = sum(v['route_distance'] for v in vehicle_states)
    total_fuel = sum(
        v['route_distance'] * get_vehicle_type(v['type'])['fuel_consumption_per_km']
        for v in vehicle_states
    )
    total_co2 = sum(
        v['route_distance'] * get_vehicle_type(v['type'])['co2_emission_per_km']
        for v in vehicle_states
    )
    total_tonnage = sum(c['estimated_tonnage'] for c in collected_containers)
    routes_completed = sum(1 for v in vehicle_states if len(v['containers_collected']) > 0)
    
    return {
        'km_driven': total_km,
        'fuel_consumed': total_fuel,
        'co2_emissions': total_co2,
        'tonnage_collected': total_tonnage,
        'routes_completed': routes_completed,
        'containers_collected': len(collected_containers),
        'missed_containers': len(missed_containers),
        'vehicle_utilization': calculate_utilization(vehicle_states)
    }
```

### Step 4: Calculate Impact Metrics
```python
def calculate_impact_metrics(baseline, simulation_results, parameters):
    """
    Compare baseline vs. simulation to quantify impact
    """
    
    # Distance changes
    km_change = simulation_results['total_km'] - baseline['km_driven']
    km_change_percent = (km_change / baseline['km_driven']) * 100
    
    # Fuel changes
    fuel_change = simulation_results['total_fuel'] - baseline['fuel_consumed']
    fuel_cost_change = fuel_change * parameters['fuel_price_per_liter']
    
    # CO2 changes
    co2_change = simulation_results['total_co2'] - baseline['co2_emissions']
    co2_change_percent = (co2_change / baseline['co2_emissions']) * 100
    
    # Cost analysis
    baseline_cost = calculate_operational_cost(
        fuel_liters=baseline['fuel_consumed'],
        total_hours=baseline['operating_hours'],
        total_km=baseline['km_driven'],
        parameters=parameters
    )
    
    simulation_cost = calculate_operational_cost(
        fuel_liters=simulation_results['total_fuel'],
        total_hours=simulation_results['total_hours'],
        total_km=simulation_results['total_km'],
        parameters=parameters
    )
    
    # Add fleet acquisition/disposal costs
    fleet_cost_change = calculate_fleet_cost_change(
        fleet_changes=parameters['fleet_changes'],
        vehicle_prices={'small_truck': 800000, 'large_truck': 1500000, 'compactor': 2000000}
    )
    
    net_cost_change = (simulation_cost - baseline_cost) + fleet_cost_change
    
    # Efficiency metrics
    efficiency_change = (
        (simulation_results['tonnage_collected'] / simulation_results['total_fuel']) -
        (baseline['tonnage_collected'] / baseline['fuel_consumed'])
    )
    
    # Service quality
    collection_rate = (
        (simulation_results['containers_collected'] / 
         (simulation_results['containers_collected'] + simulation_results['missed_collections']))
    ) * 100
    
    baseline_collection_rate = 100  # Assume baseline met all demand
    service_quality_change = collection_rate - baseline_collection_rate
    
    # Citizen satisfaction estimation (heuristic)
    citizen_satisfaction = calculate_citizen_satisfaction(
        collection_rate=collection_rate,
        missed_collections=simulation_results['missed_collections']
    )
    
    return {
        'km_change': km_change,
        'km_change_percent': km_change_percent,
        'fuel_change_liters': fuel_change,
        'fuel_cost_change': fuel_cost_change,
        'co2_change_kg': co2_change,
        'co2_change_percent': co2_change_percent,
        'baseline_cost': baseline_cost,
        'simulation_cost': simulation_cost,
        'fleet_acquisition_cost': fleet_cost_change,
        'net_cost_change': net_cost_change,
        'efficiency_change': efficiency_change,
        'collection_rate_percent': collection_rate,
        'service_quality_change': service_quality_change,
        'citizen_satisfaction_score': citizen_satisfaction,
        'missed_collections': simulation_results['missed_collections']
    }
```

### Step 5: Generate Recommendation
```python
def generate_recommendation(impact_metrics, fleet_changes):
    """
    AI-driven recommendation based on simulation results
    """
    
    # Decision criteria
    is_cost_effective = impact_metrics['net_cost_change'] < 0  # Negative = savings
    is_more_efficient = impact_metrics['efficiency_change'] > 0
    maintains_service = impact_metrics['collection_rate_percent'] >= 98
    reduces_emissions = impact_metrics['co2_change_kg'] < 0
    
    # Scoring
    score = 0
    reasons = []
    
    if is_cost_effective:
        score += 30
        reasons.append(f"Saves {abs(impact_metrics['net_cost_change']):,.0f} TRY per month")
    else:
        score -= 20
        reasons.append(f"Costs {abs(impact_metrics['net_cost_change']):,.0f} TRY per month")
    
    if is_more_efficient:
        score += 20
        reasons.append(f"Improves fuel efficiency by {impact_metrics['efficiency_change']:.2f} kg/liter")
    
    if maintains_service:
        score += 25
        reasons.append(f"Maintains high service quality ({impact_metrics['collection_rate_percent']:.1f}%)")
    else:
        score -= 30
        reasons.append(f"Service quality drops ({impact_metrics['missed_collections']} missed collections)")
    
    if reduces_emissions:
        score += 15
        reasons.append(f"Reduces CO2 emissions by {abs(impact_metrics['co2_change_kg']):,.0f} kg")
    
    # Final recommendation
    if score >= 50:
        recommendation = "STRONGLY RECOMMENDED"
        action = "Implement this fleet configuration immediately"
    elif score >= 25:
        recommendation = "RECOMMENDED"
        action = "Consider implementing after further analysis"
    elif score >= 0:
        recommendation = "NEUTRAL"
        action = "Marginal benefits. Optional implementation"
    else:
        recommendation = "NOT RECOMMENDED"
        action = "Do not implement. Current fleet is better"
    
    return {
        'recommendation': recommendation,
        'action': action,
        'score': score,
        'reasons': reasons,
        'summary': " | ".join(reasons[:3])  # Top 3 reasons
    }
```

---

## Output Format (API Response)

```json
{
  "simulation_id": 1234,
  "simulation_name": "Test: Add 2 Large Trucks",
  "created_at": "2024-12-27T10:30:00Z",
  "admin_user": "manager@nilufer.gov.tr",
  
  "input_parameters": {
    "baseline_period": {"start": "2024-11-01", "end": "2024-11-30"},
    "fleet_changes": {
      "small_trucks": 0,
      "large_trucks": +2,
      "compactors": -1
    }
  },
  
  "baseline_metrics": {
    "total_routes": 180,
    "km_driven": 5400,
    "fuel_consumed_liters": 1350,
    "co2_emissions_kg": 3510,
    "tonnage_collected": 2700,
    "operating_cost_try": 285000,
    "collection_rate": 100
  },
  
  "simulation_metrics": {
    "total_routes": 165,
    "km_driven": 4950,
    "fuel_consumed_liters": 1260,
    "co2_emissions_kg": 3276,
    "tonnage_collected": 2695,
    "operating_cost_try": 310000,
    "collection_rate": 99.8,
    "missed_collections": 5
  },
  
  "impact_analysis": {
    "km_savings": -450,
    "km_savings_percent": -8.3,
    "fuel_savings_liters": -90,
    "fuel_cost_savings_try": -3150,
    "co2_reduction_kg": -234,
    "co2_reduction_percent": -6.7,
    "fleet_acquisition_cost_try": 1500000,
    "net_monthly_cost_change_try": 25000,
    "payback_period_months": 47.6,
    "efficiency_improvement": 0.03,
    "service_quality_change": -0.2,
    "citizen_satisfaction_score": 92
  },
  
  "recommendation": {
    "decision": "NEUTRAL",
    "action": "Marginal benefits. Optional implementation",
    "score": 15,
    "reasons": [
      "Costs 25,000 TRY per month (after amortization)",
      "Reduces CO2 emissions by 234 kg",
      "Maintains high service quality (99.8%)"
    ],
    "summary": "Adding 2 large trucks reduces fuel consumption but increases costs due to acquisition expense. Consider if budget allows and environmental goals are priority."
  },
  
  "visualizations": {
    "cost_breakdown_chart_url": "/api/charts/sim-1234-costs.png",
    "efficiency_comparison_chart_url": "/api/charts/sim-1234-efficiency.png",
    "emissions_chart_url": "/api/charts/sim-1234-emissions.png"
  }
}
```

---

## Calculation Details

### Operational Cost Formula
```python
def calculate_operational_cost(fuel_liters, total_hours, total_km, parameters):
    """
    Total operational cost = Fuel + Labor + Maintenance + Fixed costs
    """
    
    fuel_cost = fuel_liters * parameters['fuel_price_per_liter']
    labor_cost = total_hours * parameters['driver_hourly_wage']
    maintenance_cost = total_km * parameters['maintenance_cost_per_km']
    fixed_cost = get_fixed_monthly_costs()  # Insurance, depreciation, etc.
    
    total = fuel_cost + labor_cost + maintenance_cost + fixed_cost
    
    return total
```

### Citizen Satisfaction Model
```python
def calculate_citizen_satisfaction(collection_rate, missed_collections):
    """
    Heuristic model for citizen satisfaction
    
    Factors:
    - Collection rate (primary driver)
    - Number of missed collections (penalty)
    - Consistency (variance in collection times)
    """
    
    base_score = collection_rate  # 0-100
    
    # Penalty for missed collections
    missed_penalty = min(missed_collections * 2, 20)  # Cap at -20 points
    
    # Add slight randomness for realism
    variance = random.uniform(-3, 3)
    
    satisfaction = max(0, min(100, base_score - missed_penalty + variance))
    
    return round(satisfaction, 1)
```

### Fleet Cost Changes
```python
def calculate_fleet_cost_change(fleet_changes, vehicle_prices):
    """
    Calculate one-time cost of adding/removing vehicles
    Amortize over 5 years for monthly impact calculation
    """
    
    total_cost = 0
    
    for vehicle_type, quantity_change in fleet_changes.items():
        if quantity_change > 0:
            # Adding vehicles - purchase cost
            total_cost += quantity_change * vehicle_prices[vehicle_type]
        else:
            # Removing vehicles - resale value (assume 40% of original)
            total_cost += quantity_change * vehicle_prices[vehicle_type] * 0.40
    
    # Amortize over 60 months (5 years)
    monthly_impact = total_cost / 60
    
    return monthly_impact
```

---

## User Interface Flow

### Admin Dashboard - Simulation Tab

```
┌─────────────────────────────────────────────────────────────────┐
│  SIMULATION SANDBOX - Fleet Configuration Testing               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1] SELECT BASELINE PERIOD                                     │
│      Start Date: [2024-11-01▼]  End Date: [2024-11-30▼]       │
│                                                                  │
│  [2] MODIFY FLEET COMPOSITION                                   │
│      ┌────────────────────────────────────────────────────┐    │
│      │ Vehicle Type    │ Current │ Change │ New Total     │    │
│      ├────────────────────────────────────────────────────┤    │
│      │ Small Trucks    │    5    │ [+0]   │      5        │    │
│      │ Large Trucks    │   10    │ [+2]   │     12        │    │
│      │ Compactors      │    3    │ [-1]   │      2        │    │
│      └────────────────────────────────────────────────────┘    │
│                                                                  │
│  [3] ADVANCED PARAMETERS (Optional)                             │
│      Fuel Price: [35.00 TRY/L]                                 │
│      Max Route Duration: [8 hours]                             │
│      Collection Strategy: [●Dynamic ○Scheduled]                │
│                                                                  │
│      [RUN SIMULATION] ← Button                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

After clicking "RUN SIMULATION" (Processing takes 5-10 seconds)

┌─────────────────────────────────────────────────────────────────┐
│  SIMULATION RESULTS                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 RECOMMENDATION: NEUTRAL                                     │
│  Score: 15/100                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  "Marginal benefits. Optional implementation"                   │
│                                                                  │
│  KEY FINDINGS:                                                  │
│  • Costs 25,000 TRY per month (after amortization)             │
│  • Reduces CO2 emissions by 234 kg                             │
│  • Maintains high service quality (99.8%)                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  COMPARATIVE METRICS                                            │
│                                                                  │
│  ┌───────────────────┬──────────────┬──────────────┬─────────┐ │
│  │ Metric            │ Current      │ Simulated    │ Change  │ │
│  ├───────────────────┼──────────────┼──────────────┼─────────┤ │
│  │ Kilometers        │ 5,400 km     │ 4,950 km     │ -8.3%   │ │
│  │ Fuel Consumed     │ 1,350 L      │ 1,260 L      │ -6.7%   │ │
│  │ CO2 Emissions     │ 3,510 kg     │ 3,276 kg     │ -6.7%   │ │
│  │ Monthly Cost      │ 285,000 TRY  │ 310,000 TRY  │ +8.8%   │ │
│  │ Collection Rate   │ 100%         │ 99.8%        │ -0.2%   │ │
│  │ Satisfaction      │ 95           │ 92           │ -3      │ │
│  └───────────────────┴──────────────┴──────────────┴─────────┘ │
│                                                                  │
│  📈 [View Detailed Charts] [Export Report PDF] [Save Scenario]  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Saved Simulations History

Admins can view past simulations to compare different scenarios:

```
┌─────────────────────────────────────────────────────────────────┐
│  SIMULATION HISTORY                                              │
├──────┬────────────────────────┬─────────────┬─────────┬─────────┤
│ ID   │ Scenario Name          │ Date        │ Score   │ Action  │
├──────┼────────────────────────┼─────────────┼─────────┼─────────┤
│ 1234 │ Add 2 Large Trucks     │ 2024-12-27  │ 15      │ [View]  │
│ 1233 │ Remove 1 Compactor     │ 2024-12-26  │ -25     │ [View]  │
│ 1232 │ Add 3 Small Trucks     │ 2024-12-25  │ 65      │ [View]  │
│ 1231 │ Electric Fleet Test    │ 2024-12-20  │ 80      │ [View]  │
└──────┴────────────────────────┴─────────────┴─────────┴─────────┘
```

---

## Technical Implementation Notes

### Performance Optimization
- **Caching**: Cache historical data to avoid repeated database queries
- **Parallel Processing**: Run multiple scenarios simultaneously using multiprocessing
- **Progress Updates**: Use WebSocket to stream progress (e.g., "Day 15/30 simulated...")

### Accuracy Considerations
- **Monte Carlo Iterations**: Run simulation 10 times with slight randomness, report average
- **Seasonal Adjustments**: Weight results based on seasonality (summer vs. winter waste patterns)
- **Weather Impact**: Optionally incorporate historical weather data

### API Endpoint
```
POST /api/admin/simulations/run
Authorization: Bearer <admin_token>

Request Body: (as shown in Input Parameters section)

Response: (as shown in Output Format section)
```

---

## Future Enhancements

1. **Scenario Comparison**: Compare 2-3 scenarios side-by-side
2. **Optimization Solver**: AI suggests optimal fleet composition automatically
3. **Real-Time Simulation**: Run simulation with live GPS data (today's routes)
4. **Budget Constraints**: Set maximum budget and find best configuration within limits
5. **Multi-Year Projections**: Simulate 3-5 year scenarios with growth assumptions
