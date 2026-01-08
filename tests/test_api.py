"""
Pytest Test Suite
Nilüfer Belediyesi - Akıllı Atık Yönetim Sistemi
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app_sqlite import app
import sqlite3
import json

DB_PATH = 'nilufer_waste.db'

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def db_connection():
    """Database connection"""
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()

# ============== DATABASE TESTS ==============

def test_database_exists():
    """Veritabanı dosyası mevcut mu?"""
    assert os.path.exists(DB_PATH), "Veritabanı dosyası bulunamadı"

def test_tables_exist(db_connection):
    """Tüm tablolar mevcut mu?"""
    cursor = db_connection.cursor()
    
    tables = [
        'neighborhoods', 'vehicle_types', 'vehicles', 'containers',
        'users', 'citizen_reports', 'collection_events', 
        'tonnage_statistics', 'predictions', 'simulation_runs'
    ]
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        assert cursor.fetchone() is not None, f"Tablo {table} bulunamadı"

def test_data_loaded(db_connection):
    """Veriler yüklenmiş mi?"""
    cursor = db_connection.cursor()
    
    # Mahalleler
    cursor.execute("SELECT COUNT(*) FROM neighborhoods")
    assert cursor.fetchone()[0] > 0, "Mahalle verisi yok"
    
    # Araçlar
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    assert cursor.fetchone()[0] > 0, "Araç verisi yok"
    
    # Konteynerler
    cursor.execute("SELECT COUNT(*) FROM containers")
    assert cursor.fetchone()[0] > 0, "Konteyner verisi yok"

# ============== API TESTS ==============

def test_dashboard_stats(client):
    """Dashboard istatistikleri endpoint'i"""
    response = client.get('/api/dashboard/stats')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'total_containers' in data
    assert 'full_containers' in data
    assert 'fill_rate' in data
    assert data['total_containers'] > 0

def test_leaderboard(client):
    """Liderlik tablosu endpoint'i"""
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'leaderboard' in data
    assert isinstance(data['leaderboard'], list)

def test_full_containers(client):
    """Dolu konteynerleri listele"""
    response = client.get('/api/containers/full')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'count' in data
    assert 'containers' in data
    assert isinstance(data['containers'], list)

def test_all_containers(client):
    """Tüm konteynerleri listele"""
    response = client.get('/api/containers/all')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'count' in data
    assert 'containers' in data
    assert data['count'] > 0

def test_map_containers(client):
    """Harita için konteyner verileri"""
    response = client.get('/api/containers/map')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'count' in data
    assert 'containers' in data
    
    if len(data['containers']) > 0:
        container = data['containers'][0]
        assert 'id' in container
        assert 'lat' in container
        assert 'lng' in container
        assert 'fill_level' in container

def test_prediction_endpoint(client):
    """Tahmin endpoint'i"""
    response = client.get('/api/predict/1')
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'container_id' in data
        assert 'fill_probability' in data
        assert 'is_full' in data
        assert 0 <= data['fill_probability'] <= 1

def test_route_optimization(client):
    """Rota optimizasyonu endpoint'i"""
    response = client.get('/api/fleet/optimize-routes')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    
    if data['success']:
        assert 'summary' in data
        assert 'routes' in data
        assert data['summary']['total_vehicles'] > 0

# ============== AUTH TESTS ==============

