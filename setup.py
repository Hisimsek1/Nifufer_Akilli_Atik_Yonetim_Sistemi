"""
Kolay Kurulum ve Çalıştırma Scripti
Nilüfer Belediyesi - Akıllı Atık Yönetim Sistemi
"""

import os
import sys
import subprocess

def print_header(title):
    """Başlık yazdır"""
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60 + "\n")

def check_python():
    """Python versiyonunu kontrol et"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ gerekli!")
        print(f"   Mevcut: Python {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_dependencies():
    """Bağımlılıkları yükle"""
    print("\n📦 Bağımlılıklar yükleniyor...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Tüm bağımlılıklar yüklendi")
        return True
    except Exception as e:
        print(f"❌ Bağımlılık yükleme hatası: {e}")
        return False

def setup_database():
    """Veritabanını hazırla"""
    print("\n💾 SQLite veritabanı hazırlanıyor...")
    
    # SQLite kullanıyoruz, setup gerekmez
    if os.path.exists("nilufer_waste.db"):
        print("✓ Veritabanı dosyası mevcut")
        choice = input("  Yeniden oluştur? (e/h): ").lower()
        if choice != 'e':
            return True
        os.remove("nilufer_waste.db")
    
    try:
        subprocess.check_call([sys.executable, "init_database.py"])
        print("✓ Veritabanı oluşturuldu")
        return True
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return False

def load_data():
    """Veri yükle"""
    print("\n📊 Gerçek veriler yükleniyor...")
    try:
        subprocess.check_call([sys.executable, "load_data_sqlite.py"])
        print("✓ Veriler yüklendi")
        return True
    except Exception as e:
        print(f"❌ Veri yükleme hatası: {e}")
        return False

def train_model():
    """Model eğit"""
    print("\n🤖 AI modeli eğitiliyor...")
    
    if os.path.exists("models/fill_predictor.pkl"):
        print("✓ Model dosyası mevcut")
        choice = input("  Yeniden eğit? (e/h): ").lower()
        if choice != 'e':
            return True
    
    try:
        subprocess.check_call([sys.executable, "train_sqlite.py"])
        print("✓ Model eğitildi")
        return True
    except Exception as e:
        print(f"❌ Model eğitim hatası: {e}")
        return False

def start_server():
    """Sunucuyu başlat"""
    print("\n🚀 Backend sunucusu başlatılıyor...")
    print("\n" + "=" * 60)
    print("SUNUCU BAŞLATILIYOR".center(60))
    print("=" * 60)
    print("\n📌 URL'ler:")
    print("   • Vatandaş Paneli: http://localhost:5000/")
    print("   • Admin Paneli: http://localhost:5000/admin")
    print("\n⚠️  Durdurmak için: Ctrl+C\n")
    print("=" * 60 + "\n")
    
    try:
        subprocess.call([sys.executable, "app_sqlite.py"])
    except KeyboardInterrupt:
        print("\n\n✓ Sunucu durduruldu")

def main():
    """Ana kurulum fonksiyonu"""
    print_header("NİLÜFER BELEDİYESİ")
    print("Akıllı Atık Yönetim Sistemi - Kurulum".center(60))
    
    # Adım 1: Python kontrolü
    if not check_python():
        sys.exit(1)
    
    # Adım 2: Bağımlılıklar
    if not install_dependencies():
        sys.exit(1)
    
    # Adım 3: Veritabanı
    if not setup_database():
        sys.exit(1)
    
    # Adım 4: Veri yükleme
    if not load_data():
        sys.exit(1)
    
    # Adım 5: Model eğitimi
    if not train_model():
        print("⚠️  Model eğitilemedi ama devam edebilirsiniz")
    
    # Adım 6: Sunucu başlat
    print_header("KURULUM TAMAMLANDI!")
    choice = input("Sunucuyu başlatmak ister misiniz? (e/h): ").lower()
    
    if choice == 'e':
        start_server()
    else:
        print("\n✓ Kurulum tamamlandı!")
        print("\nSunucuyu manuel başlatmak için:")
        print("  python app_sqlite.py")

if __name__ == "__main__":
    main()
