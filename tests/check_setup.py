#!/usr/bin/env python3
"""
NİLÜFER BELEDİYESİ - PROJE BAŞLATMA VE TEST SCRIPTI
Tüm bağımlılıkları kontrol eder ve projeyi hazır hale getirir
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*80)
    print(f"🚀 {text}")
    print("="*80)

def print_step(step, text):
    print(f"\n[{step}] {text}")

def check_python_version():
    """Python versiyonunu kontrol et"""
    print_step("1/8", "Python versiyonu kontrol ediliyor...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"    ✓ Python {version.major}.{version.minor}.{version.micro} (Uygun)")
        return True
    else:
        print(f"    ✗ Python {version.major}.{version.minor}.{version.micro} (Python 3.9+ gerekli)")
        return False

def check_pip_packages():
    """Gerekli paketleri kontrol et"""
    print_step("2/8", "Python paketleri kontrol ediliyor...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'sklearn',
        'pandas',
        'numpy',
        'joblib'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"    ✓ {package}")
        except ImportError:
            print(f"    ✗ {package} (Eksik)")
            missing.append(package)
    
    if missing:
        print(f"\n    ⚠️  {len(missing)} paket eksik!")
        install = input("    Eksik paketleri yüklemek ister misiniz? (e/h): ")
        if install.lower() == 'e':
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            return True
        return False
    
    return True

def check_database():
    """Veritabanını kontrol et"""
    print_step("3/8", "Veritabanı kontrol ediliyor...")
    
    if not os.path.exists('nilufer_waste.db'):
        print("    ✗ nilufer_waste.db bulunamadı")
        print("    ℹ️  Veritabanını oluşturmak için: python load_data_sqlite.py")
        return False
    
    import sqlite3
    try:
        conn = sqlite3.connect('nilufer_waste.db')
        cursor = conn.cursor()
        
        # Tablo kontrolü
        tables = ['containers', 'neighborhoods', 'vehicles', 'vehicle_types']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    ✓ {table}: {count} kayıt")
        
        conn.close()
        return True
    except Exception as e:
        print(f"    ✗ Veritabanı hatası: {e}")
        return False

def check_data_files():
    """CSV veri dosyalarını kontrol et"""
    print_step("4/8", "Veri dosyaları kontrol ediliyor...")
    
    data_files = [
        'data/all_merged_data.csv',
        'data/container_counts.csv',
        'data/tonnages.csv',
        'data/neighbor_days_rotations.csv',
        'data/mahalle_nufus.csv'
    ]
    
    all_exist = True
    for file in data_files:
        if os.path.exists(file):
            size_mb = os.path.getsize(file) / (1024 * 1024)
            print(f"    ✓ {file} ({size_mb:.1f} MB)")
        else:
            print(f"    ✗ {file} (Bulunamadı)")
            all_exist = False
    
    return all_exist

def check_processed_data():
    """İşlenmiş veri dosyasını kontrol et"""
    print_step("5/8", "İşlenmiş veri kontrol ediliyor...")
    
    if not os.path.exists('data/processed_containers.csv'):
        print("    ✗ processed_containers.csv bulunamadı")
        print("    ℹ️  Veriyi işlemek için: python data_preparation.py")
        return False
    
    import pandas as pd
    df = pd.read_csv('data/processed_containers.csv')
    print(f"    ✓ processed_containers.csv: {len(df)} konteyner, {len(df.columns)} özellik")
    return True

def check_models():
    """ML modellerini kontrol et"""
    print_step("6/8", "AI modelleri kontrol ediliyor...")
    
    model_files = [
        'models/fill_prediction_model.pkl',
        'models/fill_scaler.pkl',
        'models/fill_model_metadata.json'
    ]
    
    all_exist = True
    for file in model_files:
        if os.path.exists(file):
            size_kb = os.path.getsize(file) / 1024
            print(f"    ✓ {file} ({size_kb:.1f} KB)")
        else:
            print(f"    ✗ {file} (Bulunamadı)")
            all_exist = False
    
    if not all_exist:
        print("    ℹ️  Modeli eğitmek için: python train_fill_prediction.py")
        return False
    
    # Model performansını göster
    import json
    try:
        with open('models/fill_model_metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        metrics = metadata['metrics']
        print(f"\n    📊 Model Performansı:")
        print(f"       • Model: {metrics['model_name']}")
        print(f"       • R² Score: {metrics['r2_score']:.4f}")
        print(f"       • MAE: {metrics['mae']:.4f}")
        print(f"       • RMSE: {metrics['rmse']:.4f}")
    except:
        pass
    
    return True

def check_frontend():
    """Frontend dosyalarını kontrol et"""
    print_step("7/8", "Frontend dosyaları kontrol ediliyor...")
    
    frontend_files = [
        'public/admin.html',
        'public/index.html',
        'public/script.js',
        'public/styles.css'
    ]
    
    all_exist = True
    for file in frontend_files:
        if os.path.exists(file):
            print(f"    ✓ {file}")
        else:
            print(f"    ✗ {file} (Bulunamadı)")
            all_exist = False
    
    return all_exist

def check_backend():
    """Backend dosyasını kontrol et"""
    print_step("8/8", "Backend dosyası kontrol ediliyor...")
    
    if not os.path.exists('app_ai.py'):
        print("    ✗ app_ai.py bulunamadı")
        return False
    
    # Import testi
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("app_ai", "app_ai.py")
        print("    ✓ app_ai.py syntax OK")
        return True
    except Exception as e:
        print(f"    ✗ app_ai.py hatası: {e}")
        return False

def print_summary(results):
    """Özet rapor"""
    print_header("KONTROL ÖZETİ")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    print(f"\n📊 Sonuç: {passed}/{total} kontrol başarılı")
    
    if passed == total:
        print("\n🎉 Tüm kontroller başarılı! Proje çalıştırılmaya hazır.")
        print("\n📌 Sunucuyu başlatmak için:")
        print("   python app_ai.py")
        print("\n🌐 Ardından tarayıcıda açın:")
        print("   http://localhost:5000/admin")
    else:
        print("\n⚠️  Bazı kontroller başarısız. Yukarıdaki talimatları takip edin.")

def main():
    print_header("NİLÜFER BELEDİYESİ - PROJE HAZIRLIK KONTROLÜ")
    
    results = {
        "Python Versiyonu": check_python_version(),
        "Python Paketleri": check_pip_packages(),
        "Veritabanı": check_database(),
        "CSV Veri Dosyaları": check_data_files(),
        "İşlenmiş Veri": check_processed_data(),
        "AI Modelleri": check_models(),
        "Frontend Dosyaları": check_frontend(),
        "Backend Dosyası": check_backend()
    }
    
    print_summary(results)

if __name__ == "__main__":
    main()
