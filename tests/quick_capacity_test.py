from route_optimizer import RouteOptimizer

o = RouteOptimizer()
c = o.get_high_priority_containers(0.6)
v = o.get_available_vehicles()
print(f"\n{len(c)} konteyner, {len(v)} arac")
r = o.optimize_routes_by_priority(c, v)

print(f"\nSONUC: {len(r)} rota olusturuldu\n")
for route in r[:10]:
    print(f"Arac {route['vehicle_id']}: {route['container_count']} konteyner, {route['total_distance_km']} km")

avg = sum(ro['container_count'] for ro in r) / len(r)
print(f"\nOrtalama: {avg:.1f} konteyner/arac")
