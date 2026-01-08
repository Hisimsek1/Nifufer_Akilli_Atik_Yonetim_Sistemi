"""
ROTA OPTİMİZASYONU TEST - KAPASİTE KONTROLÜ
Bir aracın kaç konteyner aldığını kontrol et
"""

import sqlite3
from route_optimizer import RouteOptimizer

def test_route_capacity():
    print("="*80)
    print("ROTA OPTIMIZASYONU KAPASITE TESTI")
    print("="*80)
    
    optimizer = RouteOptimizer()
    
    # Yüksek öncelikli konteynerleri al
    print("\nKonteyner verileri aliniyor...")
    containers = optimizer.get_high_priority_containers(min_priority=0.6)
    print(f"OK {len(containers)} yuksek oncelikli konteyner bulundu")
    
    # Araçları al
    print("\nArac verileri aliniyor...")
    vehicles = optimizer.get_available_vehicles()
    print(f"OK {len(vehicles)} aktif arac bulundu")
    
    # Araç bilgilerini göster
    print("\nARAC KAPASITELERI:")
    print("-" * 80)
    for v in vehicles[:5]:  # İlk 5 aracı göster
        print(f"  Araç {v['vehicle_id']}: {v['vehicle_type']} - {v['capacity_liters']/1000:.1f} ton ({v['capacity_liters']:.0f} litre)")
    
    # Ortalama konteyner doluluk ve kapasite
    avg_fill = sum(c['fill_level'] for c in containers) / len(containers)
    avg_capacity = sum(c['capacity_liters'] for c in containers) / len(containers)
    avg_load = avg_fill * avg_capacity
    
    print(f"\nKONTEYNER ISTATISTIKLERI:")
    print("-" * 80)
    print(f"  Ortalama doluluk: {avg_fill*100:.1f}%")
    print(f"  Ortalama kapasite: {avg_capacity:.0f} litre")
    print(f"  Ortalama yuk: {avg_load:.0f} litre/konteyner")
    
    # Rotaları optimize et
    print("\nRotalar optimize ediliyor...")
    routes = optimizer.optimize_routes_by_priority(containers, vehicles)
    
    print(f"\nOK {len(routes)} rota olusturuldu")
    
    # Her rotayı analiz et
    print("\nROTA DETAYLARI:")
    print("="*80)
    
    for idx, route in enumerate(routes[:10], 1):  # İlk 10 rotayı göster
        print(f"\nARAC #{route['vehicle_id']} - {route['vehicle_type']}")
        print("-" * 80)
        print(f"  Konteyner Sayisi: {route['container_count']}")
        print(f"  Toplam Yuk: {route['total_load_liters']:.0f}L")
        print(f"  Arac Kapasitesi: {route['vehicle_capacity_liters']:.0f}L")
        print(f"  Kapasite Kullanimi: {route['capacity_usage_percent']}%")
        print(f"  Toplam Mesafe: {route['total_distance_km']} km")
        
        # Konteyner başına ortalama yük
        avg_per_container = route['total_load_liters'] / route['container_count'] if route['container_count'] > 0 else 0
        print(f"  Konteyner basina ort. yuk: {avg_per_container:.0f}L")
        
        # Mantık kontrolü
        if route['container_count'] <= 6:
            print(f"  UYARI: Sadece {route['container_count']} konteyner - Cok az!")
        elif route['container_count'] >= 25:
            print(f"  IYI: {route['container_count']} konteyner - Mantikli")
        else:
            print(f"  NORMAL: {route['container_count']} konteyner")
    
    # Genel istatistikler
    total_containers_assigned = sum(r['container_count'] for r in routes)
    avg_containers_per_route = total_containers_assigned / len(routes) if len(routes) > 0 else 0
    
    print("\n" + "="*80)
    print("GENEL ISTATISTIKLER")
    print("="*80)
    print(f"  Toplam rota sayisi: {len(routes)}")
    print(f"  Atanan konteyner: {total_containers_assigned}")
    print(f"  Kalan konteyner: {len(containers) - total_containers_assigned}")
    print(f"  Rota basina ort. konteyner: {avg_containers_per_route:.1f}")
    print(f"  Toplam mesafe: {sum(r['total_distance_km'] for r in routes):.1f} km")
    
    if avg_containers_per_route < 10:
        print(f"\n  SORUN TESPIT EDILDI!")
        print(f"     Her arac ortalama {avg_containers_per_route:.1f} konteyner aliyor.")
        print(f"     Bu cok az! Bir kamyon normalde 25-35 konteyner alabilir.")
        print(f"\n  COZUM: RouteOptimizer'da konteyner sayisi limiti eklendi (30 konteyner)")
    else:
        print(f"\n  SONUC: Kapasite mantikli gorunuyor!")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_route_capacity()
