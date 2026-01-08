"""
NİLÜFER BELEDİYESİ - PROFESYONEL ML ENTEGRELİ API
Flask Backend with AI-Powered Optimization
"""

import joblib
import json
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import sys
sys.path.append('.')
from route_optimizer import RouteOptimizer

app = Flask(__name__, static_folder='public')
CORS(app)

# Modelleri yükle
try:
    fill_prediction_model = joblib.load('models/fill_prediction_model.pkl')
    fill_scaler = joblib.load('models/fill_scaler.pkl')
    
    with open('models/fill_model_metadata.json', 'r', encoding='utf-8') as f:
        model_metadata = json.load(f)
    
    print("✅ AI Modelleri başarıyla yüklendi!")
    print(f"   Model: {model_metadata['metrics']['model_name']}")
    print(f"   R² Score: {model_metadata['metrics']['r2_score']:.4f}")
    print(f"   MAE: {model_metadata['metrics']['mae']:.4f}")
    AI_ENABLED = True
except Exception as e:
    print(f"⚠️ AI Modelleri yüklenemedi: {e}")
    print("   Klasik mod kullanılacak.")
    AI_ENABLED = False

def get_db_connection():
    conn = sqlite3.connect('nilufer_waste.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/admin')
def admin():
    return app.send_static_file('admin.html')

