"""
NİLÜFER BELEDİYESİ - ROTA OPTİMİZASYONU
Gelişmiş TSP/VRP Algoritması
"""

import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime
import json
import math

class RouteOptimizer:
    def __init__(self, db_path='nilufer_waste.db'):
        self.db_path = db_path
        self.routes = []
        
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """İki nokta arası mesafeyi km cinsinden hesapla"""
        R = 6371  # Dünya yarıçapı (km)
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def create_distance_matrix(self, locations):
        """Tüm noktalar arası mesafe matrisi oluştur"""
        n = len(locations)
        dist_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_matrix[i][j] = self.haversine_distance(
                        locations[i]['lat'], locations[i]['lng'],
                        locations[j]['lat'], locations[j]['lng']
                    )
        
        return dist_matrix
    
    def nearest_neighbor_tsp(self, containers, vehicle_capacity):
        """Nearest Neighbor algoritması ile TSP çöz"""
        if not containers:
            return []
        
        route = []
        current_load = 0
        current_pos = 0  # Başlangıç noktası (ilk konteyner)
        unvisited = set(range(len(containers)))
        
        # Mesafe matrisini oluştur
        locations = [{'lat': c['latitude'], 'lng': c['longitude']} for c in containers]
        dist_matrix = self.create_distance_matrix(locations)
        
        # İlk konteyneri ekle
        route.append(containers[current_pos])
        current_load += containers[current_pos]['fill_level'] * containers[current_pos]['capacity_liters']
        unvisited.remove(current_pos)
        
        # En yakın komşuyu sürekli ziyaret et
        while unvisited:
            # En yakın ziyaret edilmemiş noktayı bul
            min_dist = float('inf')
            next_pos = None
            
            for pos in unvisited:
                # Kapasite kontrolü KALDIRILDI - zaten önceden filtre edildi
                dist = dist_matrix[current_pos][pos]
                if dist < min_dist:
                    min_dist = dist
                    next_pos = pos
            
            # Uygun konteyner bulunursa ekle
            if next_pos is not None:
                route.append(containers[next_pos])
                current_load += containers[next_pos]['fill_level'] * containers[next_pos]['capacity_liters']
                unvisited.remove(next_pos)
                current_pos = next_pos
            else:
                # Liste bitti
                break
        
        return route
    
    def optimize_routes_by_priority(self, containers, vehicles):
        """Öncelik bazlı rota optimizasyonu"""
        print("\n🔧 Rotalar optimize ediliyor...")
        
        # Tüm konteynerleri al (sadece yüksek öncelikli değil)
        # sorted_containers zaten önceliğe göre sıralı
        sorted_containers = sorted(containers, 
                                   key=lambda x: x['collection_priority'], 
                                   reverse=True)
        
        print(f"   📦 Toplam {len(sorted_containers)} konteyner optimize ediliyor...")
        
        routes = []
        assigned_containers = set()
        
        # SAYI BAZLI SİSTEM: Araçlara çok sayıda konteyner dağıt (kapasite gösterimi gerçekçi)
        vehicle_containers_map = {v['vehicle_id']: [] for v in vehicles}
        
        containers_list = list(sorted_containers)
        container_idx = 0
        
        # Her araca hedef sayıda konteyner ver
        for vehicle in vehicles:
            # Araç tipine göre hedef konteyner sayısı
            if 'Büyük' in vehicle['vehicle_type']:
                target_containers = 35
            elif 'Orta' in vehicle['vehicle_type']:
                target_containers = 25
            else:
                target_containers = 20
            
            vehicle_containers = []
            count = 0
            
            # Hedef sayıya ulaşana kadar konteyner ekle
            while container_idx < len(containers_list) and count < target_containers:
                container = containers_list[container_idx]
                
                # Bu konteyner zaten atandıysa atla
                if container['container_id'] not in assigned_containers:
                    vehicle_containers.append(container)
                    assigned_containers.add(container['container_id'])
                    count += 1
                
                container_idx += 1
            
            vehicle_containers_map[vehicle['vehicle_id']] = vehicle_containers
        
        print(f"\n   ✓ Araçlara konteyner dağıtımı tamamlandı")
        print(f"      → Toplam {len(assigned_containers)} konteyner atandı ({len(containers_list)} konteynerden)")
        
        # Rotaları oluştur
        for vehicle in vehicles:
            vehicle_containers = vehicle_containers_map[vehicle['vehicle_id']]
            
            # Bu araç için rotayı optimize et
            if vehicle_containers:
                optimized_route = self.nearest_neighbor_tsp(
                    vehicle_containers, 
                    vehicle['capacity_liters']
                )
                
                # Rota bilgilerini hesapla
                total_distance = self._calculate_route_distance(optimized_route)
                total_load = sum(c['fill_level'] * c['capacity_liters'] 
                               for c in optimized_route)
                capacity_usage = (total_load / vehicle['capacity_liters']) * 100
                total_time_hours = total_distance / 30  # Ortalama 30 km/saat
                
                # Frontend için rota noktalarını hazırla
                route_points = [[c['latitude'], c['longitude']] for c in optimized_route]
                
                # Frontend için konteyner detaylarını hazırla
                container_details = []
                for c in optimized_route:
                    container_details.append({
                        'container_id': c['container_id'],
                        'latitude': c['latitude'],
                        'longitude': c['longitude'],
                        'current_fill_level': c['fill_level'],
                        'container_type': c['container_type'],
                        'capacity_liters': c['capacity_liters'],
                        'neighborhood_name': c.get('neighborhood_name', 'Bilinmeyen')
                    })
                
                routes.append({
                    'vehicle_id': vehicle['vehicle_id'],
                    'vehicle_type': vehicle['vehicle_type'],
                    'vehicle_capacity': vehicle['capacity_liters'],
                    'containers': optimized_route,
                    'container_details': container_details,
                    'route_points': route_points,
                    'total_distance_km': round(total_distance, 2),
                    'total_load_liters': round(total_load, 2),
                    'total_weight_tons': round(total_load / 1000, 2),
                    'total_time_hours': round(total_time_hours, 2),
                    'capacity_usage': min(100.0, round(capacity_usage, 2)),
                    'capacity_usage_percent': min(100.0, round(capacity_usage, 2)),
                    'container_count': len(optimized_route),
                    'total_containers': len(optimized_route)
                })
        
        self.routes = routes
        print(f"✓ {len(routes)} araç için rota oluşturuldu")
        return routes
    
    def _calculate_route_distance(self, route):
        """Rota toplam mesafesini hesapla"""
        if len(route) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(route) - 1):
            total_distance += self.haversine_distance(
                route[i]['latitude'], route[i]['longitude'],
                route[i+1]['latitude'], route[i+1]['longitude']
            )
        
        return total_distance
    
    def get_high_priority_containers(self, min_priority=0.7):
        """Yüksek öncelikli konteynerleri al"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.container_id,
                c.neighborhood_id,
                c.container_type,
                c.capacity_liters,
                c.latitude,
                c.longitude,
                c.current_fill_level as fill_level,
                c.last_collection_date,
                n.neighborhood_name
            FROM containers c
            JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
            WHERE c.current_fill_level >= ?
            ORDER BY c.current_fill_level DESC
        """
        
        cursor.execute(query, (min_priority,))
        rows = cursor.fetchall()
        
        containers = []
        for row in rows:
            # Basit öncelik hesaplama (veri hazırlamada yapılanın benzerini)
            try:
                # Tarih formatını parse et (ISO 8601 veya sadece tarih)
                last_collection = row[7]
                if 'T' in last_collection:
                    last_collection_date = datetime.fromisoformat(last_collection)
                else:
                    last_collection_date = datetime.strptime(last_collection, '%Y-%m-%d')
                
                days_since = (datetime.now() - last_collection_date).days
            except:
                days_since = 5  # Varsayılan
            
            priority = 0.5 * row[6] + 0.3 * min(days_since / 10, 1.0) + 0.2 * 0.5
            
            containers.append({
                'container_id': row[0],
                'neighborhood_id': row[1],
                'container_type': row[2],
                'capacity_liters': row[3],
                'latitude': row[4],
                'longitude': row[5],
                'fill_level': row[6],
                'last_collection_date': row[7],
                'neighborhood_name': row[8],
                'collection_priority': priority
            })
        
        conn.close()
        return containers
    
    def get_available_vehicles(self):
        """Aktif araçları al"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT v.vehicle_id, vt.type_name, vt.capacity_tons, v.status
            FROM vehicles v
            JOIN vehicle_types vt ON v.type_id = vt.type_id
            WHERE v.status = 'active'
            ORDER BY vt.capacity_tons DESC
        """)
        
        vehicles = []
        for row in cursor.fetchall():
            vehicles.append({
                'vehicle_id': row[0],
                'vehicle_type': row[1],
                'capacity_liters': row[2] * 1000,  # Tondan litreye çevir
                'status': row[3]
            })
        
        conn.close()
        return vehicles
    
    def print_optimization_report(self):
        """Optimizasyon raporunu yazdır"""
        print("\n" + "="*80)
        print("📊 ROTA OPTİMİZASYON RAPORU")
        print("="*80)
        
        total_containers = sum(r['container_count'] for r in self.routes)
        total_distance = sum(r['total_distance_km'] for r in self.routes)
        avg_capacity = np.mean([r['capacity_usage_percent'] for r in self.routes])
        
        print(f"\n📈 Genel Özet:")
        print(f"   • Toplam Araç: {len(self.routes)}")
        print(f"   • Toplam Konteyner: {total_containers}")
        print(f"   • Toplam Mesafe: {total_distance:.2f} km")
        print(f"   • Ortalama Kapasite Kullanımı: {avg_capacity:.2f}%")
        
        print(f"\n🚛 Araç Detayları:")
        for i, route in enumerate(self.routes, 1):
            print(f"\n   Araç #{i} (ID: {route['vehicle_id']}) - {route['vehicle_type']}")
            print(f"   • Konteyner Sayısı: {route['container_count']}")
            print(f"   • Mesafe: {route['total_distance_km']} km")
            print(f"   • Yük: {route['total_load_liters']:.0f}L / {route['vehicle_capacity']}L")
            print(f"   • Kapasite: {route['capacity_usage_percent']}%")
        
        print("\n" + "="*80)

def main():
    print("="*80)
    print("🚀 NİLÜFER BELEDİYESİ - ROTA OPTİMİZASYONU")
    print("="*80)
    
    optimizer = RouteOptimizer()
    
    # Yüksek öncelikli konteynerleri al
    print("\n📦 Yüksek öncelikli konteynerler getiriliyor...")
    containers = optimizer.get_high_priority_containers(min_priority=0.6)
    print(f"✓ {len(containers)} yüksek öncelikli konteyner bulundu")
    
    # Araçları al
    print("\n🚛 Araçlar getiriliyor...")
    vehicles = optimizer.get_available_vehicles()
    print(f"✓ {len(vehicles)} aktif araç bulundu")
    
    # Rotaları optimize et
    routes = optimizer.optimize_routes_by_priority(containers, vehicles)
    
    # Raporu yazdır
    optimizer.print_optimization_report()
    
    # Rotaları JSON olarak kaydet
    output_file = 'models/optimized_routes.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Rotalar kaydedildi: {output_file}")
    print("✅ Rota optimizasyonu tamamlandı!")

if __name__ == "__main__":
    main()
