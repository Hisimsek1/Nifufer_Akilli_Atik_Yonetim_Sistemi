from route_optimizer import RouteOptimizer

o = RouteOptimizer()
c = o.get_high_priority_containers(0.6)
v = o.get_available_vehicles()
r = o.optimize_routes_by_priority(c, v)

print(f"\n{len(r)} ROTA OLUSTURULDU:")
print("-" * 50)
for ro in r:
    print(f"Arac {ro['vehicle_id']:2d}: {ro['container_count']:2d} konteyner, {ro['total_distance_km']:6.2f} km")

bos = [ro for ro in r if ro['container_count'] == 0]
print(f"\nBos arac sayisi: {len(bos)}")

total = sum(ro['container_count'] for ro in r)
print(f"Toplam konteyner: {total} / {len(c)}")
print(f"Ortalama: {total / len(r):.1f} konteyner/arac")

# En çok ve en az alan araçlar
if r:
    max_route = max(r, key=lambda x: x['container_count'])
    min_route = min(r, key=lambda x: x['container_count'])
    print(f"\nEn cok: Arac {max_route['vehicle_id']} -> {max_route['container_count']} konteyner")
    print(f"En az: Arac {min_route['vehicle_id']} -> {min_route['container_count']} konteyner")
