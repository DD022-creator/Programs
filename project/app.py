from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import random
from datetime import datetime, timedelta
import json
import csv
import io

app = Flask(__name__)
CORS(app)

# Simple in-memory storage (enhanced with realistic data)
trucks = [
    {
        "id": 1,
        "name": "Truck-001",
        "status": "active",
        "capacity": 5.0,
        "current_load": 3.5,
        "fuel_efficiency": 4.5,
        "real_location": {"lat": 28.7045, "lng": 77.1028},
        "route_points": [],
        "current_route_index": 0,
        "speed": 0.5
    },
    {
        "id": 2,
        "name": "Truck-002",
        "status": "active",
        "capacity": 7.5,
        "current_load": 4.8,
        "fuel_efficiency": 4.2,
        "real_location": {"lat": 28.5845, "lng": 77.0502},
        "route_points": [],
        "current_route_index": 0,
        "speed": 0.6
    }
]

plants = [
    {
        "id": 1,
        "name": "Central Biogas Plant",
        "type": "biogas",
        "capacity": 100,
        "current_load": 45.5,
        "energy_output": 6500,
        "location": {"lat": 28.7041, "lng": 77.1025}
    },
    {
        "id": 2,
        "name": "West Delhi WTE Plant",
        "type": "incineration",
        "capacity": 150,
        "current_load": 89.2,
        "energy_output": 12500,
        "location": {"lat": 28.5841, "lng": 77.0498}
    }
]

routes = [
    {
        "id": 1,
        "truck_id": 1,
        "truck_name": "Truck-001",
        "source": "Sector 15 Collection Point",
        "destination": "Central Biogas Plant",
        "distance": 8.2,
        "eta": 15,
        "waste_load": 3.5,
        "co2_saved": 4.2,
        "status": "active"
    }
]

# Realistic Delhi locations
DELHI_LOCATIONS = {
    "collection_points": [
        {"name": "Sector 15 Collection Point", "lat": 28.7045, "lng": 77.1028, "type": "residential"},
        {"name": "Commercial Zone A", "lat": 28.5845, "lng": 77.0502, "type": "commercial"},
        {"name": "Residential Area B", "lat": 28.5195, "lng": 77.2025, "type": "residential"},
        {"name": "Market Complex C", "lat": 28.6100, "lng": 77.2300, "type": "commercial"}
    ],
    "intersections": [
        {"lat": 28.6139, "lng": 77.2090},
        {"lat": 28.7041, "lng": 77.1025},
        {"lat": 28.5841, "lng": 77.0498},
        {"lat": 28.5191, "lng": 77.2022}
    ]
}

@app.route('/')
def home():
    return render_template('index.html')

# Enhanced Trucks API
@app.route('/api/trucks', methods=['GET'])
def get_trucks():
    return jsonify(trucks)

@app.route('/api/trucks', methods=['POST'])
def add_truck():
    data = request.json
    new_truck = {
        "id": len(trucks) + 1,
        "name": data.get('name', f'Truck-{len(trucks) + 1:03d}'),
        "status": "active",
        "capacity": round(random.uniform(3, 8), 1),
        "current_load": 0,
        "fuel_efficiency": round(random.uniform(3.5, 5.5), 1),
        "real_location": {"lat": 28.7045, "lng": 77.1028},
        "route_points": [],
        "current_route_index": 0,
        "speed": round(random.uniform(0.4, 0.7), 2)
    }
    trucks.append(new_truck)
    return jsonify({"message": "Truck added successfully", "truck": new_truck})

@app.route('/api/trucks/<int:truck_id>', methods=['DELETE'])
def delete_truck(truck_id):
    global trucks
    trucks = [truck for truck in trucks if truck['id'] != truck_id]
    return jsonify({"message": "Truck deleted successfully"})

@app.route('/api/trucks/<int:truck_id>/location', methods=['PUT'])
def update_truck_location(truck_id):
    data = request.json
    for truck in trucks:
        if truck['id'] == truck_id:
            truck['real_location'] = {
                "lat": data.get('lat', truck['real_location']['lat']),
                "lng": data.get('lng', truck['real_location']['lng'])
            }
            return jsonify({"message": "Location updated", "truck": truck})
    return jsonify({"error": "Truck not found"}), 404