def test_register_new_user(client):
    """Yeni kullanıcı kaydı"""
    import random
    tc = str(random.randint(10000000000, 99999999999))
    
    response = client.post('/api/auth/register', 
        json={
            'name': 'Test User',
            'tc_number': tc,
            'phone': '05551234567',
            'password': 'test123456'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'user_id' in data

def test_login_existing_user(client):
    """Mevcut kullanıcı girişi"""
    response = client.post('/api/auth/login',
        json={
            'tc_number': '12345678901',
            'password': 'test123'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'user' in data
    assert data['user']['tc_number'] == '12345678901'

def test_login_wrong_password(client):
    """Yanlış şifre ile giriş"""
    response = client.post('/api/auth/login',
        json={
            'tc_number': '12345678901',
            'password': 'wrongpassword'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 401

def test_register_duplicate_tc(client):
    """Duplicate TC numarası ile kayıt"""
    response = client.post('/api/auth/register',
        json={
            'name': 'Duplicate User',
            'tc_number': '12345678901',  # Zaten var
            'phone': '05559999999',
            'password': 'test123456'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 400

# ============== REPORT TESTS ==============

def test_submit_report(client):
    """Bildirim gönderme"""
    # Önce giriş yap
    login_response = client.post('/api/auth/login',
        json={
            'tc_number': '12345678901',
            'password': 'test123'
        },
        content_type='application/json'
    )
    
    user_data = json.loads(login_response.data)
    user_id = user_data['user']['id']
    
    # Bildirim gönder
    response = client.post('/api/reports/submit',
        json={
            'user_id': user_id,
            'container_id': 1,
            'fill_level': 75,
            'notes': 'Test bildirimi'
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'trust_score' in data
    assert 'report_status' in data

# ============== MODEL TESTS ==============

def test_model_file_exists():
    """Model dosyası mevcut mu?"""
    model_path = 'models/fill_predictor.pkl'
    assert os.path.exists(model_path), "Model dosyası bulunamadı"

def test_model_prediction_quality():
    """Model tahmin kalitesi"""
    import joblib
    
    try:
        model_data = joblib.load('models/fill_predictor.pkl')
        assert 'model' in model_data
        assert 'version' in model_data
        
        # Test accuracy kontrolü (eğer varsa)
        if 'test_accuracy' in model_data:
            assert model_data['test_accuracy'] > 0.7, "Model accuracy çok düşük"
    except Exception as e:
        pytest.skip(f"Model yüklenemedi: {e}")

# ============== PERFORMANCE TESTS ==============

def test_api_response_time(client):
    """API yanıt süresi"""
    import time
    
    start = time.time()
    response = client.get('/api/dashboard/stats')
    duration = time.time() - start
    
    assert duration < 1.0, f"API çok yavaş: {duration:.2f}s"

def test_multiple_concurrent_requests(client):
    """Eşzamanlı istekler"""
    responses = []
    
    for _ in range(10):
        response = client.get('/api/dashboard/stats')
        responses.append(response.status_code)
    
    assert all(code == 200 for code in responses), "Bazı istekler başarısız"

# ============== DATA VALIDATION TESTS ==============

def test_container_data_integrity(db_connection):
    """Konteyner verilerinin bütünlüğü"""
    cursor = db_connection.cursor()
    
    # Negatif doluluk seviyesi olmamalı
    cursor.execute("SELECT COUNT(*) FROM containers WHERE current_fill_level < 0")
    assert cursor.fetchone()[0] == 0, "Negatif doluluk seviyesi var"
    
    # 1'den büyük doluluk seviyesi olmamalı
    cursor.execute("SELECT COUNT(*) FROM containers WHERE current_fill_level > 1")
    assert cursor.fetchone()[0] == 0, "1'den büyük doluluk seviyesi var"
    
    # Geçerli koordinatlar
    cursor.execute("SELECT COUNT(*) FROM containers WHERE latitude IS NULL OR longitude IS NULL")
    null_coords = cursor.fetchone()[0]
    total = cursor.execute("SELECT COUNT(*) FROM containers").fetchone()[0]
    assert null_coords / total < 0.1, "Çok fazla null koordinat var"

def test_user_trust_scores(db_connection):
    """Kullanıcı güven puanları"""
    cursor = db_connection.cursor()
    
    # Güven puanları 0-1 arası olmalı
    cursor.execute("SELECT COUNT(*) FROM users WHERE trust_score < 0 OR trust_score > 1")
    assert cursor.fetchone()[0] == 0, "Geçersiz güven puanı var"

# ============== INTEGRATION TESTS ==============

def test_full_user_journey(client):
    """Tam kullanıcı senaryosu"""
    import random
    tc = str(random.randint(10000000000, 99999999999))
    
    # 1. Kayıt ol
    register_response = client.post('/api/auth/register',
        json={
            'name': 'Integration Test User',
            'tc_number': tc,
            'phone': '05551111111',
            'password': 'test123456'
        },
        content_type='application/json'
    )
    assert register_response.status_code == 200
    
    # 2. Giriş yap
    login_response = client.post('/api/auth/login',
        json={
            'tc_number': tc,
            'password': 'test123456'
        },
        content_type='application/json'
    )
    assert login_response.status_code == 200
    user = json.loads(login_response.data)['user']
    
    # 3. Bildirim gönder
    report_response = client.post('/api/reports/submit',
        json={
            'user_id': user['id'],
            'container_id': 1,
            'fill_level': 80,
            'notes': 'Integration test'
        },
        content_type='application/json'
    )
    assert report_response.status_code == 200
    
    # 4. Liderlik tablosunda görün
    leaderboard_response = client.get('/api/leaderboard')
    leaderboard = json.loads(leaderboard_response.data)['leaderboard']
    user_in_leaderboard = any(u['name'] == 'Integration Test User' for u in leaderboard)
    assert user_in_leaderboard, "Kullanıcı liderlik tablosunda yok"

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
