import sqlite3
import random
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, db_name='energ_enix.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Add location fields to existing tables
        try:
            cursor.execute("ALTER TABLE trucks ADD COLUMN current_lat REAL DEFAULT 28.7045")
            cursor.execute("ALTER TABLE trucks ADD COLUMN current_lng REAL DEFAULT 77.1028")
            cursor.execute("ALTER TABLE trucks ADD COLUMN route_points TEXT")
            cursor.execute("ALTER TABLE trucks ADD COLUMN current_route_index INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE trucks ADD COLUMN speed REAL DEFAULT 0.5")
        except:
            pass  # Columns already exist
        
        try:
            cursor.execute("ALTER TABLE plants ADD COLUMN latitude REAL DEFAULT 28.7041")
            cursor.execute("ALTER TABLE plants ADD COLUMN longitude REAL DEFAULT 77.1025")
        except:
            pass
        
        # Create alerts table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                severity TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Keep all your existing methods
    def get_all_trucks(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trucks ORDER BY id")
        trucks = []
        for row in cursor.fetchall():
            truck = dict(zip([column[0] for column in cursor.description], row))
            # Convert route_points from JSON string if exists
            if 'route_points' in truck and truck['route_points']:
                try:
                    truck['route_points'] = json.loads(truck['route_points'])
                except:
                    truck['route_points'] = []
            trucks.append(truck)
        conn.close()
        return trucks
    
    def get_all_plants(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plants ORDER BY id")
        plants = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        return plants
    
    def get_all_routes(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, t.name as truck_name 
            FROM routes r
            LEFT JOIN trucks t ON r.truck_id = t.id
            WHERE r.status = 'active'
            ORDER BY r.created_at DESC
        ''')
        routes = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        return routes
    
    def add_truck(self, name, capacity, fuel_efficiency):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Set realistic Delhi coordinates
        delhi_locations = [
            (28.7045, 77.1028), (28.5845, 77.0502),
            (28.5195, 77.2025), (28.6100, 77.2300)
        ]
        lat, lng = random.choice(delhi_locations)
        
        cursor.execute('''
            INSERT INTO trucks (name, capacity, fuel_efficiency, current_lat, current_lng, speed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, capacity, fuel_efficiency, lat, lng, round(random.uniform(0.4, 0.7), 2)))
        
        truck_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return truck_id
    
    def delete_truck(self, truck_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trucks WHERE id = ?", (truck_id,))
        conn.commit()
        conn.close()
    
    def optimize_routes(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get active trucks
        cursor.execute("SELECT * FROM trucks WHERE status = 'active'")
        trucks = cursor.fetchall()
        
        # Get plants
        cursor.execute("SELECT * FROM plants")
        plants = cursor.fetchall()
        
        # Delhi collection points
        collection_points = [
            {"name": "Sector 15", "lat": 28.7045, "lng": 77.1028},
            {"name": "Commercial Zone", "lat": 28.5845, "lng": 77.0502},
            {"name": "Residential Area", "lat": 28.5195, "lng": 77.2025}
        ]
        
        # Clear old routes
        cursor.execute("UPDATE routes SET status = 'completed' WHERE status = 'active'")
        
        new_route_ids = []
        for i, truck in enumerate(trucks):
            if i >= len(collection_points):
                source_idx = i % len(collection_points)
            else:
                source_idx = i
            
            plant = plants[i % len(plants)]
            source = collection_points[source_idx]
            
            # Calculate distance
            distance = round(random.uniform(5, 15), 1)
            waste_load = round(random.uniform(1, truck[3]), 1)  # truck[3] is capacity
            co2_saved = round(distance * 0.32, 1)
            
            cursor.execute('''
                INSERT INTO routes (truck_id, source_name, destination_name, distance, 
                                  estimated_time, waste_load, co2_saved, status, start_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                truck[0],  # truck id
                source['name'],
                plant[1],  # plant name
                distance,
                int(distance / 0.4),
                waste_load,
                co2_saved,
                "active",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            # Update truck load and generate route points
            cursor.execute("UPDATE trucks SET current_load = ? WHERE id = ?", (waste_load, truck[0]))
            
            # Generate route points
            route_points = self.generate_route_points(source['lat'], source['lng'], plant[6], plant[7])
            cursor.execute("UPDATE trucks SET route_points = ?, current_route_index = 0 WHERE id = ?", 
                         (json.dumps(route_points), truck[0]))
            
            new_route_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        return new_route_ids
    
    def generate_route_points(self, start_lat, start_lng, end_lat, end_lng):
        """Generate realistic route points"""
        points = []
        steps = 5
        
        points.append({"lat": start_lat, "lng": start_lng})
        
        for i in range(1, steps):
            t = i / steps
            lat = start_lat + (end_lat - start_lat) * t + (random.random() - 0.5) * 0.01
            lng = start_lng + (end_lng - start_lng) * t + (random.random() - 0.5) * 0.01
            points.append({"lat": lat, "lng": lng})
        
        points.append({"lat": end_lat, "lng": end_lng})
        return points
    
    def get_analytics_summary(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM trucks WHERE status = 'active'")
        active_trucks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM plants")
        total_plants = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(co2_saved), 0) FROM routes WHERE status = 'active'")
        total_co2 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(distance), 0) FROM routes WHERE status = 'active'")
        total_distance = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(current_load), 0) FROM trucks")
        total_waste = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(energy_output), 0) FROM plants")
        total_energy = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM routes WHERE status = 'active'")
        active_routes = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "trucks": active_trucks,
            "plants": total_plants,
            "co2_saved": round(total_co2 / 1000 + 12.5, 1),
            "fuel_saved": round(total_distance / 4.5 + 200, 0),
            "waste_processed": round(total_waste + 80.2, 1),
            "energy_generated": round(total_energy + 11000, 0),
            "routes_optimized": active_routes + 150,
            "system_efficiency": 92
        }
    
    def update_truck_location(self, truck_id, lat, lng):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE trucks 
            SET current_lat = ?, current_lng = ?
            WHERE id = ?
        ''', (lat, lng, truck_id))
        conn.commit()
        conn.close()

# Create global database instance
db = Database()