# Enhanced Plants API
@app.route('/api/plants', methods=['GET'])
def get_plants():
    return jsonify(plants)

@app.route('/api/plants', methods=['POST'])
def add_plant():
    data = request.json
    plant_types = ["biogas", "incineration", "composting"]
    new_plant = {
        "id": len(plants) + 1,
        "name": data.get('name', f'Plant-{len(plants) + 1}'),
        "type": random.choice(plant_types),
        "capacity": round(random.uniform(50, 150), 1),
        "current_load": round(random.uniform(10, 50), 1),
        "energy_output": round(random.uniform(5000, 15000)),
        "location": {
            "lat": random.uniform(28.40, 28.90),
            "lng": random.uniform(77.00, 77.40)
        }
    }
    plants.append(new_plant)
    return jsonify({"message": "Plant added successfully", "plant": new_plant})

# Enhanced Routes API
@app.route('/api/routes', methods=['GET'])
def get_routes():
    return jsonify(routes)

@app.route('/api/routes/optimize', methods=['POST'])
def optimize_routes():
    global routes
    routes.clear()
    
    active_trucks = [t for t in trucks if t['status'] == 'active']
    sources = DELHI_LOCATIONS["collection_points"]
    
    for i, truck in enumerate(active_trucks):
        source = random.choice(sources)
        destination = random.choice(plants)
        
        # Calculate distance (simplified)
        lat_diff = abs(destination['location']['lat'] - source['lat'])
        lng_diff = abs(destination['location']['lng'] - source['lng'])
        distance = round((lat_diff + lng_diff) * 100, 1)
        
        new_route = {
            "id": i + 1,
            "truck_id": truck['id'],
            "truck_name": truck['name'],
            "source": source['name'],
            "destination": destination['name'],
            "distance": distance,
            "eta": int(distance / 0.4),  # 40 km/h average
            "waste_load": round(random.uniform(1, truck['capacity']), 1),
            "co2_saved": round(distance * 0.32, 1),
            "status": "active"
        }
        routes.append(new_route)
        
        # Update truck load
        truck['current_load'] = new_route['waste_load']
        
        # Generate realistic route points
        generate_route_points(truck, source, destination)
    
    return jsonify({
        "message": f"Optimized {len(routes)} routes",
        "optimized_count": len(routes),
        "routes": routes
    })

def generate_route_points(truck, source, destination):
    """Generate realistic route points for a truck"""
    points = []
    
    # Start point
    points.append({"lat": source['lat'], "lng": source['lng']})
    
    # Add 3-5 intermediate points
    num_points = random.randint(3, 5)
    for i in range(1, num_points + 1):
        t = i / (num_points + 1)
        lat = source['lat'] + (destination['location']['lat'] - source['lat']) * t
        lng = source['lng'] + (destination['location']['lng'] - source['lng']) * t
        
        # Add some randomness
        lat += random.uniform(-0.01, 0.01)
        lng += random.uniform(-0.01, 0.01)
        
        points.append({"lat": lat, "lng": lng})
    
    # End point
    points.append({"lat": destination['location']['lat'], "lng": destination['location']['lng']})
    
    truck['route_points'] = points
    truck['current_route_index'] = 0

# Enhanced Analytics API
@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    active_trucks = len([t for t in trucks if t['status'] == 'active'])
    total_co2 = sum(route['co2_saved'] for route in routes)
    total_fuel = sum(route['distance'] for route in routes) / 4.5
    total_waste = sum(truck['current_load'] for truck in trucks)
    total_energy = sum(plant['energy_output'] for plant in plants)
    
    return jsonify({
        "trucks": active_trucks,
        "plants": len(plants),
        "co2_saved": round(total_co2 / 100 + 12.5, 1),
        "fuel_saved": round(total_fuel + 200),
        "waste_processed": round(total_waste + 80.2, 1),
        "energy_generated": round(total_energy + 11000),
        "routes_optimized": len(routes) + 150,
        "system_efficiency": 92
    })