# Auth endpoints (demo - production'da JWT kullan)
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Kullanıcı girişi (demo)"""
    try:
        data = request.get_json()
        tc_number = data.get('tc_number', '')
        password = data.get('password', '')
        
        # Demo için basit kontrol (production'da hash + database)
        if tc_number and password:
            return jsonify({
                'success': True,
                'message': 'Giriş başarılı',
                'user': {
                    'tc_number': tc_number,
                    'name': 'Demo Kullanıcı',
                    'phone': '555-123-4567',
                    'role': 'user'
                },
                'token': 'demo_token_12345'  # Production'da JWT
            })
        else:
            return jsonify({
                'success': False,
                'error': 'TC kimlik no ve şifre gerekli'
            }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Kullanıcı kaydı (demo)"""
    try:
        data = request.get_json()
        name = data.get('name', '')
        tc_number = data.get('tc_number', '')
        phone = data.get('phone', '')
        password = data.get('password', '')
        
        # Demo için basit kontrol
        if name and tc_number and password:
            return jsonify({
                'success': True,
                'message': 'Kayıt başarılı! Giriş yapabilirsiniz.',
                'user': {
                    'name': name,
                    'tc_number': tc_number,
                    'phone': phone,
                    'role': 'user'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ad, TC kimlik no ve şifre gerekli'
            }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/containers')
def get_containers():
    """Tüm konteynerleri getir"""
    conn = get_db_connection()
    containers = conn.execute('''
        SELECT c.*, n.neighborhood_name, n.population 
        FROM containers c 
        JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in containers])

@app.route('/api/predict_fill/<int:container_id>')
def predict_fill_level(container_id):
    """Bir konteyner için doluluk tahmini yap"""
    if not AI_ENABLED:
        return jsonify({'error': 'AI model not loaded'}), 500
    
    conn = get_db_connection()
    container = conn.execute('''
        SELECT c.*, n.population
        FROM containers c
        JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
        WHERE c.container_id = ?
    ''', (container_id,)).fetchone()
    conn.close()
    
    if not container:
        return jsonify({'error': 'Container not found'}), 404
    
    # Feature extraction (data_preparation.py ile aynı)
    last_collection = datetime.strptime(container['last_collection_date'], '%Y-%m-%d')
    days_since = (datetime.now() - last_collection).days
    
    # Özellikleri hazırla
    features = {
        'days_since_collection': days_since,
        'day_of_week': datetime.now().weekday(),
        'month': datetime.now().month,
        'is_weekend': 1 if datetime.now().weekday() >= 5 else 0,
        'collection_days_per_week': 3,  # Varsayılan
        'type_encoded': 1 if '400' in container['container_type'] else 2,
        'capacity_category': 2,  # medium
        'population_density': 5.0,  # Varsayılan
        'current_fill_level': container['current_fill_level']
    }
    
    # Tahmin yap
    X = np.array([[
        features['days_since_collection'],
        features['day_of_week'],
        features['month'],
        features['is_weekend'],
        features['collection_days_per_week'],
        features['type_encoded'],
        features['capacity_category'],
        features['population_density'],
        features['current_fill_level']
    ]])
    
    prediction = fill_prediction_model.predict(X)[0]
    prediction = np.clip(prediction, 0, 0.95)
    
    return jsonify({
        'container_id': container_id,
        'current_fill': float(container['current_fill_level']),
        'predicted_fill': float(prediction),
        'model': model_metadata['metrics']['model_name'],
        'confidence': float(1 - model_metadata['metrics']['mae'])
    })

@app.route('/api/optimize-routes', methods=['POST'])
@app.route('/api/fleet/optimize-routes', methods=['GET', 'POST'])
def optimize_routes():
    """AI ile rotaları optimize et"""
    try:
        # Parametreler - GET ve POST için farklı
        if request.method == 'GET':
            min_priority = float(request.args.get('min_priority', 0.6))
        else:
            data = request.get_json() or {}
            min_priority = data.get('min_priority', 0.6)
        
        print(f"\n🚀 Rota optimizasyonu başlıyor (min_priority={min_priority})...")
        
        # Route Optimizer oluştur
        optimizer = RouteOptimizer()
        
        # Yüksek öncelikli konteynerleri al
        containers = optimizer.get_high_priority_containers(min_priority=min_priority)
        print(f"   ✓ {len(containers)} konteyner bulundu")
        
        # Araçları al
        vehicles = optimizer.get_available_vehicles()
        print(f"   ✓ {len(vehicles)} araç bulundu")
        
        # Rotaları optimize et
        routes = optimizer.optimize_routes_by_priority(containers, vehicles)
        print(f"   ✓ {len(routes)} rota oluşturuldu")
        
        # İstatistikleri hesapla
        total_containers = sum(r.get('container_count', 0) for r in routes)
        total_distance = sum(r.get('total_distance_km', 0) for r in routes)
        total_time = sum(r.get('total_time_hours', 0) for r in routes)
        avg_capacity = np.mean([r.get('capacity_usage', 0) for r in routes]) if routes else 0
        
        return jsonify({
            'success': True,
            'routes': routes,
            'summary': {
                'total_routes': len(routes),
                'assigned_containers': total_containers,
                'total_distance_km': round(total_distance, 2),
                'total_time_hours': round(total_time, 2),
                'avg_capacity_usage': round(avg_capacity, 2)
            },
            'ai_enabled': AI_ENABLED,
            'model_info': model_metadata['metrics'] if AI_ENABLED else None
        })
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model_info')
def model_info():
    """Model bilgilerini getir"""
    if not AI_ENABLED:
        return jsonify({'ai_enabled': False})
    
    return jsonify({
        'ai_enabled': True,
        'model_name': model_metadata['metrics']['model_name'],
        'r2_score': model_metadata['metrics']['r2_score'],
        'mae': model_metadata['metrics']['mae'],
        'rmse': model_metadata['metrics']['rmse'],
        'train_date': model_metadata['metrics']['timestamp'],
        'feature_importance': model_metadata['feature_importance']
    })

@app.route('/api/neighborhoods')
def get_neighborhoods():
    """Tüm mahalleleri getir"""
    conn = get_db_connection()
    neighborhoods = conn.execute('SELECT * FROM neighborhoods').fetchall()
    conn.close()
    return jsonify([dict(row) for row in neighborhoods])

@app.route('/api/vehicles')
def get_vehicles():
    """Tüm araçları getir"""
    conn = get_db_connection()
    vehicles = conn.execute('''
        SELECT v.*, vt.type_name, vt.capacity_tons
        FROM vehicles v
        JOIN vehicle_types vt ON v.type_id = vt.type_id
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in vehicles])

@app.route('/dashboard/stats')
def dashboard_stats():
    """Dashboard istatistikleri"""
    conn = get_db_connection()
    
    total_containers = conn.execute('SELECT COUNT(*) as count FROM containers').fetchone()['count']
    total_vehicles = conn.execute('SELECT COUNT(*) as count FROM vehicles WHERE status="active"').fetchone()['count']
    total_neighborhoods = conn.execute('SELECT COUNT(*) as count FROM neighborhoods').fetchone()['count']
    
    avg_fill = conn.execute('SELECT AVG(current_fill_level) as avg FROM containers').fetchone()['avg']
    high_priority = conn.execute('SELECT COUNT(*) as count FROM containers WHERE current_fill_level >= 0.7').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_containers': total_containers,
        'full_containers': high_priority,
        'fill_rate': avg_fill if avg_fill else 0,
        'total_vehicles': total_vehicles,
        'neighborhoods': total_neighborhoods,
        'avg_fill_level': round(avg_fill * 100, 1) if avg_fill else 0,
        'high_priority_containers': high_priority
    })

@app.route('/containers/all')
def containers_all():
    """Tüm konteynerleri detaylı getir"""
    conn = get_db_connection()
    containers = conn.execute('''
        SELECT c.*, n.neighborhood_name, n.population 
        FROM containers c 
        JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
        ORDER BY c.current_fill_level DESC
    ''').fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in containers])

if __name__ == '__main__':
    print("="*80)
    print("🚀 NİLÜFER BELEDİYESİ - AI-POWERED ATIK YÖNETİM SİSTEMİ")
    print("="*80)
    print(f"\n📊 AI Durum: {'✅ Aktif' if AI_ENABLED else '⚠️ Devre Dışı'}")
    if AI_ENABLED:
        print(f"   Model: {model_metadata['metrics']['model_name']}")
        print(f"   Performans: R²={model_metadata['metrics']['r2_score']:.4f}")
    print("\n🌐 Sunucu Başlatılıyor...")
    print("   Admin Panel: http://localhost:5000/admin")
    print("   Ana Sayfa: http://localhost:5000/")
    print("="*80 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