@app.route('/api/analytics/trends', methods=['GET'])
def get_analytics_trends():
    period = request.args.get('period', 'daily')
    
    if period == 'daily':
        trends = [
            {"date": "Mon", "co2": 12, "fuel": 180, "waste": 65},
            {"date": "Tue", "co2": 14, "fuel": 220, "waste": 72},
            {"date": "Wed", "co2": 13, "fuel": 190, "waste": 68},
            {"date": "Thu", "co2": 16, "fuel": 240, "waste": 80},
            {"date": "Fri", "co2": 15, "fuel": 210, "waste": 75},
            {"date": "Sat", "co2": 18, "fuel": 260, "waste": 85},
            {"date": "Sun", "co2": 17, "fuel": 245, "waste": 89}
        ]
    elif period == 'weekly':
        trends = [
            {"week": "Week 1", "avg_co2": 13, "avg_fuel": 200, "avg_waste": 70},
            {"week": "Week 2", "avg_co2": 14, "avg_fuel": 220, "avg_waste": 75},
            {"week": "Week 3", "avg_co2": 15, "avg_fuel": 230, "avg_waste": 78},
            {"week": "Week 4", "avg_co2": 16, "avg_fuel": 250, "avg_waste": 82}
        ]
    else:  # monthly
        trends = [
            {"month": "Jan", "total_co2": 400, "total_fuel": 6200, "total_waste": 2100},
            {"month": "Feb", "total_co2": 420, "total_fuel": 6500, "total_waste": 2250},
            {"month": "Mar", "total_co2": 450, "total_fuel": 6800, "total_waste": 2400},
            {"month": "Apr", "total_co2": 470, "total_fuel": 7100, "total_waste": 2550}
        ]
    
    return jsonify(trends)

# Enhanced Tracking API
@app.route('/api/tracking/live', methods=['GET'])
def get_live_tracking():
    active_trucks_data = []
    
    for truck in trucks:
        if truck['status'] == 'active':
            # Find truck's current route
            route = next((r for r in routes if r['truck_id'] == truck['id'] and r['status'] == 'active'), None)
            
            if route:
                plant = next((p for p in plants if p['name'] == route['destination']), None)
                
                if plant:
                    active_trucks_data.append({
                        "id": truck['id'],
                        "truck_name": truck['name'],
                        "last_latitude": truck['real_location']['lat'],
                        "last_longitude": truck['real_location']['lng'],
                        "source_lat": DELHI_LOCATIONS["collection_points"][0]['lat'],
                        "source_lng": DELHI_LOCATIONS["collection_points"][0]['lng'],
                        "destination_lat": plant['location']['lat'],
                        "destination_lng": plant['location']['lng'],
                        "distance": route['distance'],
                        "waste_load": route['waste_load'],
                        "co2_saved": route['co2_saved'],
                        "plant_name": plant['name']
                    })
    
    plants_data = [
        {
            "id": plant['id'],
            "name": plant['name'],
            "latitude": plant['location']['lat'],
            "longitude": plant['location']['lng'],
            "type": plant['type'],
            "capacity": plant['capacity'],
            "current_load": plant['current_load'],
            "energy_output": plant['energy_output']
        }
        for plant in plants
    ]
    
    return jsonify({
        "active_routes": active_trucks_data,
        "plants": plants_data,
        "timestamp": datetime.now().isoformat(),
        "collection_points": DELHI_LOCATIONS["collection_points"]
    })

@app.route('/api/tracking/update', methods=['POST'])
def update_tracking():
    data = request.json
    truck_id = data.get('truck_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    for truck in trucks:
        if truck['id'] == truck_id:
            truck['real_location'] = {"lat": lat, "lng": lng}
            return jsonify({"message": "Location updated", "truck": truck})
    
    return jsonify({"error": "Truck not found"}), 404

# Enhanced Alerts API
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = []
    
    # Maintenance alerts
    for truck in trucks:
        if truck['status'] == 'maintenance':
            alerts.append({
                "type": "maintenance",
                "severity": "warning",
                "message": f"{truck['name']} needs maintenance",
                "truck_id": truck['id']
            })
    
    # Low fuel alerts (simulated)
    for truck in trucks:
        if truck['current_load'] / truck['capacity'] > 0.9:
            alerts.append({
                "type": "high_load",
                "severity": "warning",
                "message": f"{truck['name']} at high capacity: {((truck['current_load']/truck['capacity'])*100):.1f}%",
                "truck_id": truck['id']
            })
    
    # High plant load alerts
    for plant in plants:
        utilization = (plant['current_load'] / plant['capacity']) * 100
        if utilization > 80:
            alerts.append({
                "type": "high_load",
                "severity": "warning",
                "message": f"{plant['name']} at {utilization:.1f}% capacity",
                "plant_id": plant['id']
            })
    
    # Random traffic/weather alerts
    if random.random() < 0.3:  # 30% chance
        events = [
            ("traffic", "🚦 Heavy traffic reported on major routes"),
            ("weather", "🌧️ Light rain affecting collection efficiency"),
            ("maintenance", "🛠️ Plant maintenance in progress")
        ]
        event_type, message = random.choice(events)
        alerts.append({
            "type": event_type,
            "severity": "info",
            "message": message
        })
    
    return jsonify(alerts)

# Enhanced Reports API
@app.route('/api/reports/daily', methods=['GET'])
def generate_daily_report():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    total_waste = sum(truck['current_load'] for truck in trucks)
    total_co2 = sum(route['co2_saved'] for route in routes) / 1000
    total_distance = sum(route['distance'] for route in routes)
    
    report = {
        "date": date,
        "summary": {
            "trucks_active": len([t for t in trucks if t['status'] == 'active']),
            "routes_completed": len([r for r in routes if r['status'] == 'completed']),
            "waste_processed": round(total_waste, 1),
            "co2_saved": round(total_co2, 1),
            "total_distance": round(total_distance, 1),
            "avg_route_time": 22.5
        },
        "routes": routes,
        "environmental_impact": {
            "trees_equivalent": int(total_co2 * 1000 / 22),
            "cars_removed": int(total_co2 * 1000 / 4600),
            "electricity_saved": int(sum(plant['energy_output'] for plant in plants) / 12.5)
        }
    }
    
    return jsonify(report)

@app.route('/api/reports/export/csv', methods=['GET'])
def export_csv_report():
    report_type = request.args.get('type', 'routes')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'routes':
        writer.writerow(['Date', 'Truck', 'Source', 'Destination', 'Distance (km)', 'Waste (tons)', 'CO₂ Saved (kg)', 'ETA (min)'])
        for route in routes:
            writer.writerow([
                date,
                route['truck_name'],
                route['source'],
                route['destination'],
                route['distance'],
                route['waste_load'],
                route['co2_saved'],
                route['eta']
            ])
        filename = f'routes_report_{date}.csv'
    
    elif report_type == 'trucks':
        writer.writerow(['Name', 'Status', 'Capacity', 'Current Load', 'Fuel Efficiency', 'Location'])
        for truck in trucks:
            writer.writerow([
                truck['name'],
                truck['status'],
                truck['capacity'],
                truck['current_load'],
                truck['fuel_efficiency'],
                f"{truck['real_location']['lat']:.4f}, {truck['real_location']['lng']:.4f}"
            ])
        filename = f'trucks_report_{date}.csv'
    
    else:  # plants
        writer.writerow(['Name', 'Type', 'Capacity', 'Current Load', 'Energy Output', 'Location'])
        for plant in plants:
            writer.writerow([
                plant['name'],
                plant['type'],
                plant['capacity'],
                plant['current_load'],
                plant['energy_output'],
                f"{plant['location']['lat']:.4f}, {plant['location']['lng']:.4f}"
            ])
        filename = f'plants_report_{date}.csv'
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

# Predictive Analytics API
@app.route('/api/predictive/maintenance', methods=['GET'])
def get_predictive_maintenance():
    predictive_data = []
    
    for truck in trucks:
        # Simulate predictive scores
        days_since_last = random.randint(30, 90)
        distance_since_last = random.randint(5000, 20000)
        maintenance_count = random.randint(1, 5)
        
        score = min(100, max(0,
            (days_since_last / 90 * 40) +
            (distance_since_last / 10000 * 40) +
            (maintenance_count * 5)
        ))
        
        predictive_data.append({
            "id": truck['id'],
            "name": truck['name'],
            "total_distance": distance_since_last,
            "last_maintenance": (datetime.now() - timedelta(days=days_since_last)).strftime('%Y-%m-%d'),
            "next_maintenance": (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
            "maintenance_count": maintenance_count,
            "avg_maintenance_cost": random.randint(5000, 20000),
            "maintenance_score": round(score, 1),
            "recommended_action": "Schedule Maintenance" if score > 70 else "Monitor"
        })
    
    return jsonify(predictive_data)

@app.route('/api/predictive/optimization', methods=['POST'])
def get_route_optimization():
    data = request.json
    source = data.get('source', 'Sector 15 Collection Point')
    waste_amount = data.get('waste_amount', 3.0)
    
    optimized_routes = []
    
    for plant in plants:
        # Calculate simulated distance
        distance = round(random.uniform(5, 25), 1)
        travel_time = int(distance / 0.4)
        co2_saved = round(distance * 0.32 * waste_amount, 1)
        fuel_used = round(distance / 4.5, 1)
        plant_capacity_left = plant['capacity'] - plant['current_load']
        
        priority_score = round(
            distance * 0.4 +
            travel_time * 0.3 +
            (100 - plant_capacity_left / plant['capacity'] * 100) * 0.3,
            2
        )
        
        optimized_routes.append({
            "plant_id": plant['id'],
            "plant_name": plant['name'],
            "distance": distance,
            "travel_time": travel_time,
            "co2_saved": co2_saved,
            "fuel_used": fuel_used,
            "plant_capacity_left": round(plant_capacity_left, 1),
            "priority_score": priority_score,
            "recommendation": "Recommended" if plant_capacity_left >= waste_amount else "Not Recommended"
        })
    
    # Sort by priority score
    optimized_routes.sort(key=lambda x: x['priority_score'])
    
    return jsonify({
        "source": source,
        "waste_amount": waste_amount,
        "optimized_routes": optimized_routes,
        "best_route": optimized_routes[0] if optimized_routes else None
    })

# Dashboard Stats API
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    active_trucks_today = len([t for t in trucks if t['status'] == 'active'])
    routes_today = len([r for r in routes if r['status'] == 'active'])
    waste_processed_today = sum(t['current_load'] for t in trucks)
    co2_saved_today = sum(r['co2_saved'] for r in routes) / 1000
    distance_today = sum(r['distance'] for r in routes)
    
    # Yesterday's data (simulated)
    active_trucks_yesterday = max(0, active_trucks_today - random.randint(-2, 2))
    routes_yesterday = max(0, routes_today - random.randint(-3, 3))
    waste_processed_yesterday = max(0, waste_processed_today - random.uniform(-5, 5))
    
    def calculate_percentage_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    trucks_change = calculate_percentage_change(active_trucks_today, active_trucks_yesterday)
    routes_change = calculate_percentage_change(routes_today, routes_yesterday)
    waste_change = calculate_percentage_change(waste_processed_today, waste_processed_yesterday)
    
    return jsonify({
        "today": {
            "active_trucks": active_trucks_today,
            "routes": routes_today,
            "waste_processed": round(waste_processed_today, 1),
            "co2_saved": round(co2_saved_today, 1),
            "distance_covered": round(distance_today, 1)
        },
        "changes": {
            "trucks": trucks_change,
            "routes": routes_change,
            "waste": waste_change
        },
        "timestamp": datetime.now().isoformat()
    })

# Debug endpoint
@app.route('/api/debug', methods=['GET'])
def debug_info():
    return jsonify({
        "trucks_count": len(trucks),
        "plants_count": len(plants),
        "routes_count": len(routes),
        "trucks": trucks,
        "plants": plants,
        "routes": routes
    })

if __name__ == '__main__':
    print("🚀 ENERG ENIX API Server Starting...")
    print("📍 URL: http://localhost:5000")
    print("📊 Enhanced features loaded:")
    print("   - Realistic Delhi coordinates")
    print("   - Live tracking with lat/lng")
    print("   - Enhanced analytics")
    print("   - Predictive maintenance")
    print("   - Route optimization")
    print("   - Report generation")
    print("✅ API is ready!")
    app.run(host='0.0.0.0', port=5000, debug=True)